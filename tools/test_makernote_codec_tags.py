#!/usr/bin/env python3
"""Generated containers for makernote_codec_tags: strip sequence and MakerNote status."""
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from makernote_codec_tags import measure  # noqa: E402


def ifd(entries, next_ifd=0):
    """Little-endian IFD; entries are (tag, type, count, 4-byte value field)."""
    out = struct.pack("<H", len(entries))
    for tag, typ, count, field in sorted(entries):
        out += struct.pack("<HHI", tag, typ, count) + field
    return out + struct.pack("<I", next_ifd)


def u32(v):
    return struct.pack("<I", v)


def note(header, sub_type=13, with_2050=False, v0611=14, at=0):
    """MakerNote: header, byte order, top IFD with 0x2040 (and 0x2050), then a
    0x2040 IFD holding 0x0611 = v0611 only. Offsets are relative to the start
    of the enclosing MakerNote; at is where this note starts inside it."""
    top_at = len(header) + 4
    n_top = 2 if with_2050 else 1
    sub_at = top_at + 2 + 12 * n_top + 4
    top = [(0x2040, sub_type, 1, u32(at + sub_at))]
    if with_2050:
        top.append((0x2050, 7, 4, b"abcd"))   # a byte block, not an IFD pointer
    sub = ifd([(0x0611, 3, 1, struct.pack("<HH", v0611, 0))])
    return header + b"II\x03\x00" + ifd(top) + sub


def container(strips, gap=b"\xff", maker=None):
    """TIFF with one image IFD of the given strips (separated by gap) and,
    optionally, an Exif IFD whose MakerNote is maker."""
    n_ifd0 = 4 + (maker is not None)
    data_at = 8 + 2 + 12 * n_ifd0 + 4
    offsets_at, counts_at = data_at, data_at + 4 * len(strips)
    pos = counts_at + 4 * len(strips)
    offsets, body = [], b""
    for i, s in enumerate(strips):
        if i:
            body += gap
        offsets.append(pos + len(body))
        body += s
    entries = [(0x100, 4, 1, u32(16)), (0x101, 4, 1, u32(2)),
               (0x111, 4, len(strips), u32(offsets[0] if len(strips) == 1 else offsets_at)),
               (0x117, 4, len(strips), u32(len(strips[0]) if len(strips) == 1 else counts_at))]
    tail = b""
    if maker is not None:
        exif_at = pos + len(body)
        note_at = exif_at + 2 + 12 + 4
        entries.append((0x8769, 4, 1, u32(exif_at)))
        tail = ifd([(0x927C, 7, len(maker), u32(note_at))]) + maker
    head = b"II*\x00" + u32(8) + ifd(entries)
    arrays = b"".join(u32(o) for o in offsets) + b"".join(u32(len(s)) for s in strips)
    return head + arrays + body + tail


class StripTests(unittest.TestCase):
    def test_separated_strips_skip_the_gap(self):
        # Reading 3 bytes contiguously from the first offset would give 16 (gap 0xff).
        r = measure(container([b"\0\0", b"\x01"]))
        self.assertEqual((r["strips"], r["leading_zero_bits"]), (2, 23))

    def test_single_strip(self):
        self.assertEqual(measure(container([b"\0\x10"]))["leading_zero_bits"], 11)

    def test_all_zero_payload_has_no_count(self):
        self.assertIsNone(measure(container([b"\0\0", b"\0"]))["leading_zero_bits"])

    def test_overlapping_strips_are_rejected(self):
        data = bytearray(container([b"\0\0", b"\x01"]))
        offsets_at = 8 + 2 + 12 * 4 + 4
        first = struct.unpack_from("<I", data, offsets_at)[0]
        struct.pack_into("<I", data, offsets_at + 4, first + 1)
        with self.assertRaises(ValueError):
            measure(bytes(data))


class MakerNoteTests(unittest.TestCase):
    def test_no_makernote_is_unknown_not_absent(self):
        r = measure(container([b"\x01"]))
        self.assertEqual(r["makernote"], "none")
        self.assertEqual(set(r["directories"].values()), {"unknown"})
        self.assertEqual(set(r["tags"].values()), {"unknown"})

    def test_unsupported_header_is_unknown(self):
        r = measure(container([b"\x01"], maker=note(b"OLYMP\0\x02\0")[:-1]))
        self.assertEqual(r["makernote"], "unsupported")
        self.assertEqual(r["tags"]["2040/0611"], "unknown")

    def test_om_system_present_absent_and_unsupported(self):
        r = measure(container([b"\x01"], maker=note(b"OM SYSTEM\0\0\0", with_2050=True)))
        self.assertEqual(r["makernote"], "OM SYSTEM")
        self.assertEqual(r["directories"], {"2040": "ok", "2050": "unsupported"})
        self.assertEqual(r["tags"]["2040/0611"], 14)
        self.assertIsNone(r["tags"]["2040/0620"])           # directory read, tag absent
        self.assertEqual(r["tags"]["2050/1800"], "unknown")  # directory not read

    def test_absent_directory(self):
        r = measure(container([b"\x01"], maker=note(b"OLYMPUS\0")))
        self.assertEqual((r["makernote"], r["directories"]["2050"]), ("OLYMPUS", "absent"))
        self.assertEqual(r["tags"]["2050/1800"], "unknown")

    def test_byte_block_0x2040_is_unsupported(self):
        r = measure(container([b"\x01"], maker=note(b"OLYMPUS\0", sub_type=7)))
        self.assertEqual(r["directories"]["2040"], "unsupported")
        self.assertEqual(r["tags"]["2040/0611"], "unknown")

    def test_leading_om_system_wins_over_embedded_olympus(self):
        om = note(b"OM SYSTEM\0\0\0")
        r = measure(container([b"\x01"], maker=om + note(b"OLYMPUS\0", v0611=1, at=len(om))))
        self.assertEqual(r["makernote"], "OM SYSTEM")
        self.assertEqual(r["tags"]["2040/0611"], 14)

    def test_embedded_olympus_kept_for_legacy(self):
        r = measure(container([b"\x01"], maker=b"pad" + note(b"OLYMPUS\0")))
        self.assertEqual(r["makernote"], "OLYMPUS embedded")


if __name__ == "__main__":
    unittest.main()
