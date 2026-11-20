#!/usr/bin/env python3
"""Unit and regression tests for preview_pair_payload_contrast.py."""
import contextlib
import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_pair_payload_contrast as probe


class TestPreviewPairPayloadContrast(unittest.TestCase):
    def test_calculate_autocorr(self):
        self.assertIsNone(probe.calculate_autocorr([], 1))
        self.assertIsNone(probe.calculate_autocorr([1.0], 1))
        self.assertEqual(probe.calculate_autocorr([5.0] * 10, 1), 0.0)
        alt = [1.0, -1.0] * 20
        self.assertAlmostEqual(probe.calculate_autocorr(alt, 1), -1.0, places=10)
        self.assertAlmostEqual(probe.calculate_autocorr(alt, 2), 1.0, places=10)

    def test_metadata_agreement_and_mismatch(self):
        exif_base = {
            "model": "OM-1",
            "iso": 200,
            "exposure": (1, 100),
            "fnumber": (28, 10),
            "focal": (25, 1),
        }
        feat = {
            "width": 5220, "height": 3912, "reported_samples": 5220 * 3912,
            "payload_bytes": 10000000, "bpp": 3.91, "tokens_parsed": 10000,
            "bits_used": 10000, "q0_fraction": 0.5, "escape_fraction": 0.01,
            "suffix_b4_fraction": 0.5, "suffix_b2_fraction": 0.5,
            "token_autocorr_lag1": 0.2, "token_autocorr_lag2": 0.1,
        }

        # Matched metadata
        res = probe.evaluate_pair_contrast(feat, feat, exif_base, exif_base)
        self.assertTrue(res["metadata_agreement"]["all_matched"])
        self.assertTrue(res["metadata_agreement"]["shared_exposure_settings"])
        self.assertEqual(res["feature_differences"]["delta_bpp"], 0.0)

        # Mismatched model
        res_m = probe.evaluate_pair_contrast(feat, feat, exif_base, dict(exif_base, model="OM-5"))
        self.assertFalse(res_m["metadata_agreement"]["all_matched"])
        self.assertIn("model", res_m["metadata_agreement"]["mismatches"])
        self.assertTrue(res_m["metadata_agreement"]["shared_exposure_settings"])

        # Mismatched ISO
        res_iso = probe.evaluate_pair_contrast(feat, feat, exif_base, dict(exif_base, iso=400))
        self.assertFalse(res_iso["metadata_agreement"]["all_matched"])
        self.assertFalse(res_iso["metadata_agreement"]["shared_exposure_settings"])
        self.assertIn("iso", res_iso["metadata_agreement"]["mismatches"])

    def test_composite_distance_calculation(self):
        fa = {
            "width": 100, "height": 100, "reported_samples": 10000,
            "payload_bytes": 1000, "bpp": 0.8, "tokens_parsed": 1000,
            "bits_used": 8000, "q0_fraction": 0.5, "escape_fraction": 0.0,
            "suffix_b4_fraction": 0.5, "suffix_b2_fraction": 0.5,
            "token_autocorr_lag1": 0.0, "token_autocorr_lag2": 0.0,
        }
        fb = dict(fa, q0_fraction=0.8, escape_fraction=0.4)
        exif = {"model": "A"}
        res = probe.evaluate_pair_contrast(fa, fb, exif, exif)
        # d_q0 = 0.3, d_esc = 0.4, others = 0 => composite distance = sqrt(0.09 + 0.16) = 0.5
        self.assertAlmostEqual(res["feature_differences"]["composite_fractional_distance"], 0.5, places=10)

    def test_cli_self_test(self):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["probe", "--self-test"]), contextlib.redirect_stdout(out):
            ret = probe.main()
        self.assertEqual(ret, 0)
        self.assertIn("self-test ok", out.getvalue())


if __name__ == "__main__":
    unittest.main()
