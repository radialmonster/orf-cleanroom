#!/usr/bin/env python3
"""Print a measured signature for ORF/ORI files, one CSV row per file.

Supports: VARIANTS.md (signature fields), samples/manifest.csv, OPEN-QUESTIONS 6.
Standard library only. Reads the TIFF structure (public TIFF 6.0 spec) and
reports container and payload facts; it does not decode image data.

Usage: python orf_signature.py FILE [FILE ...] > rows.csv
"""
import csv
import hashlib
import os
import struct
import sys

TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}
# Olympus uses its own magic numbers in place of TIFF's 42.
MAGICS = {42: "TIFF", 0x4F52: "ORF-RO", 0x5352: "ORF-RS"}


class Tiff:
    def __init__(self, data):
        self.data = data
        order = data[:2]
        if order == b"II":
            self.e = "<"
        elif order == b"MM":
            self.e = ">"
        else:
            raise ValueError("not a TIFF-structured file")
        self.magic = self.u16(2)
        if self.magic not in MAGICS:
            raise ValueError("unknown magic 0x%04X" % self.magic)

    def u16(self, off):
        return struct.unpack_from(self.e + "H", self.data, off)[0]

    def u32(self, off):
        return struct.unpack_from(self.e + "I", self.data, off)[0]

    def ifd(self, off):
        """Return ({tag: values}, next_ifd_offset) for the IFD at off."""
        n = self.u16(off)
        tags = {}
        for i in range(n):
            p = off + 2 + 12 * i
            tag, typ, count = struct.unpack_from(self.e + "HHI", self.data, p)
            size = TYPE_SIZES.get(typ, 1) * count
            vp = p + 8 if size <= 4 else self.u32(p + 8)
            if vp + size > len(self.data):
                continue
            if typ == 2:
                tags[tag] = self.data[vp:vp + count].split(b"\0")[0].decode("ascii", "replace").strip()
            elif typ == 3:
                tags[tag] = list(struct.unpack_from(self.e + "%dH" % count, self.data, vp))
            elif typ in (4, 13):
                tags[tag] = list(struct.unpack_from(self.e + "%dI" % count, self.data, vp))
            else:
                tags[tag] = None  # type not needed for the signature
        return tags, self.u32(off + 2 + 12 * n)

    def all_ifds(self):
        """Walk the IFD chain and SubIFDs (tag 0x14A); yield tag dicts."""
        seen = set()
        todo = [self.u32(4)]
        while todo:
            off = todo.pop()
            if off == 0 or off in seen or off + 2 > len(self.data):
                continue
            seen.add(off)
            tags, nxt = self.ifd(off)
            yield tags
            todo.append(nxt)
            todo.extend(tags.get(0x14A) or [])


def first(tags, tag):
    v = tags.get(tag)
    return v[0] if isinstance(v, list) and v else v


def signature(path):
    with open(path, "rb") as f:
        data = f.read()
    t = Tiff(data)
    ifds = list(t.all_ifds())
    make = next((d[0x10F] for d in ifds if isinstance(d.get(0x10F), str)), "")
    model = next((d[0x110] for d in ifds if isinstance(d.get(0x110), str)), "")
    # The raw payload is the image IFD with the largest total strip byte count.
    best = max(ifds, key=lambda d: sum(d.get(0x117) or [0]))
    w, h = first(best, 0x100) or 0, first(best, 0x101) or 0
    nbytes = sum(best.get(0x117) or [0])
    return {
        "file": os.path.basename(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "magic": MAGICS[t.magic],
        "make": make,
        "model": model,
        "payload_w": w,
        "payload_h": h,
        "bits_per_sample": first(best, 0x102) or "",
        "compression_tag": first(best, 0x103) or "",
        "payload_offset": first(best, 0x111) or "",
        "payload_bytes": nbytes,
        "bpp": "%.2f" % (nbytes * 8 / (w * h)) if w and h else "",
    }


def main(paths):
    if not paths:
        sys.exit(__doc__)
    out = None
    for p in paths:
        try:
            row = signature(p)
        except (ValueError, struct.error, OSError) as exc:
            print("%s: %s" % (p, exc), file=sys.stderr)
            continue
        if out is None:
            out = csv.DictWriter(sys.stdout, fieldnames=list(row), lineterminator="\n")
            out.writeheader()
        out.writerow(row)


if __name__ == "__main__":
    main(sys.argv[1:])
