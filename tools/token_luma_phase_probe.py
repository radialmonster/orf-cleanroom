#!/usr/bin/env python3
"""Scan candidate row phase for the fixed b2+b4 top-band luma map.

Supports: lead #149 (b2+b4 local-density luma proxy), lead #144 / specs/V1.md
G3 (candidate row stride) and the #296 stride/phase landscape. Standard library
only; reads sample files and prints aggregate numbers. No images or pixel data
are written.

At a fixed candidate stride S, row r is the W-token window starting at token
r*S + phase. With phase > S-W the window overlaps the next candidate row, so a
phase is an alignment hypothesis, not a physical row origin. The mapping and
the preview target are the unchanged #149/#349 ones: v = b2 + b4, a box mean
over `--window` tokens, a block average to the embedded preview's luma DC grid,
and a row-centred Pearson correlation.

The phase scan is coarse (`--step`) and then refined over `--refine` phases at
step 1. `--perms` repeats the entire coarse+refine search after a global
permutation of the suffix tokens; the null statistic is the maximum r over the
same phase family. This is a search-sensitive diagnostic, not a calibrated
p-value.

This is a low-resolution luma proxy, not a pixel value or a decoder. A phase
with a high score is a scene alignment candidate; it does not establish the
physical row period, row origin or bitstream meaning.

Usage:
    python -I tools/token_luma_phase_probe.py FILE [FILE ...] --stride S
        [--rows 300] [--start-row 0] [--step 16] [--refine 16]
        [--window 63] [--perms 0] [--seed 1] [--map sum|b2|b4]
    python -I tools/token_luma_phase_probe.py --self-test

Every requested row and phase window must fit. Any input failure exits nonzero
and identifies the input ordinal and exception type, without local paths.
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
import token_luma_probe as L  # noqa: E402
import token_luma_stride_probe as SP  # noqa: E402


def image_at(sa, rows, w, stride, phase, start=0):
    """Take w tokens from each candidate row starting at absolute `phase`."""
    if rows < 1 or w < 1 or stride < w or phase < 0 or phase >= stride or start < 0:
        raise ValueError("require rows>=1, w>=1, 0<=phase<stride, start>=0")
    last = (start + rows - 1) * stride + phase + w
    if last > len(sa):
        raise ValueError("short token stream for phase")
    out = bytearray(rows * w)
    for r in range(rows):
        base = (start + r) * stride + phase
        out[r * w:(r + 1) * w] = sa[base:base + w]
    return out


def circular_phases(best, radius, stride):
    """Refinement phases around `best`, wrapping at the candidate stride."""
    if stride < 1 or radius < 0:
        raise ValueError("require stride>=1 and radius>=0")
    return sorted({(best + d) % stride for d in range(-radius, radius + 1)})


def phase_family(stride, step, refine):
    """Coarse phases plus a deterministic coarse winner's refinement."""
    if stride < 2 or step < 1 or refine < 0:
        raise ValueError("require stride>=2, step>=1 and refine>=0")
    coarse = list(range(0, stride, step))
    if coarse[-1] != stride - 1:
        coarse.append(stride - 1)
    return coarse, step, refine


def score_phases(sa, rows, w, stride, target, mapping, window, phases, start=0):
    """Score the declared phases; ties choose the lowest phase number."""
    scores = {}
    for phase in phases:
        image = image_at(sa, rows, w, stride, phase, start)
        scores[phase] = L.score(image, rows, w, window, len(target), target, mapping)
    return scores


def search(sa, rows, w, stride, target, mapping, window, step, refine, start=0):
    coarse, _, _ = phase_family(stride, step, refine)
    scores = score_phases(sa, rows, w, stride, target, mapping, window, coarse, start)
    best = max(coarse, key=lambda p: (scores[p], -p))
    fine = circular_phases(best, refine, stride)
    scores.update(score_phases(sa, rows, w, stride, target, mapping, window, fine, start))
    best = max(scores, key=lambda p: (scores[p], -p))
    return best, scores[best], scores, coarse, fine


def shuffled(sa, seed):
    """Global suffix permutation; q and escape markers are not retained here."""
    buf = bytearray(sa)
    random.Random(seed).shuffle(buf)
    return buf


