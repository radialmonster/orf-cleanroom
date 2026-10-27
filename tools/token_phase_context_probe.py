#!/usr/bin/env python3
"""Describe token-index phase given a fixed bit context (#30; #11/#153/#179).

Stdlib Python 3.8+. Aggregate JSON only; no images or decoding. Fixed first
262144 complete candidate tokens, payload bit zero, zero extra escape bits.
For t>=2 retain only triples t-2..t without q>=17; preserve absolute indices.
Target Y=b2(t), context C=2*b4(t-1)+b2(t-2), phase P=t mod m, m=2..8.
Emit complete C-by-P-by-Y tables, stratum sizes, matched marginal I(Y;P),
and unsmoothed plug-in I(Y;P|C). Empty statistics are null. These are
descriptive scores, without null correction, thresholds or significance.
Stratification and sparse cells can increase finite-sample bias. This is
not the historical private context-gain metric or a physical-column test.
The candidate parse and post-escape framing remain unverified; excluding
triples containing escapes cannot repair an incorrect post-escape parse.
An additional held-out report discards incomplete 128-token blocks and whole
blocks containing q>=17. Original even blocks train; original odd blocks test.
Targets start at local index 2, so triples never cross block boundaries.
For all m=2..8 compare Jeffreys-smoothed P(Y|C) and P(Y|C,P) on identical
held-out targets; phase uses absolute indices. Exact tables, unseen-context
counts, losses and signed baseline-minus-phase gains are emitted. With no
training data a 0.5 prediction is scored but gain is null; no test means null
loss/gain. This selection differs from the triple-wise plug-in report above.
Adjacent train/test blocks can remain dependent. Held-out scores are not
unbiased estimates, null calibration, significance, historical reproduction,
physical columns or a decoder. Negative gains are retained.
Check public sample licences separately before use.
Incomplete requested prefixes and input failures produce a nonzero exit;
available aggregate reports are retained.
Sample IDs must be distinct positive ASCII decimals; names must be printable
and contain no path separators.
"""
import argparse
import hashlib
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class  # noqa: E402
from suffix_joint_probe import LIMIT, scan_prefix  # noqa: E402
from token_phase_probe import entropy  # noqa: E402

MODULI = tuple(range(2, 9))
HELDOUT_BLOCK = 128


def table_statistics(table):
    """Return entropy difference and marginal MI on the exact same observations."""
    if len(table) != 4 or not table[0]:
        raise ValueError("four nonempty context strata required")
    m = len(table[0])
    if any(len(stratum) != m for stratum in table):
        raise ValueError("inconsistent phase dimension")
    if any(len(row) != 2 or any(type(c) is not int or c < 0 for c in row)
           for stratum in table for row in stratum):
        raise ValueError("nonnegative integer binary counts required")
    context_counts = [sum(map(sum, stratum)) for stratum in table]
    n = sum(context_counts)
    pooled = [[sum(table[c][p][y] for c in range(4)) for y in range(2)]
              for p in range(m)]
    h_c = (sum(nc / n * entropy([sum(row[y] for row in stratum) for y in range(2)])
               for nc, stratum in zip(context_counts, table) if nc) if n else None)
    h_cp = (sum(sum(row) / n * entropy(row) for stratum in table
                for row in stratum if sum(row)) if n else None)
    h = entropy([sum(row[y] for row in pooled) for y in range(2)])
    h_p = (sum(sum(row) / n * entropy(row) for row in pooled if sum(row)) if n else None)
    return {"context_by_phase_by_target": table, "observations": n,
            "context_counts": context_counts,
            "context_phase_counts": [[sum(row) for row in stratum] for stratum in table],
            "target_entropy_bits": h, "target_given_phase_entropy_bits": h_p,
            "target_given_context_entropy_bits": h_c,
            "target_given_context_phase_entropy_bits": h_cp,
            "plugin_phase_mi_bits": h - h_p if n else None,
            "plugin_conditional_phase_mi_bits": h_c - h_cp if n else None}


def phase_context_statistics(tokens):
    for q, suffix in tokens:
        if type(q) is not int or q < 0 or type(suffix) is not int or not 0 <= suffix < 32:
            raise ValueError("invalid candidate token")
    tables = {m: [[[0, 0] for _ in range(m)] for _ in range(4)] for m in MODULI}
    omitted = 0
    for t in range(2, len(tokens)):
        if any(tokens[j][0] >= 17 for j in range(t - 2, t + 1)):
            omitted += 1
            continue
        c = 2 * ((tokens[t - 1][1] >> 4) & 1) + ((tokens[t - 2][1] >> 2) & 1)
        y = (tokens[t][1] >> 2) & 1
        for m, table in tables.items():
            table[c][t % m][y] += 1
    return {"parsed_tokens": len(tokens), "initial_context_unavailable": min(2, len(tokens)),
            "escape_tokens": sum(q >= 17 for q, _ in tokens),
            "escape_omitted_triples": omitted,
            "retained_triples": max(0, len(tokens) - 2) - omitted,
            "moduli": [dict(modulus=m, **table_statistics(table)) for m, table in tables.items()]}


