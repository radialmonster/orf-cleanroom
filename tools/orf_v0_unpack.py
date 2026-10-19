#!/usr/bin/env python3
"""Score candidate bit layouts for uncompressed (V0) ORF payloads; text stats only.

Supports: VARIANTS.md (V0: packed-12, packed-12.8, packed-16), lead #28.
Standard library only. Released under CC0 1.0.

For each file whose payload is an exact fixed-size packing (orf_signature.py
size_class packed-12 / packed-12.8 / packed-16) it unpacks a small window of
the payload under each candidate layout and prints aggregate numbers:
  min / max value, fraction of values above 4095 (12-bit range), fraction of
  values whose low 4 / low 2 bits are 0 (to spot fewer real bits stored in a wider field),
  h1 / h2  mean |difference| of horizontal neighbours at distance 1 / 2,
  v2       mean |difference| of vertical neighbours two rows apart (same CFA colour),
  vcorr    Pearson correlation of rows y and y+2,
differences are divided by the mean value of the window, so layouts
with different value scales compare. The chosen layout is the one with the
lowest score = h2 + v2. "margin" is second-best score / best score (above 1.0
means the best is that much smoother). Then, for the chosen layout only, the
correlation of row y with row y+2 when rows are read at stride = row bytes
+ delta (a wrong stride breaks the alignment and the correlation drops).

Nothing is written but text; no pixel values are printed or saved. Only a
window (default 3 bands of 16 rows, first 1200 columns) is read.

Usage: python orf_v0_unpack.py FILE [FILE ...] [--rows N] [--bands N] [--cols N]
"""
import argparse
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_signature  # noqa: E402

VARIANTS = ("lsb", "lsb-swap", "msb", "msb-swap", "mid")