def run_file(path, stride, rows, start, step, refine, window, perms, seed,
             mapping):
    if rows < 2 or start < 0 or step < 1 or refine < 0 or window < 1 or perms < 0:
        raise ValueError("invalid geometry")
    if window % 2 == 0:
        raise ValueError("window must be odd (the centred box spans 2*(window//2)+1 tokens)")
    w, h, buf = T.locate(path)
    if stride < w:
        raise ValueError("stride smaller than payload width")
    need = (start + rows) * stride + w
    qa, sa = array.array("B"), array.array("B")
    T.scan(buf, need, 0, 0, None, qa, sa, 40, None, 32)
    if len(sa) < need:
        raise ValueError("not enough complete candidate rows")
    data = open(path, "rb").read()
    best = jpeg_dc.find_preview(data)
    if best is None:
        raise ValueError("no embedded baseline preview")
    wb, hb, dc = jpeg_dc.decode(data, best[1])
    target = SP.preview_target(dc, wb, hb, start, rows, h)
    best_phase, best_r, scores, coarse, fine = search(
        sa, rows, w, stride, target, mapping, window, step, refine, start)
    ordered = sorted(scores, key=lambda p: (-scores[p], p))
    null_maxima = []
    for k in range(perms):
        null_sa = shuffled(sa, seed + k)
        _, null_r, _, _, _ = search(
            null_sa, rows, w, stride, target, mapping, window, step, refine, start)
        null_maxima.append(null_r)
    escapes = sum(1 for b in sa if b >= 32)
    print("%s  payload %dx%d  stride %d  start %d  rows %d  window %d  "
          "dc %dx%d  map %s  step %d  refine %d" % (
              os.path.basename(path), w, h, stride, start, rows, window,
              wb, hb, mapping, step, refine))
    print("  phase 0 r=%+.5f; best phase %d r=%+.5f; coarse %d fine %d"
          % (scores[0], best_phase, best_r, len(coarse), len(fine)))
    print("  top phases: " + ", ".join(
        "%d:%+.5f" % (p, scores[p]) for p in ordered[:10]))
    if null_maxima:
        mean = sum(null_maxima) / len(null_maxima)
        print("  shuffled-search max: %s (mean %+.5f, %d perms)"
              % (", ".join("%+.5f" % x for x in null_maxima), mean, len(null_maxima)))
    print("  escapes=%d (treated as 0)" % escapes)


def self_test():
    # A smooth diagonal ramp is placed at phase 7; the search must recover it.
    rows, w, stride, phase = 24, 20, 31, 7
    sa = bytearray((r * stride + c) % 256
                   for r in range(rows + 2) for c in range(stride))
    for r in range(rows):
        for c in range(w):
            v = (r + c) // 4
            sa[r * stride + phase + c] = (4 if v % 2 else 0) | (16 if v % 3 else 0)
    image = image_at(sa, rows, w, stride, phase, 0)
    target = L.block_mean(L.box_mean_rows(image.translate(L.DENSITY), rows, w, 9),
                          rows, w, 4, 8)
    best, r, scores, _, _ = search(
        sa, rows, w, stride, target, "sum", 9, 1, 2, 0)
    assert best == phase, (best, phase, sorted(scores.items(), key=lambda kv: -kv[1])[:5])
    assert r > 0.9, r
    try:
        image_at(sa, rows, w, stride, stride, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("phase at stride was accepted")
    print("self-test ok: recovered phase %d at r=%.4f" % (best, r))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--stride", type=int, required=False,
                    help="candidate tokens per row (same for every input)")
    ap.add_argument("--rows", type=int, default=300, help="token rows used")
    ap.add_argument("--start-row", type=int, default=0,
                    help="first candidate row (absolute row index)")
    ap.add_argument("--step", type=int, default=16, help="coarse phase step")
    ap.add_argument("--refine", type=int, default=16,
                    help="refine +/- this many phases at step 1")
    ap.add_argument("--window", type=int, default=63, help="box window in tokens")
    ap.add_argument("--perms", type=int, default=0,
                    help="shuffled-token repeats of the whole phase search")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--map", dest="mapping", choices=("sum", "b2", "b4"),
                    default="sum", help="fixed suffix map (default: sum)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return 0
    if not a.files:
        ap.error("no files (or use --self-test)")
    if a.stride is None:
        ap.error("--stride is required unless --self-test is used")
    if (a.rows < 2 or a.start_row < 0 or a.step < 1 or a.refine < 0
            or a.window < 1 or a.perms < 0):
        ap.error("require rows>=2, start-row>=0, step>=1, refine>=0, window>=1, perms>=0")
    if a.window % 2 == 0:
        ap.error("--window must be odd (the centred box spans 2*(window//2)+1 tokens)")
    failed = False
    for index, path in enumerate(a.files, 1):
        try:
            run_file(path, a.stride, a.rows, a.start_row, a.step, a.refine,
                     a.window, a.perms, a.seed, a.mapping)
        except (ValueError, IndexError, KeyError, OSError, struct.error) as exc:
            failed = True
            print("input %d: %s" % (index, type(exc).__name__), file=sys.stderr)
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
