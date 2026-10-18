#!/usr/bin/env python3
"""Zero-run statistics of a payload bitstream, read MSB-first.

Supports: FINDINGS F1 (token structure: q zero bits, then a stop bit).
Standard library only. A simple starting point for bitstream exploration:
it makes no assumption about suffixes or escapes, it just counts runs of 0
bits ending in a 1 and prints their histogram as aggregate numbers.

Usage: python bit_runs.py FILE [--mb N]   (default: first 4 MB of payload)
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff  # noqa: E402


def payload(path):
    with open(path, "rb") as f:
        data = f.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    off, n = best[0x111][0], sum(best[0x117])
    return data[off:off + n]


def zero_runs(buf):
    hist = collections.Counter()
    run = 0
    for byte in buf:
        for shift in range(7, -1, -1):
            if (byte >> shift) & 1:
                hist[run] += 1
                run = 0
            else:
                run += 1
    return hist


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--mb", type=float, default=4.0)
    a = ap.parse_args()
    buf = payload(a.file)[: int(a.mb * 1024 * 1024)]
    hist = zero_runs(buf)
    total = sum(hist.values())
    print("bytes=%d ones=%d" % (len(buf), total))
    for q in sorted(hist):
        print("q=%2d  count=%9d  share=%.5f" % (q, hist[q], hist[q] / total))


if __name__ == "__main__":
    main()
