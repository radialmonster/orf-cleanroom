#!/usr/bin/env python3
"""Calibrate preview_pair_screen.py output against capture-provenance labels.

Part of #295. Labels come only from each file's own metadata (EXIF
DateTimeOriginal, read with the TIFF reader of orf_signature.py), its payload
width and its file name; no preview, payload or score is used to label. Pair
classes:
  P  companion: a High Res ORF (payload wider than 6000) and an ORI with the
     same base name and the same DateTimeOriginal (camera-written pair)
  B  same second, not a companion (bursts, brackets): reported, not a negative
  H  same calendar day, different second, |dt| <= --hard-seconds (default 600)
  S  same day, |dt| > --hard-seconds
  E  different calendar days
Split held out by shooting day: sorted distinct days at even index are
"cal", odd are "val"; cross-split pairs count only in "all". On cal, t* is
the observed P/H score maximizing TPR(P) - FPR(H) (ties: highest), then
applied unchanged to val. Base names drop the extension and a trailing _<n>
copy suffix. DateTimeOriginal has 1 s resolution; files without it are
reported and left out.

Input: the JSON lines printed by preview_pair_screen.py (UTF-8 or UTF-16, as
PowerShell redirection writes) and the same files. Prints aggregates only:
counts, rates, AUC (Mann-Whitney, ties 0.5) and score ranges per class.

Usage: python -I -B tools/capture_pair_calibration.py --screen SCREEN.jsonl FILE [FILE ...]
       python -I -B tools/capture_pair_calibration.py --screen SCREEN.jsonl --files-from LIST.txt
Read-only, stdlib only.
"""
import argparse
import bisect
import hashlib
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, signature  # noqa: E402

CLASSES = "PBHSE"
HIRES_WIDTH = 6000


def load_screen(path):
    raw = open(path, "rb").read()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def base_name(name):
    return re.sub(r"(_\d+)?\.[A-Za-z0-9]+$", "", os.path.basename(name))


def date_time_original(data):
    t = Tiff(data)
    for tags in t.all_ifds():
        ptr = tags.get(0x8769)
        if ptr:
            exif, _ = t.ifd(ptr[0])
            v = exif.get(0x9003)
            return v if isinstance(v, str) and v else None
    return None


def file_meta(path):
    data = open(path, "rb").read()
    dto = date_time_original(data)
    return hashlib.sha256(data).hexdigest(), {
        "base": base_name(path),
        "ori": path.lower().endswith(".ori"),
        "hires": int(signature(path)["payload_w"] or 0) > HIRES_WIDTH,
        "dto": dto,
        "time": datetime.strptime(dto, "%Y:%m:%d %H:%M:%S") if dto else None,
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
    scores, excluded = {}, {}
    for rec in records:
        if "pair" not in rec:
            continue
        a, b = (meta.get(h) for h in rec["pair"])
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
        p("  AUC P vs H %s, P vs E %s" % ("%.4f" % a1 if a1 is not None else "n/a",
                                          "%.4f" % a2 if a2 is not None else "n/a"))
        if P and H:
            p("  min P %.6f, max H %.6f: %s" % (min(P), max(H), "separable" if min(P) > max(H) else "overlap"))
    P, H = scores.get(("cal", "P"), []), scores.get(("cal", "H"), [])
    if not P or not H:
        p("calibration: no P or H pairs on cal days")
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
    for path in paths:
        sha, m = file_meta(path)
        meta.setdefault(sha, m)
    records = load_screen(a.screen)
    print("files %d distinct %d without DateTimeOriginal %d" % (
        len(paths), len(meta), sum(1 for m in meta.values() if not m["dto"])))
    report(*analyse(records, meta, a.hard_seconds), threshold=a.threshold)


if __name__ == "__main__":
    main()
