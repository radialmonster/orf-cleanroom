#!/usr/bin/env python3
"""Held-out binary context log-loss for #29 item 4; builds on #11.

Python 3.8+, stdlib, read-only sample inputs and aggregate JSON only. Fixed
candidate parse/selection: first 262144 complete q-zero/one/5-suffix tokens,
no extra escape bits; 128-token blocks, discard any q>=17 block and tail.
Train even ORIGINAL block indices, evaluate odd; all models use t>=5 within
each block. No context crosses a block. b2 contexts are empty, two alternating
taps, five alternating taps; b4 contexts empty, b2 lag1, b2 lags1+3.

Fit P(bit=y|context)=(training_count[y]+0.5)/(training_total+1).
Held-out log-loss is -mean(log2(probability of test outcome)), not empirical
conditional entropy. Gains subtract each model loss from its same-target
empty-context loss; negative gains are retained. Unseen contexts predict 0.5.
All observed train/test tables and unseen-test counts are reported. Sixteen
Random(20261021+replicate) whole-token permutations within retained blocks
refit and re-evaluate each model, preserving original split and block
marginals, not temporal structure. Every comparison loss/gain is reported.

Blocks are not physical rows; adjacent train/test blocks can remain dependent.
This is a descriptive transfer estimate, not uncertainty/significance,
historical private-estimator reproduction, a conditional law or a decoder.
Escape omission is selective and cannot repair unknown post-escape framing.
Licence-check samples separately. No previews are accessed.
Incomplete requested prefixes and input failures produce a nonzero exit;
available aggregate reports are retained.
"""
import argparse
import hashlib
import json
import math
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class  # noqa: E402
from suffix_joint_probe import BLOCK, LIMIT, REPLICATES, SEED, scan_prefix  # noqa: E402

START = 5
MODELS = (
    ("b2_empty", 2, ()),
    ("b2_two", 2, ((4, 1), (2, 2))),
    ("b2_five", 2, ((4, 1), (2, 2), (4, 3), (2, 4), (4, 5))),
    ("b4_empty", 4, ()),
    ("b4_one", 4, ((2, 1),)),
    ("b4_two", 4, ((2, 1), (2, 3))),
)


def select_blocks(tokens):
    blocks = []
    omitted = [0, 0]
    retained = [0, 0]
    complete = len(tokens) // BLOCK
    for index in range(complete):
        block = tokens[index * BLOCK:(index + 1) * BLOCK]
        if any(q >= 17 for q, _ in block):
            omitted[index % 2] += 1
        else:
            blocks.append((index, [s for _, s in block]))
            retained[index % 2] += 1
    tail = tokens[complete * BLOCK:]
    return blocks, {"complete_blocks": complete,
                    "retained_train_test_blocks": retained,
                    "escape_omitted_train_test_blocks": omitted,
                    "retained_train_test_targets": [n * (BLOCK - START) for n in retained],
                    "parsed_escapes": sum(q >= 17 for q, _ in tokens),
                    "tail_tokens": len(tail), "tail_escapes": sum(q >= 17 for q, _ in tail)}


def fit_score(blocks):
    results = []
    baselines = {}
    previous = {}
    for name, target, taps in MODELS:
        counts = [[[0, 0] for _ in range(1 << len(taps))] for _ in range(2)]
        for index, block in blocks:
            table = counts[index % 2]
            for t in range(START, len(block)):
                context = 0
                for bit, lag in taps:
                    context = (context << 1) | ((block[t - lag] >> bit) & 1)
                table[context][(block[t] >> target) & 1] += 1
        train, test = counts
        nt = sum(map(sum, train))
        nv = sum(map(sum, test))
        loss = None
        unseen = 0
        if nv:
            terms = []
            for observed, heldout in zip(train, test):
                total = sum(observed)
                if total == 0:
                    unseen += sum(heldout)
                for y in (0, 1):
                    terms.append(-heldout[y] * math.log2((observed[y] + 0.5) / (total + 1)))
            # With no training observations the all-0.5 score is reported, but
            # not as a fitted transfer estimate or a gain.
            loss = math.fsum(terms) / nv
        fitted = bool(nt and nv)
        if not taps:
            baselines[target] = loss if fitted else None
        baseline = baselines[target]
        prior = previous.get(target)
        results.append({"name": name, "target_bit": target,
                        "context_taps_first_is_msb": [list(tap) for tap in taps],
                        "training_counts_context_by_outcome": train,
                        "test_counts_context_by_outcome": test,
                        "training_targets": nt, "test_targets": nv,
                        "fitted_transfer": fitted,
                        "test_targets_in_unseen_training_contexts": unseen,
                        "heldout_log_loss_bits": loss,
                        "gain_vs_empty_bits": baseline - loss if fitted and baseline is not None else None,
                        "gain_vs_previous_bits": prior - loss if fitted and prior is not None else None})
        previous[target] = loss if fitted else None
    return results


def measure(blocks):
    observed = fit_score(blocks)
    comparisons = [[] for _ in MODELS]
    for replicate in range(REPLICATES):
        rng = random.Random(SEED + replicate)
        shuffled = []
        for index, block in blocks:
            copy = list(block)
            rng.shuffle(copy)
            shuffled.append((index, copy))
        for i, row in enumerate(fit_score(shuffled)):
            comparisons[i].append({key: row[key] for key in
                                   ("heldout_log_loss_bits", "gain_vs_empty_bits", "gain_vs_previous_bits")})
    for row, scores in zip(observed, comparisons):
        row["permuted_scores"] = scores
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
            "selection": selection, "models": measure(blocks)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", metavar=("ID", "PUBLIC_NAME", "FILE"), required=True)
    args = parser.parse_args()
    ids = [row[0] for row in args.sample]
    if any(not x.isascii() or not x.isdecimal() or int(x) <= 0 for x in ids) or len(set(ids)) != len(ids):
        parser.error("sample IDs must be distinct positive ASCII decimal integers")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "error": type(exc).__name__})
    hashes = {}
    for source in ("token_context_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), source), "rb") as handle:
            hashes[source] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": hashes, "python_version": sys.version.split()[0],
                      "block_tokens": BLOCK, "target_start_within_block": START,
                      "smoothing_per_outcome": 0.5, "replicates": REPLICATES,
                      "seed": SEED, "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    return 1 if failures or any(r["prefix_shortfall"] for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
