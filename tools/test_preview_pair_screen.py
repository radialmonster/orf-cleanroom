"""Synthetic geometry/arithmetic controls for preview_pair_screen; no images."""
import io
import math
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_pair_screen as p


def reference(a, b):
    # Independent unnormalized Pearson formula on original synthetic values.
    n = len(a)
    numerator = n * sum(x * y for x, y in zip(a, b)) - sum(a) * sum(b)
    denominator = math.sqrt((n * sum(x * x for x in a) - sum(a) ** 2) *
                            (n * sum(y * y for y in b) - sum(b) ** 2))
    return numerator / denominator


class ScreenTests(unittest.TestCase):
    def test_malformed_scan_does_not_abort_remaining_files(self):
        # A SOF component absent from SOS raises StopIteration in jpeg_dc.decode
        # (reported in #347). Keep this per-file failure out of pair scores.
        inputs = {"bad.ORF": b"bad synthetic input", "good.ORF": b"good synthetic input"}
        dc = list(range(144))
        with patch("builtins.open", side_effect=lambda path, mode: io.BytesIO(inputs[path])), \
                patch.object(p.jpeg_dc, "find_preview", return_value=(9216, 0, 1, 96, 96)), \
                patch.object(p.jpeg_dc, "decode", side_effect=[StopIteration(), (12, 12, dc)]):
            rows = p.measure(["bad.ORF", "good.ORF"])
        by_name = {record["name"]: (record, fp) for record, fp in rows}
        bad, bad_fp = by_name["bad.ORF"]
        good, good_fp = by_name["good.ORF"]
        self.assertEqual((bad["status"], bad["error"], bad_fp),
                         ("unsupported", "StopIteration", None))
        self.assertEqual(good["status"], "ok")
        self.assertIsNotNone(good_fp)

    def test_affine_and_inverse(self):
        a = [((i * 37) % 151) - 75 for i in range(144)]
        fa, _ = p.fingerprint(12, 12, a, 96, 96)
        for b, expected in [([3*x + 100 for x in a], 1), ([-x for x in a], -1)]:
            fb, _ = p.fingerprint(12, 12, b, 96, 96)
            self.assertAlmostEqual(p.correlation(fa, fb), expected, places=13)
            self.assertAlmostEqual(p.correlation(fa, fb), reference(a, b), places=13)

    def test_independent_structure(self):
        # Orthogonal horizontal and vertical ramps are unrelated controls,
        # not sampled pictures or a claim about unrelated public captures.
        a = [x * 10 for y in range(12) for x in range(12)]
        b = [y * 10 for y in range(12) for x in range(12)]
        fa, _ = p.fingerprint(12, 12, a, 96, 96)
        fb, _ = p.fingerprint(12, 12, b, 96, 96)
        self.assertAlmostEqual(p.correlation(fa, fb), 0, places=13)
        self.assertAlmostEqual(p.correlation(fa, fb), reference(a, b), places=13)

    def test_flat_rejection(self):
        self.assertEqual(p.fingerprint(12, 12, [999]*144, 96, 96), (None, 0.0))
        self.assertIsNone(p.fingerprint(12, 12, [i % 2 for i in range(144)], 96, 96)[0])

    def test_partial_blocks_excluded(self):
        a = [x + 12*y for y in range(12) for x in range(12)]
        padded = []
        for y in range(13):
            padded.extend(a[y*12:(y+1)*12] + [999999] if y < 12 else [999999]*13)
        fa, sa = p.fingerprint(12, 12, a, 96, 96)
        fb, sb = p.fingerprint(13, 13, padded, 103, 103)
        self.assertEqual((fa, sa), (fb, sb))

    def test_disjoint_bin_means(self):
        # 24x24 replicates each 12x12 grid cell as a constant 2x2 tile.
        a = [i for i in range(144)]
        b = [a[(y//2)*12 + x//2] for y in range(24) for x in range(24)]
        self.assertEqual(p.fingerprint(12, 12, a, 96, 96),
                         p.fingerprint(24, 24, b, 192, 192))

    def test_invalid_geometry(self):
        with self.assertRaises(ValueError):
            p.fingerprint(12, 12, [], 96, 96)
        with self.assertRaises(ValueError):
            p.fingerprint(11, 12, [0]*132, 88, 96)


if __name__ == "__main__":
    unittest.main()
