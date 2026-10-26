#!/usr/bin/env python3
"""Calibrate preview_pair_screen.py output against capture-provenance labels.

Part of #295. Labels come only from each file's own metadata (EXIF
DateTimeOriginal, read with the TIFF reader of orf_signature.py), its payload
width and its file name; no preview, payload or score is used to label. Pair
classes:
  P  companion: a High Res ORF (payload wider than 6000) and an ORI with the
     same base name and the same DateTimeOriginal (camera-written pair)
  B  same second, not a companion (bursts, brackets): reported, not a negative
  H  same calendar day, different second, |dt| <= --hard-seconds (default 600);
     scene unknown, not an established unrelated negative
  S  same day, |dt| > --hard-seconds
  E  different calendar days
Split held out by shooting day: sorted distinct days at even index are
"cal", odd are "val"; cross-split pairs count only in "all". On cal, t* is
the observed P/H score maximizing P hit rate minus H hit rate (ties: highest), then
applied unchanged to val. Base names drop only the extension; numeric suffixes
remain part of the stem. DateTimeOriginal has 1 s resolution; files without it are
reported and left out. Calibration and validation each require at least 10 P
and 10 H pairs; meeting this descriptive minimum does not establish statistical
validity or independent captures.

Input: the JSON lines printed by preview_pair_screen.py (UTF-8 or UTF-16, as
PowerShell redirection writes) and the same files. Prints aggregates only:
counts, rates, AUC (Mann-Whitney, ties 0.5) and score ranges per class.
Each nonblank JSON line must be an object with unique keys.
Each unordered pair of distinct SHA-256 hashes may occur only once; malformed,
self, or duplicate pairs and correlations outside the finite [-1, 1] range
are rejected. A null correlation represents an unavailable screen score.
Unreadable or malformed input files stop the run before any report.

Usage: python -I -B tools/capture_pair_calibration.py --screen SCREEN.jsonl FILE [FILE ...]
       python -I -B tools/capture_pair_calibration.py --screen SCREEN.jsonl --files-from LIST.txt
Read-only, stdlib only.
"""
import argparse
import bisect
import hashlib
import json
import math
import os
import re
import struct
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, signature  # noqa: E402

CLASSES = "PBHSE"
HIRES_WIDTH = 6000
MIN_CLASS_PAIRS = 10


def unique_screen_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def load_screen(path):
    with open(path, "rb") as stream:
        raw = stream.read()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
    records = [json.loads(line, object_pairs_hook=unique_screen_object)
               for line in text.splitlines() if line.strip()]
    if any(not isinstance(record, dict) for record in records):
        raise ValueError("screen lines must be JSON objects")
    return records


def base_name(name):
    return os.path.splitext(os.path.basename(name))[0]


def date_time_original(data):
    t = Tiff(data)
    todo, seen = [t.u32(4)], set()
    while todo:
        offset = todo.pop()
        if offset == 0 or offset in seen or offset + 2 > len(data):
            continue
        seen.add(offset)
        tags, nxt = t.ifd(offset)
        todo.append(nxt)
        todo.extend(tags.get(0x14A) or [])
        pointers = []
        for i in range(t.u16(offset)):
            tag, typ, count = struct.unpack_from(t.e + 'HHI', data, offset + 2 + 12 * i)
            if tag == 0x8769:
                pointers.append((typ, count))
        if pointers and (len(pointers) != 1 or pointers[0] != (4, 1)):
            return None
        ptr = tags.get(0x8769)
        if ptr:
            if not isinstance(ptr, list) or len(ptr) != 1:
                return None
            exif, _ = t.ifd(ptr[0])
            v = exif.get(0x9003)
            # Tiff.ifd keeps the last occurrence; conflicting timestamps must
            # not turn an ambiguous EXIF directory into a valid capture time.
            entries = []
            for i in range(t.u16(ptr[0])):
                p = ptr[0] + 2 + 12 * i
                tag, typ, count = struct.unpack_from(t.e + "HHI", data, p)
                if tag != 0x9003:
                    continue
                if typ != 2:
                    entries.append(None)
                    continue
                start = p + 8 if count <= 4 else t.u32(p + 8)
                if start + count > len(data):
                    entries.append(None)
                else:
                    entries.append(data[start:start + count].split(b"\0")[0].decode("ascii", "replace").strip())
            if len(entries) > 1 and any(value != entries[0] for value in entries[1:]):
                return None
            return v if isinstance(v, str) and v else None
    return None


