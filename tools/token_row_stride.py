#!/usr/bin/env python3
"""Scan candidate token row strides with a row-start q profile.

Supports: specs/V1.md G3 (row stride drift), lead #30 (row period) and the
P0 follow-up to lead #11. Standard library only; reads sample files and prints
aggregate numbers.

The stream is parsed with the lead #11 model (q zero bits, stop bit, 5-bit
suffix; escape at q >= 17). Rows are not delimited in the stream, so for a
candidate stride S the tool folds the q sequence into rows of S tokens and asks
whether the first K tokens of a row carry a higher mean q than the rest of the
row. A positive peak identifies a candidate periodicity in the chosen prefix;
it does not establish a unique physical row boundary or calibrated significance.

This is a measurement, not a decoder. It makes no claim about where the extra
tokens on a busy body go; it only reports the stride that maximises the
row-start profile.

Usage:
    python -I tools/token_row_stride.py FILE [FILE ...] [--rows N]
        [--min-stride S] [--max-stride S] [--head K] [--top N]
    python -I tools/token_row_stride.py --self-test

Defaults: --rows 300, --head 32, stride range payload width .. width + 1200,
--top 10. --min-stride/--max-stride are absolute token counts.
"""
import argparse
import array
import itertools
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens as T  # noqa: E402


def stride_scores(q, lo, hi, rows, head=32):
    """Return [(z, elevation, S, nrow)] for every S in lo..hi, best first.

    q is an indexable sequence of q values. For each S, nrow is capped by
    `rows` and by the available tokens. The score is the one-sample z of
    d_i = mean(q of the first `head` tokens of row i) - mean(q of the rest),
    over rows. Strides S <= head+1 (no tokens after the head) are skipped.
    """
    n = len(q)
    prefix = array.array("I", itertools.accumulate(q, initial=0))
    out = []
    for s in range(max(lo, head + 2), hi + 1):
        nrow = min(rows, n // s)
        if nrow < 20:
            continue
        vals = []
        for i in range(nrow):
            start = i * s
            a = prefix[start + head] - prefix[start]
            b = prefix[start + s] - prefix[start + head]
            vals.append(a / head - b / (s - head))
        mean = sum(vals) / nrow
        var = sum((v - mean) ** 2 for v in vals) / (nrow - 1)
        if var > 0:
            z = mean / (math.sqrt(var) / math.sqrt(nrow))
        else:
            z = math.copysign(math.inf, mean) if mean != 0 else 0.0
        out.append((z, mean, s, nrow))
    out.sort(reverse=True)
    return out


def scan_file(path, a):
    w, h, buf = T.locate(path)
    lo = a.min_stride if a.min_stride is not None else w
    hi = a.max_stride if a.max_stride is not None else w + 1200
    limit = a.max_tokens if a.max_tokens else a.rows * hi
    qa, sa = array.array("B"), array.array("B")
    T.scan(buf, limit, 0, 0, None, qa, sa, 40)
    scores = stride_scores(qa, lo, hi, a.rows, a.head)
    print("== %s" % os.path.basename(path))
    print("payload: %dx%d  tokens=%d  scan=%d..%d  rows=%d  head=%d" % (
        w, h, len(qa), lo, hi, a.rows, a.head))
    if not scores:
        print("no stride with enough rows")
        return
    for z, elev, s, nrow in scores[:a.top]:
        print("  S=%d  S-W=%+d  rows=%d  z=%.2f  elevation=%.5f" % (
            s, s - w, nrow, z, elev))
    print()


def self_test():
    """Known stride with elevated head; check the peak is at the true S."""
    head, rows, s0 = 24, 80, 137
    q = []
    for i in range(rows):
        q.extend([3 + (i % 2)] * head)
        q.extend([0] * (s0 - head))
    scores = stride_scores(q, s0 - 5, s0 + 5, rows, head)
    best = scores[0]
    assert best[2] == s0, (best, s0)
    assert best[0] > 5, best
    # A flat sequence has no peak above noise.
    flat = [0] * (rows * s0)
    scores = stride_scores(flat, s0 - 2, s0 + 2, rows, head)
    assert scores[0][0] == 0.0, scores[0]
    print("self-test ok: peak S=%d z=%.2f on a synthetic row-start profile" % (best[2], best[0]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--rows", type=int, default=300, help="rows used per stride")
    ap.add_argument("--head", type=int, default=32, help="row-start tokens compared")
    ap.add_argument("--min-stride", type=int, help="smallest candidate stride (default: payload width)")
    ap.add_argument("--max-stride", type=int, help="largest candidate stride (default: width + 1200)")
    ap.add_argument("--max-tokens", type=int, help="cap on parsed tokens")
    ap.add_argument("--top", type=int, default=10, help="rows printed per file")
    ap.add_argument("--self-test", action="store_true", help="run the synthetic test")
    a = ap.parse_args()
    if a.head <= 0:
        ap.error("--head must be positive")
    if a.self_test:
        self_test()
        return
    if not a.files:
        ap.error("no files (or use --self-test)")
    failed = False
    for p in a.files:
        try:
            scan_file(p, a)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            print("%s: %s" % (p, exc), file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
