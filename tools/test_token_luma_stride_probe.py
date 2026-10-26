"""Synthetic checks for token_luma_stride_probe (no sample files)."""

import contextlib
import io
import math
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_luma_stride_probe as p  # noqa: E402


class ExtractTests(unittest.TestCase):
    def test_first_and_offset_rows(self):
        rows, w, stride = 3, 4, 6
        sa = bytearray(range(rows * stride))
        first = p.extract_image(sa, rows, w, stride, 0, 0)
        self.assertEqual(first, bytearray([0, 1, 2, 3, 6, 7, 8, 9, 12, 13, 14, 15]))
        shifted = p.extract_image(sa, rows, w, stride, 2, 0)
        self.assertEqual(shifted, bytearray([2, 3, 4, 5, 8, 9, 10, 11, 14, 15, 16, 17]))

    def test_start_row_skips_complete_rows(self):
        rows, w, stride = 2, 3, 5
        sa = bytearray(range(5 * stride))
        out = p.extract_image(sa, rows, w, stride, 0, 3)
        self.assertEqual(out, bytearray([15, 16, 17, 20, 21, 22]))

    def test_rejects_bad_geometry(self):
        sa = bytearray(20)
        for args in ((0, 3, 4, 0, 0), (2, 5, 4, 0, 0),
                     (2, 3, 4, 2, 0), (2, 3, -1, 0, 0)):
            with self.assertRaises(ValueError):
                p.extract_image(sa, *args)

    def test_rejects_short_row(self):
        with self.assertRaisesRegex(ValueError, "short"):
            p.extract_image(bytearray(5), 2, 3, 3, 0, 0)


class TargetTests(unittest.TestCase):
    def test_top_and_offset_crop(self):
        dc = list(range(8 * 20))
        top = p.preview_target(dc, 8, 20, 0, 10, 100)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0][0], 0)
        later = p.preview_target(dc, 8, 20, 50, 10, 100)
        self.assertEqual(len(later), 2)
        self.assertEqual(later[0][0], 80)

    def test_clamps_and_rejects(self):
        dc = list(range(8 * 20))
        # the last rows: rounding puts r0 at 19, the clamp keeps both DC rows inside
        last = p.preview_target(dc, 8, 20, 95, 5, 100)
        self.assertEqual(last[0][0], 18 * 8)
        self.assertEqual(len(last), 2)
        # past the image height: rejected, not silently shifted up
        for args in ((8, 20, 100, 10, 100), (8, 20, 0, 200, 100),
                     (8, 20, -1, 10, 100), (8, 20, 0, 1, 100),
                     (8, 1, 0, 10, 100), (8, 20, 0, 10, 0)):
            with self.assertRaises(ValueError):
                p.preview_target(dc, *args)


class ScoreTests(unittest.TestCase):
    def test_smooth_pattern_beats_its_shuffle(self):
        rows, w, window = 24, 32, 5
        image = bytearray()
        target = []
        for r in range(rows):
            row = []
            for c in range(w):
                v = ((r + c) // 4) % 2
                image.append(20 if v else 4)
                row.append(v)
            target.append(row)
        real, mean, sd, z = p.score_with_null(image, rows, w, window, target, "sum", 10, 1)
        self.assertGreater(real, 0.8)
        self.assertGreater(z, 5)

    def test_single_permutation_has_no_sample_variance(self):
        rows, w, window = 24, 32, 5
        image = bytearray((r * w + c) % 251 for r in range(rows) for c in range(w))
        target = [[((r + c) // 4) % 2 for c in range(8)] for r in range(4)]
        real, mean, sd, z = p.score_with_null(image, rows, w, window, target, "sum", 1, 1)
        self.assertTrue(math.isfinite(real))
        self.assertEqual(sd, 0.0)
        self.assertEqual(z, 0.0)

    def test_self_test(self):
        p.self_test()


class CliTests(unittest.TestCase):
    def test_requires_stride_and_valid_sizes(self):
        for argv in (["probe", "file"], ["probe", "file", "--stride", "10", "--rows", "1"],
                     ["probe", "file", "--stride", "10", "--offset", "-1"],
                     ["probe", "file", "--stride", "10", "--perms", "0"]):
            with patch.object(sys, "argv", argv):
                with patch.object(p, "run_file") as run:
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as raised:
                            p.main()
                    self.assertEqual(raised.exception.code, 2)
                    run.assert_not_called()

    def test_mixed_failures_preserve_later_inputs_and_hide_paths(self):
        stderr = io.StringIO()
        argv = ["probe", "first", "private-path", "last", "--stride", "10"]
        with patch.object(sys, "argv", argv), patch.object(
                p, "run_file", side_effect=[None, OSError("private-path"), None]) as run:
            with contextlib.redirect_stderr(stderr):
                code = p.main()
        self.assertEqual(code, 1)
        self.assertEqual(run.call_count, 3)
        self.assertEqual(stderr.getvalue(), "input 2: OSError\n")

    def test_self_test_option(self):
        with patch.object(sys, "argv", ["probe", "--self-test"]):
            with patch.object(p, "self_test") as test:
                self.assertEqual(p.main(), 0)
                test.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
