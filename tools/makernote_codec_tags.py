#!/usr/bin/env python3
"""Print fixed MakerNote tag values beside each payload's leading zero-bit count.

Reads, by hex ID only, MakerNote 0x2040 tags 0x0611, 0x0620 and 0x0640..0x0654
and 0x2050 tag 0x1800 (via orf_active_area.olympus_top: a leading OM SYSTEM or
OLYMPUS header first), the payload width and height, and the number of zero
bits before the first one bit of the payload. The payload is the declared strip
sequence of the unique image IFD with the largest total strip byte count, read
by strip_start_audit.independent_strips: separated strips are joined in table
order without gap bytes; tied, overlapping or mismatched strip tables are
rejected.

Absent and unknown stay distinct. "makernote" is the header layout read
(OM SYSTEM, OLYMPUS, OLYMPUS embedded), or "none" / "unsupported". "directories"
gives 0x2040 and 0x2050 as "ok", "absent" (no entry in the top IFD) or
"unsupported" (entry present but not an IFD pointer, e.g. a byte block). A tag
prints null only when its directory was read and the tag is not in it; it
prints "unknown" when its directory was not read. Tag meanings, codec
parameters and causes are not established by this output.

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
from orf_active_area import maker_note, olympus_top, read_ifd  # noqa: E402
from strip_start_audit import independent_strips, startup_zeros  # noqa: E402

TAGS = {0x2040: [0x0611, 0x0620] + list(range(0x0640, 0x064A)) + list(range(0x0650, 0x0655)),
        0x2050: [0x1800]}


def value(ifd, tag):
    entry = ifd.get(tag)
    if not entry or entry[3] is None:
        return None
    v = entry[3]
    if isinstance(v, tuple):
        return v[0] if len(v) == 1 else list(v)
    return v if isinstance(v, int) else None


def makernote_tags(data):
    """(layout, {directory: status}, {tag key: value | None | "unknown"})."""
    blob = maker_note(data)
    found = olympus_top(blob) if blob is not None else None
    layout = found[0] if found else ("none" if blob is None else "unsupported")
    dirs, tags = {}, {}
    for parent, wanted in TAGS.items():
        entry = found[2].get(parent) if found else None
        if not found:
            status = "unknown"
        elif entry is None:
            status = "absent"
        elif entry[0] != 13 or entry[3] is None:
            status = "unsupported"
        else:
            status = "ok"
        sub = read_ifd(blob, found[1], entry[3]) if status == "ok" else None
        dirs["%04x" % parent] = status
        for tag in wanted:
            tags["%04x/%04x" % (parent, tag)] = value(sub, tag) if sub is not None else "unknown"
    return layout, dirs, tags


def measure(data):
    geometry, payload = independent_strips(data)
    layout, dirs, tags = makernote_tags(data)
    return {"sha256": hashlib.sha256(data).hexdigest(),
            "payload": [geometry["width"], geometry["height"]],
            "strips": geometry["strip_count"],
            "leading_zero_bits": startup_zeros(payload),
            "makernote": layout, "directories": dirs, "tags": tags}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    failed = False
    for n, path in enumerate(a.files, 1):
        try:
            with open(path, "rb") as f:
                print(json.dumps(measure(f.read()), sort_keys=True))
        except (ValueError, TypeError, IndexError, KeyError, OSError, struct.error) as exc:
            reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            print("input %d: %s" % (n, reason), file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
