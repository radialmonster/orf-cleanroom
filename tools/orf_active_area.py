#!/usr/bin/env python3
"""Print the Olympus active image area from the ORF maker note.

Supports: lead #11 (token-to-preview geometry) and specs/V1.md G3-G4. The
payload can be larger than the active image; this tool reads the maker note
(Exif 0x927C -> Olympus ImageProcessing sub-IFD tag 0x2040) and prints the
active width/height (tags 0x0614/0x0615) and the crop rectangle 0x0637. It reads
the TIFF structure only and decodes nothing.
Payload geometry uses the image IFD with the largest total strip byte count,
as in orf_signature.py. Without strip counts, primary IFD dimensions are
labelled primary and no payload border is calculated.

Standard library only, Python 3.8+. Prints aggregate metadata only.

Usage:
    python -I tools/orf_active_area.py FILE [FILE ...]
    python -I tools/orf_active_area.py --self-test
"""
import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, TYPE_SIZES  # noqa: E402


def read_ifd(blob, e, off):
    """Return {tag: (type, count, raw_bytes, value)} for a small IFD."""
    if off < 0 or off + 2 > len(blob):
        return {}
    n = struct.unpack_from(e + "H", blob, off)[0]
    tags = {}
    for i in range(n):
        p = off + 2 + 12 * i
        if p + 12 > len(blob):
            break
        tag, typ, count = struct.unpack_from(e + "HHI", blob, p)
        size = TYPE_SIZES.get(typ, 1) * count
        if size <= 4:
            raw = blob[p + 8:p + 8 + size]
        else:
            vp = struct.unpack_from(e + "I", blob, p + 8)[0]
            raw = blob[vp:vp + size] if vp + size <= len(blob) else b""
        val = None
        if typ in (4, 13) and count == 1 and len(raw) >= 4:
            val = struct.unpack_from(e + "I", raw)[0]
        elif typ == 3 and count <= 8 and len(raw) >= 2 * count:
            val = struct.unpack_from(e + "%dH" % count, raw)
        tags[tag] = (typ, count, raw, val)
    return tags


def maker_note(data):
    t = Tiff(data)
    main, _ = t.ifd(t.u32(4))
    exif = main.get(0x8769)
    if not exif:
        return None
    exif_off = exif[0]
    n = t.u16(exif_off)
    for i in range(n):
        p = exif_off + 2 + 12 * i
        tag, typ, count = struct.unpack_from(t.e + "HHI", data, p)
        if tag != 0x927C:
            continue
        size = TYPE_SIZES.get(typ, 1) * count
        vp = p + 8 if size <= 4 else t.u32(p + 8)
        return data[vp:vp + size]
    return None


def olympus_tags(blob):
    idx = blob.find(b"OLYMPUS\0")
    if idx < 0:
        return {}
    base = idx + 8
    if blob[base:base + 2] not in (b"II", b"MM"):
        return {}
    e = "<" if blob[base:base + 2] == b"II" else ">"
    top = read_ifd(blob, e, base + 4)
    out = {}
    for tag, label in ((0x2010, "equipment"), (0x2020, "settings"),
                       (0x2030, "raw_development"), (0x2040, "image_processing"),
                       (0x2050, "focus_info")):
        entry = top.get(tag)
        if not entry or entry[0] != 13 or entry[3] is None:
            continue
        out[label] = read_ifd(blob, e, entry[3])
    return out


def main(paths):
    if not paths or paths[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if paths else 2
    failed = False
    for path in paths:
        try:
            with open(path, "rb") as f:
                data = f.read()
            t = Tiff(data)
            main, _ = t.ifd(t.u32(4))
            ifds = list(t.all_ifds())
            best = max(ifds, key=lambda d: sum(d.get(0x117) or [0]), default=main)
            has_payload = bool(sum(best.get(0x117) or [0]))
            if not has_payload:
                best = main
            w = (best.get(0x100) or [0])[0]
            h = (best.get(0x101) or [0])[0]
            geometry = "payload" if has_payload else "primary"
            blob = maker_note(data)
            if blob is None:
                print("%s %s %dx%d  no maker note" % (os.path.basename(path), geometry, w, h))
                continue
            imgs = olympus_tags(blob).get("image_processing", {})
            aw = imgs.get(0x0614, (0, 0, b"", None))[3]
            ah = imgs.get(0x0615, (0, 0, b"", None))[3]
            # a SHORT count-1 tag reads as a 1-tuple; use its value like a LONG
            aw = aw[0] if isinstance(aw, tuple) and len(aw) == 1 else aw
            ah = ah[0] if isinstance(ah, tuple) and len(ah) == 1 else ah
            if isinstance(aw, tuple) or isinstance(ah, tuple):
                aw = ah = None   # more than one value: not an active width/height
            cr = imgs.get(0x0637, (0, 0, b"", None))[3]
            if aw is None or ah is None:
                print("%s %s %dx%d  active dimensions not found" % (
                    os.path.basename(path), geometry, w, h))
                continue
            border = "%dx%d" % (w - aw, h - ah) if has_payload else "unavailable"
            print("%s %s %dx%d  active %dx%d  border %s  crop %s" % (
                os.path.basename(path), geometry, w, h, aw, ah, border,
                list(cr) if cr else "not found"))
        except (ValueError, TypeError, IndexError, KeyError, OSError, struct.error) as exc:
            print("%s: %s" % (path, exc), file=sys.stderr)
            failed = True
    return 1 if failed else 0


def self_test():
    e = "<"
    ifd = struct.pack(e + "H", 1)
    ifd += struct.pack(e + "HHI", 0x0614, 4, 1) + struct.pack(e + "I", 5184) + b"\0\0\0\0"
    ifd += struct.pack(e + "I", 0)  # next IFD
    blob = b"OLYMPUS\0II\x03\x00" + ifd
    tags = read_ifd(blob, e, 12)
    assert tags[0x0614][3] == 5184, tags
    assert tags[0x0614][1] == 1, tags
    print("self-test ok: synthetic Olympus IFD tag 0x0614 reads 5184")


def main_cli():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    return main(a.files)


if __name__ == "__main__":
    sys.exit(main_cli())
