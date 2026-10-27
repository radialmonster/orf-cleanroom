#!/usr/bin/env python3
"""Screen numeric preview-DC similarity without rendering or printing arrays.

Part of #295, not a same-scene classifier. The largest baseline preview is
selected by jpeg_dc. Only complete 8x8 luma blocks are used. Their quantized
DC values are averaged into a fixed 12x12 full-frame grid, then centered and
scaled to unit Euclidean norm. Identity alignment only: no crop, rotation,
reflection or shift search. Quantization is not inverted; a uniform positive
DC scale/offset cancels in correlation. Camera tone curves need not cancel.

Every distinct-content pair is printed, sorted by SHA-256. Exact-content
inputs are deduplicated. A 0.98 correlation cutoff is a predeclared screening
threshold, not calibrated evidence of shared scene/exposure. Grid SD below 1
quantized DC unit is rejected as low-information; this heuristic is quantizer
dependent and cannot reject every ambiguous flat/dark scene. No train/test
split or unrelated-pair labels are inferred from filenames or camera models.
Licence verification must be established separately before using this tool.
Read-only, stdlib CPU; outputs aggregates only, never grid/DC/pixel arrays.
Unreadable or unsupported inputs cause exit 1; other inputs are still screened.
Low-information previews are reported separately and do not count as failures.
"""
import argparse
import hashlib
import itertools
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc

GRID = 12
THRESHOLD = 0.98
MIN_SD = 1.0


def fingerprint(wb, hb, dc, width, height):
    """Return normalized grid and SD; discard partial right/bottom blocks."""
    nx, ny = width // 8, height // 8
    if nx < GRID or ny < GRID or wb < nx or hb < ny or len(dc) != wb * hb:
        raise ValueError("inconsistent or undersized DC geometry")
    means = []
    for gy in range(GRID):
        y0, y1 = gy * ny // GRID, (gy + 1) * ny // GRID
        for gx in range(GRID):
            x0, x1 = gx * nx // GRID, (gx + 1) * nx // GRID
            total = sum(sum(dc[y * wb + x0:y * wb + x1]) for y in range(y0, y1))
            means.append(total / ((x1 - x0) * (y1 - y0)))
    mean = math.fsum(means) / len(means)
    centered = [x - mean for x in means]
    energy = math.fsum(x * x for x in centered)
    sd = math.sqrt(energy / len(means))
    if sd < MIN_SD:
        return None, sd
    scale = math.sqrt(energy)
    return [x / scale for x in centered], sd


def correlation(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("inconsistent fingerprints")
    return max(-1.0, min(1.0, math.fsum(x * y for x, y in zip(a, b))))


def measure(paths, failures=None):
    records = []
    seen = set()
    for index, path in enumerate(paths, 1):
        try:
            with open(path, "rb") as stream:
                data = stream.read()
        except OSError as exc:
            if failures is None:
                raise
            failures.append((index, type(exc).__name__))
            continue
        sha = hashlib.sha256(data).hexdigest()
        if sha in seen:
            continue
        seen.add(sha)
        record = {"sha256": sha, "name": os.path.basename(path)}
        try:
            preview = jpeg_dc.find_preview(data)
            if preview is None:
                raise ValueError("no supported large baseline preview")
            _, offset, _, width, height = preview
            wb, hb, dc = jpeg_dc.decode(data, offset)
            fp, sd = fingerprint(wb, hb, dc, width, height)
            record.update(width=width, height=height, grid_sd=sd,
                          status="ok" if fp is not None else "low_information")
        except (ValueError, IndexError, KeyError, StopIteration, ZeroDivisionError) as exc:
            fp = None
            record.update(status="unsupported", error=type(exc).__name__)
        records.append((record, fp))
    return sorted(records, key=lambda row: row[0]["sha256"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="previously licence-verified ORF/ORI files")
    args = parser.parse_args()
    start = time.perf_counter()
    failures = []
    records = measure(args.files, failures)
    for index, error in failures:
        print("input %d: %s" % (index, error), file=sys.stderr)
    for record, _ in records:
        print(json.dumps({"sample": record}, sort_keys=True))
    count = screened = eligible = 0
    for (a, fa), (b, fb) in itertools.combinations(records, 2):
        count += 1
        score = correlation(fa, fb) if fa is not None and fb is not None else None
        eligible += score is not None
        candidate = score is not None and score >= THRESHOLD
        screened += candidate
        print(json.dumps({"pair": [a["sha256"], b["sha256"]],
                          "r": score, "screen_positive": candidate}, sort_keys=True))
    print(json.dumps({"summary": {"samples": len(records), "pairs": count,
          "eligible_pairs": eligible, "screen_positive": screened,
          "grid": GRID, "min_sd": MIN_SD, "threshold": THRESHOLD,
          "alignment": "identity_only", "seconds": time.perf_counter() - start,
          "interpretation": "uncalibrated screening only; scene identity not established"}}, sort_keys=True))
    return int(bool(failures) or any(record["status"] == "unsupported" for record, _ in records))


if __name__ == "__main__":
    sys.exit(main())
