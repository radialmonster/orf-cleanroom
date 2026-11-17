#!/usr/bin/env python3
"""Unit and regression tests for sensor_window_scale_probe.py."""
import contextlib
import io
import json
import os
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sensor_window_scale_probe as probe


class TestSensorWindowScaleProbe(unittest.TestCase):
    def test_scale_dimensions(self):
        self.assertEqual(probe.scale_dimensions(1), (32, 24))
        self.assertEqual(probe.scale_dimensions(2), (64, 48))
        self.assertEqual(probe.scale_dimensions(3), (96, 72))
        self.assertEqual(probe.scale_dimensions(4), (128, 96))

    def test_synthetic_cohort_generation(self):
        trials = probe.synthetic_cohort_at_scale([1], 32, 24)
        # 1 seed * 3 scenes * 2 noise levels * 5 mappings = 30 trials
        self.assertEqual(len(trials), 30)
        self.assertEqual(set(t["mapping"] for t in trials),
                         {"identity", "complement", "xor_high", "affine_permutation", "offset_range"})

    def test_envelope_and_confusion_scale1(self):
        res = probe.evaluate_scale_sensitivity([1], include_heldout=False)
        self.assertIn("scale_1x", res)
        s1 = res["scale_1x"]
        self.assertEqual(s1["width"], 32)
        self.assertEqual(s1["height"], 24)
        self.assertEqual(s1["sample_count"], 768)
        self.assertEqual(s1["development_confusion"]["identity_accepted"], 18)
        self.assertEqual(s1["development_confusion"]["identity_rejected"], 0)
        self.assertEqual(s1["development_confusion"]["nonidentity_rejected"], 31)

    def test_xor_high_counts_for_declared_generator(self):
        res = probe.evaluate_scale_sensitivity([1, 2], include_heldout=False)
        xor1 = res["scale_1x"]["development_by_mapping"]["xor_high"]["rejected"]
        xor2 = res["scale_2x"]["development_by_mapping"]["xor_high"]["rejected"]
        self.assertEqual((xor1, xor2), (0, 6))

    def test_extract_v0_windows_mock(self):
        # Create a mock packed-16 container buffer with width 64, height 48
        info = {
            "width": 64,
            "height": 48,
            "payload_offset": 8,
            "byte_order": "little",
        }
        words = list(range(64 * 48))
        data = b"\x00" * 8 + struct.pack("<%dH" % len(words), *words)
        extracted = probe.extract_v0_windows(data, info, 32, 24)
        self.assertEqual(set(extracted.keys()), {"top", "middle", "bottom"})
        self.assertEqual(extracted["top"]["x"], 16)
        self.assertEqual(extracted["top"]["y"], 0)
        self.assertEqual(len(extracted["top"]["shifted_words"]), 32 * 24)
        self.assertEqual(extracted["middle"]["y"], 12)
        self.assertEqual(extracted["bottom"]["y"], 24)

    def test_extract_v0_windows_oversized_raises(self):
        info = {"width": 32, "height": 24, "payload_offset": 0, "byte_order": "little"}
        with self.assertRaises(ValueError):
            probe.extract_v0_windows(b"", info, 64, 48)

    def test_cli_self_test(self):
        out = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--self-test']), contextlib.redirect_stdout(out):
            ret = probe.main()
        self.assertEqual(ret, 0)
        self.assertIn("self-test ok", out.getvalue())

    def test_cli_scales_run(self):
        out = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--scales', '1', '--no-heldout']), \
             contextlib.redirect_stdout(out):
            ret = probe.main()
        self.assertEqual(ret, 0)
        parsed = json.loads(out.getvalue())
        self.assertEqual(parsed["method"], "sensor_window_scale_probe")
        self.assertEqual(parsed["scales_evaluated"], [1])
        self.assertIn("scale_1x", parsed["synthetic_scaling"])

    def test_cli_rejects_scale_that_breaks_affine_permutation(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as raised:
            probe.main(["--scales", "5", "--no-heldout"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("multiples of 5", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())


if __name__ == '__main__':
    unittest.main()
