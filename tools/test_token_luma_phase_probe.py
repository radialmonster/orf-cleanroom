"""Synthetic checks for token_luma_phase_probe (no sample files)."""

import contextlib
import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_luma_phase_probe as p  # noqa: E402


class ImageTests(unittest.TestCase):
    def test_phase_can_overlap_the_next_candidate_row(self):
        rows, w, stride, phase = 2, 4, 6, 5
        sa = bytearray(range(20))
        out = p.image_at(sa, rows, w, stride, phase, 0)
        self.assertEqual(out, bytearray([5, 6, 7, 8, 11, 12, 13, 14]))

    def test_start_row_and_short_stream(self):
        rows, w, stride = 2, 3, 5
        sa = bytearray(range(30))
        self.assertEqual(p.image_at(sa, rows, w, stride, 4, 1),
                         bytearray([9, 10, 11, 14, 15, 16]))
        with self.assertRaisesRegex(ValueError, "short"):
            p.image_at(bytearray(8), rows, w, stride, 4, 0)

    def test_rejects_bad_geometry(self):
        sa = bytearray(20)
        for args in ((0, 3, 4, 0, 0), (2, 5, 4, 0, 0),
                     (2, 3, 4, 6, 0), (2, 3, 4, 0, -1)):
            with self.assertRaises(ValueError):
                p.image_at(sa, *args)


class PhaseTests(unittest.TestCase):
    def test_circular_refinement_wraps(self):
        self.assertEqual(p.circular_phases(1, 2, 10), [0, 1, 2, 3, 9])
        self.assertEqual(p.circular_phases(0, 0, 10), [0])

    def test_family_includes_last_phase(self):
        coarse, _, _ = p.phase_family(31, 8, 2)
        self.assertEqual(coarse, list(range(0, 31, 8)) + [30])

    def test_search_recovers_inserted_phase(self):
        rows, w, stride, phase = 24, 20, 31, 7
        sa = bytearray((r * stride + c) % 256
                       for r in range(rows + 2) for c in range(stride))
        for r in range(rows):
            for c in range(w):
                v = (r + c) // 4
                sa[r * stride + phase + c] = ((4 if v % 2 else 0)
                                              | (16 if v % 3 else 0))
        image = p.image_at(sa, rows, w, stride, phase, 0)
        target = p.L.block_mean(
            p.L.box_mean_rows(image.translate(p.L.DENSITY), rows, w, 9),
            rows, w, 4, 8)
        best, r, scores, coarse, fine = p.search(
            sa, rows, w, stride, target, "sum", 9, 1, 2, 0)
        self.assertEqual(best, phase)
        self.assertGreater(r, 0.9)
        self.assertIn(phase, scores)
        self.assertGreater(len(coarse), 1)
        self.assertGreater(len(fine), 1)

    def test_shuffle_is_deterministic_and_preserves_multiset(self):
        sa = bytearray(range(64))
        a = p.shuffled(sa, 3)
        b = p.shuffled(sa, 3)
        self.assertEqual(a, b)
        self.assertEqual(sorted(a), sorted(sa))
        self.assertNotEqual(a, sa)


class CliTests(unittest.TestCase):
    def test_requires_stride_and_valid_sizes(self):
        for argv in (["probe", "file"],
                     ["probe", "file", "--stride", "10", "--rows", "1"],
                     ["probe", "file", "--stride", "10", "--step", "0"],
                     ["probe", "file", "--stride", "10", "--perms", "-1"]):
            with patch.object(sys, "argv", argv):
                with patch.object(p, "run_file") as run:
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as raised:
                            p.main()
                    self.assertEqual(raised.exception.code, 2)
                    run.assert_not_called()

    def test_window_must_be_positive_and_odd_before_file_access(self):
        for window in (0, 2, 64):
            argv = ["probe", "missing", "--stride", "10", "--window", str(window)]
            with self.subTest(window=window), patch.object(sys, "argv", argv), \
                    patch.object(p, "run_file") as run, \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    p.main()
                self.assertEqual(raised.exception.code, 2)
                run.assert_not_called()
        for window in (1, 63):
            argv = ["probe", "synthetic", "--stride", "10", "--window", str(window)]
            with self.subTest(window=window), patch.object(sys, "argv", argv), \
                    patch.object(p, "run_file") as run:
                self.assertEqual(p.main(), 0)
                self.assertEqual(run.call_args.args[6], window)

    def test_run_file_rejects_even_window_before_file_access(self):
        with patch.object(p.T, "locate") as locate:
            with self.assertRaisesRegex(ValueError, "window must be odd"):
                p.run_file("synthetic", 10, 2, 0, 1, 0, 2, 0, 1, "sum")
            locate.assert_not_called()

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
