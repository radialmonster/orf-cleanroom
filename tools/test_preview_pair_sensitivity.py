"""Synthetic controls for preview_pair_sensitivity; no images or raw files."""
import contextlib
import csv
import datetime
import io
import json
import math
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_pair_screen as screen
import preview_pair_sensitivity as sensitivity


def reference(a, b):
    n = len(a)
    numerator = n * sum(x * y for x, y in zip(a, b)) - sum(a) * sum(b)
    denominator = math.sqrt((n * sum(x * x for x in a) - sum(a) ** 2) *
                            (n * sum(y * y for y in b) - sum(b) ** 2))
    return numerator / denominator


def synthetic_tiff():
    """Minimal little-endian TIFF with IFD0 and one ExifIFD."""
    data = bytearray(256)
    data[0:2] = b"II"
    struct.pack_into("<H", data, 2, 42)
    struct.pack_into("<I", data, 4, 8)
    # IFD0: Model and ExifIFD pointer.
    struct.pack_into("<H", data, 8, 2)
    struct.pack_into("<HHI", data, 10, 0x0110, 2, 10)
    struct.pack_into("<I", data, 18, 120)
    struct.pack_into("<HHI", data, 22, 0x8769, 4, 1)
    struct.pack_into("<I", data, 30, 40)
    struct.pack_into("<I", data, 34, 0)
    # ExifIFD: six scalar tags, ending at byte 118.
    struct.pack_into("<H", data, 40, 6)
    struct.pack_into("<HHI", data, 42, 0x9003, 2, 20)
    struct.pack_into("<I", data, 50, 132)
    struct.pack_into("<HHI", data, 54, 0x829A, 5, 1)
    struct.pack_into("<I", data, 62, 152)
    struct.pack_into("<HHI", data, 66, 0x829D, 5, 1)
    struct.pack_into("<I", data, 74, 160)
    struct.pack_into("<HHI", data, 78, 0x8827, 3, 1)
    struct.pack_into("<H", data, 86, 200)
    struct.pack_into("<HHI", data, 90, 0xA434, 2, 9)
    struct.pack_into("<I", data, 98, 168)
    struct.pack_into("<HHI", data, 102, 0x920A, 5, 1)
    struct.pack_into("<I", data, 110, 177)
    struct.pack_into("<I", data, 114, 0)
    data[120:130] = b"TestModel\x00"
    data[132:152] = b"2020:01:02 03:04:05\x00"
    struct.pack_into("<II", data, 152, 1, 100)
    struct.pack_into("<II", data, 160, 28, 10)
    data[168:177] = b"TestLens\x00"
    struct.pack_into("<II", data, 177, 14, 1)
    return bytes(data)


class GridTests(unittest.TestCase):
    def test_12_matches_reviewed_screen(self):
        dc = [((i * 37) % 151) - 75 for i in range(24 * 24)]
        ours, sd = sensitivity.grid_fingerprint(24, 24, dc, 192, 192, 12)
        theirs, their_sd = screen.fingerprint(24, 24, dc, 192, 192)
        self.assertEqual(sd, their_sd)
        self.assertEqual(ours, theirs)

    def test_affine_and_inverse(self):
        a = [((i * 37) % 151) - 75 for i in range(24 * 24)]
        fa, _ = sensitivity.grid_fingerprint(24, 24, a, 192, 192, 24)
        for b, expected in [([3 * x + 100 for x in a], 1),
                            ([-x for x in a], -1)]:
            fb, _ = sensitivity.grid_fingerprint(24, 24, b, 192, 192, 24)
            self.assertAlmostEqual(sensitivity.correlation(fa, fb),
                                   expected, places=13)
            self.assertAlmostEqual(sensitivity.correlation(fa, fb),
                                   reference(a, b), places=13)

    def test_flat_rejection(self):
        self.assertEqual(
            sensitivity.grid_fingerprint(12, 12, [999] * 144, 96, 96, 12),
            (None, 0.0))
        self.assertIsNone(sensitivity.grid_fingerprint(
            12, 12, [i % 2 for i in range(144)], 96, 96, 12)[0])

    def test_partial_blocks_excluded(self):
        a = [x + 12 * y for y in range(12) for x in range(12)]
        padded = []
        for y in range(13):
            padded.extend(a[y * 12:(y + 1) * 12] + [999999]
                          if y < 12 else [999999] * 13)
        fa, sa = sensitivity.grid_fingerprint(12, 12, a, 96, 96, 12)
        fb, sb = sensitivity.grid_fingerprint(13, 13, padded, 103, 103, 12)
        self.assertEqual((fa, sa), (fb, sb))

    def test_invalid_geometry(self):
        with self.assertRaises(ValueError):
            sensitivity.grid_fingerprint(12, 12, [], 96, 96, 12)
        with self.assertRaises(ValueError):
            sensitivity.grid_fingerprint(11, 12, [0] * 132, 88, 96, 12)


