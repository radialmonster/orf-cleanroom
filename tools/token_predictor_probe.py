#!/usr/bin/env python3
"""Score fixed token-value readings with causal predictors against the preview.

Supports: lead #11 (token parse and geometry), lead #31 (predictor and
integration loops over the token stream), lead #32 (ways of turning the token
fields into a value). Standard library only, Python 3.8+. Reads sample files and
prints aggregate numbers; it writes no images and no pixel data.

Each candidate reads a token as a signed residual d(q, s), reconstructs a prefix
with a causal predictor (raster or same-colour lag 2), block-averages the result
to the preview's luma DC grid, and correlates it after row-centring. The null
shuffles whole tokens within each row and reconstructs with the same predictor.

The natural sign-magnitude readings `sig0`, `sig0_32`, `sig1`, `sig3`, `sig4`
take bit b0/b1/b3/b4 as the sign and the other four suffix bits plus q as the
magnitude. They follow the adjacent-pixel-difference plus Huffman description in
public Olympus patent US8218885B2 (not decoder code); the patent does not give
the table in text, so these are candidate readings, not the camera's table.

Re-encoding a reconstruction with the same predictor is exact by construction,
so it is not evidence for the camera's model; this tool scores the reconstruction
against the embedded preview instead. No round-trip is claimed.

Every tested combination is printed. The fixed RNG is shared across the ordered
kind/predictor loops, so selecting or reordering combinations changes the null
draws. Reports state that order and the seed. The small-shuffle z scores are
descriptive standardized differences, not calibrated significance tests.

Usage:
    python -I tools/token_predictor_probe.py FILE [FILE ...] [--rows 156]
        [--perms 2] [--kinds ...] [--preds ...]
    python -I tools/token_predictor_probe.py --self-test
"""
import argparse
import array
import math
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc  # noqa: E402
import orf_tokens as T  # noqa: E402

KINDS = ("zz32", "m16b2", "m16b2f", "m32b2", "u32", "s16",
         "sig0", "sig0_32", "sig1", "sig3", "sig4")
PREDS = ("left", "up", "avg", "grad", "paeth", "med", "left2", "up2", "avg2")


def read_tokens(path, rows):
    w, h, buf = T.locate(path)
    qa, sa = array.array("B"), array.array("B")
    T.scan(buf, rows * w, w, 0, None, qa, sa, 40, None, 32)
    n = min(len(sa), rows * w)
    rows = n // w
    if rows < 2:
        raise ValueError("not enough tokens")
    return w, h, qa[:rows * w], sa[:rows * w], rows


def read_preview(path, rows, h):
    with open(path, "rb") as f:
        data = f.read()
    best = jpeg_dc.find_preview(data)
    if best is None:
        raise ValueError("no embedded baseline preview")
    wb, hb, dc = jpeg_dc.decode(data, best[1])
    nd = max(2, min(hb, round(rows * hb / h)))
    return wb, hb, dc, nd


def value(q, s, kind):
    q = q if q < 40 else 40
    s &= 31
    b4, b3, b2, b1, b0 = (s >> 4) & 1, (s >> 3) & 1, (s >> 2) & 1, (s >> 1) & 1, s & 1
    if kind == "u32":
        return (q << 5) | s
    if kind == "zz32":
        v = (q << 5) | s
        return v // 2 if v % 2 == 0 else -((v + 1) // 2)
    if kind in ("m16b2", "m16b2f"):
        m = (q << 4) + 4 * ((b4 << 1) | b3) + ((b1 << 1) | b0)
        neg = bool(b2) if kind == "m16b2" else not b2
        return -m if neg else m
    if kind == "m32b2":
        m = (q << 5) + 8 * ((b4 << 1) | b3) + ((b1 << 1) | b0)
        return -m if b2 else m
    if kind == "s16":
        return s - 16
    if kind == "sig0":
        m = (q << 4) | (s >> 1)
        return -m if b0 else m
    if kind == "sig0_32":
        m = (q << 5) | (s >> 1)
        return -m if b0 else m
    if kind == "sig1":
        m = (q << 4) | ((b4 << 3) | (b3 << 2) | (b2 << 1) | b0)
        return -m if b1 else m
    if kind == "sig3":
        m = (q << 4) | ((b4 << 3) | (b2 << 2) | (b1 << 1) | b0)
        return -m if b3 else m
    if kind == "sig4":
        m = (q << 4) | ((b3 << 3) | (b2 << 2) | (b1 << 1) | b0)
        return -m if b4 else m
    raise ValueError(kind)


