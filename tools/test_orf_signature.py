#!/usr/bin/env python3
"""Signature CSV and failure exit status; synthetic TIFF metadata only."""
import contextlib
import csv
import hashlib
import io
import os
import runpy
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_signature as S


def fixture(width=2):
    entries = [(256, width), (257, 2), (258, 16), (259, 1),
               (273, 86), (279, width * 4)]
    return (struct.pack("<2sHIH", b"II", 0x5352, 8, len(entries))
            + b"".join(struct.pack("<HHII", tag, 4, 1, value)
                       for tag, value in entries)
            + struct.pack("<I", 0) + bytes(width * 4))


class Tests(unittest.TestCase):
    def test_out_of_bounds_ifd_links_fail_batch_and_preserve_valid_rows(self):
        for link in ('next', 'subifd'):
            data = bytearray(fixture())
            if link == 'next':
                struct.pack_into('<I', data, 82, len(data) + 100)
            else:
                # Add a numeric SubIFD tag as an extra IFD entry.
                data = bytearray(fixture())
                data[82:82] = struct.pack('<HHII', 0x14a, 4, 1, len(data) + 112)
                struct.pack_into('<H', data, 8, 7)
                struct.pack_into('<I', data, 10 + 4 * 12 + 8, 98)
            with self.subTest(link=link):
                status, output, error = self.call(['bad.orf', 'valid.orf'],
                    {'bad.orf': bytes(data), 'valid.orf': fixture()})
                self.assertEqual(status, 1)
                self.assertEqual([r['file'] for r in csv.DictReader(io.StringIO(output))], ['valid.orf'])
                self.assertIn('bad.orf:', error)

    def test_ifd_offsets_order_default_and_cycles(self):
        data = bytearray(160)
        struct.pack_into('<2sHIH', data, 0, b'II', 42, 8, 1)
        struct.pack_into('<HHII', data, 10, 0x14a, 4, 2, 128)
        struct.pack_into('<I', data, 22, 80)
        struct.pack_into('<II', data, 128, 32, 56)
        for offset, value, nxt in ((32, 1, 8), (56, 2, 0), (80, 3, 32)):
            struct.pack_into('<H', data, offset, 1)
            struct.pack_into('<HHII', data, offset + 2, 0x100, 4, 1, value)
            struct.pack_into('<I', data, offset + 14, nxt)
        tiff = S.Tiff(data)
        with_offsets = list(tiff.all_ifds(with_offsets=True))
        self.assertEqual([offset for offset, _ in with_offsets], [8, 56, 32, 80])
        default = list(tiff.all_ifds())
        self.assertTrue(all(isinstance(tags, dict) for tags in default))
        self.assertEqual(default, [tags for _, tags in with_offsets])
        self.assertEqual([tags[0x100][0] for tags in default[1:]], [2, 1, 3])

    def call(self, paths, blobs):
        def opening(path, mode):
            self.assertEqual(mode, "rb")
            if path not in blobs:
                raise FileNotFoundError("synthetic missing input")
            return io.BytesIO(blobs[path])
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("builtins.open", side_effect=opening), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = S.main(paths)
        return status, out.getvalue(), err.getvalue()

    def test_valid_csv_and_input_order(self):
        a, b = fixture(), fixture(3)
        status, output, error = self.call(["b.orf", "a.orf"],
                                           {"a.orf": a, "b.orf": b})
        self.assertEqual(status, 0)
        self.assertEqual(error, "")
        rows = list(csv.DictReader(io.StringIO(output)))
        self.assertEqual([r["file"] for r in rows], ["b.orf", "a.orf"])
        self.assertEqual(rows[0]["sha256"], hashlib.sha256(b).hexdigest())
        self.assertEqual(rows[0]["payload_w"], "3")
        self.assertEqual(rows[0]["payload_bytes"], "12")
        self.assertEqual(rows[0]["size_class"], "packed-16")
        self.assertEqual(output.count("file,sha256,"), 1)

    def test_all_missing_inputs_fail_without_csv(self):
        status, output, error = self.call(["missing.orf", "absent.orf"], {})
        self.assertEqual(status, 1)
        self.assertEqual(output, "")
        self.assertIn("missing.orf: synthetic missing input", error)
        self.assertIn("absent.orf: synthetic missing input", error)

    def test_mixed_errors_preserve_successful_rows(self):
        blobs = {"valid.orf": fixture(), "bad.orf": b"not TIFF",
                 "short.orf": b"II", "last.orf": fixture(3)}
        paths = ["missing.orf", "valid.orf", "bad.orf", "short.orf", "last.orf"]
        status, output, error = self.call(paths, blobs)
        self.assertEqual(status, 1)
        rows = list(csv.DictReader(io.StringIO(output)))
        self.assertEqual([r["file"] for r in rows], ["valid.orf", "last.orf"])
        self.assertEqual(len(error.splitlines()), 3)
        self.assertEqual(output.count("file,sha256,"), 1)

    def test_no_ifds_fails(self):
        status, output, error = self.call(["empty.orf"],
            {"empty.orf": struct.pack("<2sHI", b"II", 0x5352, 0)})
        self.assertEqual(status, 1)
        self.assertEqual(output, "")
        self.assertIn("empty.orf:", error)

    def test_truncated_payload_does_not_produce_signature(self):
        # The IFD declares 8 bytes at offset 86; the file contains only 4.
        truncated = fixture()[:-4]
        status, output, error = self.call(["truncated.orf", "valid.orf"],
                                          {"truncated.orf": truncated, "valid.orf": fixture()})
        self.assertEqual(status, 1)
        self.assertEqual([r["file"] for r in csv.DictReader(io.StringIO(output))], ["valid.orf"])
        self.assertIn("truncated.orf:", error)

    def test_mismatched_strip_tables_do_not_produce_signature(self):
        data = bytearray(fixture())
        # StripOffsets is the fifth entry; replace its one value with two.
        struct.pack_into("<II", data, 10 + 4 * 12 + 4, 2, len(data))
        data.extend(struct.pack("<II", 86, 90))
        status, output, error = self.call(["mismatch.orf"], {"mismatch.orf": bytes(data)})
        self.assertEqual(status, 1)
        self.assertEqual(output, "")
        self.assertIn("mismatch.orf:", error)

    def test_reordered_strips_are_valid(self):
        data = bytearray(fixture())
        offsets_at = len(data)
        data.extend(struct.pack("<II", 90, 86))
        counts_at = len(data)
        data.extend(struct.pack("<II", 4, 4))
        struct.pack_into("<II", data, 10 + 4 * 12 + 4, 2, offsets_at)
        struct.pack_into("<II", data, 10 + 5 * 12 + 4, 2, counts_at)
        status, output, error = self.call(["reordered.orf"], {"reordered.orf": bytes(data)})
        self.assertEqual((status, error), (0, ""))
        row = next(csv.DictReader(io.StringIO(output)))
        self.assertEqual((row["payload_offset"], row["payload_bytes"], row["size_class"]),
                         ("90", "8", "packed-16"))

    def test_overlapping_strip_extents_are_rejected(self):
        # Each strip is individually in bounds, but overlapping extents double-count bytes.
        for offsets in ((86, 86), (86, 88), (88, 86)):
            data = bytearray(fixture())
            offsets_at = len(data)
            data.extend(struct.pack("<II", *offsets))
            counts_at = len(data)
            data.extend(struct.pack("<II", 4, 4))
            struct.pack_into("<II", data, 10 + 4 * 12 + 4, 2, offsets_at)
            struct.pack_into("<II", data, 10 + 5 * 12 + 4, 2, counts_at)
            with self.subTest(offsets=offsets):
                status, output, error = self.call(["bad.orf", "valid.orf"],
                    {"bad.orf": bytes(data), "valid.orf": fixture()})
                self.assertEqual(status, 1)
                self.assertEqual([r["file"] for r in csv.DictReader(io.StringIO(output))], ["valid.orf"])
                self.assertIn("overlap", error)

    def test_multiple_dimensions_are_rejected(self):
        for entry in (0, 1):
            for typ in (3, 4):
                with self.subTest(entry=entry, typ=typ):
                    data = bytearray(fixture())
                    pos = 10 + entry * 12
                    if typ == 3:
                        struct.pack_into("<HHIHH", data, pos, 256 + entry, 3, 2, 2, 4)
                    else:
                        struct.pack_into("<II", data, pos + 4, 2, len(data))
                        data.extend(struct.pack("<II", 2, 4))
                    status, output, error = self.call(
                        ["bad.orf", "valid.orf"],
                        {"bad.orf": bytes(data), "valid.orf": fixture()})
                    self.assertEqual(status, 1)
                    self.assertEqual([r["file"] for r in csv.DictReader(io.StringIO(output))],
                                     ["valid.orf"])
                    self.assertIn("bad.orf:", error)

    def test_single_short_dimensions_remain_valid(self):
        data = bytearray(fixture())
        for entry in (0, 1):
            struct.pack_into("<HHIHH", data, 10 + entry * 12, 256 + entry, 3, 1, 2, 0)
        status, output, error = self.call(["short.orf"], {"short.orf": bytes(data)})
        self.assertEqual((status, error), (0, ""))
        row = next(csv.DictReader(io.StringIO(output)))
        self.assertEqual((row["payload_w"], row["payload_h"], row["bpp"], row["size_class"]),
                         ("2", "2", "16.000", "packed-16"))

    def test_non_numeric_dimension_and_strip_count_fail_per_file(self):
        for entry in (0, 1, 5):
            data = bytearray(fixture())
            struct.pack_into("<HI4s", data, 10 + entry * 12 + 2, 2, 2, b"2\0\0\0")
            for paths in (["bad.orf"], ["bad.orf", "valid.orf"]):
                with self.subTest(entry=entry, paths=paths):
                    status, output, error = self.call(paths, {"bad.orf": bytes(data), "valid.orf": fixture()})
                    self.assertEqual(status, 1)
                    self.assertEqual([r["file"] for r in csv.DictReader(io.StringIO(output))],
                                     ["valid.orf"] if len(paths) == 2 else [])
                    self.assertIn("bad.orf:", error)

    def test_missing_dimension_keeps_existing_empty_bpp(self):
        data = bytearray(fixture())
        struct.pack_into("<H", data, 10, 65000)
        status, output, error = self.call(["missing.orf"], {"missing.orf": bytes(data)})
        self.assertEqual((status, error), (0, ""))
        row = next(csv.DictReader(io.StringIO(output)))
        self.assertEqual((row["payload_w"], row["bpp"], row["size_class"]), ("0", "", "variable"))

    def test_help_and_no_arguments(self):
        for paths, expected in [(["--help"], 0), (["-h"], 0), ([], 2)]:
            status, output, error = self.call(paths, {})
            self.assertEqual(status, expected)
            self.assertIn("Print a measured signature", output)
            self.assertEqual(error, "")

    def test_script_entrypoint_propagates_failure(self):
        # Run the reviewed tool entrypoint in this process; no child programs.
        path = os.path.join(os.path.dirname(__file__), "orf_signature.py")
        with mock.patch.object(sys, "argv", [path, "missing-synthetic.orf"]), \
                mock.patch("builtins.open", side_effect=FileNotFoundError("missing")), \
                contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit) as raised:
            runpy.run_path(path, run_name="__main__")
        self.assertEqual(raised.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
