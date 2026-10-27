#!/usr/bin/env python3
"""Measure complete positive b2 zero runs under the candidate parse (#30, #11).

Default design: first 262144 complete tokens, payload bit zero, q+6 bits/token,
no extra escape bits. Split at and omit every q>=17 token. Count only maximal
positive zero runs bounded by ones inside a segment. Leading/trailing zeros
are censored; an all-zero segment is counted separately, never twice.

The histogram and exact integer sums define population moments. Compare the
variance with mean*(mean-1), the positive-support geometric variance fitted
to that mean. Censoring, nonstationarity and escape selection limit this
descriptive comparison: no goodness-of-fit test, physical rows, run-copy
semantics, decoder or reproduction of historical private figures is claimed.
Omission cannot repair uncertain framing after escapes. Check CC0 separately.
Reads files and prints aggregates only; stdlib Python 3.8+.
Optional --start-token and --tokens select an absolute candidate-token window.
Scanning still begins at payload bit zero; skipped tokens are not retained.
Each window censors both edges independently, even inside an ongoing run.
These windows alone do not establish stationarity or representativeness.
The CLI prints all available reports, then exits 1 if any input failed or any
requested start/window was incomplete; complete error-free reports exit 0.
Public names must be printable basenames; licence verification remains separate.
Public sample IDs must be distinct numerically; leading-zero aliases count as
the same ID. Licence verification remains separate from this identity check.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class  # noqa: E402
from suffix_joint_probe import LIMIT  # noqa: E402


def scan_window(payload, start_token=0, limit=LIMIT):
    """Retain only the selected window; indices count escapes too.

    start_bit is the boundary reached after skipping, even on start shortfall.
    Incomplete terminal tokens are rejected.
    """
    if start_token < 0 or limit <= 0:
        raise ValueError("nonnegative start and positive token count required")
    selected = []
    pos = skipped = skipped_escapes = start_bit = 0
    nbits = len(payload) * 8
    while skipped < start_token or len(selected) < limit:
        boundary = pos
        q = 0
        while pos < nbits and not ((payload[pos >> 3] >> (7 - (pos & 7))) & 1):
            q += 1
            pos += 1
        if pos + 6 > nbits:
            pos = boundary
            break
        suffix = 0
        for j in range(1, 6):
            suffix = (suffix << 1) | ((payload[(pos + j) >> 3] >> (7 - ((pos + j) & 7))) & 1)
        pos += 6
        if skipped < start_token:
            skipped += 1
            skipped_escapes += q >= 17
            start_bit = pos
        else:
            selected.append((q, suffix))
    return selected, dict(bits_consumed=pos, window_start_bit=start_bit,
                          window_bits_consumed=pos-start_bit,
                          skipped_tokens=skipped, skipped_escape_tokens=skipped_escapes,
                          start_shortfall=start_token-skipped)


def measure(tokens):
    histogram = Counter()
    counts = dict(retained_tokens=0, omitted_escape_tokens=0, segments=0,
                  zero_tokens=0, one_tokens=0, leading_censored_zeros=0,
                  trailing_censored_zeros=0, all_zero_segment_zeros=0)
    segment_length = zeros = 0
    seen_one = False

    def finish():
        if segment_length:
            counts["segments"] += 1
            key = "trailing_censored_zeros" if seen_one else "all_zero_segment_zeros"
            counts[key] += zeros

    for q, suffix in tokens:
        if q >= 17:
            finish()
            counts["omitted_escape_tokens"] += 1
            segment_length = zeros = 0
            seen_one = False
            continue
        counts["retained_tokens"] += 1
        segment_length += 1
        bit = (suffix >> 2) & 1
        counts["one_tokens" if bit else "zero_tokens"] += 1
        if not bit:
            zeros += 1
        else:
            if zeros:
                if seen_one:
                    histogram[zeros] += 1
                else:
                    counts["leading_censored_zeros"] += zeros
            seen_one = True
            zeros = 0
    finish()
    n = sum(histogram.values())
    total = sum(k * v for k, v in histogram.items())
    squares = sum(k * k * v for k, v in histogram.items())
    mean = total / n if n else None
    variance = (squares * n - total * total) / (n * n) if n else None
    geometric = mean * (mean - 1) if n else None
    assert counts["zero_tokens"] == total + sum(counts[k] for k in (
        "leading_censored_zeros", "trailing_censored_zeros", "all_zero_segment_zeros"))
    return dict(counts, complete_positive_runs=n, sum_run_lengths=total,
                sum_squared_run_lengths=squares,
                histogram=[{"length": k, "count": histogram[k]} for k in sorted(histogram)],
                population_mean=mean, population_variance=variance,
                fitted_positive_geometric_variance=geometric,
                variance_ratio=variance / geometric if geometric else None)


def report(sample_id, name, path, start_token=0, limit=LIMIT):
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
    tokens, window = scan_window(data[off:off + count], start_token, limit)
    return dict(pixls_id=sample_id, pixls_name=name,
                sha256=hashlib.sha256(data).hexdigest(), variant="unassigned",
                payload_w=w, payload_h=h, payload_offset=off, payload_bytes=count,
                size_class="variable", compression_tag=best.get(0x103),
                requested_start_token=start_token,
                requested_tokens=limit, returned_tokens=len(tokens),
                prefix_shortfall=limit-len(tokens),
                token_shortfall=limit-len(tokens), **window,
                statistics=measure(tokens))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    parser.add_argument("--start-token", type=int, default=0,
                        help="absolute candidate token index (default: 0)")
    parser.add_argument("--tokens", type=int, default=LIMIT,
                        help="requested window length (default: 262144)")
    args = parser.parse_args()
    if args.start_token < 0 or args.tokens <= 0:
        parser.error("--start-token must be nonnegative and --tokens positive")
    ids = [sample[0] for sample in args.sample]
    if any(not x.isascii() or not x.isdecimal() or int(x) <= 0 for x in ids) or len(set(map(int, ids))) != len(ids):
        parser.error("sample IDs must be distinct positive ASCII decimal integers")
    if any(not name or not name.isprintable() or any(c in name for c in "/\\")
           for _, name, _ in args.sample):
        parser.error("sample public name must be a printable basename")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path, args.start_token, args.tokens))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append(dict(pixls_id=sample_id, error=type(exc).__name__))
    sources = {}
    for filename in ("token_zero_runs_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps(dict(source_sha256=sources, python_version=sys.version.split()[0],
                          escape_extra_bits=0, suffix_bit=2, samples=reports,
                          failures=failures), indent=2, allow_nan=False))
    incomplete = any(r["start_shortfall"] or r["token_shortfall"] for r in reports)
    return 1 if failures or incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
