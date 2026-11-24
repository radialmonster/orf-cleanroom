#!/usr/bin/env python3
"""Print fixed MakerNote tag values beside each payload's leading zero-bit count.

Reads, by hex ID only, MakerNote 0x2040 tags 0x0611, 0x0620 and 0x0640..0x0654
and 0x2050 tag 0x1800 (leading OLYMPUS or OM SYSTEM header, via
orf_active_area.olympus_tags), the payload width and height, and the number of
zero bits before the first one bit of the payload (image IFD with the largest
total strip byte count, as in orf_signature.py). A missing tag prints null.
Tag meanings, codec parameters and causes are not established by this output.

One JSON line per input: SHA-256, payload dimensions, leading zero bits, tags.
No paths. Standard library only, Python 3.8+.

Usage:
    python -I tools/makernote_codec_tags.py FILE [FILE ...]
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_active_area import maker_note, olympus_tags  # noqa: E402
from orf_signature import Tiff  # noqa: E402

TAGS = [("image_processing", t) for t in [0x0611, 0x0620] + list(range(0x0640, 0x064A))
        + list(range(0x0650, 0x0655))] + [("focus_info", 0x1800)]


def value(ifd, tag):
    entry = ifd.get(tag)
    if not entry or entry[3] is None:
        return None
    v = entry[3]
    if isinstance(v, tuple):
        return v[0] if len(v) == 1 else list(v)
    return v if isinstance(v, int) else None


def leading_zero_bits(data, off, size):
    for i in range(min(size, 64)):
        b = data[off + i]
        if b:
            return 8 * i + (7 - b.bit_length() + 1)
    return None


def measure(data):
    t = Tiff(data)
    best = max(t.all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    off, size = best[0x111][0], sum(best[0x117])
    blob = maker_note(data)
    subs = olympus_tags(blob) if blob is not None else {}
    tags = {"%04x/%04x" % (0x2040 if sub == "image_processing" else 0x2050, tag):
            value(subs.get(sub, {}), tag) for sub, tag in TAGS}
    return {"sha256": hashlib.sha256(data).hexdigest(),
            "payload": [best[0x100][0], best[0x101][0]],
            "leading_zero_bits": leading_zero_bits(data, off, size),
            "tags": tags}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    failed = False
    for path in a.files:
        try:
            with open(path, "rb") as f:
                print(json.dumps(measure(f.read()), sort_keys=True))
        except (ValueError, TypeError, IndexError, KeyError, OSError, struct.error) as exc:
            print("input %d: %s" % (a.files.index(path) + 1, type(exc).__name__), file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
