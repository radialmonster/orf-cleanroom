#!/usr/bin/env python3
"""Q-inclusive candidate-token bridge energies for lead #32 (not a decoder).

Fixed first 262144 complete tokens, MSB-first q zeros/one/5-bit suffix,
zero extra escape bits. Omit whole 128-token blocks containing q>=17 and
incomplete tails. Evaluate u=32*q+s and zigzag(u), each in one/two lanes.
Absolute token parity is preserved. Check public CC0 input licences first.

Builds on #11, #32 and @mtakemoto's bridge-energy design (#64); original
suffix-only experiments remain unchanged. #159 tests the same readings with
predictor/preview scores; this tool uses no previews. E=A/n^3 and the exact
permutation mean N=(n+1)*V/(6*n^2), where A=sum(n*S_k-k*T)^2 and
V=n*sum(x*x)-T*T. Pool sum(E)/sum(N), never mean ratios. The null depends
on observed lane multisets. Zero null energy gives null, not zero.

These are descriptive candidate-token blocks/parity, not physical rows or
channels. Escape omission can bias selection and cannot repair uncertain
framing. Detrending removes drift; low ratios establish neither a bounded
reconstruction, significance nor historical private numerical replication.
Stdlib only; reads inputs and prints aggregates, never token/pixel arrays.
Incomplete fixed prefixes produce diagnostic failures without bridge statistics.
IDs that cannot be converted to integers are argument errors.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_joint_probe as candidate

LIMIT = 262144
BLOCK = 128
MAPPINGS = ("u32", "zigzag_u32")


class IncompletePrefix(ValueError):
    """Public counts only; never retain input bytes or a local path."""
    def __init__(self, returned, consumed, payload_bits):
        super().__init__("incomplete fixed prefix")
        self.diagnostic = {"reason": "incomplete_prefix", "requested_tokens": LIMIT,
                           "returned_tokens": returned, "token_shortfall": LIMIT - returned,
                           "consumed_bits": consumed, "payload_bits": payload_bits}


class PrivateParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, "invalid command line; use --help\n")


def mapped(q, s, mapping):
    u = 32 * q + s
    if mapping == "u32":
        return u
    if mapping == "zigzag_u32":
        return -(u // 2) - 1 if u % 2 else u // 2
    raise ValueError("unknown mapping")


def terms(values):
    """Exact integer (A,V), independently implemented from the cited definition."""
    n = len(values)
    if not n:
        raise ValueError("empty lane")
    total = sum(values)
    variance = n * sum(x * x for x in values) - total * total
    prefix = 0
    a = 0
    for k, x in enumerate(values, 1):
        prefix += x
        a += (n * prefix - k * total) ** 2
    return a, variance


def rational(value):
    return (None if value is None else
            {"numerator": value.numerator, "denominator": value.denominator,
             "approx": float(value)})


def pool(n, lanes):
    a, v = sum(t[0] for t in lanes), sum(t[1] for t in lanes)
    return {"lane_count": len(lanes), "sum_A": a, "sum_V": v,
            "zero_variance_lanes": sum(t[1] == 0 for t in lanes),
            "sum_E": rational(Fraction(a, n ** 3)),
            "sum_N": rational(Fraction((n + 1) * v, 6 * n ** 2)),
            "R_pool": rational(Fraction(6 * a, n * (n + 1) * v)) if v else None}


def aggregate(tokens):
    if len(tokens) > LIMIT or any(type(q) is not int or q < 0
                                 or type(s) is not int or not 0 <= s < 32
                                 for q, s in tokens):
        raise ValueError("invalid tokens")
    complete = len(tokens) // BLOCK
    retained = [i for i in range(complete)
                if all(q < 17 for q, _ in tokens[i * BLOCK:(i + 1) * BLOCK])]
    tail = tokens[complete * BLOCK:]
    selection = {"complete_blocks": complete, "retained_blocks": len(retained),
                 "escape_omitted_blocks": complete - len(retained),
                 "escape_omitted_tokens": (complete - len(retained)) * BLOCK,
                 "incomplete_tail_tokens": len(tail),
                 "parsed_escapes": sum(q >= 17 for q, _ in tokens),
                 "tail_escapes": sum(q >= 17 for q, _ in tail)}
    cells = []
    for mapping in MAPPINGS:
        for lane_count in (1, 2):
            n = BLOCK // lane_count
            blocks, lanes, parity = [], [], [[], []]
            for i in retained:
                block = tokens[i * BLOCK:(i + 1) * BLOCK]
                block_lanes = [terms([mapped(q, s, mapping) for q, s in block[p::lane_count]])
                               for p in range(lane_count)]
                lanes.extend(block_lanes)
                if lane_count == 2:
                    for p in range(2):
                        parity[p].append(block_lanes[p])
                blocks.append({"absolute_block_index": i,
                               "lanes_A_V": [list(t) for t in block_lanes]})
            cells.append({"mapping": mapping, "lane_count": lane_count,
                          "increments_per_lane": n, "blocks": blocks,
                          "pool": pool(n, lanes),
                          "parity_pools": [dict(absolute_parity=p, **pool(n, parity[p]))
                                           for p in range(2)] if lane_count == 2 else []})
    return {"selection": selection, "cells": cells}


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def report(sample_id, name, path):
    with open(path, "rb") as source:
        data = source.read()
    best = max(candidate.Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, sizes = best[0x111], best[0x117]
    if len(offsets) != 1 or len(sizes) != 1:
        raise ValueError("one contiguous strip required")
    off, count = offsets[0], sizes[0]
    w, h = best[0x100][0], best[0x101][0]
    if (off < 0 or count <= 0 or off + count > len(data) or w <= 0 or h <= 0
            or candidate.size_class(count, w, h) != "variable"
            or best.get(0x103) != [1]):
        raise ValueError("variable-size in-bounds payload with compression tag 1 required")
    tokens, consumed = candidate.scan_prefix(data[off:off + count], LIMIT)
    if len(tokens) != LIMIT:
        raise IncompletePrefix(len(tokens), consumed, count * 8)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_bytes": count,
            "payload_offset": off, "compression_tag": 1, "size_class": "variable",
            "requested_tokens": LIMIT, "returned_tokens": len(tokens),
            "token_shortfall": LIMIT - len(tokens), "consumed_bits": consumed,
            **aggregate(tokens)}


def main(argv=None):
    parser = PrivateParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    args = parser.parse_args(argv)
    ids = []
    for sample_id, name, _ in args.sample:
        try:
            numeric_id = int(sample_id) if sample_id.isascii() and sample_id.isdigit() else 0
        except ValueError:
            parser.error("invalid sample")
        if (numeric_id <= 0 or numeric_id in ids or not name or not name.isprintable()
                or any(c in name for c in "/\\")):
            parser.error("invalid sample")
        ids.append(numeric_id)
    samples, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            samples.append(report(int(sample_id), name, path))
        except IncompletePrefix as exc:
            failures.append({"pixls_id": int(sample_id), "category": "input_or_measurement_error",
                             **exc.diagnostic})
        except (OSError, ValueError, TypeError, KeyError, IndexError, struct.error, OverflowError):
            failures.append({"pixls_id": int(sample_id), "category": "input_or_measurement_error"})
    sources = {os.path.basename(p): file_hash(p) for p in
               (__file__, candidate.__file__, os.path.join(os.path.dirname(__file__), "orf_signature.py"))}
    print(json.dumps({"schema": "orf-lead32-q-bridge-v1", "builds_on": [11, 32, 64],
                      "python_version": sys.version.split()[0], "source_sha256": sources,
                      "settings": {"prefix_tokens": LIMIT, "block_tokens": BLOCK,
                                   "escape_extra": 0, "escape_q_min": 17,
                                   "mappings": list(MAPPINGS), "lane_counts": [1, 2],
                                   "pooling": "sum(E)/sum(N)", "null": "exact permutation mean"},
                      "samples": samples, "failures": failures}, sort_keys=True,
                     indent=2, allow_nan=False))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
