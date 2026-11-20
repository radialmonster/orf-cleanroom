"""Synthetic algebra, undefined variance and complete generated CLI."""
import hashlib
import io
import json
import math
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_profile_probe as p
from test_suffix_table_cross_body_probe import real_fixture


class Tests(unittest.TestCase):
    def test_decomposition_and_degenerate(self):
        a = [1., 2., 3., 4., 5., 6.]
        b = [4., 1., 5., 3., 8., 2.]
        d = p.decomposition(a, b, 3, 2)
        shifts = p.shift_scores(a, b, 3, 2)
        self.assertAlmostEqual(d['stationary_contribution'], math.fsum(shifts['scores'])/3, places=12)
        self.assertAlmostEqual(d['stationary_contribution']+d['residual_contribution'], shifts['zero_r'], places=12)
        self.assertAlmostEqual(d['profile_target_energy']+d['residual_target_energy'], d['full_target_energy'])
        flat_profile = p.decomposition([1., 2., 1., 2.], [2., 1., 2., 1.], 2, 2)
        self.assertEqual(flat_profile['residual_status'], 'undefined_variance')
        self.assertIsNone(flat_profile['residual_correlation'])
        decimals = p.decomposition([0.1, 0.3]*7, [0.3, 0.1]*7, 7, 2)
        self.assertEqual(decimals['residual_target_energy'], 0.0)
        self.assertEqual(decimals['residual_prediction_energy'], 0.0)
        self.assertEqual(decimals['residual_status'], 'undefined_variance')
        with self.assertRaises(ValueError):
            p.decomposition([0.]*4, [1., 2., 3., 4.], 2, 2)

    def test_generated_cli(self):
        data = real_fixture()
        digest = hashlib.sha256(data).hexdigest()
        samples = {sid: ('synthetic.orf', digest, 1250, 4)
                   for sid in set(p.PHASES['verification']) | {'1995'}}
        args = ['probe', '--phase', 'discovery', '--train', 'input']
        for sid in p.PHASES['discovery']:
            args.extend(('--sample', sid, 'input'))
        output = io.StringIO()
        with mock.patch.object(p.cross, 'ROWS', 4), mock.patch.object(p.cross, 'SAMPLES', samples), \
             mock.patch.object(p, 'ADDITIONAL', {}), mock.patch.object(p, 'EXTRA', {}), \
             mock.patch('builtins.open', mock.mock_open(read_data=data)), \
             mock.patch.object(sys, 'argv', args), mock.patch('sys.stdout', output):
            self.assertEqual(p.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(len(report['results']), 3)
        for row in report['results']:
            self.assertEqual(row['status'], 'ok')
            self.assertEqual(len(row['measurement']['shuffles']), 4)
            self.assertAlmostEqual(row['measurement']['real']['stationary_contribution'],
                                   row['measurement']['shift_mean'], places=12)


if __name__ == '__main__':
    unittest.main()
