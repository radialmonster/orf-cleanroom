#!/usr/bin/env python3
"""Value field of capped-prefix k=5 ORF strips, assembled from two neighbouring tokens.

Supports: the value-field lead (issue to follow); builds on #951 (token grammar and rows).

Grammar (measured on flat OM-3 payloads, #951): a marker of leading zeros and a 1, then tokens. A token is
q zeros, a 1 stop bit and 5 suffix bits (b4..b0); q >= 12 is an escape (12 zeros and 12 raw
bits). Escapes are skipped. q of the other token is ignored.

For token n with neighbour m (n+1 in the row; n+W+1 with --null):
L = 2*b1(n) + b0(n), X = b2(n), Y = b4(m), N = 1 - b3(m),
value = L + (1 - 2X) * (8Y - 4N) - 12X (read off value histograms; not a decode).

Region: rows 20..ROWS-1, columns 20..W-21. The container is read with orf_signature.Tiff;
the payload is the image IFD with the largest total strip byte count. Standard library only
(Python 3.8+). Prints numbers only: no paths, no image data.

Usage: python -I -B tools/value_field_probe.py [--rows N] [--null] FILE [FILE ...]
"""
import argparse
import collections
import hashlib
import math
import os
import sys
from array import array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff  # noqa: E402

OCTETS = [format(i, "08b") for i in range(256)]
TOP, EDGE = 20, 20           # first region row; columns EDGE..W-EDGE-1
NONE = -128                  # cell without a value
HIST = range(-20, 12)
LAGS = ("1", "2", "3", "4", "W", "2W", "2W-2", "2W+2")


def tokens(strip, need):
    """5-bit suffix of each token, -1 for an escape, for the first `need` tokens."""
    s = "".join(OCTETS[b] for b in strip[:3 * need + 16])   # a token is at most 24 bits
    p = s.find("1") + 1
    out = array("h")
    while len(out) < need and p + 24 <= len(s):
        j = s.find("1", p, p + 12)
        if j < 0:
            out.append(-1)
            p += 24
        else:
            out.append(int(s[j + 1:j + 6], 2))
            p = j + 6
    return out


def corr(val, lag, lo, hi):
    """Pearson r over pairs (i, i+lag) with both values present, from exact integer sums."""
    n = sa = sb = saa = sbb = sab = 0
    for i in range(lo, hi - lag):
        x = val[i]
        if x == NONE:
            continue
        y = val[i + lag]
        if y == NONE:
            continue
        n += 1
        sa += x
        sb += y
        saa += x * x
        sbb += y * y
        sab += x * y
    return (n * sab - sa * sb) / math.sqrt((n * saa - sa * sa) * (n * sbb - sb * sb))


def analyse(path, rows, null):
    with open(path, "rb") as f:
        data = f.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    start, counts = best[0x111][0], best[0x117]
    strip, W, H = data[start:start + sum(counts)], best[0x100][0], best[0x101][0]
    step = W + 1 if null else 1
    S = tokens(strip, (rows + 1) * W)
    if len(S) < (rows + 1) * W:
        raise SystemExit("too few tokens for --rows %d" % rows)
    val = array("b", [NONE]) * len(S)
    vals, csum, cnum, skipped = [], [0, 0], [0, 0], 0
    for r in range(TOP, rows):
        for c in range(EDGE, W - EDGE):
            i = r * W + c
            a, b = S[i], S[i + step]
            if a < 0 or b < 0:
                skipped += 1
                continue
            X, Y, N = (a >> 2) & 1, (b >> 4) & 1, 1 - ((b >> 3) & 1)
            v = (a & 3) + (1 - 2 * X) * (8 * Y - 4 * N) - 12 * X
            val[i] = v
            vals.append(v)
            csum[(r + c) % 2] += v
            cnum[(r + c) % 2] += 1
    n = len(vals)
    m = sum(vals) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / n)
    skew = sum((x - m) ** 3 for x in vals) / n / sd ** 3
    hist = collections.Counter(vals)
    lo, hi = TOP * W, rows * W
    lags = [corr(val, d, lo, hi) for d in (1, 2, 3, 4, W, 2 * W, 2 * W - 2, 2 * W + 2)]
    print("sha256=%s W=%d H=%d region=%d skipped=%d%s" % (
        hashlib.sha256(data).hexdigest(), W, H, (rows - TOP) * (W - 2 * EDGE), skipped,
        " control=n+W+1" if null else ""), flush=True)
    print("n=%d mean=%+.3f sd=%.2f skew=%+.2f class0=%+.3f class1=%+.3f" % (
        n, m, sd, skew, csum[0] / cnum[0], csum[1] / cnum[1]), flush=True)
    print("hist -20..11: " + " ".join("%d:%.3f" % (k, hist[k] / n) for k in HIST), flush=True)
    print("lags " + " ".join("%s=%+.3f" % (name, r) for name, r in zip(LAGS, lags)), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--rows", type=int, default=600,
                    help="region rows 20..N-1 (default 600)")
    ap.add_argument("--null", action="store_true",
                    help="control: neighbour is the cell one row below n+1 (n+W+1)")
    args = ap.parse_args()
    if args.rows <= TOP:
        ap.error("--rows must be greater than %d" % TOP)
    for path in args.files:
        analyse(path, args.rows, args.null)


if __name__ == "__main__":
    main()
