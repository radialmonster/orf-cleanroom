"""Synthetic checks for token_luma_probe (no sample files)."""

import array
import contextlib
import io
import os
import random
import sys
import unittest
from unittest.mock import mock_open, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_luma_probe as p  # noqa: E402


class BoxTests(unittest.TestCase):
    def test_box_mean_clamped(self):
        v = [0, 1, 2, 3, 4, 5, 6, 7]
        out = p.box_mean_rows(v, 2, 4, 3)
        self.assertEqual(list(out), [0.5, 1.0, 2.0, 2.5, 4.5, 5.0, 6.0, 6.5])

    def test_block_mean(self):
        v = [float(i) for i in range(16)]
        out = p.block_mean(v, 4, 4, 2, 2)
        self.assertEqual(out, [[2.5, 4.5], [10.5, 12.5]])

    def test_corr_rows(self):
        a = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        self.assertAlmostEqual(p.corr_rows(a, a), 1.0)
        b = [[3.0, 2.0, 1.0], [6.0, 5.0, 4.0]]
        self.assertAlmostEqual(p.corr_rows(a, b), -1.0)


class ShiftTests(unittest.TestCase):
    def test_shift_scores_match_rolled_targets(self):
        rows, w, window, nd = 4, 4, 1, 4
        image = bytes([0, 0, 20, 20, 20, 20, 0, 0,
                       0, 0, 20, 20, 20, 20, 0, 0])
        target = [[0, 0, 1, 1], [1, 1, 0, 0], [0, 0, 1, 1], [1, 1, 0, 0]]
        shifts = p.preview_shift_scores(image, rows, w, window, target)
        self.assertEqual([k for k, _ in shifts], [1, 2, 3])
        for k, value in shifts:
            self.assertAlmostEqual(
                value, p.score(image, rows, w, window, nd,
                               target[k:] + target[:k]))

    def test_shift_summary_rank_and_extremes(self):
        summary = p.shift_summary(0.5, [(1, 0.6), (2, 0.4), (3, 0.2)])
        self.assertEqual(summary["rank"], 2)
        self.assertEqual(summary["best_shift"], 1)
        self.assertAlmostEqual(summary["best"], 0.6)
        self.assertAlmostEqual(summary["maximum"], 0.6)
        self.assertAlmostEqual(summary["mean"], 0.4)
        self.assertEqual(summary["shifts"], 3)
        self.assertEqual(p.shift_summary(0.5, [(1, 0.4), (2, 0.3)])["rank"], 1)
        self.assertEqual(p.shift_summary(0.5, [(1, 0.5)])["rank"], 2)
        self.assertEqual(p.shift_summary(0.1, [(1, 0.6), (2, 0.4), (3, 0.2)])["rank"], 4)

    def test_shift_scores_require_two_rows(self):
        with self.assertRaisesRegex(ValueError, "two preview rows"):
            p.preview_shift_scores(b"", 1, 1, 1, [[0]])
        with self.assertRaisesRegex(ValueError, "shifted score"):
            p.shift_summary(0.5, [])


class MappingTests(unittest.TestCase):
    def test_all_translation_entries_and_escapes(self):
        for value in range(256):
            b2 = int(value < 32 and bool(value & 4))
            b4 = int(value < 32 and bool(value & 16))
            self.assertEqual(p.MAPPINGS["b2"][value], b2)
            self.assertEqual(p.MAPPINGS["b4"][value], b4)
            self.assertEqual(p.MAPPINGS["sum"][value], b2 + b4)
        self.assertEqual(p.MAPPINGS["sum"], p.DENSITY)

    def test_orthogonal_single_bit_grids(self):
        # Each four-column row exhausts the independent b2/b4 bit pairs.
        suffix = bytes([0, 4, 16, 20] * 2)
        target_b2 = [[0, 1, 0, 1]] * 2
        target_b4 = [[0, 0, 1, 1]] * 2
        for own, other, target in (("b2", "b4", target_b2),
                                   ("b4", "b2", target_b4)):
            self.assertAlmostEqual(p.score(suffix, 2, 4, 1, 2, target, own), 1)
            self.assertAlmostEqual(p.score(suffix, 2, 4, 1, 2, target, other), 0)
            self.assertAlmostEqual(p.score(suffix, 2, 4, 1, 2, target, "sum"), 2 ** -0.5)
        self.assertEqual(p.score(suffix, 2, 4, 1, 2, target_b2),
                         p.score(suffix, 2, 4, 1, 2, target_b2, "sum"))

    def test_paired_shuffles_preserve_whole_suffix_rows(self):
        suffix = bytes([0, 4, 16, 20, 32, 0, 4, 20] * 2)
        before = bytes(suffix)
        first = p.shuffle_rows(suffix, 2, 8, random.Random(19))
        second = p.shuffle_rows(suffix, 2, 8, random.Random(19))
        self.assertEqual(first, second)
        self.assertEqual(suffix, before)
        for row in range(2):
            part = slice(row * 8, (row + 1) * 8)
            self.assertEqual(sorted(first[part]), sorted(suffix[part]))
        b2 = first.translate(p.MAPPINGS["b2"])
        b4 = first.translate(p.MAPPINGS["b4"])
        combined = first.translate(p.MAPPINGS["sum"])
        self.assertEqual(list(combined), [a + b for a, b in zip(b2, b4)])

    def test_invalid_cli_map_before_file_read(self):
        old_argv = sys.argv
        sys.argv = ["token_luma_probe.py", "--map", "unknown", "missing.orf"]
        try:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                p.main()
            self.assertEqual(exc.exception.code, 2)
        finally:
            sys.argv = old_argv