def pairs12(buf, off, npx, variant):
    """Unpack npx 12-bit values from 3-byte groups (two values each)."""
    out = []
    for i in range(off, off + npx // 2 * 3, 3):
        b0, b1, b2 = buf[i], buf[i + 1], buf[i + 2]
        if variant.startswith("lsb"):       # bit stream read least-significant bit first
            a, b = b0 | (b1 & 15) << 8, b1 >> 4 | b2 << 4
        elif variant.startswith("msb"):     # bit stream read most-significant bit first
            a, b = b0 << 4 | b1 >> 4, (b1 & 15) << 8 | b2
        else:                               # "mid": the shared nibble is the low part of both
            a, b = b0 << 4 | (b1 & 15), b2 << 4 | b1 >> 4
        out.extend((b, a) if variant.endswith("-swap") else (a, b))
    return out


def swapped(buf, width):
    """Reverse the byte order inside every width-byte word (width 2 or 4)."""
    n = len(buf) // width * width
    out = bytearray(n)
    for k in range(width):
        out[k::width] = buf[width - 1 - k:n:width]
    return out


def u16(buf, npx, order):
    return list(struct.unpack_from("%s%dH" % (order, npx), buf, 0))


def candidates(size_class):
    """Return {name: function(rowbytes, npx) -> list of values}."""
    c = {}
    if size_class == "packed-16":
        c["u16-le"] = lambda r, n: u16(r, n, "<")
        c["u16-be"] = lambda r, n: u16(r, n, ">")
    elif size_class == "packed-12":
        for v in VARIANTS:
            c["12-" + v] = lambda r, n, v=v: pairs12(r, 0, n, v)
            # same 3-byte layouts, after reversing bytes inside 16-bit or 32-bit words
            for width in (2, 4):
                c["w%d-12-%s" % (width, v)] = lambda r, n, v=v, wd=width: pairs12(
                    swapped(r[:n * 3 // 2], wd), 0, n, v)
    elif size_class == "packed-12.8":
        for v in VARIANTS:
            for pad in (15, 0):
                def f(r, n, v=v, pad=pad):
                    out = []
                    for g in range(n // 10):
                        out.extend(pairs12(r, 16 * g + (1 if pad == 0 else 0), 10, v))
                    return out
                c["group16-%s-pad%d" % (v, pad)] = f
        for v in ("lsb", "msb"):
            c["rowpad-" + v] = lambda r, n, v=v: pairs12(r, 0, n, v)
    return c


def stats(rows):
    """rows: list of equal-length value lists (consecutive image rows)."""
    flat = [x for r in rows for x in r]
    n = len(flat)
    mean = sum(flat) / n
    sd = mean or 1.0   # scale: mean value (a wrong layout mixes high and low parts, which inflates the spread)
    h1 = sum(abs(r[i] - r[i + 1]) for r in rows for i in range(len(r) - 1)) / (n - len(rows))
    # h1 split by parity of x: odd/even differs from 1 when pixel pairs are in the wrong order
    ho = sum(abs(r[i] - r[i + 1]) for r in rows for i in range(1, len(r) - 1, 2))
    he = sum(abs(r[i] - r[i + 1]) for r in rows for i in range(0, len(r) - 1, 2))
    h2 = sum(abs(r[i] - r[i + 2]) for r in rows for i in range(len(r) - 2)) / (n - 2 * len(rows))
    v2s = [abs(a - b) for y in range(len(rows) - 2) for a, b in zip(rows[y], rows[y + 2])]
    v2 = sum(v2s) / len(v2s)
    return {
        "min": min(flat), "max": max(flat),
        "over4095": sum(x > 4095 for x in flat) / n,
        "low4zero": sum((x & 15) == 0 for x in flat) / n,
        "low2zero": sum((x & 3) == 0 for x in flat) / n,
        "h1": h1 / sd, "oe": ho / he if he else 1.0, "h2": h2 / sd, "v2": v2 / sd,
    }


def corr(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((x - mb) ** 2 for x in b))
    if not sa or not sb:
        return float("nan")
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def vcorr(rows):
    cs = [corr(rows[y], rows[y + 2]) for y in range(len(rows) - 2)]
    return sum(cs) / len(cs)


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def analyse(path, nrows, nbands, ncols):
    sig = orf_signature.signature(path)
    sc, w, h = sig["size_class"], sig["payload_w"], sig["payload_h"]
    print("== %s" % sig["file"])
    print("sha256 %s  %s  %dx%d  size_class %s" % (sig["sha256"], sig["model"], w, h, sc))
    if sc == "variable":
        print("not a fixed-size packing; skipped")
        return
    rb, rem = divmod(sig["payload_bytes"], h)
    if rem:
        print("payload bytes not a multiple of height; skipped")
        return
    off = int(sig["payload_offset"])
    ncols = min(ncols, w) // 30 * 30   # multiple of 2, 3, 5, 10 so every layout aligns
    cand = candidates(sc)
    # window rows start at even rows, bands spread through the frame
    starts = [min((h * (2 * k + 1) // (2 * nbands)) // 2 * 2, h - nrows) for k in range(nbands)]
    with open(path, "rb") as f:
        def read(pos):
            f.seek(off + pos)
            return f.read(rb)
        bands = [[read((s + i) * rb) for i in range(nrows)] for s in starts]
        res = {}
        for name, fn in cand.items():
            dec = [[fn(r, ncols) for r in band] for band in bands]
            agg = [stats(rows) for rows in dec]
            r = {k: mean(a[k] for a in agg) for k in ("over4095", "low4zero", "low2zero", "h1", "oe", "h2", "v2")}
            r["min"] = min(a["min"] for a in agg)
            r["max"] = max(a["max"] for a in agg)
            r["vcorr"] = mean(vcorr(rows) for rows in dec)
            r["score"] = r["h2"] + r["v2"]
            res[name] = r
        # Smoothness at distance 2 and vertically picks the layout; layouts within 2% of the
        # best score (pixel pairs in the other order) are then separated by h1.
        top = min(r["score"] for r in res.values())
        order = sorted(res, key=lambda k: (res[k]["score"] > top * 1.02, res[k]["h1"]
                                           if res[k]["score"] <= top * 1.02 else res[k]["score"]))
        print("window: %d bands x %d rows x %d cols at rows %s; row bytes %d" % (nbands, nrows, ncols, starts, rb))
        print("%-22s %6s %6s %8s %8s %8s %6s %6s %6s %6s %7s %6s" % (
            "layout", "min", "max", ">4095", "low4=0", "low2=0", "h1", "odd/ev", "h2", "v2", "vcorr", "score"))
        for k in order:
            r = res[k]
            print("%-22s %6d %6d %8.4f %8.4f %8.4f %6.3f %6.3f %6.3f %6.3f %7.4f %6.3f" % (
                k, r["min"], r["max"], r["over4095"], r["low4zero"], r["low2zero"], r["h1"], r["oe"], r["h2"], r["v2"],
                r["vcorr"], r["score"]))
        best = order[0]
        close = [k for k in order[1:] if res[k]["score"] <= top * 1.02]
        other = min((res[k]["score"] for k in order if res[k]["score"] > top * 1.02), default=float("nan"))
        print("chosen: %s  margin (best layout family vs next, by score) %.2f  h2/h1 %.3f" % (
            best, other / res[best]["score"], res[best]["h2"] / res[best]["h1"]))
        if close:
            print("pair-order alternatives within 2%% of the best score: %s; h1 %s vs %.3f (chosen)" % (
                ", ".join(close), ", ".join("%.3f" % res[k]["h1"] for k in close), res[best]["h1"]))
            gap = min(res[k]["h1"] for k in close) / res[best]["h1"] - 1
            print("pair order %s (h1 gap to the alternative %.1f%%)" % (
                "undecided" if gap < 0.01 else "weakly favoured" if gap < 0.05 else "favoured", 100 * gap))
        fn = cand[best]
        out = []
        for delta in (-16, -2, -1, 0, 1, 2, 16):
            cs = []
            for s in starts:
                rows = [fn(read(s * rb + i * (rb + delta)), ncols) for i in range(nrows)]
                cs.append(vcorr(rows))
            out.append("%+d:%.3f" % (delta, mean(cs)))
        print("row-stride test (vcorr at row bytes + delta): " + " ".join(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog="Text statistics only; no pixel values or images are written.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--rows", type=int, default=16, help="rows per band (default 16)")
    ap.add_argument("--bands", type=int, default=3, help="bands spread through the frame (default 3)")
    ap.add_argument("--cols", type=int, default=1200, help="columns read per row (default 1200)")
    a = ap.parse_args()
    for p in a.files:
        try:
            analyse(p, a.rows, a.bands, a.cols)
        except (ValueError, struct.error, OSError) as exc:
            print("%s: %s" % (p, exc), file=sys.stderr)


if __name__ == "__main__":
    main()
