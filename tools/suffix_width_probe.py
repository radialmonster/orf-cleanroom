#!/usr/bin/env python3
"""Whole-payload candidate suffix-width scan (leads #29/#197, specs/V1.md G8).

Reads files and prints aggregate JSON only, stdlib Python 3.8+.
For each k=2..8 and stop=0,1: consume q bits opposite to stop, one stop,
then skip k suffix bits. Accept only complete tokens; q>=17 consumes no
extra bits. The exact q histogram includes all accepted tokens, including
candidate escapes. An incomplete final token is wholly unconsumed.
This is a candidate-parse comparison, not a codec selection, physical-row
measure, padding interpretation, significance test or decode. A small tail
is possible under multiple arbitrary parses; near-one tokens/pixel alone
cannot establish a code. Licence-check public inputs before measurement.
Optional fixed-token-block summaries measure within-file q0 variation. Blocks
are candidate-token intervals, not shared bit intervals or physical rows;
the histogram contains q0 counts in complete blocks, with the tail separate.
Sample IDs must be distinct positive ASCII decimals and names printable basenames.
"""
import argparse
import collections
import hashlib
import json
import os
import stat
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class

MAX_BYTES = 512 * 1024 * 1024


def scan(payload, k, stop, block_tokens=0):
    """Count complete candidate tokens without retaining suffixes or samples."""
    if k not in range(2, 9) or stop not in (0, 1):
        raise ValueError("invalid candidate")
    if not isinstance(block_tokens, int) or block_tokens < 0:
        raise ValueError("invalid block size")
    nbits = len(payload) * 8
    pos = 0
    histogram = collections.Counter()
    block_histogram = collections.Counter()
    block_n = block_q0 = 0
    flip = 0 if stop else 255
    while pos < nbits:
        start = pos
        # Find the next stop using only the unconsumed bits of each byte.
        while pos < nbits:
            shift = pos & 7
            candidate = (payload[pos >> 3] ^ flip) & (255 >> shift)
            if candidate:
                pos += (8 - shift) - candidate.bit_length()
                break
            pos += 8 - shift
        if pos + 1 + k > nbits:
            pos = start
            break
        q = pos - start
        histogram[q] += 1
        if block_tokens:
            block_n += 1
            block_q0 += q == 0
            if block_n == block_tokens:
                block_histogram[block_q0] += 1
                block_n = block_q0 = 0
        pos += 1 + k
    count = sum(histogram.values())
    result = {"k": k, "stop_bit": stop, "tokens": count,
            "q_histogram": [[q, histogram[q]] for q in sorted(histogram)],
            "q_ge_17": sum(n for q, n in histogram.items() if q >= 17),
            "bits_consumed": pos, "unconsumed_bits": nbits - pos}
    if block_tokens:
        result["q0_blocks"] = {
            "tokens_per_full_block": block_tokens,
            "full_blocks": sum(block_histogram.values()),
            "full_block_q0_histogram": [[q0, block_histogram[q0]]
                                        for q0 in sorted(block_histogram)],
            "tail_tokens": block_n, "tail_q0": block_q0}
    return result


def report(sample_id, name, path, block_tokens=0):
    if not stat.S_ISREG(os.stat(path).st_mode):
        raise ValueError("regular file required")
    with open(path, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("regular file required")
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("input too large")
    ifds = list(Tiff(data).all_ifds())
    best = max(ifds, key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError("one contiguous strip required")
    off, count = offsets[0], lengths[0]
    w, h = best[0x100][0], best[0x101][0]
    if (off < 0 or count <= 0 or off + count > len(data) or w <= 0 or h <= 0
            or size_class(count, w, h) != "variable" or best.get(0x103) != [1]):
        raise ValueError("positive variable payload with compression tag 1 required")
    payload = data[off:off + count]
    cells = []
    for stop in (0, 1):
        for k in range(2, 9):
            cell = scan(payload, k, stop, block_tokens)
            cell["tokens_per_pixel"] = cell["tokens"] / (w * h)
            cells.append(cell)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "size_class": "variable", "compression_tag": 1,
            "payload_w": w, "payload_h": h, "payload_bytes": count,
            "cells": cells}


def source_hashes():
    result = {}
    for name in ("suffix_width_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), name), "rb") as handle:
            result[name] = hashlib.sha256(handle.read()).hexdigest()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    parser.add_argument("--block-tokens", type=int, default=0,
                        help="optional q0 block size, 0 disables (default)")
    args = parser.parse_args(argv)
    if args.block_tokens < 0:
        parser.error("block token count must be nonnegative")
    ids = [entry[0] for entry in args.sample]
    try:
        invalid_ids = any(not value.isascii() or not value.isdecimal() or int(value) <= 0 for value in ids) or len(set(map(int, ids))) != len(ids)
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        parser.error("sample IDs must be distinct positive ASCII decimals")
    if any(not name or not name.isprintable() or any(c in name for c in '/\\') for _, name, _ in args.sample):
        parser.error("sample public name must be a printable basename")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path, args.block_tokens))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error):
            failures.append({"pixls_id": sample_id, "error": "invalid_or_unreadable_input"})
    print(json.dumps({"source_sha256": source_hashes(),
                      "python_version": sys.version.split()[0],
                      "samples": reports, "failures": failures},
                     indent=2, allow_nan=False))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