class AggregationTests(unittest.TestCase):
    def test_manifest_structural_errors_and_valid_empty_model(self):
        work = Path(__file__).resolve().parent.parent / 'work' / 'test-preview-csv'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            path = Path(folder) / 'fixture.csv'
            digest = 'a' * 64
            for text in ('sha256,model,pixls_id,model\n%s,Good,1,Wrong\n' % digest,
                         'sha256,pixls_id\n%s,1\n' % digest,
                         'sha256,pixls_id,model\n%s,1\n' % digest,
                         'sha256,pixls_id,model\n%s,1,"unterminated\n' % digest):
                path.write_text(text, encoding='utf-8')
                with self.subTest(text=text), self.assertRaises((ValueError, csv.Error)):
                    sensitivity.read_manifest(str(path))
            path.write_text('sha256,pixls_id,model\n%s,1,Old\n%s,2,\n' % (digest, digest), encoding='utf-8')
            result = sensitivity.read_manifest(str(path))
            self.assertEqual((result[digest]['pixls_id'], result[digest]['model']), ('2', ''))

    def test_invalid_manifest_stops_cli_before_sample_reads(self):
        work = Path(__file__).resolve().parent.parent / 'work' / 'test-preview-csv'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            manifest = Path(folder) / 'fixture.csv'
            manifest.write_text('sha256,pixls_id,model,model\n' + 'a' * 64 + ',1,One,Two\n', encoding='utf-8')
            out, err = io.StringIO(), io.StringIO()
            with patch.object(sys, 'argv', ['probe', 'sample.ORF', '--manifest', str(manifest)]), \
                 patch.object(sensitivity, 'measure') as measure, \
                 contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as raised:
                    sensitivity.main()
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(out.getvalue(), '')
            self.assertIn('invalid or unreadable manifest', err.getvalue())
            measure.assert_not_called()

    def test_missing_manifest_is_not_an_empty_manifest(self):
        work = Path(__file__).resolve().parent.parent / 'work' / 'test-preview-manifest'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            missing = root / 'private-missing.csv'
            with self.assertRaises(OSError):
                sensitivity.read_manifest(str(missing))
            manifest = root / 'manifest.csv'
            manifest.write_text('sha256,pixls_id,model\n' + 'a' * 64 + ',1,TestModel\n', encoding='utf-8')
            self.assertEqual(sensitivity.read_manifest(str(manifest))['a' * 64]['model'], 'TestModel')
            self.assertEqual(sensitivity.read_manifest(''), {})

    def test_cli_manifest_errors_stop_before_measurement(self):
        work = Path(__file__).resolve().parent.parent / 'work' / 'test-preview-manifest'
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(work)) as folder:
            root = Path(folder)
            bad = root / 'private-invalid.csv'
            bad.write_bytes(b'\xff')
            for path in (root / 'private-missing.csv', bad):
                output, error = io.StringIO(), io.StringIO()
                with self.subTest(path=path.name), \
                     patch.object(sys, 'argv', ['probe', 'sample.ORF', '--manifest', str(path)]), \
                     patch.object(sensitivity, 'measure') as measure, \
                     contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    with self.assertRaises(SystemExit) as raised:
                        sensitivity.main()
                    self.assertEqual(raised.exception.code, 2)
                    self.assertEqual(output.getvalue(), '')
                    self.assertNotIn('private', error.getvalue())
                    measure.assert_not_called()

    def test_unscored_pairs_stay_out_of_low_and_time_denominators(self):
        def record(sha, status):
            return {"sha256": sha, "name": sha[:6] + ".ORF", "pixls_id": "1",
                    "model": "TestModel", "manifest_row": True,
                    "exif_model": "TestModel", "make": "Test",
                    "datetime": "2020:01:02 03:04:05",
                    "exposure": (1, 100), "fnumber": (28, 10), "iso": 200,
                    "lens": "TestLens", "focal": (14, 1), "status": status}

        left = record("a" * 64, "unsupported")
        right = record("b" * 64, "low_information")
        results = [(left, {12: None, 24: [1.0, 0.0]}),
                   (right, {12: None, 24: [1.0, 0.0]})]
        stdout = io.StringIO()
        with patch.object(sys, "argv",
                          ["probe", "a.ORF", "b.ORF", "--grids", "12,24"]), \
                patch.object(sensitivity, "measure", return_value=results), \
                patch.object(sensitivity, "read_manifest", return_value={}), \
                contextlib.redirect_stdout(stdout):
            sensitivity.main()
        rows = [json.loads(line) for line in stdout.getvalue().splitlines()]

        grids = {row["grid"]["size"]: row["grid"] for row in rows if "grid" in row}
        self.assertEqual(grids[12]["eligible_pairs"], 0)
        self.assertEqual(grids[12]["same_model_scored"], 0)
        self.assertEqual(grids[24]["eligible_pairs"], 1)
        self.assertEqual(grids[24]["same_model_scored"], 1)

        times = {(row["time"]["grid"], row["time"]["bin"]): row["time"]
                 for row in rows if "time" in row}
        self.assertEqual(times[(12, "<=60s")],
                         {"grid": 12, "bin": "<=60s", "pairs": 0,
                          "positive": 0, "unscored": 1})
        self.assertEqual(times[(24, "<=60s")]["pairs"], 1)
        self.assertEqual(times[(24, "<=60s")]["positive"], 1)
        self.assertEqual(times[(24, "<=60s")]["unscored"], 0)

        low = [row["metadata"] for row in rows
               if row.get("metadata", {}).get("class") == "low"]
        self.assertTrue(low)
        self.assertTrue(all(entry["pairs"] == 0 for entry in low))