def predictive_score(train, test):
    """Jeffreys binary loss from exact context-by-outcome tables."""
    if len(train) != len(test) or not train:
        raise ValueError("matching nonempty context tables required")
    if any(len(row) != 2 or any(type(c) is not int or c < 0 for c in row)
           for table in (train, test) for row in table):
        raise ValueError("nonnegative integer binary counts required")
    nt, nv = sum(map(sum, train)), sum(map(sum, test))
    terms = [-heldout[y] * math.log2((observed[y] + 0.5) / (sum(observed) + 1))
             for observed, heldout in zip(train, test) for y in range(2)]
    return {"training_counts_context_by_target": train,
            "test_counts_context_by_target": test,
            "training_targets": nt, "test_targets": nv,
            "fitted_transfer": bool(nt and nv),
            "test_targets_in_unseen_training_contexts":
                sum(sum(heldout) for observed, heldout in zip(train, test) if not sum(observed)),
            "heldout_log_loss_bits": math.fsum(terms) / nv if nv else None}


def heldout_statistics(tokens):
    """Fixed even-block training / odd-block test; no context crosses blocks."""
    for q, suffix in tokens:
        if type(q) is not int or q < 0 or type(suffix) is not int or not 0 <= suffix < 32:
            raise ValueError("invalid candidate token")
    tables = {m: [[[[0, 0] for _ in range(m)] for _ in range(4)]
                  for _ in range(2)] for m in MODULI}
    complete = len(tokens) // HELDOUT_BLOCK
    retained, omitted = [0, 0], [0, 0]
    for index in range(complete):
        start = index * HELDOUT_BLOCK
        block = tokens[start:start + HELDOUT_BLOCK]
        split = index % 2
        if any(q >= 17 for q, _ in block):
            omitted[split] += 1
            continue
        retained[split] += 1
        for local in range(2, HELDOUT_BLOCK):
            c = 2 * ((block[local - 1][1] >> 4) & 1) + ((block[local - 2][1] >> 2) & 1)
            y = (block[local][1] >> 2) & 1
            for m, table in tables.items():
                table[split][c][(start + local) % m][y] += 1
    results = []
    for m, (train, test) in tables.items():
        pooled = [[[sum(table[c][p][y] for p in range(m)) for y in range(2)]
                   for c in range(4)] for table in (train, test)]
        baseline = predictive_score(*pooled)
        phase = predictive_score([row for stratum in train for row in stratum],
                                 [row for stratum in test for row in stratum])
        results.append({"modulus": m, "training_context_by_phase_by_target": train,
                        "test_context_by_phase_by_target": test,
                        "context_baseline": baseline, "context_plus_phase": phase,
                        "gain_vs_context_bits":
                            baseline["heldout_log_loss_bits"] - phase["heldout_log_loss_bits"]
                            if baseline["fitted_transfer"] else None})
    tail = tokens[complete * HELDOUT_BLOCK:]
    return {"block_tokens": HELDOUT_BLOCK, "training_original_block_parity": 0,
            "test_original_block_parity": 1, "first_local_target": 2,
            "smoothing_per_outcome": 0.5, "complete_blocks": complete,
            "retained_train_test_blocks": retained,
            "escape_omitted_train_test_blocks": omitted,
            "retained_train_test_targets": [n * (HELDOUT_BLOCK - 2) for n in retained],
            "omitted_context_boundary_train_test_targets": [n * 2 for n in retained],
            "tail_tokens": len(tail), "tail_escapes": sum(q >= 17 for q, _ in tail),
            "parsed_escapes": sum(q >= 17 for q, _ in tokens), "moduli": results}


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
    tokens, end = scan_prefix(data[off:off + count], LIMIT)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_offset": off,
            "payload_bytes": count, "size_class": "variable",
            "compression_tag": best.get(0x103), "bits_consumed": end,
            "requested_tokens": LIMIT, "prefix_shortfall": LIMIT - len(tokens),
            "statistics": phase_context_statistics(tokens),
            "heldout": heldout_statistics(tokens)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", metavar=("ID", "PUBLIC_NAME", "FILE"), required=True)
    args = parser.parse_args()
    ids = [sample[0] for sample in args.sample]
    try:
        invalid_ids = (any(not x.isascii() or not x.isdecimal() or int(x) <= 0 for x in ids)
                       or len(set(map(int, ids))) != len(ids))
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        parser.error("sample IDs must be distinct positive ASCII decimal integers")
    if any(not name or not name.isprintable() or any(c in name for c in "/\\")
           for _, name, _ in args.sample):
        parser.error("sample public name must be printable without path separators")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "error": type(exc).__name__})
    sources = {}
    for filename in ("token_phase_context_probe.py", "token_phase_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": sources, "python_version": sys.version.split()[0],
                      "escape_extra_bits": 0, "requested_prefix_tokens": LIMIT,
                      "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    return 1 if failures or any(r["prefix_shortfall"] for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
