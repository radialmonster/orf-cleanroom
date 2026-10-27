#!/usr/bin/env python3
"""Test exact affine b2/b4 context consistency under the candidate parse (#29).

Reads samples and prints aggregate JSON only, stdlib Python 3.8+.
First 262144 complete q-zero/one/five-suffix tokens, no extra escape bits.
For each target b2/b4 use both bits at lags 1..12: context bit 2*(lag-1)
is b2 and bit 2*(lag-1)+1 is b4. Bit24 is the affine intercept (one).
Discard any context-plus-target 13-token window containing q>=17; preserve
absolute target indices for pooled/even/odd systems. No bridging omissions.
Report rank(X) and rank([X|y]) over GF(2). Equal ranks mean some exact affine
predictor fits these selected rows; an increase excludes only that function
class/context on these rows. Empty systems have no evidence (null verdict).
Selective omissions cannot repair uncertain post-escape framing. No historical
private rank reproduction, significance, general scrambler exclusion, physical
row identification, nonlinear/noisy-law exclusion or decoding is claimed.
Incomplete requested prefixes retain diagnostic ranks but exit nonzero; their
consistency verdict applies only to observed selected rows. All supplied sample
identities survive input errors, with sanitized error classes and no local paths.
Reuse verified CC0 records after matching local hashes; new content needs its
first licence verification. Builds on #11, #29, #166 and #169.
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
from suffix_joint_probe import LIMIT, scan_prefix  # noqa: E402

LAGS = 12
CONTEXT_COLUMNS = 2 * LAGS + 1


class Basis:
    """Incremental exact binary row elimination; Python integers pack columns."""
    def __init__(self):
        self.pivots = {}

    def add(self, row):
        if not isinstance(row, int) or row < 0:
            raise ValueError("row must be a nonnegative integer")
        while row:
            pivot = row.bit_length() - 1
            if pivot not in self.pivots:
                self.pivots[pivot] = row
                return
            row ^= self.pivots[pivot]

    def rank(self):
        return len(self.pivots)


def measure(tokens):
    systems = {(bit, group): [Basis(), Basis(), 0]
               for bit in (2, 4) for group in ("pooled", "even", "odd")}
    candidate = max(0, len(tokens) - LAGS)
    omitted = {"pooled": 0, "even": 0, "odd": 0}
    escapes = 0
    for t, (q, suffix) in enumerate(tokens):
        escapes += q >= 17
        if t > LAGS:
            escapes -= tokens[t - LAGS - 1][0] >= 17
        if t < LAGS:
            continue
        parity = "odd" if t % 2 else "even"
        if escapes:
            omitted["pooled"] += 1
            omitted[parity] += 1
            continue
        context = 1 << (CONTEXT_COLUMNS - 1)
        for lag in range(1, LAGS + 1):
            past = tokens[t - lag][1]
            context |= ((past >> 2) & 1) << (2 * (lag - 1))
            context |= ((past >> 4) & 1) << (2 * (lag - 1) + 1)
        for bit in (2, 4):
            augmented = context | (((suffix >> bit) & 1) << CONTEXT_COLUMNS)
            for group in ("pooled", parity):
                x, xy, _ = systems[bit, group]
                x.add(context)
                xy.add(augmented)
                systems[bit, group][2] += 1
    results = []
    for (bit, group), (x, xy, count) in systems.items():
        results.append({"target": "b%d" % bit, "stratum": group,
                        "retained_rows": count, "omitted_escape_windows": omitted[group],
                        "context_rank": x.rank(), "augmented_rank": xy.rank(),
                        "exact_affine_consistent": x.rank() == xy.rank() if count else None})
    return {"candidate_windows": candidate,
            "parsed_escapes": sum(q >= 17 for q, _ in tokens), "systems": results}


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
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": w, "payload_h": h, "payload_bytes": count,
            "size_class": "variable", "bits_consumed": end,
            "requested_tokens": LIMIT, "returned_tokens": len(tokens),
            "token_shortfall": LIMIT - len(tokens),
            "prefix_complete": len(tokens) == LIMIT, "statistics": measure(tokens)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    args = parser.parse_args()
    ids = [sample_id for sample_id, _, _ in args.sample]
    try:
        invalid_ids = any(not i.isascii() or not i.isdecimal() or int(i) <= 0 for i in ids) or len(set(map(int, ids))) != len(ids)
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        parser.error("sample IDs must be distinct positive ASCII decimals")
    if any(not name or not name.isprintable() or any(c in name for c in '/\\') for _, name, _ in args.sample):
        parser.error("sample public name must be a printable basename")
    reports = []
    failures = []
    incomplete = False
    for sample_id, name, path in args.sample:
        try:
            item = report(sample_id, name, path)
            reports.append(item)
            incomplete = incomplete or not item["prefix_complete"]
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "pixls_name": name,
                             "error": type(exc).__name__})
    sources = {}
    for name in ("token_affine_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), name), "rb") as handle:
            sources[name] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": sources, "python_version": sys.version.split()[0],
                      "lags": LAGS, "context_columns_including_intercept": CONTEXT_COLUMNS,
                      "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    return 1 if failures or incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