class ExifTests(unittest.TestCase):
    def test_synthetic_tiff(self):
        meta = sensitivity.read_exif(synthetic_tiff())
        self.assertEqual(meta["model"], "TestModel")
        self.assertEqual(meta["datetime"],
                         datetime.datetime(2020, 1, 2, 3, 4, 5))
        self.assertTrue(sensitivity.rational_equal(meta["exposure"], (1, 100)))
        self.assertTrue(sensitivity.rational_equal(meta["fnumber"], (28, 10)))
        self.assertEqual(meta["iso"], 200)
        self.assertEqual(meta["lens"], "TestLens")
        self.assertTrue(sensitivity.rational_equal(meta["focal"], (14, 1)))

    def test_sshort_tag(self):
        data = bytearray(64)
        data[0:2] = b"II"
        struct.pack_into("<H", data, 2, 42)
        struct.pack_into("<I", data, 4, 8)
        struct.pack_into("<H", data, 8, 1)
        struct.pack_into("<HHI", data, 10, 0x1234, 8, 1)
        struct.pack_into("<h", data, 18, -7)
        self.assertEqual(sensitivity.read_ifd(bytes(data), 8, "<")[0x1234], [-7])

    def test_rational_equality(self):
        self.assertTrue(sensitivity.rational_equal((1, 100), (2, 200)))
        self.assertFalse(sensitivity.rational_equal((1, 100), (1, 50)))
        self.assertIsNone(sensitivity.rational_equal(None, (1, 2)))
        self.assertIsNone(sensitivity.rational_equal((1, 0), (1, 1)))

    def test_parse_datetime(self):
        self.assertEqual(sensitivity.parse_datetime("2020:01:02 03:04:05"),
                         datetime.datetime(2020, 1, 2, 3, 4, 5))
        self.assertIsNone(sensitivity.parse_datetime("0000:00:00 00:00:00"))
        self.assertIsNone(sensitivity.parse_datetime(None))

    def test_time_bins(self):
        self.assertEqual(sensitivity.time_bin(None), "unknown")
        self.assertEqual(sensitivity.time_bin(0), "<=60s")
        self.assertEqual(sensitivity.time_bin(60), "<=60s")
        self.assertEqual(sensitivity.time_bin(61), "<=1h")
        self.assertEqual(sensitivity.time_bin(3600), "<=1h")
        self.assertEqual(sensitivity.time_bin(3601), "<=1d")
        self.assertEqual(sensitivity.time_bin(86400), "<=1d")
        self.assertEqual(sensitivity.time_bin(86401), ">1d")


if __name__ == "__main__":
    unittest.main()
