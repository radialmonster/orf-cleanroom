#!/usr/bin/env python3
"""Held-out binary-q running-count prediction under the candidate parse (#29/7).

Stdlib Python 3.8+. Reads samples and prints aggregates only. Builds on #11,
#29 and suffix_joint_probe.py's bounded scanner, not another raw decoder.
First 262144 complete tokens; q>=17 consumes q+6 bits with no extra skip.
Omit entire escape-containing 128-token blocks and incomplete tail. Original
even blocks train; odd blocks test, without renumbering omissions. No context
crosses a block boundary. Every model predicts q>0 at common targets t>=16.

Models: frequency only; prior q>0; positive-q count in preceding 8/16 tokens;
prior q>0 plus each count. Counts include t-1 and exclude the target. The joint
context is previous_bit*(window+1)+count. Jeffreys half-count smoothing fits
P(y|c)=(n[c,y]+0.5)/(n[c]+1); unseen contexts predict 0.5. Held-out log-loss is
cross-entropy, not empirical entropy. Print exact train/test tables, every loss
and signed gain vs frequency/lag1, and unseen-context test counts. A loss/gain
requires nonempty training AND test sets; negative gains remain negative.
Incomplete requested prefixes retain observed-block diagnostics, but report
prefix_complete=false and make the CLI exit nonzero. Input failures retain
other reports and expose only public identity and sanitized error class.

Sixteen Random(20261021+replicate) within-block whole-token permutations refit
and retest. They preserve block marginals, not temporal dependence. Comparison
means are descriptive, not p-values. Blocks are not camera rows; adjacent split
blocks may depend. Omissions are selective and cannot repair unknown escape
framing. Binary-q counts differ from historical q/running-mean entropy claims;
no codec, causal, stationarity or historical private-number inference follows.

Usage: python -I -B tools/token_scale_probe.py --sample ID PUBLIC_NAME FILE
Repeat --sample; check public licences separately before measurement.
Sample IDs must be distinct positive ASCII decimals and names printable basenames.
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
from suffix_joint_probe import BLOCK, LIMIT, REPLICATES, SEED, scan_prefix
from orf_signature import Tiff, size_class

MODELS = (("frequency", 0, False), ("lag1", 1, False),
          ("count8", 8, False), ("count16", 16, False),
          ("lag1_count8", 8, True), ("lag1_count16", 16, True))


def select_blocks(tokens):
    """Retain (original block number, binary q sequence), never close a gap."""
    complete = len(tokens) // BLOCK
    retained = []
    omitted = [0, 0]
    for index in range(complete):
        block = tokens[index * BLOCK:(index + 1) * BLOCK]
        if any(q >= 17 for q, _ in block):
            omitted[index % 2] += 1
        else:
            retained.append((index, [int(q > 0) for q, _ in block]))
    tail = tokens[complete * BLOCK:]
    return retained, {
        "complete_blocks": complete,
        "train_blocks": sum(index % 2 == 0 for index, _ in retained),
        "test_blocks": sum(index % 2 == 1 for index, _ in retained),
        "escape_omitted_train_blocks": omitted[0],
        "escape_omitted_test_blocks": omitted[1],
        "tail_tokens": len(tail), "tail_escapes": sum(q >= 17 for q, _ in tail),
        "parsed_escapes": sum(q >= 17 for q, _ in tokens)}


def tables(blocks, window, joint):
    contexts = (window + 1) * (2 if joint else 1)
    train, test = ([[0, 0] for _ in range(contexts)] for _ in range(2))
    for index, bits in blocks:
        table = test if index % 2 else train
        for t in range(16, len(bits)):
            context = sum(bits[t - window:t]) if window else 0
            if joint:
                context += bits[t - 1] * (window + 1)
            table[context][bits[t]] += 1
    return train, test


def score(train, test):
    n_train, n_test = sum(map(sum, train)), sum(map(sum, test))
    unseen = sum(sum(b) for a, b in zip(train, test) if not sum(a))
    loss = None
    if n_train and n_test:
        terms = []
        for a, b in zip(train, test):
            for y in range(2):
                probability = (a[y] + 0.5) / (sum(a) + 1)
                terms.append(-b[y] * math.log2(probability))
        loss = math.fsum(terms) / n_test
    return {"train_targets": n_train, "test_targets": n_test,
            "test_targets_with_unseen_context": unseen, "loss_bits": loss}


def fitted_scores(blocks, include_tables=True):
    reports = []
    for name, window, joint in MODELS:
        train, test = tables(blocks, window, joint)
        result = {"model": name, "window": window, "joint_lag1": joint}
        result.update(score(train, test))
        if include_tables:
            result.update({"train_context_by_target": train, "test_context_by_target": test})
        reports.append(result)
    for result in reports:
        for label, control in (("frequency", reports[0]), ("lag1", reports[1])):
            a, b = control["loss_bits"], result["loss_bits"]
            result["gain_vs_" + label + "_bits"] = a - b if a is not None and b is not None else None
    return reports


def measure(blocks):
    observed = fitted_scores(blocks)
    permutations = []
    for replicate in range(REPLICATES):
        rng = random.Random(SEED + replicate)
        shuffled = []
        for index, bits in blocks:
            copied = list(bits)
            rng.shuffle(copied)
            shuffled.append((index, copied))
        permutations.append(fitted_scores(shuffled, False))
    means = []
    for i, (name, _, _) in enumerate(MODELS):
        result = {"model": name}
        for key in ("loss_bits", "gain_vs_frequency_bits", "gain_vs_lag1_bits"):
            values = [rep[i][key] for rep in permutations]
            result[key] = math.fsum(values) / len(values) if all(v is not None for v in values) else None
        means.append(result)
    return {"observed": observed, "permutations": permutations, "permutation_means": means}


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
        raise ValueError("requires positive variable-size payload")
    tokens, end = scan_prefix(data[off:off + count])
    blocks, selection = select_blocks(tokens)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_bytes": count,
            "payload_offset": off, "size_class": "variable",
            "compression_tag": (best.get(0x103) or [None])[0],
            "requested_tokens": LIMIT, "returned_tokens": len(tokens),
            "shortfall_tokens": LIMIT - len(tokens),
            "prefix_complete": len(tokens) == LIMIT, "bits_consumed": end,
            "selection": selection, "statistics": measure(blocks)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    args = parser.parse_args(argv)
    ids = [sid for sid, _, _ in args.sample]
    try:
        invalid_ids = any(not sid.isascii() or not sid.isdecimal() or int(sid) <= 0 for sid in ids) or len(set(map(int, ids))) != len(ids)
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        parser.error("sample IDs must be distinct positive ASCII decimals")
    if any(not name or not name.isprintable() or any(c in name for c in '/\\') for _, name, _ in args.sample):
        parser.error("sample public name must be a printable basename")
    reports, errors = [], []
    for sid, name, path in args.sample:
        try:
            result = report(sid, name, path)
            reports.append(result)
            if not result["prefix_complete"]:
                errors.append({"pixls_id": sid, "pixls_name": name,
                               "error_type": "IncompletePrefix"})
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            errors.append({"pixls_id": sid, "pixls_name": name,
                           "error_type": type(exc).__name__})
    hashes = {}
    for source in ("token_scale_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), source), "rb") as handle:
            hashes[source] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": hashes, "python_version": sys.version.split()[0],
                      "block_tokens": BLOCK, "first_target": 16, "seed": SEED,
                      "permutation_replicates": REPLICATES,
                      "samples": reports, "errors": errors}, indent=2, allow_nan=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
