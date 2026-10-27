#!/usr/bin/env python3
"""Print samples/manifest.csv rows for local raw.pixls.us files.

Supports: samples/manifest.csv, issue "Fill the sample manifest".
Standard library only. Combines the site's licence listing (pixls_samples.py)
with the measured container facts (orf_signature.py). Non-CC0 raw.pixls.us
files are always skipped. Files not on raw.pixls.us are skipped unless you pass
--own, which confirms they are yours (or their owner agreed); they are then
recorded with source=own and licence=not-shared. Bitstream columns are left
blank; fill them only from a tools/ script you ran. Invalid or unreadable
inputs are reported by ordinal; valid rows still append and the command exits 1.

Usage: python manifest_rows.py --by '@yourhandle' [--own] [--licence-records JSON]
                              --append samples/manifest.csv FILE [FILE ...]
"""
import argparse
import csv
from contextlib import nullcontext
import json
import os
import re
import subprocess
import struct
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
    return "hires" if width and int(width) > 6000 else ("normal" if width else "")


def clean(text):
    # Make and model come from the file's own tags: keep them to plain characters so a row
    # cannot carry CSV tricks, formulas or shell metacharacters into the manifest.
    return re.sub(r"[^A-Za-z0-9 ,._()/-]", "_", str(text)).strip()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def licence_records(path):
    """Read retained identities; original licence verification is the caller's responsibility."""
    with open(path, encoding="utf-8-sig") as stream:
        data = json.load(stream, object_pairs_hook=unique_object)
    if isinstance(data, dict):
        data = data.get("files")
    if not isinstance(data, list):
        raise ValueError("licence records must be a list or an object with a files list")
    identities = {}
    for r in data:
        if not isinstance(r, dict):
            raise ValueError("licence record must be an object")
        rid, name, digest, licence = (r.get(k) for k in ("id", "name", "sha256", "licence"))
        if type(rid) is int:
            rid = str(rid)
        if not isinstance(rid, str) or not re.fullmatch(r"[1-9][0-9]*", rid):
            raise ValueError("licence record ID must be a positive decimal")
        if (not isinstance(name, str) or not name or not name.isprintable() or
                any(c in name for c in "/\\") or not name.lower().endswith((".orf", ".ori"))):
            raise ValueError("licence record name must be a public ORF/ORI filename")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("licence record needs a lowercase SHA-256")
        if not isinstance(licence, str) or not licence or not licence.isprintable() or licence != licence.strip():
            raise ValueError("licence record needs a licence")
        identity = (name, digest)
        if rid in identities and identities[rid] != identity:
            raise ValueError("conflicting identities for the same public ID")
        identities[rid] = identity
        yield dict(r, id=rid)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--by", required=True, help="your own GitHub handle, e.g. @you")
    ap.add_argument("--own", action="store_true",
                    help="include files not on raw.pixls.us: you confirm they are yours or the owner agreed")
    ap.add_argument("--header", action="store_true", help="also print the header line")
    ap.add_argument("--licence-records", metavar="JSON",
                    help="use previously verified local licence records instead of the live catalogue")
    ap.add_argument("--append", metavar="CSV",
                    help="append the rows to this file (e.g. samples/manifest.csv) with LF endings, instead of printing them")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    if not re.fullmatch(r"@[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", a.by):
        ap.error("--by must be a single GitHub @login")
    # Appending to a row without a terminating LF would join two CSV rows.
    fresh = not a.append or not os.path.exists(a.append) or os.path.getsize(a.append) == 0
    if a.append and not fresh:
        with open(a.append, "rb") as existing:
            existing.seek(-1, os.SEEK_END)
            if existing.read(1) != b"\n":
                ap.error("--append destination must end in a newline")
            existing.seek(0)
            try:
                header = next(csv.reader([existing.readline().decode("utf-8-sig")], strict=True))
            except (UnicodeError, csv.Error, StopIteration):
                ap.error("--append destination has an invalid manifest header")
            if header != COLUMNS:
                ap.error("--append destination has an invalid manifest header")
    if a.licence_records is not None:
        try:
            listing = by_hash(licence_records(a.licence_records))
        except (OSError, UnicodeError, ValueError):
            ap.error("invalid or unreadable licence records")
    else:
        listing = by_hash(rows())
    # Write LF endings ourselves; shell redirection on Windows can turn them into CRLF.
    # --header with --append writes the header only into a new or empty file.
    dest = open(a.append, "a", encoding="utf-8", newline="") if a.append else nullcontext(sys.stdout)
    failed = False
    with dest as dest:
        out = csv.DictWriter(dest, fieldnames=COLUMNS, lineterminator="\n")
        if a.header and fresh:
            out.writeheader()
        by = "%s tools/orf_signature.py %s" % (a.by, commit())
        for index, p in enumerate(a.files, 1):
            try:
                s = signature(p)
            except (OSError, ValueError, TypeError, struct.error) as exc:
                print("input %d: %s" % (index, type(exc).__name__), file=sys.stderr)
                failed = True
                continue
            r = listing.get(s["sha256"])
            if r is not None and r["licence"] != "CC0":
                print("skipped (raw.pixls.us file under %s, not CC0): %s" % (r["licence"], p), file=sys.stderr)
                continue
            if r is None and not a.own:
                print("skipped (not on raw.pixls.us; pass --own if it's yours): %s" % p, file=sys.stderr)
                continue
            own = r is None
            # A missing dimension is represented as zero by signature().  Without
            # both dimensions the fixed-size test cannot classify the payload.
            width, height = s["payload_w"] or "", s["payload_h"] or ""
            size_class = s["size_class"] if width and height else ""
            out.writerow({
                "source": "own" if own else "pixls",
                "pixls_id": "" if own else r["id"], "pixls_name": "" if own else r["name"],
                "sha256": s["sha256"], "licence": "not-shared" if own else "CC0",
                "make": clean(s["make"]), "model": clean(s["model"]), "mode": mode(width),
                "payload_w": width, "payload_h": height, "bpp": s["bpp"],
                "size_class": size_class,
                "compression_tag": s["compression_tag"], "escape_bits": "", "calm_parse": "",
                "row_stride": "", "variant": variant(size_class), "measured_by": by,
            })
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
