#!/usr/bin/env python3
"""Measure pairwise b2/b4 lag dependence for #29 item 4; builds on #11.

Stdlib Python 3.8+, aggregate JSON only, no preview access or decoding.
Fixed design: first 262144 complete candidate tokens from payload bit zero,
128-token blocks, omit whole blocks containing q>=17 and incomplete tails.
Escapes consume q+6 bits with no extra skip. Omission does not repair unknown
post-escape framing; blocks are not established camera rows.

For every lag 1..5 and ordered source/target pair in {b2,b4} squared, report
the exact 2x2 counts of source(t-lag), target(t), unsmoothed plug-in MI in bits
and Pearson correlation. Pairs never cross block boundaries. Sixteen fixed
seed within-block whole-token permutations preserve block marginals and
within-token dependence, destroying temporal structure. All comparison MI
values are reported; these are descriptive comparisons, not p-values.
Pairwise MI cannot establish the multivariate conditional chain, historical
held-out/smoothed gains, a deeper law, physical rows or a decoder.
Match samples to retained verified licence/hash records before use. An unmet
fixed-prefix request exits nonzero; retained short-prefix statistics describe
only observed blocks. Source hashes pin all repository imports.
Sample IDs must be distinct positive ASCII decimals; names must be printable
and contain no path separators.
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
from suffix_joint_probe import (BLOCK, LIMIT, REPLICATES, SEED, correlation,
                                mutual_information, scan_prefix, select_blocks)  # noqa: E402

LAGS = tuple(range(1, 6))
BITS = (2, 4)


def tables(blocks):
    """Pool symbol pairs once, then marginalize into all ordered bit pairs."""
    result = {}
    symbols = [[((s >> 2) & 1) + 2 * ((s >> 4) & 1) for s in block] for block in blocks]
    for lag in LAGS:
        joint = [[0] * 4 for _ in range(4)]
        for block in symbols:
            for i in range(lag, len(block)):
                joint[block[i - lag]][block[i]] += 1
        for source in BITS:
            for target in BITS:
                table = [[0] * 2 for _ in range(2)]
                for a in range(4):
                    for b in range(4):
                        table[(a >> (source == 4)) & 1][(b >> (target == 4)) & 1] += joint[a][b]
                result[(lag, source, target)] = table
    return result


def measure(blocks):
    observed = tables(blocks)
    comparisons = {key: [] for key in observed}
    for replicate in range(REPLICATES):
        rng = random.Random(SEED + replicate)
        shuffled = []
        for block in blocks:
            copy = list(block)
            rng.shuffle(copy)
            shuffled.append(copy)
        for key, table in tables(shuffled).items():
            comparisons[key].append(mutual_information(table))
    results = []
    for (lag, source, target), table in observed.items():
        values = comparisons[(lag, source, target)]
        n = sum(map(sum, table))
        results.append({"lag_tokens": lag, "source_bit": source, "target_bit": target,
                        "pair_count": n, "joint_source_rows_target_columns": table,
                        "plugin_mi_bits": mutual_information(table), "pearson": correlation(table),
                        "permuted_plugin_mi_bits": values,
                        "permuted_mi_mean_bits": sum(values) / len(values) if n else None})
    return results


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
            "payload_bytes": count, "size_class": "variable",
            "compression_tag": best.get(0x103), "bits_consumed": end,
            "requested_tokens": LIMIT, "returned_tokens": len(tokens),
            "prefix_shortfall": LIMIT - len(tokens), "selection": selection,
            "statistics": measure(blocks)}


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
    for filename in ("token_bit_chain_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": sources, "python_version": sys.version.split()[0],
                      "escape_extra_bits": 0, "block_tokens": BLOCK,
                      "permutation_replicates": REPLICATES, "seed": SEED,
                      "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    return 1 if failures or any(r["prefix_shortfall"] for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
