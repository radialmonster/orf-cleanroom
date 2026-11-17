#!/usr/bin/env python3
"""Measure within-token suffix balance in fixed candidate-token windows (#11).

Parse from payload bit zero as q zeros, stop bit, five suffix bits, with no
extra escape skip. Indices include every complete candidate, including q>=17;
only individual q<17 tokens enter the 4x8 H-by-L table and bit counts. H is
suffix>>3 and L is suffix&7. Windows are sequential candidate indices, not
physical rows. The descriptive thresholds are not significance tests or proof
of independence, fairness, framing, or a decoder.

Discovery: four adjacent 262144-token windows starting at zero. Verification:
repeat those four, add four adjacent windows, and a 524288-token window
overlapping the first two added windows. The file is previously exposed.
Read inputs and print aggregate JSON only; verify input licence separately.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class
from suffix_joint_probe import mutual_information, scan_prefix

WINDOW = 262144


def windows(mode):
    result = [(i * WINDOW, WINDOW) for i in range(4 if mode == "discovery" else 8)]
    if mode == "verification":
        result.append((4 * WINDOW, 2 * WINDOW))
    return result


def measure(tokens, start, length):
    selected = tokens[start:start + length]
    table = [[0] * 8 for _ in range(4)]
    for q, suffix in selected:
        if q < 17:
            table[suffix >> 3][suffix & 7] += 1
    n = sum(map(sum, table))
    ones = {"b%d" % bit: sum(table[h][l] for h in range(4) for l in range(8)
                                if ((h << 3 | l) >> bit) & 1) for bit in (0, 1)}
    complete = len(selected) == length and n > 0
    mi = mutual_information(table) if complete else None
    proportions = {key: str(Fraction(value, n)) if complete else None for key, value in ones.items()}
    passes = None if not complete else (
        mi <= 0.010 and all(abs(Fraction(value, n) - Fraction(1, 2)) <= Fraction(1, 20)
                            for value in ones.values()))
    return {"start_token": start, "requested_tokens": length,
            "returned_tokens": len(selected), "escape_tokens": len(selected) - n,
            "retained_tokens": n, "joint_h_rows_l_columns": table,
            "one_counts": ones, "one_proportions_exact": proportions,
            "plugin_mi_bits": mi, "tolerance_pass": passes}


def report(sample_id, name, path, mode):
    with open(path, "rb") as handle:
        data = handle.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError("one strip required")
    off, count = offsets[0], lengths[0]
    w, h = best[0x100][0], best[0x101][0]
    if off < 0 or count <= 0 or off + count > len(data):
        raise ValueError("payload out of bounds")
    if w <= 0 or h <= 0 or size_class(count, w, h) != "variable" or best.get(0x103) != [1]:
        raise ValueError("positive variable-size payload with compression tag 1 required")
    design = windows(mode)
    requested = max(start + length for start, length in design)
    tokens, end = scan_prefix(data[off:off + count], requested)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_offset": off,
            "payload_bytes": count, "requested_scan_tokens": requested,
            "returned_tokens": len(tokens), "bits_consumed": end,
            "windows": [measure(tokens, start, length) for start, length in design]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("discovery", "verification"), required=True)
    parser.add_argument("--sample", nargs=3, required=True, metavar=("ID", "PUBLIC_NAME", "FILE"))
    args = parser.parse_args()
    sample_id, name, path = args.sample
    if not sample_id.isascii() or not sample_id.isdecimal() or int(sample_id) <= 0:
        parser.error("sample ID must be a positive ASCII decimal")
    if not name or not name.isprintable() or any(c in name for c in "/\\"):
        parser.error("public name must be a printable basename")
    try:
        result = report(sample_id, name, path, args.mode)
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
        parser.exit(1, "sample %s: %s\n" % (sample_id, type(exc).__name__))
    sources = {}
    for filename in ("suffix_balance_windows.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"mode": args.mode, "source_sha256": sources,
                      "python_version": sys.version.split()[0], "escape_extra_bits": 0,
                      "sample": result}, indent=2, allow_nan=False))
    return int(any(w["returned_tokens"] != w["requested_tokens"] for w in result["windows"]))


if __name__ == "__main__":
    sys.exit(main())
