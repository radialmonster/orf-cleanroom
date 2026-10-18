#!/usr/bin/env python3
"""Print samples/manifest.csv rows for local raw.pixls.us files.

Supports: samples/manifest.csv, issue "Fill the sample manifest".
Standard library only. Combines the site's licence listing (pixls_samples.py)
with the measured container facts (orf_signature.py). Files that are not CC0
raw.pixls.us files are reported on stderr and skipped. Bitstream columns are
left blank; fill them only from a tools/ script you ran.

Usage: python manifest_rows.py --by @yourhandle FILE [FILE ...] >> ../samples/manifest.csv
"""
import argparse
import csv
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import signature  # noqa: E402
from pixls_samples import rows  # noqa: E402

COLUMNS = ["pixls_id", "pixls_name", "sha256", "licence", "make", "model", "mode",
           "payload_w", "payload_h", "bpp", "compression_tag", "escape_bits",
           "calm_parse", "row_stride", "variant", "measured_by"]


def commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
    except OSError:
        return ""


def variant(bpp):
    # VARIANTS.md: V0 (uncompressed) is the only variant assignable from the
    # container alone; compressed files stay unassigned until a bitstream test.
    return "V0" if bpp and float(bpp) >= 12 else "unassigned"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--by", required=True, help="your own GitHub handle, e.g. @you")
    ap.add_argument("--header", action="store_true", help="also print the header line")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    listing = {r["sha256"]: r for r in rows()}
    out = csv.DictWriter(sys.stdout, fieldnames=COLUMNS, lineterminator="\n")
    if a.header:
        out.writeheader()
    by = "%s tools/orf_signature.py %s" % (a.by, commit())
    for p in a.files:
        s = signature(p)
        r = listing.get(s["sha256"])
        if r is None or r["licence"] != "CC0":
            print("skipped (not a CC0 raw.pixls.us file): %s" % p, file=sys.stderr)
            continue
        out.writerow({
            "pixls_id": r["id"], "pixls_name": r["name"], "sha256": s["sha256"], "licence": "CC0",
            "make": s["make"], "model": s["model"], "mode": r["mode"],
            "payload_w": s["payload_w"], "payload_h": s["payload_h"], "bpp": s["bpp"],
            "compression_tag": s["compression_tag"], "escape_bits": "", "calm_parse": "",
            "row_stride": "", "variant": variant(s["bpp"]), "measured_by": by,
        })


if __name__ == "__main__":
    main()
