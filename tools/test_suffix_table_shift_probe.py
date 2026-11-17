"""Synthetic-only checks of learned-table shift scoring and cohort rules."""
import math
import io
import json
import os
import random
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_table_shift_probe as probe


class Synthetic(unittest.TestCase):
    def test_shift_sign_and_legacy_score(self):
        rng = random.Random(155)
        rows, cols = 8, 10
        p = [rng.random() for _ in range(rows * cols)]
        raw = [p[((r + 3) % rows) * cols + c] for r in range(rows) for c in range(cols)]
        y = probe.legacy.row_center(raw, rows, cols)
        result = probe.shift_scores(y, p, rows, cols)
        self.assertEqual(result['best_shifts_within_tolerance'], [3])
        self.assertFalse(result['operationally_specific'])
        self.assertAlmostEqual(result['zero_r'], probe.legacy.stats(y, p)[0], places=12)
        aligned = probe.legacy.row_center(p, rows, cols)
        self.assertTrue(probe.shift_scores(aligned, p, rows, cols)['operationally_specific'])

    def test_ties_and_undefined(self):
        p = [1.0, -1.0, 0.0, 0.0] * 4
        got = probe.shift_scores(p, p, 4, 4)
        self.assertEqual(got['zero_min_rank'], 1)
        self.assertEqual(got['zero_ties'], [0, 1, 2, 3])
        self.assertFalse(got['operationally_specific'])
        self.assertEqual(probe.shift_scores([0.0] * 16, p, 4, 4)['status'], 'undefined_variance')
        self.assertEqual(probe.shift_scores(p, [math.nan] * 16, 4, 4)['status'], 'undefined_nonfinite')
        with self.assertRaises(ValueError):
            probe.shift_scores(p[:-1], p, 4, 4)

    def test_training_legacy_and_fixed_rows(self):
        rng = random.Random(7)
        rows, cols = 6, 8
        x = [[rng.random() for _ in range(32)] for _ in range(rows * cols)]
        y = [rng.random() for _ in range(rows * cols)]
        fit = probe.fitted_table(x, y, rows, cols)
        mask = [(r % 2 == 0) for r in range(rows) for _ in range(cols)]
        expected = probe.legacy.solve([a[:] for a, keep in zip(x, mask) if keep],
                                     [a for a, keep in zip(y, mask) if keep], 1.0, 10.0, 32, intercept=False)
        self.assertEqual(fit, expected)

    def test_identity_mismatch_and_short_input(self):
        with mock.patch.object(probe, 'digest', return_value='wrong'):
            with self.assertRaises(ValueError):
                probe.features_from_file('1995', 'not-opened')
        with mock.patch.object(probe, 'digest', return_value=probe.SAMPLES['1995'][1]), \
             mock.patch.object(probe.legacy, 'read_tokens', return_value=(5240, 3912, [], [], 599)):
            with self.assertRaises(ValueError):
                probe.features_from_file('1995', 'not-opened')

    def test_cli_redacts_paths_and_reports_fixed_fit_hash(self):
        def fixture(sample_id, path):
            if sample_id == '1998':
                raise OSError('secret/path')
            info = {'id': sample_id, 'used_preview_rows': 2, 'preview_width_blocks': 2}
            return [[1.0] + [0.0] * 31] * 4, [1.0, -1.0, 2.0, -2.0], info
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--phase', 'discovery', '--train', 'secret',
                                            '--sample', '1997', 'secret', '--sample', '1998', 'secret']), \
             mock.patch.object(probe, 'features_from_file', side_effect=fixture), \
             mock.patch.object(probe, 'fitted_table', return_value=[1.0] * 32), \
             mock.patch('sys.stdout', output):
            self.assertEqual(probe.main(), 1)
        self.assertNotIn('secret', output.getvalue())
        report = json.loads(output.getvalue())
        self.assertEqual(len(report['train']['table_sha256_binary64_be']), 64)
        self.assertEqual(report['results'][1]['measurement']['status'], 'unknown')


if __name__ == '__main__':
    unittest.main()
