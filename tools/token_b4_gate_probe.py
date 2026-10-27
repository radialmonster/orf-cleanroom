#!/usr/bin/env python3
"""Descriptive b4-gate tables for lead #32; builds on candidate parse #11.

First 262144 complete q-zero/one/5-suffix tokens, zero extra escape bits.
For ordinary q<17 tokens report all low3=s&7 and low4=s&15 histograms by b4,
plus current-q/current-b4 counts. For lag1 report previous-q/current-b4 only
when BOTH adjacent original tokens are ordinary; never compact indices.
Every q=0..16 cell is retained. Plugin MI is unsmoothed and descriptive.

Optional --q-stratified adds low3/low4 histograms by current q and b4,
exact mean(b4=0)-mean(b4=1) contrasts and a per-file equal-weight average
over all q strata having both groups nonempty. Empty groups give null;
all strata and the exact support are reported. Sparse strata receive equal
weight; this diagnostic is not a causal adjustment or significance test.

The historical phrase 'low bits', files and estimator were unspecified: these
new explicit metrics do not reproduce its exact figures. No significance,
independence, significance-gate semantics, physical rows or decoder follows.
Escape omission is selective and cannot repair unknown post-escape framing.
No previews accessed. Read-only stdlib Python 3.8+; aggregate JSON only.
Licence-check public files separately before measurement.
Sample IDs must be distinct positive ASCII decimals and names printable basenames.
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
from suffix_joint_probe import LIMIT, mutual_information, scan_prefix


def summarize(table):
    """Rows are q=0..16; columns are b4=0,1, including empty rows."""
    return {"q_by_b4_counts": table,
            "retained": sum(map(sum, table)),
            "p_b4_one_given_q": [row[1] / sum(row) if sum(row) else None for row in table],
            "plugin_mi_bits": mutual_information(table)}


def rational(value):
    return (None if value is None else
            {"numerator": value.numerator, "denominator": value.denominator,
             "approx": float(value)})


def stratified_fields(histograms):
    """All q=0..16, exact contrasts, equal weights on each file's support."""
    fields = {}
    for name, strata in histograms.items():
        rows, support, differences = [], [], []
        for q, hist in enumerate(strata):
            counts = list(map(sum, hist))
            sums = [sum(i * n for i, n in enumerate(row)) for row in hist]
            means = [Fraction(total, n) if n else None
                     for total, n in zip(sums, counts)]
            difference = means[0] - means[1] if all(counts) else None
            if difference is not None:
                support.append(q)
                differences.append(difference)
            rows.append({"q": q, "b4_rows_value_columns": hist,
                         "counts_b4_0_1": counts, "integer_sums_b4_0_1": sums,
                         "means_b4_0_1": [rational(m) for m in means],
                         "mean_b4_0_minus_b4_1": rational(difference)})
        fields[name] = {"strata": rows, "support_q": support,
                        "excluded_q": [q for q in range(17) if q not in support],
                        "support_strata": len(support),
                        "equal_weight_mean_b4_0_minus_b4_1": rational(
                            sum(differences, Fraction()) / len(differences)
                            if differences else None)}
    return fields


def measure(tokens, q_stratified=False):
    for q, s in tokens:
        if type(q) is not int or q < 0 or type(s) is not int or not 0 <= s < 32:
            raise ValueError("invalid candidate token")
    hist = {"low3": [[0] * 8 for _ in range(2)],
            "low4": [[0] * 16 for _ in range(2)]}
    strata = ({name: [[[0] * width for _ in range(2)] for _ in range(17)]
               for name, width in (("low3", 8), ("low4", 16))}
              if q_stratified else None)
    current, previous = [[[0, 0] for _ in range(17)] for _ in range(2)]
    escapes = 0
    omitted_pairs = 0
    for t, (q, s) in enumerate(tokens):
        if q >= 17:
            escapes += 1
        else:
            b4 = s >> 4
            current[q][b4] += 1
            hist["low3"][b4][s & 7] += 1
            hist["low4"][b4][s & 15] += 1
            if strata is not None:
                strata["low3"][q][b4][s & 7] += 1
                strata["low4"][q][b4][s & 15] += 1
        if t:
            past_q = tokens[t - 1][0]
            if q >= 17 or past_q >= 17:
                omitted_pairs += 1
            else:
                previous[past_q][s >> 4] += 1
    fields = {}
    for name, rows in hist.items():
        counts = list(map(sum, rows))
        sums = [sum(i * n for i, n in enumerate(row)) for row in rows]
        fields[name] = {"b4_rows_value_columns": rows, "counts_b4_0_1": counts,
                        "integer_sums_b4_0_1": sums,
                        "means_b4_0_1": [total / n if n else None for total, n in zip(sums, counts)]}
    result = {"ordinary_tokens": len(tokens) - escapes, "escape_tokens_omitted": escapes,
            "fields": fields, "current_q_current_b4": summarize(current),
            "previous_q_current_b4": summarize(previous),
            "lag1_candidate_pairs": max(0, len(tokens) - 1),
            "lag1_escape_endpoint_omitted_pairs": omitted_pairs}
    if strata is not None:
        result["q_stratified_fields"] = stratified_fields(strata)
    return result


def report(sample_id, name, path, q_stratified=False):
    with open(path, "rb") as handle:
        data = handle.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError("single strip required")
    off, count = offsets[0], lengths[0]
    if off < 0 or count <= 0 or off + count > len(data):
        raise ValueError("invalid strip bounds")
    width, height = best[0x100][0], best[0x101][0]
    if width <= 0 or height <= 0 or size_class(count, width, height) != "variable":
        raise ValueError("positive variable-size payload required")
    tokens, end = scan_prefix(data[off:off + count], LIMIT)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": width, "payload_h": height, "payload_offset": off,
            "payload_bytes": count, "size_class": "variable",
            "requested_tokens": LIMIT, "returned_tokens": len(tokens),
            "token_shortfall": LIMIT - len(tokens), "bits_consumed": end,
            "statistics": measure(tokens, q_stratified)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    parser.add_argument("--q-stratified", action="store_true",
                        help="add exact within-q contrasts and per-file equal-weight summary")
    args = parser.parse_args(argv)
    ids = [row[0] for row in args.sample]
    try:
        invalid_ids = any(not i.isascii() or not i.isdecimal() or int(i) <= 0 for i in ids) or len(set(map(int, ids))) != len(ids)
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        parser.error("sample IDs must be distinct positive ASCII decimals")
    if any(not name or not name.isprintable() or any(c in name for c in '/\\') for _, name, _ in args.sample):
        parser.error("sample public name must be a printable basename")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path, args.q_stratified))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "error_type": type(exc).__name__})
    hashes = {}
    for filename in ("token_b4_gate_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            hashes[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": hashes, "python_version": sys.version.split()[0],
                      "escape_extra_bits": 0, "samples": reports, "failures": failures},
                     indent=2, allow_nan=False))
    return 1 if failures or any(s["token_shortfall"] for s in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
