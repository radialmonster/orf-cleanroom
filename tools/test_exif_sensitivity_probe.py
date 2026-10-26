#!/usr/bin/env python3
"""Synthetic TIFF bounds, byte-order and numeric sensitivity tests for #106."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exif_sensitivity_probe as probe


def fixture(endian="<", values=(200,), kind=3, pointer_kind=4):
    """Build standard TIFF bytes with independently positioned IFDs and values."""
    data = bytearray(128)
    data[:2] = b"II" if endian == "<" else b"MM"
    struct.pack_into(endian + "HI", data, 2, 42, 8)
    struct.pack_into(endian + "H", data, 8, 1)
    struct.pack_into(endian + "HHII", data, 10, 0x8769, pointer_kind, 1, 32)
    struct.pack_into(endian + "H", data, 32, 1)
    struct.pack_into(endian + "HHI", data, 34, 0x8827, kind, len(values))
    target = 42 if len(values) <= 2 else 64
    if len(values) > 2:
        struct.pack_into(endian + "I", data, 42, target)
    struct.pack_into(endian + "%dH" % len(values), data, target, *values)
    return data


class SensitivityTests(unittest.TestCase):
    def test_byte_orders_and_inline_arrays(self):
        for endian in ("<", ">"):
            for values in ((200,), (100, 6400), (100, 200, 65535)):
                self.assertEqual(probe.sensitivity(fixture(endian, values)), list(values))

    def test_absent_is_distinct(self):
        data = fixture()
        struct.pack_into("<H", data, 10, 1)
        self.assertEqual(probe.sensitivity(data), [])
        data = fixture()
        struct.pack_into("<H", data, 34, 1)
        self.assertEqual(probe.sensitivity(data), [])

    def test_wrong_types_and_empty(self):
        for data in (fixture(kind=4), fixture(pointer_kind=3), fixture(values=())):
            with self.assertRaises(ValueError):
                probe.sensitivity(data)

    def test_malformed_offsets_and_tables(self):
        for position, value in ((4, 0), (18, 127), (18, 0)):
            data = fixture()
            struct.pack_into("<I", data, position, value)
            with self.assertRaises(ValueError):
                probe.sensitivity(data)
        with self.assertRaises(ValueError):
            probe.sensitivity(fixture()[:48])
        data = fixture(values=(100, 200, 400))
        struct.pack_into("<I", data, 42, 126)
        with self.assertRaises(ValueError):
            probe.sensitivity(data)

    def test_duplicate_selected_tag(self):
        data = fixture()
        struct.pack_into("<H", data, 32, 2)
        data[46:58] = data[34:46]
        with self.assertRaises(ValueError):
            probe.sensitivity(data)

    def test_measure_sentinel_and_path_privacy(self):
        data = bytes(fixture(values=(65535,)))
        measured = {"file": "private.ORF", "sha256": hashlib.sha256(data).hexdigest()}
        with mock.patch("builtins.open", mock.mock_open(read_data=data)), \
                mock.patch.object(probe.signature, "signature", return_value=measured):
            result = probe.measure("1", "public.ORF", "private/path")
        self.assertTrue(result["contains_65535_sentinel"])
        self.assertEqual(result["photographic_sensitivity_raw"], [65535])
        self.assertNotIn("private", json.dumps(result))

    def test_changed_input_cannot_attach_other_hash_to_sensitivity(self):
        original = bytes(fixture(values=(200,)))
        changed = bytes(fixture(values=(400,)))
        other_signature = {"file": "private.ORF", "sha256": hashlib.sha256(changed).hexdigest()}
        with mock.patch("builtins.open", mock.mock_open(read_data=original)), \
                mock.patch.object(probe.signature, "signature", return_value=other_signature):
            with self.assertRaises(ValueError):
                probe.measure("1", "public.ORF", "private/path")

    def test_cli_failure_keeps_success_and_sanitizes(self):
        with mock.patch.object(probe, "measure", side_effect=[{"pixls_id": "1"},
                                OSError("private/path")]), contextlib.redirect_stdout(io.StringIO()) as out:
            result = probe.main(["--sample", "1", "a", "path", "--sample", "2", "b", "path"])
        report = json.loads(out.getvalue())
        self.assertEqual(result, 1)
        self.assertEqual(report["samples"], [{"pixls_id": "1"}])
        self.assertEqual(report["failures"], [{"pixls_id": "2", "error_type": "OSError"}])
        self.assertNotIn("private", out.getvalue())

    def test_cli_bad_tiff_type_keeps_later_sample(self):
        work = Path(__file__).resolve().parent.parent / "work" / "test-exif-types"
        work.mkdir(parents=True, exist_ok=True)
        entries = [(256, 2), (257, 2), (273, 74), (279, 8), (258, 16)]
        valid = (struct.pack("<2sHIH", b"II", 42, 8, len(entries)) +
                 b"".join(struct.pack("<HHII", tag, 4, 1, value) for tag, value in entries) +
                 struct.pack("<I", 0) + bytes(8))
        for index in (0, 1, 3):
            with self.subTest(entry=index), tempfile.TemporaryDirectory(dir=str(work)) as folder:
                bad = bytearray(valid)
                struct.pack_into("<HI4s", bad, 10 + index * 12 + 2, 2, 2, b"2\0\0\0")
                bad_path, good_path = Path(folder) / "private-bad.ORF", Path(folder) / "private-good.ORF"
                bad_path.write_bytes(bad)
                good_path.write_bytes(valid)
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    result = probe.main(["--sample", "1", "bad.ORF", str(bad_path),
                                         "--sample", "2", "good.ORF", str(good_path)])
                report = json.loads(out.getvalue())
                self.assertEqual(result, 1)
                self.assertEqual([r["pixls_id"] for r in report["samples"]], ["2"])
                self.assertEqual(report["failures"], [{"pixls_id": "1", "error_type": "TypeError"}])
                self.assertEqual(err.getvalue(), "")
                self.assertNotIn(folder, out.getvalue())


if __name__ == "__main__":
    unittest.main()
