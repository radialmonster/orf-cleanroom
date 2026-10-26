#!/usr/bin/env python3
"""Synthetic failure-accounting tests for the Figure 8 probe (lead #196).

No sample files, network or filesystem writes.
"""
import contextlib
import collections
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import huffman_figure8_probe as probe


class CommandTests(unittest.TestCase):
    def test_actual_payload_height_reaches_both_score_calls(self):
        with mock.patch.object(probe.T, "locate", return_value=(2, 7792, b"\x00" * 20)), \
                mock.patch.object(probe, "parse_rows", return_value=(
                    [1] * 4, [0], collections.Counter({1: 4}), 0, 4)), \
                mock.patch.object(probe, "score", return_value=0.0) as score, \
                contextlib.redirect_stdout(io.StringIO()):
            probe.run("synthetic.orf", 2, 0, 5, "extend", False)
        self.assertEqual(score.call_count, 2)
        self.assertEqual([call.args[-1] for call in score.call_args_list], [7792, 7792])

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = probe.main(args)
        return status, out.getvalue(), err.getvalue()

    def test_missing_input_fails(self):
        with mock.patch("builtins.open", side_effect=FileNotFoundError):
            status, out, err = self.invoke(["missing.orf"])
        self.assertEqual(status, 1)
        self.assertIn("requested=1 complete=0 failed=1", out)
        self.assertIn("status=incomplete", out)
        self.assertIn("report incomplete", err)

    def test_non_orf_input_fails(self):
        with mock.patch("builtins.open", mock.mock_open(read_data=b"not an ORF")):
            status, out, _ = self.invoke(["invalid.orf"])
        self.assertEqual(status, 1)
        self.assertIn("requested=1 complete=0 failed=1", out)

    def test_mixed_inputs_keep_success_and_count_every_failure(self):
        def run(path, *_args):
            if path == "bad.orf":
                raise ValueError("bad input")
            print("synthetic successful report")
        with mock.patch.object(probe, "run", side_effect=run):
            status, out, _ = self.invoke(["good.orf", "bad.orf", "last.orf"])
        self.assertEqual(status, 1)
        self.assertEqual(out.count("synthetic successful report"), 2)
        self.assertIn("requested=3 complete=2 failed=1", out)

    def test_failure_after_output_marks_report_incomplete(self):
        with mock.patch.object(probe.T, "locate", return_value=(2, 2, b"\x00" * 20)), \
                mock.patch.object(probe, "parse_rows", return_value=(
                    [1] * 4, [0], collections.Counter({1: 4}), 0, 4)), \
                mock.patch.object(probe, "score", side_effect=ValueError("no preview")):
            status, out, _ = self.invoke(["partial.orf", "--rows", "2", "--start", "0"])
        self.assertEqual(status, 1)
        self.assertIn("transcribed: values=4", out)
        self.assertIn("partial.orf status=incomplete", out)

    def test_success_returns_zero(self):
        with mock.patch.object(probe, "run"):
            status, out, _ = self.invoke(["good.orf"])
        self.assertEqual(status, 0)
        self.assertIn("requested=1 complete=1 failed=0", out)

    def test_bad_numeric_options_rejected_before_input(self):
        for opts in (["--start", "-1"], ["--rows", "0"], ["--rows", "-2"],
                     ["--missing-category", "-1"], ["--missing-category", "12"]):
            with self.subTest(opts=opts), mock.patch.object(probe, "run") as run:
                with self.assertRaises(SystemExit) as exc:
                    self.invoke(["input.orf"] + opts)
                self.assertEqual(exc.exception.code, 2)
                run.assert_not_called()

    def test_start_beyond_payload_rejected(self):
        with mock.patch.object(probe.T, "locate", return_value=(2, 2, b"\x00")):
            with self.assertRaises(ValueError):
                probe.run("synthetic.orf", 2, 8, 5, "extend", False)


if __name__ == "__main__":
    unittest.main()
