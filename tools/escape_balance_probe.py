#!/usr/bin/env python3
"""Compare suffix balance before/after first candidate escape (#11).

Fixed first 262144 complete MSB-first tokens: q zeros, stop one, five suffix
bits, zero extra bits for q>=17. The first q>=17 divides the prefix; exclude
all such escapes from both groups. Report exact suffix counts and b4..b0
marginals, not significance, a decoder or escape causality. Post-escape
framing is unknown and scenes may differ across the groups. No first escape
means all ordinary tokens are before and the after group is empty. This is a
new public metric, not reproduction of historical private balance numbers.
Reads only input files and prints aggregate JSON; stdlib, Python 3.8+.
Check CC0 licences separately. Repeat --sample ID PUBLIC_NAME FILE.
The CLI returns 1 if any requested prefix is incomplete or an input fails;
all available aggregate reports and sanitized errors are still printed.
IDs that cannot be converted to integers are argument errors.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suffix_joint_probe import scan_prefix, LIMIT
from orf_signature import Tiff, size_class


def balance(histogram):
    n = sum(histogram)
    ones = [sum(c for s, c in enumerate(histogram) if (s >> bit) & 1)
            for bit in range(4, -1, -1)]
    return {"ordinary_tokens": n, "suffix_counts_0_to_31": histogram,
            "ones_b4_to_b0": ones,
            "p_one_b4_to_b0": [x / n if n else None for x in ones]}


def measure(tokens):
    histograms = [[0] * 32 for _ in range(2)]
    first = None
    escapes = 0
    for index, (q, suffix) in enumerate(tokens):
        if q >= 17:
            escapes += 1
            if first is None:
                first = index
        else:
            histograms[first is not None][suffix] += 1
    return {"first_escape_token_index_zero_based": first,
            "escape_tokens_excluded": escapes,
            "before": balance(histograms[0]), "after": balance(histograms[1])}


def report(sample_id, name, path):
    with open(path, "rb") as handle:
        data = handle.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError("requires one contiguous strip")
    off, count = offsets[0], lengths[0]
    if off < 0 or count <= 0 or off + count > len(data):
        raise ValueError("payload out of bounds")
    w, h = best[0x100][0], best[0x101][0]
    if w <= 0 or h <= 0 or size_class(count, w, h) != "variable":
        raise ValueError("requires variable-size payload")
    tokens, end = scan_prefix(data[off:off + count])
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_bytes": count,
            "payload_offset": off, "size_class": "variable",
            "requested_tokens": LIMIT, "returned_tokens": len(tokens),
            "prefix_shortfall_tokens": LIMIT - len(tokens), "bits_consumed": end,
            "statistics": measure(tokens)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    args = parser.parse_args()
    ids = [sample[0] for sample in args.sample]
    try:
        invalid_ids = any(not i.isascii() or not i.isdigit() or int(i) <= 0 for i in ids)
        distinct = len(set(map(int, ids))) == len(ids) if not invalid_ids else True
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        parser.error("sample IDs must be positive ASCII decimals")
    if not distinct:
        parser.error("sample IDs must be distinct")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "error": type(exc).__name__})
    hashes = {}
    for filename in ("escape_balance_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            hashes[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": hashes, "python_version": sys.version.split()[0],
                      "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    incomplete = any(sample["prefix_shortfall_tokens"] > 0 for sample in reports)
    return 1 if failures or incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
