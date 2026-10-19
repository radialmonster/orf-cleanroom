#!/usr/bin/env python3
"""Parse the token stream (lead #11) of compressed ORF/ORI files and print aggregate statistics.

Supports: lead #11 (token structure and neighbour dependence), specs/V1.md Gaps.
Standard library only (Python 3.8+). Prints numbers only, no images or pixel dumps.

The payload is located as in orf_signature.py (the image IFD with the largest
strip byte count) and read MSB-first from its first byte. A token is q zero bits,
a 1 stop bit, then a 5-bit suffix b4..b0. q >= 17 is an escape. What follows an
escape is not understood (lead #11), so by default an escape is parsed like any other
token (zeros, stop bit, 5 bits) and then left out of every H/L statistic;
--escape-extra N skips N more bits after an escape to try other layouts.
Suffix: H = b4b3 and L = b2b1b0 are only labels for the two bit groups; both are
read as plain unsigned numbers (no signed or other meaning is assumed).

Rows cannot be delimited from the stream alone: no row marker is known. So the
tool reports (a) total tokens against width x height, and (b) the bit position,
modulo 8, at every multiple of the payload width in tokens (if rows were
byte-aligned this would be 0 every time). Token positions are sequential across
what would be row ends; neighbour pairs skip escapes.

Statistics (plug-in estimates, bits, with a rotated-pair baseline that shows
the estimator bias; read a value as real only if well above its baseline):
  MI at token lags 1-3 for H->L, L->H, L->L, H->H; the gain of b2 given
  b4(t-1) and b2(t-2); and, using the payload width as the row stride,
  vertical lag-2 L-L and H-H.

Also printed: tokens per pixel against a Bernoulli null (every bit independent,
with the ones-density of the parsed bits; the null token costs 6 + (1-p)/p bits),
and the correlation of min(q,8) at lags 1, 2, 3, 6 and W. With --escape-landing,
for every escape it finds the distance from the start of its zero run to the
start of the next token that makes the following 24 tokens most q=0 (only
meaningful on bodies where q=0 is the large majority), tabulated by escape q.

Usage: python orf_tokens.py FILE [FILE ...] [--max-tokens N | --all] [--rows N]
                            [--stride W] [--escape-extra N] [--escape-landing]
Default is the first 2,000,000 tokens; --all parses the whole payload (slow in
pure Python, roughly a million tokens per second or less; speed is reported).
--rows N is shorthand for --max-tokens N x width.
"""
import argparse
import array
import collections
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff  # noqa: E402

ESC_Q = 17
WIN = 12  # bytes in the read window (96 bits)


def locate(path):
    with open(path, "rb") as f:
        data = f.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    off, n = best[0x111][0], sum(best[0x117])
    return best[0x100][0], best[0x101][0], data[off:off + n]


def parse(buf, max_tokens, w, esc_extra=0, esc_pos=None):
    """Return (q list, suffix list, bit position at every w-th token, bits used)."""
    nbits = len(buf) * 8
    pad = buf + bytes(WIN)
    qs, ss, marks = [], [], []
    pos = 0
    n = 0
    frm = int.from_bytes
    while n < max_tokens and pos + 6 <= nbits:
        if w and n % w == 0:
            marks.append(pos)
        win = frm(pad[pos >> 3:(pos >> 3) + WIN], "big")
        avail = WIN * 8 - (pos & 7)
        v = win & ((1 << avail) - 1)
        if v == 0 or avail - v.bit_length() + 6 > avail:
            # zero run longer than the window: count it bit by bit
            q = 0
            p = pos
            while p < nbits and not (buf[p >> 3] >> (7 - (p & 7))) & 1:
                q += 1
                p += 1
            if p + 6 > nbits:
                break
            s = 0
            for k in range(1, 6):
                s = (s << 1) | ((buf[(p + k) >> 3] >> (7 - ((p + k) & 7))) & 1)
            pos = p + 6
        else:
            q = avail - v.bit_length()
            s = (v >> (avail - q - 6)) & 31
            pos += q + 6
        if q >= ESC_Q:
            if esc_pos is not None:
                esc_pos.append((pos - q - 6, q))  # bit position of the zero run's first bit
            pos += esc_extra
        qs.append(q)
        ss.append(s)
        n += 1
    return qs, ss, marks, pos


MISSING = 9  # symbol for "no value" (escape tokens)


def entropy(counter):
    n = sum(counter.values())
    return -sum(c / n * math.log2(c / n) for c in counter.values() if c) if n else 0.0


def mi_pairs(xs, ys, rot=0):
    """Plug-in MI (bits) of aligned sequences; pairs holding MISSING are dropped.
    rot > 0 rotates ys by rot positions first: that destroys local dependence but
    keeps the marginals, so it measures the estimator's bias (the baseline)."""
    if rot:
        ys = ys[rot:] + ys[:rot]
    joint = collections.Counter(zip(xs, ys))
    cx, cy = collections.Counter(), collections.Counter()
    for (x, y), c in list(joint.items()):
        if x == MISSING or y == MISSING:
            del joint[(x, y)]
        else:
            cx[x] += c
            cy[y] += c
    return entropy(cx) + entropy(cy) - entropy(joint), sum(joint.values())