class CliStatusTests(unittest.TestCase):
    def test_mixed_failures_preserve_later_inputs_and_hide_paths(self):
        for mapping in ("sum", "b2", "b4"):
            for error in (OSError("private-path"), ValueError("private-path")):
                stderr = io.StringIO()
                argv = ["probe", "first", "private-path", "last", "--map", mapping]
                with patch.object(sys, "argv", argv), patch.object(
                        p, "run_file", side_effect=[None, error, None]) as run:
                    with contextlib.redirect_stderr(stderr):
                        code = p.main()
                self.assertEqual(code, 1)
                self.assertEqual(run.call_count, 3)
                self.assertEqual(run.call_args.args[5], mapping)
                self.assertEqual(stderr.getvalue(), "input 2: %s\n" % type(error).__name__)

    def test_complete_batch_and_self_test_succeed(self):
        with patch.object(sys, "argv", ["probe", "first", "second"]):
            with patch.object(p, "run_file") as run:
                self.assertEqual(p.main(), 0)
                self.assertEqual(run.call_count, 2)
        with patch.object(sys, "argv", ["probe", "--self-test"]):
            with patch.object(p, "self_test") as test:
                self.assertEqual(p.main(), 0)
                test.assert_called_once_with()

    def test_shift_null_flag_reaches_run_file(self):
        with patch.object(sys, "argv", ["probe", "first", "--shift-null"]):
            with patch.object(p, "run_file") as run:
                self.assertEqual(p.main(), 0)
                self.assertTrue(run.call_args.args[-1])

    def test_invalid_measurement_sizes_reject_before_reads(self):
        for option, value in (("--rows", "1"), ("--window", "0"), ("--perms", "0")):
            with patch.object(sys, "argv", ["probe", "missing", option, value]):
                with patch.object(p, "run_file") as run:
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as raised:
                            p.main()
                    self.assertEqual(raised.exception.code, 2)
                    run.assert_not_called()

    def test_short_token_rows_reject_before_preview_read(self):
        for mapping in ("sum", "b2", "b4"):
            for count in (0, 7, 13):
                def scan(*args):
                    args[6].extend([0] * count)
                with patch.object(p.T, "locate", return_value=(7, 2, b"")):
                    with patch.object(p.T, "scan", side_effect=scan):
                        with patch.object(p.jpeg_dc, "find_preview") as preview:
                            with self.assertRaisesRegex(ValueError, "requested rows"):
                                p.run_file("unused", 2, 1, 2, 1, mapping)
                            preview.assert_not_called()

    def test_exact_requested_rows_keep_complete_output(self):
        for mapping in ("sum", "b2", "b4"):
            def scan(*args):
                args[6].extend([0] * 14)
            output = io.StringIO()
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(p.T, "locate", return_value=(7, 2, b"")))
                stack.enter_context(patch.object(p.T, "scan", side_effect=scan))
                stack.enter_context(patch("builtins.open", mock_open(read_data=b"synthetic")))
                stack.enter_context(patch.object(p.jpeg_dc, "find_preview", return_value=(None, 0)))
                stack.enter_context(patch.object(p.jpeg_dc, "decode", return_value=(2, 2, [0, 1, 1, 0])))
                stack.enter_context(patch.object(p, "score", side_effect=[0.3, 0.1, 0.2]))
                stack.enter_context(contextlib.redirect_stdout(output))
                p.run_file("unused", 2, 1, 2, 1, mapping)
            self.assertIn("rows 2", output.getvalue())
            self.assertIn("r=+0.30000", output.getvalue())
            self.assertEqual("mapping=" in output.getvalue(), mapping != "sum")

    def test_shift_rank_denominator_includes_observed_alignment(self):
        def scan(*args):
            args[6].extend([0] * 14)
        output = io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(p.T, "locate", return_value=(7, 2, b"")))
            stack.enter_context(patch.object(p.T, "scan", side_effect=scan))
            stack.enter_context(patch("builtins.open", mock_open(read_data=b"synthetic")))
            stack.enter_context(patch.object(p.jpeg_dc, "find_preview", return_value=(None, 0)))
            stack.enter_context(patch.object(p.jpeg_dc, "decode", return_value=(2, 2, [0, 1, 1, 0])))
            stack.enter_context(patch.object(p, "score", side_effect=[0.3, 0.1, 0.2]))
            stack.enter_context(patch.object(p, "preview_shift_scores", return_value=[(1, 0.5)]))
            stack.enter_context(contextlib.redirect_stdout(output))
            p.run_file("unused", 2, 1, 2, 1, shift_null=True)
        self.assertIn("observed rank 2/2", output.getvalue())


