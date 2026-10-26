#!/usr/bin/env python3
"""Test a fixed token-field -> low-resolution luma mapping against a shuffle null.

Supports: the P0 token-to-value probe, lead #11 (geometry) and the b2/b4
statistics of leads #11/#29. Standard library only; reads sample files and
prints aggregate numbers. No images or pixel data are written.

Mapping (fixed, no fitting): --map sum (default) uses v = b2 + b4;
--map b2 or --map b4 uses that bit alone. Every map is box-averaged
over `--window` tokens within each row and block-averaged to the preview's
luma DC grid. The target is the embedded preview's luma DC from
tools/jpeg_dc.py. The score is the Pearson correlation after subtracting each
row's mean. The null is the same measure after permuting the suffix tokens
within each row.

This is a low-resolution luma proxy, not a full pixel decode. The default
`--rows 300` compares the top 300 token rows with the top part of the preview;
a full-frame reshape is not used because the token row stride can drift.

Usage:
    python -I tools/token_luma_probe.py FILE [FILE ...] [--rows 300]
        [--window 63] [--perms 20] [--seed 1] [--map sum|b2|b4]
        [--shift-null]
    python -I tools/token_luma_probe.py --self-test

`--shift-null` also scores every circular shift of the preview rows. A rank
above 1 means a shifted preview scores at least as well as the declared
vertical alignment; the within-row shuffle null tests horizontal structure
only. The shift null is a sensitivity diagnostic, not a calibrated p-value.

Escape tokens (q >= 17) are treated as 0 for b2/b4; their rate is printed.
Every requested token row must be complete. Any input failure exits nonzero;
errors identify the input ordinal and exception type, without local paths.
"""
import argparse
import array
import itertools
import math
import operator
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc  # noqa: E402
import orf_tokens as T  # noqa: E402

DENSITY = bytes((((v >> 2) & 1) + ((v >> 4) & 1)) if v < 32 else 0 for v in range(256))
MAPPINGS = {"sum": DENSITY,
            "b2": bytes(((v >> 2) & 1) if v < 32 else 0 for v in range(256)),
            "b4": bytes(((v >> 4) & 1) if v < 32 else 0 for v in range(256))}


def box_mean_rows(v, rows, w, window):
    """Centered box mean within each row, clamped at the row edges."""
    out = array.array("f", [0.0]) * (rows * w)
    half = window // 2
    # The clamped window ends are the same in every row; the per-row work runs in
    # accumulate/map with the same integer sums and one division per value.
    lo = [max(0, c - half) for c in range(w)]
    hi = [min(w, c + half + 1) for c in range(w)]
    size = [b - a for a, b in zip(lo, hi)]
    for r in range(rows):
        base = r * w
        prefix = list(itertools.accumulate(v[base:base + w], initial=0))
        get = prefix.__getitem__
        out[base:base + w] = array.array("f", map(
            operator.truediv, map(operator.sub, map(get, hi), map(get, lo)), size))
    return out


