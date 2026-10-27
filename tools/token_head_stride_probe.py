#!/usr/bin/env python3
"""Bounded head-by-stride held-out diagnostic for #144; aggregates only.

Builds on #11/#218/#230. All candidate training/test cells are retained.
Strides define absolute r*S token blocks, with a global nonoverlap guard.
Known-profile reused inputs remain exploratory. No null, significance,
physical rows, true escape grammar, historical reproduction or decode.
Stdlib only; reads samples and prints JSON, never token/pixel arrays.
Sample IDs must be unique positive ASCII decimals; names must be printable
and contain no path separators.
"""
import argparse
import hashlib
import json
import os
import platform
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_band_profile as B


def diagnostic(qs, strides, heads, rows):
    """Select signed training mean/SE per head; test starts after ALL training."""
    strides, heads = sorted(set(strides)), sorted(set(heads))
    if not strides or not heads or rows < 2 or min(heads) < 1 or min(strides) <= max(heads):
        raise ValueError("require rows>=2 and stride>head>=1")
    training_end = rows * max(strides)
    test_row = (training_end + min(strides) - 1) // min(strides)
    earliest_test = test_row * min(strides)
    cells = []
    selections = []
    for head in heads:
        group = []
        for stride in strides:
            train = B.profile(qs, stride, 0, rows, head)
            test = B.profile(qs, stride, test_row, rows, head)
            cell = dict(head=head, stride=stride, train=train, test=test)
            group.append(cell)
            cells.append(cell)
        # Complete training is mandatory; undefined scores cannot win.
        eligible = [c for c in group if c["train"]["complete"] and c["train"]["score_defined"]]
        if eligible:
            maximum = max(c["train"]["signed_mean_over_se"] for c in eligible)
            ties = [c["stride"] for c in eligible if c["train"]["signed_mean_over_se"] == maximum]
            selected = next(c for c in group if c["stride"] == min(ties))
            selections.append(dict(head=head, selected_stride=min(ties),
                                   training_score_maximum=maximum, tied_strides=ties,
                                   selected_test=selected["test"]))
        else:
            selections.append(dict(head=head, selected_stride=None, tied_strides=[],
                                   training_score_maximum=None, selected_test=None))
    complete = all(c["train"]["complete"] and c["test"]["complete"] for c in cells)
    return dict(strides=strides, heads=heads, rows_per_split=rows,
                training_latest_end_token_exclusive=training_end,
                test_start_candidate_row=test_row, test_earliest_start_token=earliest_test,
                training_test_gap_tokens=earliest_test-training_end,
                requested_tokens=(test_row + rows)*max(strides), complete=complete,
                selections=selections, cells=cells)


def measure(path, digest, center, radius, heads, rows):
    strides = list(range(center-radius, center+radius+1))
    # Validate geometry and compute global parse bound before sample access.
    shape = diagnostic(B.array.array("B"), strides, heads, rows)
    with open(path, "rb") as source:
        data = source.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest.lower():
        raise ValueError("SHA-256 does not match supplied verified record")
    t = B.Tiff(data)
    best = max(t.all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    w, h = best[0x100][0], best[0x101][0]
    offsets, sizes = best[0x111], best[0x117]
    if len(offsets) != 1 or len(sizes) != 1:
        raise ValueError("require one contiguous payload strip")
    off, size = offsets[0], sizes[0]
    if off < 0 or size <= 0 or off + size > len(data):
        raise ValueError("payload strip outside file")
    if B.size_class(size, w, h) != "variable":
        raise ValueError("require variable-size payload")
    qs, bits = B.scan_q(data[off:off+size], shape["requested_tokens"])
    result = diagnostic(qs, strides, heads, rows)
    result.update(sha256=actual, payload_width=w, payload_height=h,
                  payload_bytes=size, compression_tag=best.get(0x103), size_class="variable",
                  center=center, radius=radius, parsed_tokens=len(qs), consumed_bits=bits,
                  token_shortfall=shape["requested_tokens"]-len(qs))
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", nargs=5, action="append", required=True,
                    metavar=("ID", "NAME", "SHA256", "CENTER", "FILE"))
    ap.add_argument("--radius", type=int, default=16)
    ap.add_argument("--head", type=int, action="append")
    ap.add_argument("--rows", type=int, default=150)
    args = ap.parse_args(argv)
    heads = sorted(set(args.head if args.head is not None else [8, 32, 128]))
    if args.radius < 0 or args.rows < 2 or min(heads) < 1:
        ap.error("require radius>=0, rows>=2 and head>=1")
    ids = [sample[0] for sample in args.sample]
    try:
        if any(not sid.isascii() or not sid.isdecimal() or int(sid) <= 0 for sid in ids):
            raise ValueError
        if len(set(int(sid) for sid in ids)) != len(ids):
            raise ValueError
    except ValueError:
        ap.error("sample IDs must be distinct positive ASCII decimals")
    if any(not name or not name.isprintable() or any(c in name for c in "/\\")
           for _, name, _, _, _ in args.sample):
        ap.error("sample public name must be printable without path separators")
    samples, failed = [], False
    for sid, name, digest, center, path in args.sample:
        entry = dict(pixls_id=sid, pixls_name=name)
        try:
            if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
                raise ValueError("invalid verified hash")
            entry.update(measure(path, digest, int(center), args.radius, heads, args.rows))
            entry["ok"] = entry["complete"] and entry["token_shortfall"] == 0
        except (OSError, ValueError, KeyError, TypeError, IndexError, struct.error) as exc:
            entry.update(ok=False, error=type(exc).__name__)
        failed = failed or not entry["ok"]
        samples.append(entry)
    print(json.dumps(dict(schema_version=1, method="head-stride-signed-score-holdout",
                          python_version=platform.python_version(), q_cap=40,
                          escape_extra_bits=0, samples=samples), indent=2, allow_nan=False))
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
