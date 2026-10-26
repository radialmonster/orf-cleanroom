#!/usr/bin/env python3
"""Test the fixed b2+b4 top-band luma map with candidate-stride row segmentation.

Supports: lead #149 (b2+b4 local-density luma proxy) and lead #144 /
specs/V1.md G3 (candidate token row stride). Standard library only; reads
sample files and prints aggregate numbers. No images or pixel data are written.

The merged `token_luma_probe.py` assumes one token row is the payload width W.
This tool lets a row be S tokens (S >= W), takes the first W tokens of each
row (or an explicit `--offset`), and otherwise uses the same fixed mapping:
v = b2 + b4 per token, box-average over `--window` tokens, block-average to
the embedded preview's luma DC grid, subtract row means, and correlate. The
null permutes the used suffix tokens within each W-token image row.

This is a measurement, not a decoder. A candidate stride S is a periodicity
of the q row-start profile; it is not established as a physical row length.
Different S, offset or start-row values are separate declared measurements.

Usage:
    python -I tools/token_luma_stride_probe.py FILE [FILE ...] --stride S
        [--rows 300] [--start-row 0] [--offset 0] [--window 63]
        [--perms 20] [--seed 1] [--map sum|b2|b4]
    python -I tools/token_luma_stride_probe.py --self-test

Every requested row must be complete. Any input failure exits nonzero and
identifies the input ordinal and exception type, without local paths.
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


def extract_image(sa, rows, w, stride, offset=0, start=0):
    """Take w suffix bytes per candidate S-token row, starting at `offset`."""
    if rows < 1 or w < 1 or stride < w:
        raise ValueError("require rows>=1, w>=1 and stride>=w")
    if offset < 0 or offset + w > stride:
        raise ValueError("require 0 <= offset and offset + w <= stride")
    out = bytearray(rows * w)
    for r in range(rows):
        base = (start + r) * stride + offset
        chunk = sa[base:base + w]
        if len(chunk) != w:
            raise ValueError("short candidate row")
        out[r * w:(r + 1) * w] = chunk
    return out


def preview_target(dc, wb, hb, start, rows, image_h):
    """Preview DC rows covering the same vertical fraction as the token rows."""
    if rows < 2 or hb < 2 or image_h < 1 or start < 0:
        raise ValueError("require rows>=2, hb>=2, image_h>=1 and start>=0")
    if start + rows > image_h:
        # clamping the window to the bottom would compare token rows with the wrong
        # preview rows and still print a normal-looking r/z
        raise ValueError("start + rows (%d) is past the image height %d" % (start + rows, image_h))
    nd = min(hb, max(2, round(rows * hb / image_h)))
    # the clamp below only absorbs rounding (at most one DC row)
    r0 = min(max(0, hb - nd), max(0, round(start * hb / image_h)))
    return [dc[r * wb:(r + 1) * wb] for r in range(r0, r0 + nd)]


def score_with_null(image, rows, w, window, target, mapping, perms, seed):
    real = L.score(image, rows, w, window, len(target), target, mapping)
    rng = random.Random(seed)
    null = [L.score(L.shuffle_rows(image, rows, w, rng), rows, w, window,
                    len(target), target, mapping) for _ in range(perms)]
    mean = sum(null) / len(null)
    var = sum((x - mean) ** 2 for x in null) / (len(null) - 1) if len(null) > 1 else 0.0
    sd = math.sqrt(var) if var > 0 else 0.0
    return real, mean, sd, ((real - mean) / sd if sd else 0.0)


def run_file(path, stride, rows, start, offset, window, perms, seed, mapping):
    w, h, buf = T.locate(path)
    if stride < w:
        raise ValueError("stride smaller than payload width")
    need = (start + rows) * stride
    qa, sa = array.array("B"), array.array("B")
    T.scan(buf, need, 0, 0, None, qa, sa, 40, None, 32)
    if len(sa) < need:
        raise ValueError("not enough complete candidate rows")
    image = extract_image(sa, rows, w, stride, offset, start)
    data = open(path, "rb").read()
    best = jpeg_dc.find_preview(data)
    if best is None:
        raise ValueError("no embedded baseline preview")
    wb, hb, dc = jpeg_dc.decode(data, best[1])
    target = preview_target(dc, wb, hb, start, rows, h)
    real, mean, sd, z = score_with_null(
        image, rows, w, window, target, mapping, perms, seed)
    escapes = sum(1 for b in image if b >= 32)
    print("%s  payload %dx%d  stride %d  start %d  offset %d  rows %d  "
          "window %d  dc %dx%d  map %s" % (
              os.path.basename(path), w, h, stride, start, offset, rows,
              window, wb, hb, mapping))
    print("  r=%+.5f  shuffle=%+.5f +/- %.5f  z=%+.2f  escapes=%d (treated as 0)" % (
        real, mean, sd, z, escapes))


def self_test():
    rows, w, stride, offset = 5, 6, 9, 2
    sa = bytearray((r * stride + c) % 256
                   for r in range(rows) for c in range(stride))
    image = extract_image(sa, rows, w, stride, offset, 0)
    assert len(image) == rows * w
    for r in range(rows):
        assert image[r * w:(r + 1) * w] == sa[r * stride + offset:r * stride + offset + w]
    try:
        extract_image(sa, rows, w, stride, stride - w + 1, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("offset past the row end was accepted")
    target = preview_target(list(range(20 * 8)), 8, 20, 50, 10, 100)
    assert len(target) == 2, target
    assert target[0][0] == 10 * 8, target
    print("self-test ok: stride/offset extraction and preview row crop")


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
    ap.add_argument("--offset", type=int, default=0,
                    help="row-internal image start in tokens")
    ap.add_argument("--window", type=int, default=63, help="box window in tokens")
    ap.add_argument("--perms", type=int, default=20, help="within-row shuffles")
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
    if a.rows < 2 or a.start_row < 0 or a.offset < 0 or a.window < 1 or a.perms < 1:
        ap.error("require rows>=2, start-row>=0, offset>=0, window>=1, perms>=1")
    if a.window % 2 == 0:
        ap.error("--window must be odd (the centred box spans 2*(window//2)+1 tokens)")
    failed = False
    for index, path in enumerate(a.files, 1):
        try:
            run_file(path, a.stride, a.rows, a.start_row, a.offset,
                     a.window, a.perms, a.seed, a.mapping)
        except (ValueError, IndexError, KeyError, OSError, struct.error) as exc:
            failed = True
            print("input %d: %s" % (index, type(exc).__name__), file=sys.stderr)
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
