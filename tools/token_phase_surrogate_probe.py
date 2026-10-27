#!/usr/bin/env python3
"""Conditional block-phase offset diagnostic for #30; builds on #203/#211.

Candidate k=5 prefix, fixed 128-token whole-block escape omission, even-block
training and odd-block testing, local targets 2..127. Target b2(t), context
2*b4(t-1)+b2(t-2). For each modulus 2..8 independently shift only the phase
labels of each retained block by a uniform offset. Context/target ordering,
selection and split remain unchanged. Sixteen Random(20261021+replicate)
streams are restarted for each modulus, consumed in retained block order.
Report complete observed/surrogate tables, losses, gains, offset histograms
and rank counts with ties. These are diagnostics under an ASSUMED offset
exchangeability model, not inferential p-values: the model is not justified
for ORFs. Adjacent blocks may depend; within-block phase structure remains.
No historical private-number reproduction, physical-column or decode claim.
Stdlib, reads samples/prints aggregate JSON only. Reuse retained CC0 records
only after matching the local SHA256. New content needs first verification.
Sample IDs must be distinct positive ASCII decimals and names printable basenames.
"""
import argparse
import hashlib
import json
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class
from suffix_joint_probe import LIMIT, scan_prefix
from token_phase_context_probe import HELDOUT_BLOCK, MODULI, predictive_score

REPLICATES = 16
SEED = 20261021


def select_blocks(tokens):
    for q, suffix in tokens:
        if type(q) is not int or q < 0 or type(suffix) is not int or not 0 <= suffix < 32:
            raise ValueError("invalid candidate token")
    complete = len(tokens) // HELDOUT_BLOCK
    retained, omitted = [0, 0], [0, 0]
    blocks = []
    for index in range(complete):
        start = index * HELDOUT_BLOCK
        block = tokens[start:start + HELDOUT_BLOCK]
        if any(q >= 17 for q, _ in block):
            omitted[index % 2] += 1
            continue
        retained[index % 2] += 1
        triples = [(start + t,
                    2 * ((block[t-1][1] >> 4) & 1) + ((block[t-2][1] >> 2) & 1),
                    (block[t][1] >> 2) & 1) for t in range(2, HELDOUT_BLOCK)]
        blocks.append((index % 2, triples))
    tail = tokens[complete * HELDOUT_BLOCK:]
    return blocks, {"complete_blocks": complete,
                    "retained_train_test_blocks": retained,
                    "escape_omitted_train_test_blocks": omitted,
                    "retained_train_test_targets": [126*n for n in retained],
                    "tail_tokens": len(tail), "tail_escapes": sum(q >= 17 for q, _ in tail),
                    "parsed_escapes": sum(q >= 17 for q, _ in tokens)}


def block_tables(blocks, modulus):
    tables = []
    for split, triples in blocks:
        table = [[[0, 0] for _ in range(modulus)] for _ in range(4)]
        for t, c, y in triples:
            table[c][t % modulus][y] += 1
        tables.append((split, table))
    return tables


def combine(tables, modulus, offsets):
    if len(tables) != len(offsets):
        raise ValueError("one offset per retained block required")
    result = [[[[0, 0] for _ in range(modulus)] for _ in range(4)] for _ in range(2)]
    histograms = [[0] * modulus for _ in range(2)]
    for (split, table), offset in zip(tables, offsets):
        if type(offset) is not int or not 0 <= offset < modulus:
            raise ValueError("invalid phase offset")
        histograms[split][offset] += 1
        for c, stratum in enumerate(table):
            for p, row in enumerate(stratum):
                dest = result[split][c][(p + offset) % modulus]
                for y in range(2):
                    dest[y] += row[y]
    pooled = [[[sum(table[c][p][y] for p in range(modulus)) for y in range(2)]
               for c in range(4)] for table in result]
    baseline = predictive_score(*pooled)
    phase = predictive_score([row for s in result[0] for row in s],
                             [row for s in result[1] for row in s])
    return {"training_context_by_phase_by_target": result[0],
            "test_context_by_phase_by_target": result[1],
            "offset_histogram_train_test": histograms,
            "context_baseline": baseline, "context_plus_phase": phase,
            "gain_vs_context_bits": baseline["heldout_log_loss_bits"] - phase["heldout_log_loss_bits"]
            if baseline["fitted_transfer"] else None}


def measure(tokens):
    blocks, selection = select_blocks(tokens)
    results = []
    for m in MODULI:
        tables = block_tables(blocks, m)
        observed = combine(tables, m, [0] * len(blocks))
        surrogates = []
        for r in range(REPLICATES):
            rng = random.Random(SEED + r)
            offsets = [rng.randrange(m) for _ in blocks]
            surrogates.append(dict(replicate=r, **combine(tables, m, offsets)))
        gain = observed["gain_vs_context_bits"]
        gains = [row["gain_vs_context_bits"] for row in surrogates]
        ranks = ({"surrogate_lt_observed": sum(v < gain for v in gains),
                  "surrogate_eq_observed": sum(v == gain for v in gains),
                  "surrogate_gt_observed": sum(v > gain for v in gains)} if gain is not None else None)
        results.append({"modulus": m, "observed": observed,
                        "surrogates": surrogates, "descriptive_rank_counts": ranks})
    return {"selection": selection, "moduli": results}


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
    if w <= 0 or h <= 0 or size_class(count, w, h) != "variable":
        raise ValueError("positive variable-size payload required")
    tokens, end = scan_prefix(data[off:off+count], LIMIT)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_offset": off,
            "payload_bytes": count, "compression_tag": best.get(0x103),
            "size_class": "variable", "requested_tokens": LIMIT,
            "returned_tokens": len(tokens), "prefix_shortfall": LIMIT-len(tokens),
            "bits_consumed": end, "statistics": measure(tokens)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    args = parser.parse_args(argv)
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
    for filename in ("token_phase_surrogate_probe.py", "token_phase_context_probe.py",
                     "token_phase_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": sources, "python_version": sys.version.split()[0],
                      "seed": SEED, "replicates": REPLICATES, "block_tokens": HELDOUT_BLOCK,
                      "escape_extra_bits": 0, "first_local_target": 2,
                      "training_original_block_parity": 0, "test_original_block_parity": 1,
                      "model_assumption": "Independent uniform per-block phase offsets; exchangeability "
                      "is assumed, not established for ORFs. Rank diagnostic only, no inferential p-value.",
                      "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    return 1 if failures or any(s["prefix_shortfall"] for s in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