def predictor(rec, i, x, y, w, pred):
    a = rec[i - 1] if x else 0
    b = rec[i - w] if y else 0
    c = rec[i - w - 1] if x and y else 0
    if pred == "left":
        return a
    if pred == "up":
        return b
    if pred == "avg":
        return (a + b) >> 1
    if pred == "grad":
        return a + b - c
    if pred == "paeth":
        p = a + b - c
        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
        return a if pa <= pb and pa <= pc else (b if pb <= pc else c)
    if pred == "med":
        if c >= max(a, b):
            return min(a, b)
        if c <= min(a, b):
            return max(a, b)
        return a + b - c
    if pred == "left2":
        return rec[i - 2] if x >= 2 else 0
    if pred == "up2":
        return rec[i - 2 * w] if y >= 2 else 0
    if pred == "avg2":
        a2 = rec[i - 2] if x >= 2 else 0
        b2 = rec[i - 2 * w] if y >= 2 else 0
        return (a2 + b2) >> 1
    raise ValueError(pred)


def reconstruct(d, rows, w, pred):
    rec = [0] * (rows * w)
    for y in range(rows):
        base = y * w
        for x in range(w):
            i = base + x
            rec[i] = predictor(rec, i, x, y, w, pred) + d[i]
    return rec


def block_mean(seq, rows, w, nd, nw):
    out = []
    for r in range(nd):
        r0 = r * rows // nd
        r1 = max(r0 + 1, (r + 1) * rows // nd)
        acc = [0.0] * w
        for tr in range(r0, min(r1, rows)):
            base = tr * w
            for c in range(w):
                acc[c] += seq[base + c]
        prefix = [0.0] * (w + 1)
        s = 0.0
        for c in range(w):
            s += acc[c]
            prefix[c + 1] = s
        row = []
        for c in range(nw):
            c0 = c * w // nw
            c1 = max(c0 + 1, (c + 1) * w // nw)
            row.append((prefix[c1] - prefix[c0]) / ((r1 - r0) * (c1 - c0)))
        out.append(row)
    return out


def corr_rows(a, b):
    sa = sb = saa = sbb = sab = 0.0
    for ra, rb in zip(a, b):
        ma = sum(ra) / len(ra)
        mb = sum(rb) / len(rb)
        for x, y in zip(ra, rb):
            x -= ma
            y -= mb
            sa += x
            sb += y
            saa += x * x
            sbb += y * y
            sab += x * y
    if saa <= 0 or sbb <= 0:
        return float("nan")
    return sab / math.sqrt(saa * sbb)


def score(d, rows, w, nd, wb, target, pred):
    rec = reconstruct(d, rows, w, pred)
    grid = block_mean(rec, rows, w, nd, wb)
    return corr_rows(grid, target)


def run_file(path, rows, perms, kinds, preds):
    w, h, qa, sa, rows = read_tokens(path, rows)
    wb, hb, dc, nd = read_preview(path, rows, h)
    target = [dc[r * wb:(r + 1) * wb] for r in range(nd)]
    print("%s  payload %dx%d  rows %d  preview used %dx%d  perms %d" % (
        os.path.basename(path), w, h, rows, nd, wb, perms))
    print("  settings kinds=%s preds=%s seed=20261021 rng=shared-ordered" % (
        ",".join(kinds), ",".join(preds)))
    print("  z is descriptive, not calibrated significance; all %d combinations follow" % (
        len(kinds) * len(preds)))
    rng = random.Random(20261021)
    rows_out = []
    for kind in kinds:
        d = [value(q, s, kind) for q, s in zip(qa, sa)]
        for pred in preds:
            real = score(d, rows, w, nd, wb, target, pred)
            null = []
            for _ in range(perms):
                qb, sb = shuffle_pairs(qa, sa, rows, w, rng)
                dn = [value(q, s, kind) for q, s in zip(qb, sb)]
                null.append(score(dn, rows, w, nd, wb, target, pred))
            m = sum(null) / len(null)
            sd = math.sqrt(sum((v - m) ** 2 for v in null) / max(1, len(null) - 1))
            z = (real - m) / sd if sd else 0.0
            rows_out.append((abs(real), kind, pred, real, m, sd, z))
    # NaN |r| (constant predictor or target) sorts last instead of breaking the order
    rows_out.sort(key=lambda t: -1.0 if t[0] != t[0] else t[0], reverse=True)
    for _, kind, pred, real, m, sd, z in rows_out:
        print("  %-7s %-6s r=%+.5f  null=%+.5f +/- %.5f  z=%+.2f" % (
            kind, pred, real, m, sd, z))


def shuffle_pairs(qa, sa, rows, w, rng):
    qb = bytearray(qa)
    sb = bytearray(sa)
    for r in range(rows):
        idx = list(range(r * w, (r + 1) * w))
        rng.shuffle(idx)
        qpart = [qb[i] for i in idx]
        spart = [sb[i] for i in idx]
        for k, i in enumerate(range(r * w, (r + 1) * w)):
            qb[i] = qpart[k]
            sb[i] = spart[k]
    return qb, sb


def self_test():
    rows, w = 12, 16
    img = [(x * 3 + y * 5 + (x * y) % 7) for y in range(rows) for x in range(w)]
    for pred in PREDS:
        rec = [0] * (rows * w)
        d = [0] * (rows * w)
        for y in range(rows):
            for x in range(w):
                i = y * w + x
                p = predictor(rec, i, x, y, w, pred)
                d[i] = img[i] - p
                rec[i] = img[i]
        got = reconstruct(d, rows, w, pred)
        assert got == img, pred
    # a shuffled residual stream must lose the reconstruction
    rec = [0] * (rows * w)
    d = [0] * (rows * w)
    for y in range(rows):
        for x in range(w):
            i = y * w + x
            p = predictor(rec, i, x, y, w, "left")
            d[i] = img[i] - p
            rec[i] = img[i]
    rng = random.Random(7)
    sh = list(d)
    for y in range(rows):
        part = sh[y * w:(y + 1) * w]
        rng.shuffle(part)
        sh[y * w:(y + 1) * w] = part
    a = reconstruct(d, rows, w, "left")
    b = reconstruct(sh, rows, w, "left")
    ca = block_mean(a, rows, w, 6, 4)
    cb = block_mean(b, rows, w, 6, 4)
    assert corr_rows(ca, cb) < 0.95
    bm = block_mean([3.0] * (rows * w), rows, w, 6, 4)
    assert all(abs(v - 3.0) < 1e-9 for row in bm for v in row)
    print("self-test ok: all predictors invert their own residuals; shuffle loses the match")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--rows", type=int, default=156)
    ap.add_argument("--perms", type=int, default=2,
                    help="shuffles per cell (default 2: a rough screen; z is descriptive, "
                         "not calibrated significance)")
    ap.add_argument("--kinds", default=",".join(KINDS))
    ap.add_argument("--preds", default=",".join(PREDS))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.rows <= 0 or a.perms < 2:
        # one permutation has no spread, so z would print as a meaningless +0.00
        ap.error("--rows must be positive and --perms at least 2")
    if a.self_test:
        self_test()
        import unittest
        import test_token_predictor_probe
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_token_predictor_probe)
        return 0 if unittest.TextTestRunner().run(suite).wasSuccessful() else 1
    if not a.files:
        ap.error("no files (or use --self-test)")
    kinds = [k for k in a.kinds.split(",") if k]
    preds = [p for p in a.preds.split(",") if p]
    if not kinds or any(k not in KINDS for k in kinds):
        ap.error("--kinds must list known readings")
    if not preds or any(p not in PREDS for p in preds):
        ap.error("--preds must list known predictors")
    succeeded = failed = 0
    for p in a.files:
        try:
            run_file(p, a.rows, a.perms, kinds, preds)
        except (ValueError, IndexError, KeyError, OSError, struct.error):
            failed += 1
            print("%s: report incomplete; input or measurement failed" % os.path.basename(p),
                  file=sys.stderr)
            print("%s status=incomplete" % os.path.basename(p))
        else:
            succeeded += 1
            print("%s status=complete" % os.path.basename(p))
    print("files: requested=%d complete=%d failed=%d" % (len(a.files), succeeded, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