def file_meta(path):
    with open(path, "rb") as stream:
        data = stream.read()
    dto = date_time_original(data)
    try:
        if not dto or not re.fullmatch(r"[0-9]{4}:[0-9]{2}:[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}", dto):
            raise ValueError("missing or malformed DateTimeOriginal")
        when = datetime.strptime(dto, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        dto, when = None, None
    digest = hashlib.sha256(data).hexdigest()
    measured = signature(path)
    if measured["sha256"] != digest:
        raise ValueError("sample changed while reading metadata")
    return digest, {
        "base": base_name(path),
        "ori": path.lower().endswith(".ori"),
        "hires": int(measured["payload_w"] or 0) > HIRES_WIDTH,
        "dto": dto,
        "time": when,
    }


def classify(a, b, hard_seconds):
    if a["dto"] == b["dto"]:
        if a["base"] == b["base"] and ((a["hires"] and b["ori"]) or (b["hires"] and a["ori"])):
            return "P"
        return "B"
    if a["dto"][:10] != b["dto"][:10]:
        return "E"
    return "H" if abs((a["time"] - b["time"]).total_seconds()) <= hard_seconds else "S"


def auc(pos, neg):
    if not pos or not neg:
        return None
    neg = sorted(neg)
    total = 0.0
    for p in pos:
        lo = bisect.bisect_left(neg, p)
        hi = bisect.bisect_right(neg, p)
        total += lo + 0.5 * (hi - lo)
    return total / (len(pos) * len(neg))


def calibrate(pos, neg):
    best = None
    for th in sorted(set(pos + neg)):
        j = sum(x >= th for x in pos) / len(pos) - sum(x >= th for x in neg) / len(neg)
        if best is None or j > best[0] or (j == best[0] and th > best[1]):
            best = (j, th)
    return best


def analyse(records, meta, hard_seconds):
    days = sorted({m["dto"][:10] for m in meta.values() if m["dto"]})
    split_of = dict((d, "cal" if i % 2 == 0 else "val") for i, d in enumerate(days))
    scores, excluded, seen = {}, {}, set()
    for rec in records:
        if "pair" not in rec:
            continue
        pair = rec["pair"]
        if (not isinstance(pair, list) or len(pair) != 2
                or any(not isinstance(h, str) or not re.fullmatch(r"[0-9a-f]{64}", h) for h in pair)):
            raise ValueError("pair must contain two lowercase SHA-256 hashes")
        if pair[0] == pair[1]:
            raise ValueError("self pair is invalid")
        key = tuple(sorted(pair))
        if key in seen:
            raise ValueError("duplicate unordered pair")
        seen.add(key)
        if "r" not in rec:
            raise ValueError("missing pair correlation")
        r = rec["r"]
        if r is not None and (isinstance(r, bool) or not isinstance(r, (int, float))
                              or not -1 <= r <= 1 or not math.isfinite(r)):
            raise ValueError("correlation must be null or a finite number in [-1, 1]")
        a, b = (meta.get(h) for h in pair)
        if a is None or b is None or not a["dto"] or not b["dto"]:
            excluded["no_metadata"] = excluded.get("no_metadata", 0) + 1
            continue
        c = classify(a, b, hard_seconds)
        if rec["r"] is None:
            excluded[c] = excluded.get(c, 0) + 1
            continue
        sa, sb = split_of[a["dto"][:10]], split_of[b["dto"][:10]]
        for sp in ("all", sa if sa == sb else None):
            if sp:
                scores.setdefault((sp, c), []).append(rec["r"])
    return days, split_of, scores, excluded


def report(days, split_of, scores, excluded, threshold, out=sys.stdout):
    def p(*args):
        print(*args, file=out)
    p("days %d (cal %d, val %d); excluded pairs %s" % (
        len(days), sum(v == "cal" for v in split_of.values()), sum(v == "val" for v in split_of.values()),
        json.dumps(excluded, sort_keys=True)))
    p("H: same-session, scene unknown; its hit rate is not a verified false-positive rate")
    for sp in ("all", "cal", "val"):
        p("== %s" % sp)
        for c in CLASSES:
            v = sorted(scores.get((sp, c), []))
            if v:
                hits = sum(x >= threshold for x in v)
                p("  %s n=%d >=%g: %d (%.4f) min %.6f median %.6f max %.6f" % (
                    c, len(v), threshold, hits, hits / len(v), v[0], v[len(v) // 2], v[-1]))
        P, H, E = (scores.get((sp, c), []) for c in "PHE")
        a1, a2 = auc(P, H), auc(P, E)
        p("  AUC P (n=%d) vs H (n=%d) %s, P (n=%d) vs E (n=%d) %s" % (
            len(P), len(H), "%.4f" % a1 if a1 is not None else "n/a",
            len(P), len(E), "%.4f" % a2 if a2 is not None else "n/a"))
        if P and H:
            p("  min P %.6f, max H %.6f: %s" % (min(P), max(H), "separable" if min(P) > max(H) else "overlap"))
    P, H = scores.get(("cal", "P"), []), scores.get(("cal", "H"), [])
    vp, vh = scores.get(("val", "P"), []), scores.get(("val", "H"), [])
    cal_ok = len(P) >= MIN_CLASS_PAIRS and len(H) >= MIN_CLASS_PAIRS
    val_ok = len(vp) >= MIN_CLASS_PAIRS and len(vh) >= MIN_CLASS_PAIRS
    p("minimum support per split: P >= %d and H >= %d pairs; descriptive only" % (MIN_CLASS_PAIRS, MIN_CLASS_PAIRS))
    p("calibration: %s (P=%d H=%d)" % ("supported" if cal_ok else "unsupported", len(P), len(H)))
    p("validation: %s (P=%d H=%d)" % ("supported" if val_ok and cal_ok else "unsupported", len(vp), len(vh)))
    if not cal_ok:
        return
    j, th = calibrate(P, H)
    p("calibrated t* %.9f (J on cal %.4f)" % (th, j))
    for sp in ("cal", "val"):
        parts = ["%s %d/%d" % (c, sum(x >= th for x in scores[(sp, c)]), len(scores[(sp, c)]))
                 for c in CLASSES if scores.get((sp, c))]
        p("  %s at t*: %s" % (sp, ", ".join(parts)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--screen", required=True, help="JSON lines from preview_pair_screen.py")
    ap.add_argument("--files-from", help="text file with one input path per line (UTF-8)")
    ap.add_argument("--hard-seconds", type=float, default=600.0)
    ap.add_argument("--threshold", type=float, default=0.98, help="fixed screen cutoff to report")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args(argv)
    paths = list(a.files)
    if a.files_from:
        with open(a.files_from, encoding="utf-8-sig") as f:
            paths += [line.strip() for line in f if line.strip()]
    meta = {}
    for index, path in enumerate(paths, 1):
        try:
            sha, m = file_meta(path)
        except (OSError, ValueError, TypeError, IndexError, KeyError, struct.error) as exc:
            ap.error("input %d: %s" % (index, type(exc).__name__))
        meta.setdefault(sha, m)
    try:
        records = load_screen(a.screen)
    except ValueError:
        ap.error("invalid screen JSON")
    try:
        analysis = analyse(records, meta, a.hard_seconds)
    except ValueError as exc:
        ap.error(str(exc))
    print("files %d distinct %d without DateTimeOriginal %d" % (
        len(paths), len(meta), sum(1 for m in meta.values() if not m["dto"])))
    report(*analysis, threshold=a.threshold)


if __name__ == "__main__":
    main()
