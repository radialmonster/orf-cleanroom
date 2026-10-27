#!/usr/bin/env python3
"""Synthetic, no-file-write CPU references for token_phase_drift.py."""
import os
import contextlib
import hashlib
import io
import json
import random
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from token_phase_drift import experiment, fit_predict, phase_profile, scan_bands, measure, main
import token_phase_drift as probe


class PhaseDriftTests(unittest.TestCase):
    def test_bad_hash_remains_a_per_sample_failure(self):
        args = ['--sample', '1', 'public', '0' * 64, 'unused',
                '--sample', '2', 'public', 'bad', 'unused']
        out = io.StringIO()
        with mock.patch.object(probe, 'measure', return_value={'bands_complete': True}) as measured, \
             contextlib.redirect_stdout(out):
            self.assertEqual(probe.main(args), 1)
        samples = json.loads(out.getvalue())['samples']
        self.assertEqual([s['ok'] for s in samples], [True, False])
        self.assertEqual(samples[1]['error'], 'ValueError')
        self.assertEqual(measured.call_count, 1)

    def test_identity_rejected_before_any_measurement(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        cases = [([('1', 'public'), ('0', 'public')], False),
                 ([('1', 'public'), ('\u0661', 'public')], False),
                 ([('1', 'public'), ('01', 'public')], False),
                 ([('1', 'public'), ('2', '')], False),
                 ([('1', 'public'), ('2', 'private/path')], False),
                 ([('1', 'public'), ('2', 'private\\path')], False),
                 ([('1', 'public'), ('2', 'bad\nname')], False),
                 ([('1', 'public'), ('2', 'public')], True)]
        if limit:
            cases.append(([('1', 'public'), ('9' * (limit + 1), 'public')], False))
        for samples, simulated in cases:
            args = []
            for sid, name in samples:
                args += ['--sample', sid, name, '0' * 64, 'unused']
            out, err = io.StringIO(), io.StringIO()
            conversion = mock.patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated, case=samples[-1][0][:4]), mock.patch.object(probe, 'measure') as measured, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(args)
                self.assertEqual(caught.exception.code, 2)
                measured.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_valid_public_identity_spelling_is_preserved(self):
        name = 'OM - Élite "camera" (4:3).ORF'
        def echo(sid, public=None, path=None, *args):
            return {'bands_complete': True}
        args = ['--sample', '01', name, '0' * 64, 'unused']
        out = io.StringIO()
        with mock.patch.object(probe, 'measure', side_effect=echo), contextlib.redirect_stdout(out):
            status = probe.main(args)
        self.assertEqual(status, 0)
        sample = json.loads(out.getvalue())['samples'][0]
        self.assertEqual((sample['pixls_id'], sample['pixls_name']), ('01', name))


    def test_profile_independent_direct_heads(self):
        rng = random.Random(421)
        cells = 0
        for stride in range(3, 18):
            for head in range(1, stride):
                band = [rng.randrange(41) for _ in range(stride * 3)]
                shifts = [rng.randrange(stride) for _ in range(3)]
                got = phase_profile(band, stride, head, shifts)
                expected = []
                for p in range(stride):
                    value = 0
                    for r in range(3):
                        row = band[r * stride:(r + 1) * stride]
                        hs = sum(row[(p + shifts[r] + j) % stride] for j in range(head))
                        value += stride * hs - head * sum(row)
                    expected.append(value)
                self.assertEqual(got, expected)
                cells += stride
        self.assertEqual(cells, 1630)

    @staticmethod
    def synthetic(phases):
        bands = []
        for p in phases:
            row = [0] * 16
            row[p] = 10
            bands.append(row * 4)
        return bands

    def test_stationary_control(self):
        result = experiment(self.synthetic([3] * 6), 16, [0, 10, 20, 30, 40, 50], 1, 3, 296)
        obs = result['observed']
        self.assertEqual(obs['constant_validation_phases'], [3] * 3)
        self.assertEqual(obs['linear_validation_phases'], [3] * 3)
        self.assertEqual(obs['linear_minus_constant'], 0)
        self.assertTrue(all(n['linear_validation_sum'] <= obs['linear_validation_sum'] for n in result['rotation_results']))

    def test_drift_and_wrap_control(self):
        phases = [13, 15, 1, 3, 5, 7]
        result = experiment(self.synthetic(phases), 16, [0, 10, 20, 30, 40, 50], 1, 3, 296)
        obs = result['observed']
        self.assertEqual(obs['unwrapped_discovery_phases'], [13, 15, 17])
        self.assertEqual(obs['linear_validation_phases'], phases[3:])
        self.assertGreater(obs['linear_minus_constant'], 0)

    def test_zero_signal_ties_and_null(self):
        result = experiment([[0] * 64] * 6, 16, [0, 10, 20, 30, 40, 50], 1, 3, 296)
        self.assertEqual(result['observed']['discovery_maximum_phases'], [list(range(16))] * 3)
        self.assertEqual(result['rotation_linear_sum_ge'], 3)
        self.assertEqual(result['rotation_linear_minus_constant_ge'], 3)

    def test_no_validation_leakage_and_half_turn(self):
        profiles = [phase_profile(b, 16, 1) for b in self.synthetic([0, 8, 0, 1, 2, 3])]
        first = fit_predict(profiles, [0, 10, 20, 30, 40, 50], 16)
        second = fit_predict(profiles[:3] + [[999] * 16] * 3, [0, 10, 20, 30, 40, 50], 16)
        for key in ('discovery_selected_phases', 'unwrapped_discovery_phases',
                    'constant_validation_phases', 'linear_validation_phases', 'slope_numerator',
                    'slope_denominator', 'intercept_numerator', 'intercept_denominator'):
            self.assertEqual(first[key], second[key])
        self.assertEqual(first['unwrapped_discovery_phases'], [0, -8, -16])
        self.assertEqual(first['half_circle_ties'], [True, True])

    def test_bounded_parser_coordinates_and_escape_accounting(self):
        qs = [0, 1, 18, 42, 2, 3, 0, 1, 2, 3, 4, 5, 0, 0, 1, 2, 0, 1]
        bits = ''.join('0' * q + '1' + '10101' for q in qs)
        packed = bits + '0' * ((-len(bits)) % 8)
        payload = bytes(int(packed[i:i + 8], 2) for i in range(0, len(packed), 8))
        bands, coords, parsed, end = scan_bands(payload, 2, [0, 4, 7], 2)
        self.assertEqual([list(b) for b in bands], [[0, 1, 18, 40], qs[8:12], qs[14:18]])
        for start, coord in zip([0, 4, 7], coords):
            self.assertEqual(coord['start_bit'], sum(q + 6 for q in qs[:start * 2]))
            self.assertEqual(coord['end_bit'], sum(q + 6 for q in qs[:(start + 2) * 2]))
        self.assertEqual((parsed, end), (18, len(bits)))
        short, cshort, nshort, pshort = scan_bands(payload[:2], 2, [0, 4, 7], 2)
        self.assertEqual(nshort, 2)
        self.assertEqual(pshort, 13)
        self.assertEqual(len(short[0]), 2)
        self.assertNotIn('end_bit', cshort[0])

    def test_rng_repeats_and_cpu_pilot(self):
        rng = random.Random(296)
        bands = [[rng.randrange(41) for _ in range(128 * 8)] for _ in range(6)]
        before = time.perf_counter()
        first = experiment(bands, 128, [0, 20, 40, 60, 80, 100], 8, 3, 296)
        elapsed = time.perf_counter() - before
        self.assertEqual(first, experiment(bands, 128, [0, 20, 40, 60, 80, 100], 8, 3, 296))
        print('CPU synthetic pilot seconds: %.6f; no GPU used' % elapsed)

    @staticmethod
    def mock_measure(data, tags=None, digest=None):
        if tags is None:
            tags = {0x100: [5], 0x101: [5], 0x111: [0], 0x117: [len(data)], 0x103: [1]}
        with mock.patch('builtins.open', return_value=io.BytesIO(data)), mock.patch('token_phase_drift.Tiff') as tiff:
            tiff.return_value.all_ifds.return_value = iter([tags])
            return measure('synthetic', digest or hashlib.sha256(data).hexdigest(),
                           2, [0, 3, 6, 9], 2, 1, 1, 296)

    def test_measure_guards_and_partial_coverage(self):
        with self.assertRaises(ValueError):
            self.mock_measure(b'\xff' * 20, digest='0' * 64)
        base = {0x100: [5], 0x101: [5], 0x111: [0], 0x117: [20], 0x103: [1]}
        for changed in ({0x111: [0, 10], 0x117: [10, 10]}, {0x111: [1]},
                        {0x100: [2], 0x101: [5]}, {0x103: [2]}):
            tags = dict(base)
            tags.update(changed)
            with self.assertRaises(ValueError):
                self.mock_measure(b'\xff' * 20, tags=tags)
        full = self.mock_measure(b'\xff' * 20)
        self.assertTrue(full['bands_complete'])
        self.assertEqual(full['complete_band_bits'], 4 * 4 * 6)
        self.assertEqual(full['partial_band_bits'], 0)
        partial = self.mock_measure(b'\xff' * 2)
        self.assertFalse(partial['bands_complete'])
        self.assertNotIn('results', partial)
        self.assertEqual(partial['complete_band_bits'], 0)
        self.assertEqual(partial['partial_band_bits'], 12)
        self.assertEqual(partial['band_accounting'][0]['retained_tokens'], 2)
        self.assertEqual(partial['payload_bits_outside_complete_bands'], 16)

    def test_cli_duplicate_and_incomplete_failures(self):
        one = ['--sample', '1', 'public synthetic', '0' * 64, 'synthetic']
        with mock.patch('sys.stderr', new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as caught:
                main(one + one)
        self.assertEqual(caught.exception.code, 2)
        with mock.patch('token_phase_drift.measure', return_value={'bands_complete': False}), mock.patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(main(one), 1)


if __name__ == '__main__':
    unittest.main()
