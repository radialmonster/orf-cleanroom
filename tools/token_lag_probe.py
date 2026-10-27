#!/usr/bin/env python3
"""Measure candidate-token lag dependence for lead #29 item 6, building on #11.

Stdlib, Python 3.8+. Read-only inputs; aggregate JSON only. Fixed design:
first 262144 complete q-zero/one/5-bit-suffix tokens, no extra escape skip.
Consecutive 128-token blocks from token zero; omit entire q>=17 blocks and
incomplete tails. Pairs stay within retained blocks; no concatenated-gap pairs.
At each lag 1..5 report exact joint counts and unsmoothed plug-in MI for
q>0 (binary) and suffix&7 (eight symbols). Every comparison replicate shuffles
whole (q,suffix) tokens independently within each retained block, then forms
the same lagged pairs. Random(seed+replicate), seed 20261021, 16 replicates.
This preserves block marginals and within-token dependence, not temporal
dependence. The comparison is descriptive, not a p-value or significance test.
Blocks are not camera rows; selective escape omission does not repair unknown
post-escape framing. Historical private held-out/smoothed figures, stationarity,
log-magnitude and physical interpretation are not reproduced by this metric.

Usage: python -I -B tools/token_lag_probe.py --sample ID PUBLIC_NAME FILE
Repeat --sample. Licence-check downloaded samples separately before use.
Incomplete requested prefixes and input failures produce a nonzero exit;
available aggregate reports are retained.
"""
import argparse
import hashlib
import json
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class  # noqa: E402
from suffix_joint_probe import scan_prefix, mutual_information  # noqa: E402

LIMIT = 262144
BLOCK = 128
LAGS = (1, 2, 3, 4, 5)
REPLICATES = 16
SEED = 20261021


def select_blocks(tokens):
    complete = len(tokens) // BLOCK
    blocks = []
    omitted = 0
    for start in range(0, complete * BLOCK, BLOCK):
        block = tokens[start:start + BLOCK]
        if any(q >= 17 for q, _ in block):
            omitted += 1
        else:
            blocks.append(block)
    tail = tokens[complete * BLOCK:]
    return blocks, {"complete_blocks": complete, "retained_blocks": len(blocks),
                    "escape_omitted_blocks": omitted,
                    "escape_omitted_tokens": BLOCK * omitted,
                    "retained_tokens": BLOCK * len(blocks), "tail_tokens": len(tail),
                    "parsed_escapes": sum(q >= 17 for q, _ in tokens),
                    "tail_escapes": sum(q >= 17 for q, _ in tail)}


def lag_tables(blocks):
    result = []
    for lag in LAGS:
        qt = [[0] * 2 for _ in range(2)]
        lt = [[0] * 8 for _ in range(8)]
        for block in blocks:
            for (qa, sa), (qb, sb) in zip(block[:-lag], block[lag:]):
                qt[int(qa > 0)][int(qb > 0)] += 1
                lt[sa & 7][sb & 7] += 1
        result.append({"lag": lag, "pairs": sum(map(sum, qt)),
                       "q_positive_counts": qt, "low3_counts": lt,
                       "q_positive_mi_bits": mutual_information(qt),
                       "low3_mi_bits": mutual_information(lt)})
    return result


def measure(blocks):
    observed = lag_tables(blocks)
    comparisons = []
    for replicate in range(REPLICATES):
        rng = random.Random(SEED + replicate)
        shuffled = []
        for block in blocks:
            copied = list(block)
            rng.shuffle(copied)
            shuffled.append(copied)
        comparisons.append(lag_tables(shuffled))
    for index, cell in enumerate(observed):
        for field in ("q_positive", "low3"):
            values = [row[index][field + "_mi_bits"] for row in comparisons]
            cell[field + "_permuted_mi_bits"] = values
            cell[field + "_permuted_mean_bits"] = (
                sum(values) / len(values) if cell["pairs"] else None)
    return observed


def report(sample_id, name, path):
    with open(path, "rb") as handle:
        data = handle.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError("single strip required")
    off, count = offsets[0], lengths[0]
    if off < 0 or count <= 0 or off + count > len(data):
        raise ValueError("invalid strip bounds")
    w, h = best[0x100][0], best[0x101][0]
    if w <= 0 or h <= 0 or size_class(count, w, h) != "variable":
        raise ValueError("positive variable-size payload required")
    tokens, end = scan_prefix(data[off:off + count], LIMIT)
    blocks, selection = select_blocks(tokens)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_offset": off,
            "payload_bytes": count, "size_class": "variable",
            "requested_tokens": LIMIT, "returned_tokens": len(tokens),
            "prefix_shortfall": LIMIT - len(tokens), "bits_consumed": end,
            "selection": selection, "lags": measure(blocks)}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append",
                        metavar=("ID", "PUBLIC_NAME", "FILE"), required=True)
    args = parser.parse_args()
    ids = [row[0] for row in args.sample]
    if any(not value.isdecimal() or not value.isascii() or int(value) <= 0 for value in ids):
        parser.error("sample IDs must be positive ASCII decimals")
    if len(set(ids)) != len(ids):
        parser.error("sample IDs must be distinct")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "error": type(exc).__name__})
    hashes = {}
    for source in ("token_lag_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), source), "rb") as handle:
            hashes[source] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": hashes, "python_version": sys.version.split()[0],
                      "block_tokens": BLOCK, "lags": LAGS, "replicates": REPLICATES,
                      "seed": SEED, "samples": reports, "failures": failures},
                     indent=2, allow_nan=False))
    return 1 if failures or any(r["prefix_shortfall"] for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
