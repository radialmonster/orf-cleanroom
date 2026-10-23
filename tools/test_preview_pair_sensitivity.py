"""Synthetic controls for preview_pair_sensitivity; no images or raw files."""
import datetime
import math
import os
import struct
import sys
import unittest

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
