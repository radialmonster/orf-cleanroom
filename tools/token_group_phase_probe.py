#!/usr/bin/env python3
"""Group-phase log-proxy ICC diagnostic for lead #32's shared-scale question.

Stdlib Python 3.8+. Reads files, emits aggregates only. Builds on #11/#32 and
repository-original bounded scanner/locator. First 262144 complete candidate
q-zero/stop1/five-suffix tokens, zero extra escape skip. Proxy=log2(1+32q+s),
not established magnitude. Consecutive 126-token blocks start at original 0;
omit entire escape(q>=17) blocks and final tail, never join gaps. For g=3,6
and every phase p=0..g-1, use m=floor((126-g+1)/g) groups per retained block,
starting at p+j*g. Thus each phase has equal group count and no wraparound.

Equal-size one-way ANOVA ICC(1): J groups, grand mean mu, B=g*sum((mean_j-mu)^2),
W=sum_j,sum_i((x_ji-mean_j)^2), MSB=B/(J-1), MSW=W/(J*(g-1));
ICC=(MSB-MSW)/(MSB+(g-1)*MSW). J<2 or zero denominator is null; negative
ICC is retained. Pool groups across retained blocks. Report B/W, dfs, all
phases and max-minus-min phase ICC. Different phases omit different edges;
equal group counts do not imply identical token sets. Slow scene drift can
inflate ICC: 16 Random(20261021+r) whole-token shuffles within each 126 block
preserve block distributions/drift, but remove within-block order. Report
all shuffled phase cells and means. No p-values or selected best phase.

Phase shifts retain local order. Flat phases alone do not rule out physical
blocks, and a shuffle contrast alone does not establish phase locking. Escape
omission is selective and cannot repair unknown framing. This new explicit
proxy/estimator cannot reproduce historical 0.327 on unspecified files. No
valid magnitude, physical groups/rows, significance, decoder or finding.
Short requested prefixes retain observed diagnostics only and exit 1. Errors are
sanitized and successful inputs survive a mixed batch. Verify public CC0
provenance/hash separately. Usage: --sample ID PUBLIC_NAME FILE (repeatable).
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
from orf_signature import Tiff, size_class
from suffix_joint_probe import LIMIT, REPLICATES, SEED, scan_prefix

BLOCK = 126
GROUPS = (3, 6)


def select_blocks(tokens):
    retained = []
    complete = len(tokens) // BLOCK
    omitted = []
    for index in range(complete):
        block = tokens[index * BLOCK:(index + 1) * BLOCK]
        if any(q >= 17 for q, _ in block):
            omitted.append(index)
        else:
            retained.append([math.log2(1 + 32 * q + s) for q, s in block])
    tail = tokens[complete * BLOCK:]
    return retained, {"complete_blocks": complete, "retained_blocks": len(retained),
                      "escape_omitted_blocks": len(omitted), "escape_omitted_tokens": len(omitted) * BLOCK,
                      "escape_omitted_original_block_indices": omitted,
                      "retained_tokens": len(retained) * BLOCK, "tail_tokens": len(tail),
                      "parsed_escapes": sum(q >= 17 for q, _ in tokens),
                      "tail_escapes": sum(q >= 17 for q, _ in tail)}


def phase_cell(blocks, group, phase):
    if group not in GROUPS or type(phase) is not int or not 0 <= phase < group:
        raise ValueError("invalid group or phase")
    if any(len(block) != BLOCK or any(not math.isfinite(x) for x in block) for block in blocks):
        raise ValueError("requires finite complete blocks")
    per_block = (BLOCK - group + 1) // group
    sums, within = [], []
    first_value = None
    varying = False
    for block in blocks:
        for j in range(per_block):
            start = phase + j * group
            values = block[start:start + group]
            if first_value is None:
                first_value = values[0]
            varying = varying or any(x != first_value for x in values)
            total = math.fsum(values)
            mean = total / group
            sums.append(total)
            within.append(math.fsum((x - mean) ** 2 for x in values))
    count = len(sums)
    grand = math.fsum(sums) / (count * group) if count else None
    between = group * math.fsum((s / group - grand) ** 2 for s in sums) if count else 0.0
    wss = math.fsum(within)
    if not varying:
        between, wss = 0.0, 0.0
    dfb, dfw = max(0, count - 1), count * (group - 1)
    msb = between / dfb if dfb else None
    msw = wss / dfw if dfw else None
    denom = msb + (group - 1) * msw if msb is not None and msw is not None else None
    icc = (msb - msw) / denom if denom else None
    return {"group_size": group, "phase": phase, "groups_per_block": per_block,
            "group_count": count, "selected_tokens": count * group,
            "unused_tokens_per_retained_block": BLOCK - per_block * group,
            "grand_mean": grand, "between_ss": between, "within_ss": wss,
            "between_df": dfb, "within_df": dfw, "between_ms": msb,
            "within_ms": msw, "icc1": icc}


def phase_tables(blocks):
    return [phase_cell(blocks, group, phase) for group in GROUPS for phase in range(group)]


def measure(blocks):
    observed = phase_tables(blocks)
    permutations = []
    for replicate in range(REPLICATES):
        rng = random.Random(SEED + replicate)
        shuffled = []
        for block in blocks:
            copied = list(block)
            rng.shuffle(copied)
            shuffled.append(copied)
        permutations.append(phase_tables(shuffled))
    means = []
    for i, cell in enumerate(observed):
        scores = [rep[i]["icc1"] for rep in permutations]
        means.append({"group_size": cell["group_size"], "phase": cell["phase"],
                      "icc1": math.fsum(scores) / len(scores) if all(s is not None for s in scores) else None})
    spread = []
    for group in GROUPS:
        scores = [c["icc1"] for c in observed if c["group_size"] == group]
        spread.append({"group_size": group,
                       "max_minus_min_icc1": max(scores) - min(scores) if all(s is not None for s in scores) else None})
    return {"observed": observed, "phase_spreads": spread,
            "permutations": permutations, "permutation_means": means}


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
    blocks, selection = select_blocks(tokens)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_offset": off,
            "payload_bytes": count, "size_class": "variable", "compression_tag": best.get(0x103),
            "requested_tokens": LIMIT, "returned_tokens": len(tokens),
            "prefix_complete": len(tokens) == LIMIT, "prefix_shortfall": LIMIT - len(tokens),
            "bits_consumed": end, "selection": selection, "statistics": measure(blocks)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    args = parser.parse_args(argv)
    ids = [s[0] for s in args.sample]
    try:
        invalid_ids = any(not s.isascii() or not s.isdecimal() or int(s) <= 0 for s in ids) or len(set(map(int, ids))) != len(ids)
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        parser.error("sample IDs must be distinct positive ASCII decimal integers")
    if any(not name or not name.isprintable() or any(c in name for c in '/\\') for _, name, _ in args.sample):
        parser.error("sample public name must be a printable basename")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            result = report(sample_id, name, path)
            reports.append(result)
            if not result["prefix_complete"]:
                failures.append({"pixls_id": sample_id, "pixls_name": name, "error": "IncompletePrefix"})
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "pixls_name": name, "error": type(exc).__name__})
    hashes = {}
    for source in ("token_group_phase_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), source), "rb") as handle:
            hashes[source] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": hashes, "python_version": sys.version.split()[0],
                      "block_tokens": BLOCK, "group_sizes": GROUPS, "seed": SEED,
                      "permutation_replicates": REPLICATES, "escape_extra_bits": 0,
                      "proxy": "log2(1+32*q+s)", "samples": reports, "failures": failures},
                     indent=2, allow_nan=False))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
