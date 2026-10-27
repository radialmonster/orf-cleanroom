#!/usr/bin/env python3
"""Aggregate candidate-token nominal-row starts for lead #29 item 9.

Stdlib Python 3.8+. Builds on #11 and suffix_joint_probe.py. First 262144
complete candidate tokens; q zeros/one/five suffix bits, no extra escape skip.
W is payload width. Only complete W-token nominal rows starting at token0
contribute. Omit q>=17 tokens individually without renumbering indices.
Report exact ordinary-q and unsigned-suffix histograms for positions0..23
and remainder, plus first10/first24/remainder pools, counts and means.

These new explicit fields cannot reproduce #29's unspecified historical
9.5..14/13 statistic. Nominal rows and origin are hypotheses, not physical
row boundaries. Escape omission cannot repair unknown framing. No elevation
criterion, null model, significance, decoder or finding follows. Aggregate
JSON only; no preview access. Check public CC0 licences separately first.
Incomplete requested prefixes and input failures produce a nonzero exit;
available aggregate reports are retained.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class  # noqa: E402
from suffix_joint_probe import LIMIT, scan_prefix  # noqa: E402


def empty_cell():
    return {"candidate_tokens": 0, "escape_omitted_tokens": 0,
            "ordinary_q_counts_0_to_16": [0] * 17,
            "suffix_counts_0_to_31": [0] * 32}


def finish_cell(cell):
    result = dict(cell)
    n = sum(cell["ordinary_q_counts_0_to_16"])
    result["retained_tokens"] = n
    for key, prefix in (("ordinary_q_counts_0_to_16", "q"),
                        ("suffix_counts_0_to_31", "unsigned_suffix")):
        total = sum(i * c for i, c in enumerate(cell[key]))
        result[prefix + "_sum"] = total
        result[prefix + "_mean"] = total / n if n else None
    return result


def pool(cells):
    result = empty_cell()
    for cell in cells:
        for key in ("candidate_tokens", "escape_omitted_tokens"):
            result[key] += cell[key]
        for key in ("ordinary_q_counts_0_to_16", "suffix_counts_0_to_31"):
            result[key] = [a + b for a, b in zip(result[key], cell[key])]
    return finish_cell(result)


def position_statistics(tokens, width):
    if type(width) is not int or width <= 24:
        raise ValueError("nominal width must exceed 24")
    for q, suffix in tokens:
        if type(q) is not int or q < 0 or type(suffix) is not int or not 0 <= suffix < 32:
            raise ValueError("invalid candidate token")
    rows, tail = divmod(len(tokens), width)
    used = rows * width
    cells = [empty_cell() for _ in range(25)]
    for index in range(used):
        q, suffix = tokens[index]
        col = index % width
        cell = cells[col if col < 24 else 24]
        cell["candidate_tokens"] += 1
        if q >= 17:
            cell["escape_omitted_tokens"] += 1
        else:
            cell["ordinary_q_counts_0_to_16"][q] += 1
            cell["suffix_counts_0_to_31"][suffix] += 1
    return {"parsed_tokens": len(tokens), "nominal_width": width,
            "complete_nominal_rows": rows, "complete_row_tokens": used,
            "incomplete_nominal_tail_tokens": tail,
            "incomplete_nominal_tail_escapes": sum(q >= 17 for q, _ in tokens[used:]),
            "parsed_escapes": sum(q >= 17 for q, _ in tokens),
            "positions_0_to_23_and_remainder": [finish_cell(c) for c in cells],
            "pools": {"first10": pool(cells[:10]), "first24": pool(cells[:24]),
                      "remainder_after24": pool(cells[24:]), "all_complete_rows": pool(cells)}}


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
    w, h = best[0x100][0], best[0x101][0]
    if w <= 24 or h <= 0 or size_class(count, w, h) != "variable":
        raise ValueError("positive variable-size payload with width >24 required")
    tokens, end = scan_prefix(data[off:off + count], LIMIT)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_offset": off,
            "payload_bytes": count, "size_class": "variable",
            "compression_tag": best.get(0x103), "bits_consumed": end,
            "requested_tokens": LIMIT, "prefix_shortfall": LIMIT - len(tokens),
            "statistics": position_statistics(tokens, w)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", metavar=("ID", "PUBLIC_NAME", "FILE"), required=True)
    args = parser.parse_args()
    ids = [s[0] for s in args.sample]
    if any(not x.isascii() or not x.isdecimal() or int(x) <= 0 for x in ids) or len(set(ids)) != len(ids):
        parser.error("sample IDs must be distinct positive ASCII decimal integers")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "error": type(exc).__name__})
    sources = {}
    for filename in ("token_position_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": sources, "python_version": sys.version.split()[0],
                      "escape_extra_bits": 0, "requested_prefix_tokens": LIMIT,
                      "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    return 1 if failures or any(r["prefix_shortfall"] for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
