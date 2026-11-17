#!/usr/bin/env python3
"""Unit and regression tests for two_stage_residual_probe.py."""
import contextlib
import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import two_stage_residual_probe as probe


class TestTwoStageResidualProbe(unittest.TestCase):
    def test_derived_synthetic_fixture_exact_values(self):
        # Synthetic algebraic example derived from US7715639B2 formulas;
        # these values are not a printed example in the publication.
        p_seq = [-3, -1, 0, 1, 3]
        enc, states = probe.two_stage_encode(p_seq, c_init=0)
        self.assertEqual([e for e, l in enc], [-2, 0, 1, 1, 2])
        self.assertEqual([l for e, l in enc], [1, 1, 0, 1, 1])
        self.assertEqual(states, [-2, -2, -1, -1, 0])

        dec, dec_states = probe.two_stage_decode(enc, c_init=0)
        self.assertEqual(dec, p_seq)
        self.assertEqual(dec_states, states)

    def test_empty_sequence(self):
        enc, states = probe.two_stage_encode([])
        self.assertEqual(enc, [])
        self.assertEqual(states, [])
        dec, dec_states = probe.two_stage_decode([])
        self.assertEqual(dec, [])
        self.assertEqual(dec_states, [])

    def test_single_element_cases(self):
        for val in (-10, -5, -1, 0, 1, 2, 9, 100):
            enc, states = probe.two_stage_encode([val], c_init=0)
            dec, _ = probe.two_stage_decode(enc, c_init=0)
            self.assertEqual(dec, [val])

    def test_low_bit_separation(self):
        # Errors 0 and 1 with c_init=0 must have identical E=0, but distinct L
        enc0, _ = probe.two_stage_encode([0], c_init=0)
        enc1, _ = probe.two_stage_encode([1], c_init=0)
        self.assertEqual(enc0[0][0], enc1[0][0])
        self.assertEqual(enc0[0][0], 0)
        self.assertEqual(enc0[0][1], 0)
        self.assertEqual(enc1[0][1], 1)

    def test_history_changes_inverse_for_same_current_pair(self):
        first, _ = probe.two_stage_encode([0, 0])
        second, _ = probe.two_stage_encode([4, 2])
        self.assertEqual(first[-1], second[-1])
        self.assertEqual(first[-1], (0, 0))
        self.assertEqual(probe.two_stage_decode(first)[0], [0, 0])
        self.assertEqual(probe.two_stage_decode(second)[0], [4, 2])

    def test_zero_residual_direct_map_expected_exact_success(self):
        report = probe.evaluate_cascade([1000] * 32, [0] * 32)
        self.assertTrue(report['stateless_direct_map_failure']['stateless_reconstructs_exact'])
        self.assertEqual(report['stateless_direct_map_failure']['max_pixel_drift'], 0)
        self.assertIn('is exact on this finite synthetic sequence', report['diagnostic_conclusion'])

    def test_roundtrip_exhaustive_small_integers(self):
        for p0 in range(-3, 4):
            for p1 in range(-3, 4):
                for p2 in range(-3, 4):
                    seq = [p0, p1, p2]
                    enc, st = probe.two_stage_encode(seq, c_init=0)
                    dec, dec_st = probe.two_stage_decode(enc, c_init=0)
                    self.assertEqual(dec, seq)
                    self.assertEqual(dec_st, st)

    def test_scene_simulation_and_stateless_failure(self):
        for scene in ('flat', 'gradient', 'textured'):
            pixels, residuals = probe.simulate_pixel_sequence(n=500, scene=scene, seed=123)
            report = probe.evaluate_cascade(pixels, residuals)
            self.assertTrue(report['exact_residual_roundtrip'])
            self.assertTrue(report['stateful_pixel_roundtrip'])
            self.assertFalse(report['stateless_direct_map_failure']['stateless_reconstructs_exact'])
            self.assertGreater(report['stateless_direct_map_failure']['max_pixel_drift'], 0)

    def test_unknown_scene_raises(self):
        with self.assertRaises(ValueError):
            probe.simulate_pixel_sequence(n=10, scene='invalid_scene')

    def test_cli_self_test(self):
        out = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--self-test']), contextlib.redirect_stdout(out):
            ret = probe.main()
        self.assertEqual(ret, 0)
        self.assertIn("self-test ok", out.getvalue())

    def test_cli_synthetic_run(self):
        out = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--synthetic', '--tokens', '100', '--scene', 'flat']), \
             contextlib.redirect_stdout(out):
            ret = probe.main()
        self.assertEqual(ret, 0)
        parsed = json.loads(out.getvalue())
        self.assertEqual(parsed['method'], 'us7715639b2_two_stage_residual_probe')
        self.assertEqual(parsed['parameters']['tokens'], 100)
        self.assertTrue(parsed['results']['exact_residual_roundtrip'])


if __name__ == '__main__':
    unittest.main()
