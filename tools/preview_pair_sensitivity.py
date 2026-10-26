#!/usr/bin/env python3
"""Follow-up measurements for the preview-DC pair screen (leads #327, #295).

This tool repeats three descriptive measurements on a supplied cohort and
prints aggregate JSON lines only. It never renders or writes an image, preview
or pixel array.

1. Grid sensitivity: the same embedded-preview luma DC values are averaged into
   complete-block 12x12, 24x24 and 32x32 grids, centred and scaled to unit
   Euclidean norm, and compared with identity alignment only. The frozen
   r >= 0.98 screening cutoff is not a classifier and is not configurable here.
2. Capture-time grouping: standard EXIF DateTimeOriginal (0x9003), falling back
   to DateTimeDigitized (0x9004) and DateTime (0x0132), is read from IFD0 and
   the ExifIFD. Same-model pairs are binned by absolute camera-local wall-clock
   gap. Clock offsets, time zones and wrong camera clocks are not corrected.
3. EXIF setting agreement: exposure time (0x829A), F-number (0x829D), ISO
   (0x8827, then 0x8833), lens model (0xA434) and focal length (0x920A) are
   compared for same-model pairs above and below the cutoff. Agreement is a
   descriptive negative control; it does not establish shared exposure, scene
   or capture, and exact rational equality is used.

Same-model grouping uses the `model` text in samples/manifest.csv, matched by
SHA-256, because that is the grouping used by #327. Inputs without a manifest
row fall back to the EXIF Model tag and are labelled in the sample record.
Input licence verification is the caller's responsibility. Read-only, standard
library CPU; all output is aggregate numbers and public file identities.
"""
import argparse
import csv
import datetime
import hashlib
import itertools
import json
import math
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc

DEFAULT_GRIDS = (12, 24, 32)
THRESHOLD = 0.98
MIN_SD = 1.0
TIME_BINS = ("<=60s", "<=1h", "<=1d", ">1d", "unknown")
METADATA_FIELDS = ("exposure", "fnumber", "iso", "lens", "focal")
TYPE_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8,
             11: 4, 12: 8}
DEFAULT_MANIFEST = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "samples", "manifest.csv"))


def read_ifd(data, offset, endian):
    """Parse one TIFF IFD. Returns tag -> decoded value; bounds-checked."""
    if offset < 0 or offset + 2 > len(data):
        raise ValueError("IFD offset outside file")
    count = struct.unpack_from(endian + "H", data, offset)[0]
    if offset + 2 + 12 * count > len(data):
        raise ValueError("IFD entries outside file")
    out = {}
    for index in range(count):
        position = offset + 2 + 12 * index
        tag, kind, number = struct.unpack_from(endian + "HHI", data, position)
        size = TYPE_SIZE.get(kind, 1) * number
        if size < 0 or size > len(data):
            raise ValueError("IFD value size outside file")
        raw = data[position + 8:position + 12]
        if size <= 4:
            value = raw[:size]
        else:
            pointer = struct.unpack_from(endian + "I", raw)[0]
            if pointer + size > len(data):
                raise ValueError("IFD value offset outside file")
            value = data[pointer:pointer + size]
        if kind == 2:
            out[tag] = value.split(b"\x00", 1)[0].decode("ascii", "replace").strip()
        elif kind in (3, 4, 8, 9):
            code = {3: "H", 4: "I", 8: "h", 9: "i"}[kind]
            out[tag] = list(struct.unpack_from(endian + code * number, value))
        elif kind in (5, 10):
            code = "I" if kind == 5 else "i"
            numbers = struct.unpack_from(endian + code * (2 * number), value)
            out[tag] = [(numbers[2 * i], numbers[2 * i + 1])
                        for i in range(number)]
        else:
            out[tag] = value
    return out


def first(value):
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return None