def scalar_box_mean_rows(v, rows, w, window):
    # The original one-value-at-a-time loop; the fast version must match it bit for bit.
    out = array.array("f", [0.0]) * (rows * w)
    half = window // 2
    for r in range(rows):
        base = r * w
        prefix = [0] * (w + 1)
        s = 0
        for c in range(w):
            s += v[base + c]
            prefix[c + 1] = s
        for c in range(w):
            a = max(0, c - half)
            b = min(w, c + half + 1)
            out[base + c] = (prefix[b] - prefix[a]) / (b - a)
    return out


def scalar_block_mean(v, rows, w, nd, wb):
    out = []
    for r in range(nd):
        r0 = r * rows // nd
        r1 = max(r0 + 1, (r + 1) * rows // nd)
        acc = [0.0] * w
        for tr in range(r0, min(r1, rows)):
            for c in range(w):
                acc[c] += v[tr * w + c]
        prefix = [0.0] * (w + 1)
        s = 0.0
        for c in range(w):
            s += acc[c]
            prefix[c + 1] = s
        row = []
        for c in range(wb):
            c0 = c * w // wb
            c1 = max(c0 + 1, (c + 1) * w // wb)
            row.append((prefix[c1] - prefix[c0]) / ((r1 - r0) * (c1 - c0)))
        out.append(row)
    return out


class ScalarReferenceTests(unittest.TestCase):
    def test_fast_paths_match_scalar_loops_exactly(self):
        rng = random.Random(7)
        for _ in range(300):
            rows, w = rng.randint(1, 8), rng.randint(1, 90)
            window = rng.choice([1, 3, 9, 63, 121, 201])
            v = bytes(rng.randrange(3) for _ in range(rows * w))
            boxed = p.box_mean_rows(v, rows, w, window)
            self.assertEqual(boxed.tobytes(), scalar_box_mean_rows(v, rows, w, window).tobytes())
            nd, wb = rng.randint(1, rows + 3), rng.randint(1, w + 3)
            self.assertEqual(repr(p.block_mean(boxed, rows, w, nd, wb)),
                             repr(scalar_block_mean(boxed, rows, w, nd, wb)))

    def test_shift_scores_equal_full_rescoring(self):
        rng = random.Random(11)
        rows, w, window, nd, wb = 12, 70, 9, 6, 10
        sa = bytes(rng.choice([0, 4, 16, 20, 33]) for _ in range(rows * w))
        target = [[rng.random() for _ in range(wb)] for _ in range(nd)]
        for k, value in p.preview_shift_scores(sa, rows, w, window, target):
            self.assertEqual(repr(value), repr(p.score(sa, rows, w, window, nd,
                                                       target[k:] + target[:k])))


class SelfTest(unittest.TestCase):
    def test_builtin(self):
        p.self_test()


if __name__ == "__main__":
    unittest.main()
