#!/usr/bin/env python3
"""Print samples/manifest.csv rows for local raw.pixls.us files.

Supports: samples/manifest.csv, issue "Fill the sample manifest".
Standard library only. Combines the site's licence listing (pixls_samples.py)
with the measured container facts (orf_signature.py). Non-CC0 raw.pixls.us
files are always skipped. Files not on raw.pixls.us are skipped unless you pass
--own, which confirms they are yours (or their owner agreed); they are then
recorded with source=own and licence=not-shared. Bitstream columns are left
blank; fill them only from a tools/ script you ran.

Usage: python manifest_rows.py --by @yourhandle [--own] FILE [FILE ...] >> ../samples/manifest.csv
"""
import argparse
import csv
from contextlib import nullcontext
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import signature  # noqa: E402
from pixls_samples import by_hash, rows  # noqa: E402

COLUMNS = ["source", "pixls_id", "pixls_name", "sha256", "licence", "make", "model", "mode",
           "payload_w", "payload_h", "bpp", "size_class", "compression_tag", "escape_bits",
           "calm_parse", "row_stride", "variant", "measured_by"]


def commit(path="orf_signature.py"):
    """Short hash of the last commit that changed the measuring script."""
    try:
        return subprocess.run(["git", "log", "-1", "--format=%h", "--", path], capture_output=True, text=True,
                              cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
    except OSError:
        return ""


def variant(size_class):
    # VARIANTS.md: V0 (fixed-size packing) is the only variant assignable from
    # the container alone; compressed files stay unassigned until a bitstream test.
    return "V0" if size_class.startswith("packed-") else "unassigned"


def mode(width):
    # Four Thirds and Micro Four Thirds sensors are at most ~5.3k wide; High
    # Res Shot payloads are 8k+ wide. Measured from the payload, not the name.
    return "hires" if width and int(width) > 6000 else "normal"


def clean(text):
    # Make and model come from the file's own tags: keep them to plain characters so a row
    # cannot carry CSV tricks, formulas or shell metacharacters into the manifest.
    return re.sub(r"[^A-Za-z0-9 ,._()/-]", "_", str(text)).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--by", required=True, help="your own GitHub handle, e.g. @you")
    ap.add_argument("--own", action="store_true",
                    help="include files not on raw.pixls.us: you confirm they are yours or the owner agreed")
    ap.add_argument("--header", action="store_true", help="also print the header line")
    ap.add_argument("--append", metavar="CSV",
                    help="append the rows to this file (e.g. samples/manifest.csv) with LF endings, instead of printing them")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    listing = by_hash(rows())
    # Write LF endings ourselves; shell redirection on Windows can turn them into CRLF.
    # --header with --append writes the header only into a new or empty file.
    fresh = not a.append or not os.path.exists(a.append) or os.path.getsize(a.append) == 0
    dest = open(a.append, "a", encoding="utf-8", newline="") if a.append else nullcontext(sys.stdout)
    with dest as dest:
        out = csv.DictWriter(dest, fieldnames=COLUMNS, lineterminator="\n")
        if a.header and fresh:
            out.writeheader()
        by = "%s tools/orf_signature.py %s" % (a.by, commit())
        for p in a.files:
            s = signature(p)
            r = listing.get(s["sha256"])
            if r is not None and r["licence"] != "CC0":
                print("skipped (raw.pixls.us file under %s, not CC0): %s" % (r["licence"], p), file=sys.stderr)
                continue
            if r is None and not a.own:
                print("skipped (not on raw.pixls.us; pass --own if it's yours): %s" % p, file=sys.stderr)
                continue
            own = r is None
            out.writerow({
                "source": "own" if own else "pixls",
                "pixls_id": "" if own else r["id"], "pixls_name": "" if own else r["name"],
                "sha256": s["sha256"], "licence": "not-shared" if own else "CC0",
                "make": clean(s["make"]), "model": clean(s["model"]), "mode": mode(s["payload_w"]),
                "payload_w": s["payload_w"], "payload_h": s["payload_h"], "bpp": s["bpp"],
                "size_class": s["size_class"],
                "compression_tag": s["compression_tag"], "escape_bits": "", "calm_parse": "",
                "row_stride": "", "variant": variant(s["size_class"]), "measured_by": by,
            })


if __name__ == "__main__":
    main()