def parse_datetime(raw):
    if not isinstance(raw, str):
        return None
    try:
        return datetime.datetime.strptime(raw.strip(), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def read_exif(data):
    """Return the standard capture tags used here; no maker notes are read."""
    if data[:2] == b"II":
        endian = "<"
    elif data[:2] == b"MM":
        endian = ">"
    else:
        raise ValueError("not a TIFF-structured file")
    if len(data) < 8:
        raise ValueError("short TIFF header")
    ifd0 = read_ifd(data, struct.unpack_from(endian + "I", data, 4)[0], endian)
    pointer = first(ifd0.get(0x8769))
    exif = read_ifd(data, pointer, endian) if pointer else {}
    raw_datetime = (exif.get(0x9003) or exif.get(0x9004)
                    or ifd0.get(0x0132))
    return {
        "make": ifd0.get(0x010F, ""),
        "model": ifd0.get(0x0110, ""),
        "datetime": parse_datetime(raw_datetime),
        "datetime_raw": raw_datetime if isinstance(raw_datetime, str) else None,
        "exposure": first(exif.get(0x829A)),
        "fnumber": first(exif.get(0x829D)),
        "iso": first(exif.get(0x8827)) or first(exif.get(0x8833)),
        "lens": exif.get(0xA434, ""),
        "focal": first(exif.get(0x920A)),
    }


def rational_equal(a, b):
    """Exact rational equality; None if either value is missing or invalid."""
    if not a or not b or len(a) < 2 or len(b) < 2 or not a[1] or not b[1]:
        return None
    return a[0] * b[1] == b[0] * a[1]


def time_bin(seconds):
    if seconds is None:
        return "unknown"
    if seconds <= 60:
        return "<=60s"
    if seconds <= 3600:
        return "<=1h"
    if seconds <= 86400:
        return "<=1d"
    return ">1d"


def grid_fingerprint(wb, hb, dc, width, height, grid):
    """Area-mean a complete-block luma DC grid; return unit vector and SD."""
    nx, ny = width // 8, height // 8
    if grid < 2 or nx < grid or ny < grid or wb < nx or hb < ny \
            or len(dc) != wb * hb:
        raise ValueError("inconsistent or undersized DC geometry")
    prefix = [[0.0] * (nx + 1) for _ in range(ny + 1)]
    for y in range(ny):
        row = dc[y * wb:y * wb + nx]
        running = 0.0
        current = prefix[y + 1]
        previous = prefix[y]
        for x, value in enumerate(row):
            running += value
            current[x + 1] = previous[x + 1] + running
    means = []
    for gy in range(grid):
        y0, y1 = gy * ny // grid, (gy + 1) * ny // grid
        for gx in range(grid):
            x0, x1 = gx * nx // grid, (gx + 1) * nx // grid
            total = (prefix[y1][x1] - prefix[y0][x1]
                     - prefix[y1][x0] + prefix[y0][x0])
            means.append(total / ((x1 - x0) * (y1 - y0)))
    mean = math.fsum(means) / len(means)
    centered = [value - mean for value in means]
    energy = math.fsum(value * value for value in centered)
    sd = math.sqrt(energy / len(means))
    if sd < MIN_SD:
        return None, sd
    scale = math.sqrt(energy)
    return [value / scale for value in centered], sd


def correlation(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("inconsistent fingerprints")
    return max(-1.0, min(1.0, math.fsum(x * y for x, y in zip(a, b))))


def read_manifest(path):
    models = {}
    if not path or not os.path.exists(path):
        return models
    with open(path, "r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            models[row["sha256"].lower()] = row
    return models


def measure(paths, manifest, grids):
    records = []
    seen = set()
    for path in paths:
        with open(path, "rb") as stream:
            data = stream.read()
        sha = hashlib.sha256(data).hexdigest()
        if sha in seen:
            continue
        seen.add(sha)
        row = manifest.get(sha)
        record = {"sha256": sha, "name": os.path.basename(path),
                  "pixls_id": row["pixls_id"] if row else "?",
                  "model": row["model"] if row else "?",
                  "manifest_row": row is not None}
        fingerprints = {}
        try:
            meta = read_exif(data)
            record.update(model=row["model"] if row else meta["model"],
                          exif_model=meta["model"], make=meta["make"],
                          datetime=(meta["datetime"].strftime("%Y:%m:%d %H:%M:%S")
                                    if meta["datetime"] else None),
                          exposure=meta["exposure"], fnumber=meta["fnumber"],
                          iso=meta["iso"], lens=meta["lens"], focal=meta["focal"])
            preview = jpeg_dc.find_preview(data)
            if preview is None:
                raise ValueError("no supported large baseline preview")
            _, offset, _, width, height = preview
            wb, hb, dc = jpeg_dc.decode(data, offset)
            record.update(width=width, height=height)
            for grid in grids:
                fingerprint, sd = grid_fingerprint(wb, hb, dc, width, height, grid)
                fingerprints[grid] = fingerprint
                record["grid_sd_%d" % grid] = sd
            if any(value is None for value in fingerprints.values()):
                record["status"] = "low_information"
            else:
                record["status"] = "ok"
        except (ValueError, IndexError, KeyError, struct.error) as exc:
            record["status"] = "unsupported"
            record["error"] = type(exc).__name__
            fingerprints = {grid: None for grid in grids}
        records.append((record, fingerprints))
    return sorted(records, key=lambda item: item[0]["sha256"])


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+",
                        help="public ORF/ORI files with licence already verified")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST,
                        help="CSV mapping SHA-256 to model (default: %(default)s)")
    parser.add_argument("--grids", default=",".join(str(g) for g in DEFAULT_GRIDS),
                        help="comma-separated grid sizes (default: %(default)s)")
    args = parser.parse_args()
    try:
        grids = tuple(sorted({int(value) for value in args.grids.split(",")}))
    except ValueError:
        parser.error("--grids must be comma-separated integers")
    if not grids or grids[0] < 2 or grids[-1] > 128:
        parser.error("grid sizes must be between 2 and 128")
    start = time.perf_counter()
    records = measure(args.files, read_manifest(args.manifest), grids)
    for record, _ in records:
        print(json.dumps({"sample": record}, sort_keys=True))
    by_sha = {record["sha256"]: record for record, _ in records}
    primary = grids[0]
    pairs = []
    positive = {grid: set() for grid in grids}
    for (a, fa), (b, fb) in itertools.combinations(records, 2):
        pair = {
            "sha256": [a["sha256"], b["sha256"]],
            "pixls_id": [a["pixls_id"], b["pixls_id"]],
            "model": [a["model"], b["model"]],
            "same_model": (a["model"] == b["model"]
                           and a["model"] not in ("", "?")),
            "gap_s": None,
            "r": {},
            "positive": {},
        }
        if a.get("datetime") and b.get("datetime"):
            left = parse_datetime(a["datetime"])
            right = parse_datetime(b["datetime"])
            if left and right:
                pair["gap_s"] = abs((left - right).total_seconds())
        for grid in grids:
            score = None
            if fa[grid] is not None and fb[grid] is not None:
                score = correlation(fa[grid], fb[grid])
                if score >= THRESHOLD:
                    positive[grid].add((a["sha256"], b["sha256"]))
            pair["r"][str(grid)] = score
            pair["positive"][str(grid)] = (score is not None
                                           and score >= THRESHOLD)
        pair["time_bin"] = time_bin(pair["gap_s"])
        pairs.append(pair)
    for pair in pairs:
        print(json.dumps({"pair": pair}, sort_keys=True))

    same = [pair for pair in pairs if pair["same_model"]]
    for grid in grids:
        scores = [pair["r"][str(grid)] for pair in pairs
                  if pair["r"][str(grid)] is not None]
        selected = [pair for pair in same if pair["positive"][str(grid)]]
        positive_scores = [pair["r"][str(grid)] for pair in pairs
                           if pair["positive"][str(grid)]]
        cross = [pair for pair in pairs if not pair["same_model"]
                 and pair["r"][str(grid)] is not None]
        print(json.dumps({"grid": {
            "size": grid, "pairs": len(pairs), "eligible_pairs": len(scores),
            "positive": len(positive[grid]), "same_model_pairs": len(same),
            "same_model_scored": sum(1 for pair in same
                                     if pair["r"][str(grid)] is not None),
            "same_model_positive": len(selected),
            "cross_model_pairs": len(cross),
            "cross_model_positive": sum(pair["positive"][str(grid)]
                                        for pair in cross),
            "cross_model_max": max((pair["r"][str(grid)] for pair in cross),
                                   default=None),
            "positive_min": min(positive_scores, default=None),
            "positive_max": max(positive_scores, default=None),
        }}, sort_keys=True))
        bins = {key: [0, 0, 0] for key in TIME_BINS}  # scored, positive, unscored
        for pair in same:
            if pair["r"][str(grid)] is None:
                bins[pair["time_bin"]][2] += 1
            else:
                bins[pair["time_bin"]][0] += 1
                bins[pair["time_bin"]][1] += 1 if pair["positive"][str(grid)] else 0
        for key in TIME_BINS:
            print(json.dumps({"time": {"grid": grid, "bin": key,
                                       "pairs": bins[key][0],
                                       "positive": bins[key][1],
                                       "unscored": bins[key][2]}}, sort_keys=True))

    for first_grid, second_grid in itertools.combinations(grids, 2):
        left, right = positive[first_grid], positive[second_grid]
        print(json.dumps({"overlap": {
            "grids": [first_grid, second_grid],
            "both": len(left & right), "first_only": len(left - right),
            "second_only": len(right - left)}}, sort_keys=True))

    high = [pair for pair in pairs if pair["same_model"]
            and pair["positive"][str(primary)]]
    low = [pair for pair in pairs if pair["same_model"]
           and pair["r"][str(primary)] is not None
           and not pair["positive"][str(primary)]]
    for label, group in (("high", high), ("low", low)):
        for field in METADATA_FIELDS:
            both = equal = 0
            for pair in group:
                left = by_sha[pair["sha256"][0]]
                right = by_sha[pair["sha256"][1]]
                a, b = left.get(field), right.get(field)
                if field in ("exposure", "fnumber", "focal"):
                    same = rational_equal(a, b)
                    present = same is not None
                elif field == "iso":
                    same = (a == b) if (a and b) else None
                    present = same is not None
                else:
                    same = (a == b) if (a and b) else None
                    present = same is not None
                if present:
                    both += 1
                    equal += 1 if same else 0
            print(json.dumps({"metadata": {
                "primary_grid": primary, "class": label, "pairs": len(group),
                "field": field, "both_present": both, "equal": equal}},
                sort_keys=True))
        complete = agree = 0
        for pair in group:
            left = by_sha[pair["sha256"][0]]
            right = by_sha[pair["sha256"][1]]
            values = []
            for field in METADATA_FIELDS:
                a, b = left.get(field), right.get(field)
                if field in ("exposure", "fnumber", "focal"):
                    values.append(rational_equal(a, b))
                elif field == "iso":
                    values.append((a == b) if (a and b) else None)
                else:
                    values.append((a == b) if (a and b) else None)
            if all(value is not None for value in values):
                complete += 1
                agree += 1 if all(values) else 0
        print(json.dumps({"metadata": {
            "primary_grid": primary, "class": label, "pairs": len(group),
            "all_five_present": complete, "all_five_equal": agree}},
            sort_keys=True))

    print(json.dumps({"summary": {
        "samples": len(records),
        "usable": sum(1 for record, _ in records if record["status"] == "ok"),
        "low_information": sum(1 for record, _ in records
                               if record["status"] == "low_information"),
        "unsupported": sum(1 for record, _ in records
                           if record["status"] == "unsupported"),
        "pairs": len(pairs), "grids": list(grids), "primary_grid": primary,
        "threshold": THRESHOLD, "min_sd": MIN_SD,
        "seconds": time.perf_counter() - start,
        "interpretation": ("uncalibrated screening and descriptive metadata; "
                           "scene, capture and exposure identity not established"),
    }}, sort_keys=True))


if __name__ == "__main__":
    main()
