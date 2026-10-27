#!/usr/bin/env python3
"""Nominal-lattice b2 donor contingencies for lead #30; builds on #11.

Stdlib Python 3.8+. First 262144 complete candidate tokens from payload bit
zero, q zeros/one/five suffix bits, zero extra escape bits. W is measured
payload width. For lags 2W-2,2W,2W+2, split target indices into nominal
((t//W)%2,(t%W)%2) classes; count donor b2(t-lag) by target b2(t).
Omit pairs with q>=17 at either endpoint, preserving absolute indices.
Intervening escapes remain; omission cannot repair uncertain framing.
No wrapping. Emit all tables, denominators, omissions and binary Pearson.

The W lattice is not established camera rows: busy files can have more than
W tokens per row. These descriptive tables cannot establish serpentine or
other spatial layout, significance, or reproduce #30's unspecified private
donor metric. No images or decode. Reuse retained CC0 verification after
matching local hashes. All input errors and prefix shortfalls fail the CLI.
Sample IDs must be distinct positive ASCII decimals and names printable basenames.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class  # noqa: E402
from suffix_joint_probe import LIMIT, correlation, scan_prefix  # noqa: E402


def donor_statistics(tokens, width):
    if type(width) is not int or width < 2:
        raise ValueError("width must be at least two")
    for q, suffix in tokens:
        if type(q) is not int or q < 0 or type(suffix) is not int or not 0 <= suffix < 32:
            raise ValueError("invalid candidate token")
    result = []
    for lag in (2 * width - 2, 2 * width, 2 * width + 2):
        classes = [{"nominal_row_parity": row, "nominal_column_parity": col,
                    "candidate_pairs": 0, "endpoint_escape_omitted_pairs": 0,
                    "donor_by_target_b2": [[0, 0], [0, 0]]}
                   for row in range(2) for col in range(2)]
        for t in range(lag, len(tokens)):
            cell = classes[2 * ((t // width) % 2) + (t % width) % 2]
            cell["candidate_pairs"] += 1
            donor, target = tokens[t - lag], tokens[t]
            if donor[0] >= 17 or target[0] >= 17:
                cell["endpoint_escape_omitted_pairs"] += 1
                continue
            cell["donor_by_target_b2"][(donor[1] >> 2) & 1][(target[1] >> 2) & 1] += 1
        for cell in classes:
            table = cell["donor_by_target_b2"]
            cell["retained_pairs"] = sum(map(sum, table))
            cell["pearson"] = correlation(table)
        result.append({"lag": lag, "initial_targets_without_donor": min(lag, len(tokens)),
                       "classes": classes})
    return {"parsed_tokens": len(tokens), "nominal_width": width,
            "parsed_escape_tokens": sum(q >= 17 for q, _ in tokens), "lags": result}


def report(sample_id, name, path):
    with open(path, "rb") as handle:
        data = handle.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError("one contiguous strip required")
    off, count = offsets[0], lengths[0]
    if off < 0 or count <= 0 or off + count > len(data):
        raise ValueError("payload out of bounds")
    width, height = best[0x100][0], best[0x101][0]
    if width < 2 or height <= 0 or size_class(count, width, height) != "variable":
        raise ValueError("positive variable-size payload required")
    tokens, end = scan_prefix(data[off:off + count], LIMIT)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": width, "payload_h": height, "payload_offset": off,
            "payload_bytes": count, "size_class": "variable",
            "compression_tag": best.get(0x103), "bits_consumed": end,
            "requested_tokens": LIMIT, "prefix_shortfall": LIMIT - len(tokens),
            "statistics": donor_statistics(tokens, width)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", metavar=("ID", "PUBLIC_NAME", "FILE"), required=True)
    args = parser.parse_args()
    ids = [sample[0] for sample in args.sample]
    try:
        invalid_ids = any(not x.isascii() or not x.isdecimal() or int(x) <= 0 for x in ids) or len(set(map(int, ids))) != len(ids)
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        parser.error("sample IDs must be distinct positive ASCII decimal integers")
    if any(not name or not name.isprintable() or any(c in name for c in '/\\') for _, name, _ in args.sample):
        parser.error("sample public name must be a printable basename")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "error": type(exc).__name__})
    sources = {}
    for filename in ("token_donor_comb_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": sources, "python_version": sys.version.split()[0],
                      "escape_extra_bits": 0, "requested_prefix_tokens": LIMIT,
                      "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    return 1 if failures or any(r["prefix_shortfall"] for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