def block_mean(v, rows, w, nd, wb):
    """Block-average a rows x w float sequence to nd x wb."""
    out = []
    c0s = [c * w // wb for c in range(wb)]
    c1s = [max(c0 + 1, (c + 1) * w // wb) for c, c0 in enumerate(c0s)]
    for r in range(nd):
        r0 = r * rows // nd
        r1 = max(r0 + 1, (r + 1) * rows // nd)
        # Columns are summed row by row in the same order as a scalar loop.
        acc = [0.0] * w
        for tr in range(r0, min(r1, rows)):
            base = tr * w
            acc = list(map(operator.add, acc, v[base:base + w]))
        prefix = list(itertools.accumulate(acc, initial=0.0))
        out.append([(prefix[c1] - prefix[c0]) / ((r1 - r0) * (c1 - c0))
                    for c0, c1 in zip(c0s, c1s)])
    return out


def corr_rows(a, b):
    """Pearson correlation of two nd x wb grids after subtracting row means."""
    n = len(a)
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


def token_grid(sa, rows, w, window, nd, wb, mapping="sum"):
    v = sa.translate(MAPPINGS[mapping])
    boxed = box_mean_rows(v, rows, w, window)
    return block_mean(boxed, rows, w, nd, wb)


def score(sa, rows, w, window, nd, target, mapping="sum"):
    return corr_rows(token_grid(sa, rows, w, window, nd, len(target[0]), mapping), target)


def shuffle_rows(sa, rows, w, rng):
    buf = bytearray(sa)
    for r in range(rows):
        base = r * w
        part = buf[base:base + w]
        rng.shuffle(part)
        buf[base:base + w] = part
    return buf


def preview_shift_scores(sa, rows, w, window, target, mapping="sum"):
    """Score the declared target and every circular shift of its rows.

    The target must be rectangular (every row len(target[0]) values): one token
    grid sized from row 0 is scored against every shift."""
    nd = len(target)
    if nd < 2:
        raise ValueError("require at least two preview rows")
    # Only the target rows move; the token grid is the same for every shift.
    grid = token_grid(sa, rows, w, window, nd, len(target[0]), mapping)
    return [(k, corr_rows(grid, target[k:] + target[:k])) for k in range(1, nd)]


def shift_summary(real, shifts):
    """Summarize the observed score against the circular-shift scores."""
    vals = [r for _, r in shifts]
    if not vals:
        raise ValueError("require at least one shifted score")
    mean = sum(vals) / len(vals)
    var = (sum((x - mean) ** 2 for x in vals) / (len(vals) - 1)
           if len(vals) > 1 else 0.0)
    sd = math.sqrt(var) if var > 0 else 0.0
    best_shift, best = max(shifts, key=lambda kv: kv[1])
    return dict(observed=real, best_shift=best_shift, best=best,
                mean=mean, sd=sd, maximum=max(vals),
                rank=1 + sum(1 for x in vals if x >= real),
                shifts=len(vals))


def run_file(path, rows, window, perms, seed, mapping="sum", shift_null=False):
    if rows < 2 or window < 1 or perms < 1:
        raise ValueError("require rows>=2, window>=1, perms>=1")
    if window % 2 == 0:
        raise ValueError("window must be odd (the centred box spans 2*(window//2)+1 tokens)")
    w, h, buf = T.locate(path)
    qa, sa = array.array("B"), array.array("B")
    T.scan(buf, rows * w, w, 0, None, qa, sa, 40, None, 32)
    if len(sa) < rows * w:
        raise ValueError("not enough tokens for requested rows")
    sa = sa[:rows * w].tobytes()
    best = jpeg_dc.find_preview(open(path, "rb").read())
    if best is None:
        raise ValueError("no embedded baseline preview")
    wb, hb, dc = jpeg_dc.decode(open(path, "rb").read(), best[1])
    nd = max(1, min(hb, round(rows * hb / h)))
    target = [dc[r * wb:(r + 1) * wb] for r in range(nd)]
    real = score(sa, rows, w, window, nd, target, mapping)
    rng = random.Random(seed)
    null = [score(shuffle_rows(sa, rows, w, rng), rows, w, window, nd, target, mapping)
            for _ in range(perms)]
    mean = sum(null) / len(null)
    var = sum((x - mean) ** 2 for x in null) / (len(null) - 1) if len(null) > 1 else 0.0
    sd = math.sqrt(var) if var > 0 else 0.0
    z = (real - mean) / sd if sd else 0.0
    escapes = sum(1 for b in sa if b >= 32)
    if mapping != "sum":
        print("  mapping=%s" % mapping)
    print("%s  payload %dx%d  rows %d  window %d  dc %dx%d  used %dx%d" % (
        os.path.basename(path), w, h, rows, window, wb, hb, nd, wb))
    print("  r=%+.5f  shuffle=%+.5f +/- %.5f  z=%+.2f  escapes=%d (treated as 0)" % (
        real, mean, sd, z, escapes))
    if shift_null:
        summary = shift_summary(
            real, preview_shift_scores(sa, rows, w, window, target, mapping))
        print("  shift-null: best k=%d r=%+.5f; observed rank %d/%d; "
              "shifts %+.5f +/- %.5f max %+.5f" % (
                  summary["best_shift"], summary["best"], summary["rank"],
                  summary["shifts"] + 1, summary["mean"], summary["sd"],
                  summary["maximum"]))


def self_test():
    rows, w, window, nd, wb = 40, 64, 9, 4, 8
    sa = bytearray(rows * w)
    for r in range(rows):
        for c in range(w):
            # b2 and b4 form a smooth diagonal ramp
            v = (r * w + c) % 97
            if v < 48:
                b2 = 1
            else:
                b2 = 0
            b4 = 1 if (r + c) % 7 < 3 else 0
            sa[r * w + c] = (b4 << 4) | (b2 << 2)
    v = sa.translate(DENSITY)
    boxed = box_mean_rows(v, rows, w, window)
    target = block_mean(boxed, rows, w, nd, wb)
    real = score(sa, rows, w, window, nd, target)
    assert real > 0.99, real
    rng = random.Random(1)
    shuffled = score(shuffle_rows(sa, rows, w, rng), rows, w, window, nd, target)
    assert shuffled < 0.5, shuffled
    print("self-test ok: r=%.4f on the matched grid, r=%.4f after a row shuffle" % (real, shuffled))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--rows", type=int, default=300, help="token rows to use")
    ap.add_argument("--window", type=int, default=63, help="box window in tokens")
    ap.add_argument("--perms", type=int, default=20, help="within-row shuffles")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--map", dest="mapping", choices=("sum", "b2", "b4"),
                    default="sum", help="fixed suffix map (default: sum)")
    ap.add_argument("--shift-null", action="store_true",
                    help="also score every circular shift of the preview rows")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return 0
    if not a.files:
        ap.error("no files (or use --self-test)")
    if a.rows < 2 or a.window < 1 or a.perms < 1:
        ap.error("require rows>=2, window>=1, perms>=1")
    if a.window % 2 == 0:
        ap.error("--window must be odd (the centred box spans 2*(window//2)+1 tokens)")
    failed = False
    for index, p in enumerate(a.files, 1):
        try:
            run_file(p, a.rows, a.window, a.perms, a.seed, a.mapping,
                     a.shift_null)
        except (ValueError, IndexError, KeyError, OSError, struct.error) as exc:
            failed = True
            print("input %d: %s" % (index, type(exc).__name__), file=sys.stderr)
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
