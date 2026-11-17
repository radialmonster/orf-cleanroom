#!/usr/bin/env python3
"""Unit and regression tests for paired_covariance_probe.py."""
import contextlib
import io
import json
import math
import os
import struct
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
        self.assertEqual(const['std_dev'], 0.0)
        self.assertEqual(const['status'], 'zero_variance')
        self.assertIsNone(const['lags'][1]['rho'])
        self.assertEqual(const['lags'][1]['valid_pairs'], 19)

    def test_analysis_undefined_and_unequal_counts(self):
        for left, right, status in (([], [], 'insufficient_valid_samples'),
                                    ([0], [1], 'insufficient_valid_samples'),
                                    ([0, 0], [0, 0], 'zero_variance'),
                                    ([None, None], [0, 0], 'insufficient_valid_samples')):
            result = probe.analyze_pair_difference(left, right)
            self.assertEqual(result['status'], status)
            self.assertIsNone(result['best_matching_predictor'])
            self.assertIsNone(result['best_matching_rmse'])
            self.assertIn('difference_std_dev', result)
            json.dumps(result, allow_nan=False)
        unequal = probe.analyze_pair_difference([0, 1, 2, 3], [0, 0])
        self.assertEqual(unequal['stream_counts'], {'a':4, 'b':2})
        self.assertEqual(unequal['unpaired_tail_counts'], {'a':2, 'b':0})
        self.assertFalse(unequal['complete_pair_lengths'])
        self.assertIsNone(unequal['best_matching_predictor'])

    def test_escape_masks_preserve_distances_and_pair_counts(self):
        result = probe.analyze_pair_difference([0, None, 2, 4], [0, 0, None, 0], max_lag=3)
        self.assertEqual(result['valid_difference_samples'], 2)
        self.assertEqual(result['masked_difference_samples'], 2)
        self.assertEqual(result['autocorrelation_lags'][1]['valid_pairs'], 0)
        self.assertIsNone(result['autocorrelation_lags'][1]['rho'])
        self.assertEqual(result['autocorrelation_lags'][3]['valid_pairs'], 1)
        self.assertEqual(result['autocorrelation_lags'][3]['rho'], -1)
        with mock.patch.object(probe.orf_tokens, 'locate_data', return_value=(10, 20, b'payload')), \
             mock.patch.object(probe.orf_tokens, 'parse', return_value=([0,17,0],[0,1,2],[],30)):
            stream = probe.extract_candidate_stream(b'container', max_tokens=5)
        self.assertEqual(stream['residuals'], [0, None, 1])
        self.assertEqual(stream['escape_tokens'], 1)
        self.assertEqual(stream['tokens_parsed'], 3)
        self.assertEqual(stream['token_shortfall'], 2)

    def test_colliding_stencil_offsets_accumulate(self):
        average = probe.theoretical_predictor_signature('2d_average', max_lag=4, stride=2)
        planar = probe.theoretical_predictor_signature('2d_planar', max_lag=4, stride=2)
        self.assertAlmostEqual(average[2], -0.5)
        self.assertAlmostEqual(planar[2], -2/3)
        self.assertAlmostEqual(planar[4], 1/6)
        with self.assertRaises(ValueError):
            probe.theoretical_predictor_signature('lag0')

    def test_literal_token_extraction_from_generated_tiff(self):
        bits = '100000' + '0'*17 + '100001' + '100010'
        payload = int(bits+'0'*(-len(bits) % 8), 2).to_bytes((len(bits)+7)//8, 'big')
        tags = ((256,10), (257,20), (259,1), (273,74), (279,len(payload)))
        fixture = (b'II' + struct.pack('<HIH',42,8,len(tags))
                   + b''.join(struct.pack('<HHII',tag,4,1,value) for tag,value in tags)
                   + struct.pack('<I',0) + payload)
        # Actual TIFF locator and literal scanner; no patched implementation.
        stream = probe.extract_candidate_stream(fixture, max_tokens=5)
        self.assertEqual((stream['width'],stream['height']), (10,20))
        self.assertEqual(stream['payload_bytes'], 5)
        self.assertEqual(stream['bits_used'], 35)
        self.assertEqual(stream['residuals'], [0,None,1])
        self.assertEqual(stream['escape_tokens'], 1)
        self.assertEqual(stream['tokens_parsed'], 3)
        self.assertEqual(stream['token_shortfall'], 2)

    def test_spatially_colored_noise_changes_reference(self):
        left, right = probe.generate_synthetic_pair(
            n_samples=100000, seed=764, predictor='lag1', noise_correlation=0.6)
        result = probe.analyze_pair_difference(left, right, max_lag=4)
        rho = result['autocorrelation_lags'][1]['rho']
        self.assertAlmostEqual(rho, -0.2, delta=0.02)
        self.assertGreater(abs(rho+0.5), 0.2)

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
        for missing_geom in (None, (), (0,20), (10,0), (None,None)):
            unknown = probe.check_metadata_match(base_exif, base_exif, missing_geom, missing_geom)
            self.assertFalse(unknown['eligible'])
            self.assertIn('geometry', unknown['mismatches'])
        for field in ('model', 'iso', 'exposure', 'fnumber', 'focal'):
            missing = dict(base_exif)
            missing.pop(field)
            check_missing = probe.check_metadata_match(missing, missing, geom, geom)
            self.assertFalse(check_missing['eligible'])
            self.assertIn(field, check_missing['mismatches'])

    def test_cli_raw_shortfall_reports_both_streams_without_winner(self):
        exif = {'model':'test', 'iso':200, 'exposure':(1,1), 'fnumber':(1,1), 'focal':(1,1)}
        def stream(count):
            return {'width':10, 'height':20, 'payload_bytes':100,
                    'tokens_parsed':count, 'tokens_requested':5, 'token_shortfall':5-count,
                    'escape_tokens':0, 'bits_used':6*count, 'residuals':list(range(count))}
        out = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe','A','B','--tokens','5']), \
             mock.patch('builtins.open', mock.mock_open(read_data=b'synthetic')), \
             mock.patch.object(probe, 'read_exif', return_value=exif), \
             mock.patch.object(probe, 'extract_candidate_stream', side_effect=[stream(3),stream(4)]), \
             contextlib.redirect_stdout(out):
            status = probe.main()
        result = json.loads(out.getvalue())
        self.assertEqual(status, 1)
        self.assertFalse(result['complete'])
        self.assertEqual(result['streams']['a']['token_shortfall'], 2)
        self.assertEqual(result['streams']['b']['token_shortfall'], 1)
        self.assertEqual(result['analysis']['stream_counts'], {'a':3,'b':4})
        self.assertIsNone(result['analysis']['best_matching_predictor'])
        self.assertEqual(result['method'], 'exploratory_candidate_index_difference_covariance')

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
