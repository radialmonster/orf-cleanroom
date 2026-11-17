#!/usr/bin/env python3
"""Unit and regression tests for paired_covariance_probe.py."""
import contextlib
import io
import json
import math
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paired_covariance_probe as probe


class TestPairedCovarianceProbe(unittest.TestCase):
    def test_theoretical_white_noise(self):
        th = probe.theoretical_predictor_signature('white_noise', max_lag=8)
        self.assertEqual(len(th), 8)
        for l in range(1, 9):
            self.assertEqual(th[l], 0.0)

    def test_theoretical_lag_d(self):
        for d in (1, 2, 3, 4):
            th = probe.theoretical_predictor_signature('lag%d' % d, max_lag=6)
            self.assertAlmostEqual(th[d], -0.5, places=12)
            for l in range(1, 7):
                if l != d:
                    self.assertAlmostEqual(th[l], 0.0, places=12)

    def test_theoretical_2d_planar(self):
        th = probe.theoretical_predictor_signature('2d_planar', max_lag=4, stride=100)
        self.assertAlmostEqual(th[2], -0.5, places=12)
        self.assertAlmostEqual(th[100], -0.5, places=12)
        self.assertAlmostEqual(th[102], 0.25, places=12)

    def test_theoretical_unknown_raises(self):
        with self.assertRaises(ValueError):
            probe.theoretical_predictor_signature('unknown_stencil')

    def test_autocovariance_short_or_constant(self):
        self.assertIsNone(probe.autocovariance([])['mean'])
        self.assertIsNone(probe.autocovariance([5.0])['mean'])
        const = probe.autocovariance([4.0] * 20, max_lag=4)
        self.assertEqual(const['mean'], 4.0)
        self.assertEqual(const['variance'], 0.0)
        self.assertEqual(const['lags'], {})

    def test_autocovariance_alternating(self):
        series = [1.0, -1.0] * 50
        res = probe.autocovariance(series, max_lag=4)
        self.assertAlmostEqual(res['mean'], 0.0, places=10)
        self.assertAlmostEqual(res['variance'], 1.0, places=10)
        self.assertAlmostEqual(res['lags'][1]['rho'], -1.0, places=10)
        self.assertAlmostEqual(res['lags'][2]['rho'], 1.0, places=10)

    def test_synthetic_fpn_cancellation(self):
        res_a, res_b = probe.generate_synthetic_pair(
            n_samples=50000, seed=999, predictor='none',
            noise_sigma=5.0, fpn_sigma=100.0, scene_gradient=10.0
        )
        diff = [a - b for a, b in zip(res_a, res_b)]
        mean_diff = sum(diff) / len(diff)
        var_diff = sum((d - mean_diff) ** 2 for d in diff) / len(diff)
        self.assertAlmostEqual(mean_diff, 0.0, delta=0.2)
        self.assertAlmostEqual(var_diff, 50.0, delta=2.5)

    def test_synthetic_lag1_detection(self):
        res_a, res_b = probe.generate_synthetic_pair(
            n_samples=60000, seed=42, predictor='lag1', noise_sigma=10.0
        )
        report = probe.analyze_pair_difference(res_a, res_b, max_lag=6)
        self.assertEqual(report['best_matching_predictor'], 'lag1')
        self.assertAlmostEqual(report['autocorrelation_lags'][1]['rho'], -0.5, delta=0.03)
        self.assertLess(report['best_matching_rmse'], 0.02)

    def test_metadata_match_and_mismatch(self):
        base_exif = {
            'model': 'OM-1',
            'iso': 200,
            'exposure': (1, 250),
            'fnumber': (40, 10),
            'focal': (50, 1)
        }
        geom = (5220, 3912)
        check_ok = probe.check_metadata_match(base_exif, dict(base_exif), geom, geom)
        self.assertTrue(check_ok['eligible'])
        self.assertEqual(len(check_ok['mismatches']), 0)

        check_model = probe.check_metadata_match(base_exif, dict(base_exif, model='OM-5'), geom, geom)
        self.assertFalse(check_model['eligible'])
        self.assertIn('model', check_model['mismatches'])

        check_iso = probe.check_metadata_match(base_exif, dict(base_exif, iso=400), geom, geom)
        self.assertFalse(check_iso['eligible'])
        self.assertIn('iso', check_iso['mismatches'])

        check_exp = probe.check_metadata_match(base_exif, dict(base_exif, exposure=(1, 500)), geom, geom)
        self.assertFalse(check_exp['eligible'])
        self.assertIn('exposure', check_exp['mismatches'])

        check_geom = probe.check_metadata_match(base_exif, base_exif, geom, (5240, 3912))
        self.assertFalse(check_geom['eligible'])
        self.assertIn('geometry', check_geom['mismatches'])

    def test_signed_zig_zag(self):
        self.assertEqual(probe.signed_zig_zag(0), 0)
        self.assertEqual(probe.signed_zig_zag(1), -1)
        self.assertEqual(probe.signed_zig_zag(2), 1)
        self.assertEqual(probe.signed_zig_zag(3), -2)
        self.assertEqual(probe.signed_zig_zag(4), 2)

    def test_cli_self_test(self):
        out = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--self-test']), contextlib.redirect_stdout(out):
            ret = probe.main()
        self.assertEqual(ret, 0)
        self.assertIn("self-test ok", out.getvalue())

    def test_cli_synthetic(self):
        out = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--synthetic', '--tokens', '5000']), contextlib.redirect_stdout(out):
            ret = probe.main()
        self.assertEqual(ret, 0)
        parsed = json.loads(out.getvalue())
        self.assertEqual(parsed['method'], 'synthetic_paired_difference_covariance')
        self.assertEqual(parsed['analysis']['sample_count'], 5000)
        self.assertEqual(parsed['analysis']['best_matching_predictor'], 'lag2')


if __name__ == '__main__':
    unittest.main()