def lagged(a, b, lag):
    """Aligned (a[t-lag], b[t]) sequences."""
    return a[:len(a) - lag], b[lag:]


def mi_base(a, b, lag=0):
    x, y = lagged(a, b, lag)
    v, n = mi_pairs(x, y)
    base, _ = mi_pairs(x, y, len(y) // 2 + 12345)
    return v, base, n


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((u - mx) ** 2 for u in x)
    syy = sum((v - my) ** 2 for v in y)
    sxy = sum((u - mx) * (v - my) for u, v in zip(x, y))
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


def landing(buf, esc_extra, look=24, span=48, needed=20):
    """Table of escape q against where the next token lattice starts. After an escape the
    stream is a 6-bit-period lattice again, so only the landing distance modulo 6 is
    identifiable: for every escape, the distance L (bits from the zero run's first bit to
    the next token's first bit) is tried over `span` values, scored by how many of the next
    `look` tokens have q=0, and the best residue of L mod 6 is kept if it scores >= needed
    and is unique. A plain parse lands at q + 6 + escape-extra; a fixed 31-bit word at 31.
    Only meaningful on bodies where q=0 is the large majority."""
    escs = []
    parse(buf, 1 << 62, 0, esc_extra, escs)
    tab = collections.defaultdict(collections.Counter)
    unsure = 0
    for start, q in escs:
        best = {}
        for land in range(q + 1, q + 1 + span):
            sc = sum(1 for x in parse_at(buf, start + land, look) if x == 0)
            r = land % 6
            if sc > best.get(r, -1):
                best[r] = sc
        top = max(best.values())
        winners = [r for r, sc in best.items() if sc == top]
        if top >= needed and len(winners) == 1:
            tab[q][winners[0]] += 1
        else:
            unsure += 1
    print("escape landing, best L mod 6 (unique, >= %d of %d q=0 tokens): %d escapes, %d unresolved" % (
        needed, look, len(escs), unsure))
    for q in sorted(tab):
        tot = sum(tab[q].values())
        print("  q=%d: n=%d  L mod 6 -> %s  | plain parse (q+6+extra) = %d, 31-bit word = %d" % (
            q, tot, " ".join("%d:%d" % kv for kv in sorted(tab[q].items())), (q + 6 + esc_extra) % 6, 31 % 6))


def parse_at(buf, pos, count):
    """q values of `count` tokens starting at bit position pos."""
    nbits = len(buf) * 8
    out = []
    for _ in range(count):
        q = 0
        while pos < nbits and not (buf[pos >> 3] >> (7 - (pos & 7))) & 1:
            q += 1
            pos += 1
        if pos + 6 > nbits:
            break
        out.append(q)
        pos += 6
    return out


def report(path, a):
    t0 = time.time()
    w, h, buf = locate(path)
    stride = a.stride or w
    limit = a.max_tokens
    if a.rows:
        limit = a.rows * w
    if a.all:
        limit = 1 << 62
    qs, ss, marks, endpos = parse(buf, limit, stride, a.escape_extra)
    dt = time.time() - t0
    n = len(qs)
    nbits = len(buf) * 8
    print("== %s" % os.path.basename(path))
    print("payload: %dx%d  bytes=%d  bpp=%.3f" % (w, h, len(buf), nbits / (w * h)))
    complete = endpos + 6 > nbits
    print("tokens parsed: %d%s  in %.1fs (%.2f Mtok/s)" % (
        n, " (whole payload)" if complete else " (prefix)", dt, n / dt / 1e6 if dt else 0))
    if complete:
        print("tokens / (W*H): %.5f  (%+.3f%%)" % (n / (w * h), (n / (w * h) - 1) * 100))
    print("bits per token: %.4f  bits consumed=%d" % (endpos / n if n else 0, endpos))
    if marks:
        al = sum(1 for m in marks if m % 8 == 0)
        mod = collections.Counter(m % 8 for m in marks)
        print("row-start (every %d tokens) bit pos mod 8: aligned %d/%d  dist=%s" % (
            stride, al, len(marks), dict(sorted(mod.items()))))
        if len(marks) > 1:
            d = [y - x for x, y in zip(marks, marks[1:])]
            print("bits per %d-token block: mean=%.1f min=%d max=%d" % (
                stride, sum(d) / len(d), min(d), max(d)))
    qh = collections.Counter(min(q, 40) for q in qs)
    esc = sum(c for q, c in qh.items() if q >= ESC_Q)
    print("escapes (q>=%d): %d (%.5f%% of tokens)" % (ESC_Q, esc, 100.0 * esc / n if n else 0))
    print("q histogram (share): " + " ".join(
        "%d:%.4f" % (q, qh[q] / n) for q in sorted(qh) if q < 12) + (
        " 12+:%.5f" % (sum(c for q, c in qh.items() if q >= 12) / n)))
    esc_q = collections.Counter(q for q in qs if q >= ESC_Q)
    if esc_q:
        print("escape q values: " + " ".join("%d:%d" % kv for kv in sorted(esc_q.items())))
    if not n:
        return
    ones = sum(bin(b).count("1") for b in buf[:endpos // 8]) / (8.0 * (endpos // 8)) if endpos >= 8 else 0.5
    if 0 < ones < 1:
        null_bits = 6 + (1 - ones) / ones
        print("ones-density %.4f; tokens per pixel (estimated from bits per token): real %.4f, Bernoulli null %.4f" % (
            ones, nbits / (endpos / n) / (w * h), nbits / null_bits / (w * h)))
    qc = [float(min(q, 8)) for q in qs]
    cs = []
    for lag in (1, 2, 3, 6, stride):
        if 0 < lag < n - 100:
            cs.append("lag %d: %+.4f" % (lag, pearson(qc[:-lag], qc[lag:])))
    print("correlation of min(q,8): " + "  ".join(cs))
    if a.escape_landing:
        landing(buf, a.escape_extra)

    # symbol streams; MISSING at escape tokens. L is the unsigned value 0..7.
    isesc = [q >= ESC_Q for q in qs]
    H = array.array("b", [MISSING if e else s >> 3 for e, s in zip(isesc, ss)])
    L = array.array("b", [MISSING if e else s & 7 for e, s in zip(isesc, ss)])
    B2 = array.array("b", [MISSING if e else (s >> 2) & 1 for e, s in zip(isesc, ss)])
    B4 = array.array("b", [MISSING if e else s >> 4 for e, s in zip(isesc, ss)])
    good = [s for e, s in zip(isesc, ss) if not e]
    m = len(good)
    print("suffix bit balance P(bit=1): " + " ".join(
        "b%d=%.4f" % (k, sum((s >> k) & 1 for s in good) / m) for k in (4, 3, 2, 1, 0)))
    hc = collections.Counter(s >> 3 for s in good)
    lc = collections.Counter(s & 7 for s in good)
    print("H share: " + " ".join("%d:%.4f" % (k, hc[k] / m) for k in sorted(hc)))
    print("L share: " + " ".join("%d:%.4f" % (k, lc[k] / m) for k in sorted(lc)))
    v, bs, _ = mi_base(H, L)
    print("within-token MI(H;L): %.4f (baseline %.4f)" % (v, bs))
    print("neighbour MI in bits, value (rotated-pair baseline):")
    for lag in (1, 2, 3):
        parts = []
        for name, xs, ys in (("H->L", H, L), ("L->H", L, H), ("L->L", L, L), ("H->H", H, H)):
            v, base, np_ = mi_base(xs, ys, lag)
            parts.append("%s %.4f(%.4f)" % (name, v, base))
        print("  lag %d: %s  n=%d" % (lag, "  ".join(parts), np_))
    v4, base4, _ = mi_base(B4, B2, 1)
    vh, baseh, _ = mi_base(H, L, 1)
    print("b4(t-1)->b2(t): %.4f (%.4f); H(t-1)->L(t) total %.4f (%.4f); "
          "share carried by b4->b2 after baseline: %.2f" % (
              v4, base4, vh, baseh, (v4 - base4) / (vh - baseh) if vh > baseh else float("nan")))
    # b2(t) context: (b4(t-1), b2(t-2))
    ctx = array.array("b", [MISSING] * len(B2))
    for t in range(2, len(B2)):
        p, r = B4[t - 1], B2[t - 2]
        if p != MISSING and r != MISSING:
            ctx[t] = p * 2 + r
    g, gb, ng = mi_base(ctx, B2)
    g1, g1b, _ = mi_base(B4, B2, 1)
    g2, g2b, _ = mi_base(B2, B2, 2)
    print("b2(t) gain from [b4(t-1), b2(t-2)]: %.4f (baseline %.4f) n=%d; "
          "from b4(t-1) alone %.4f (%.4f); from b2(t-2) alone %.4f (%.4f)" % (
              g, gb, ng, g1, g1b, g2, g2b))
    k = 2 * stride
    if len(H) > k + 100:
        vl, vlb, nv = mi_base(L, L, k)
        vhh, vhb, _ = mi_base(H, H, k)
        print("vertical lag 2 (stride %d): L-L %.4f (%.4f)  H-H %.4f (%.4f)  n=%d" % (
            stride, vl, vlb, vhh, vhb, nv))
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("files", nargs="+")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--max-tokens", type=int, default=2000000)
    g.add_argument("--rows", type=int, help="parse N x payload-width tokens")
    g.add_argument("--all", action="store_true", help="parse the whole payload")
    ap.add_argument("--stride", type=int, default=0, help="tokens per row (default: payload width)")
    ap.add_argument("--escape-extra", type=int, default=0, help="extra bits skipped after an escape")
    ap.add_argument("--escape-landing", action="store_true",
                    help="tabulate, per escape q, where the next token starts (calm bodies only)")
    a = ap.parse_args()
    for p in a.files:
        try:
            report(p, a)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            print("%s: %s" % (p, exc), file=sys.stderr)


if __name__ == "__main__":
    main()
