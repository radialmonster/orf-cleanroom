"""Synthetic integration checks for the fixed high-resolution comparison."""
import hashlib
import io
import json
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_table_highres_probe as p
from test_suffix_table_cross_body_probe import real_fixture


class Tests(unittest.TestCase):
    def test_generated_full_cli(self):
        data = real_fixture()
        digest = hashlib.sha256(data).hexdigest()
        identity = ('synthetic.orf', digest, 1250, 4)
        samples = {sid: identity for sid in ('1995', '3801', '3800', '6343')}
        additional = {sid: identity for sid in ('6344', '3803', '6346', '3802')}
        args = ['probe', '--phase', 'discovery', '--train', 'input']
        for sid in p.PHASES['discovery']:
            args.extend(('--sample', sid, 'input'))
        output = io.StringIO()
        with mock.patch.object(p.cross, 'ROWS', 4), mock.patch.object(p.cross, 'SAMPLES', samples), \
             mock.patch.object(p, 'ADDITIONAL', additional), \
             mock.patch('builtins.open', mock.mock_open(read_data=data)), \
             mock.patch.object(sys, 'argv', args), mock.patch('sys.stdout', output):
            self.assertEqual(p.main(), 0)
            self.assertEqual(set(p.cross.SAMPLES), {'1995', '3801', '3800', '6343'})
        report = json.loads(output.getvalue())
        self.assertEqual(len(report['results']), 5)
        for row in report['results']:
            self.assertEqual(row['status'], 'ok')
            measurement = row['measurement']
            self.assertEqual(len(measurement['transfer']['shuffles']), 4)
            self.assertEqual(len(measurement['vertical_shifts']['scores']), 125)
            self.assertEqual(measurement['vertical_shifts']['best_nonzero_r'],
                             max(measurement['vertical_shifts']['scores'][1:]))
            self.assertAlmostEqual(measurement['transfer']['r'],
                                   measurement['vertical_shifts']['zero_r'], places=12)

    def test_undefined_shift(self):
        with mock.patch.object(p.cross, 'score', return_value={'r': 0.1}), \
             mock.patch.object(p.cross.legacy, 'predict', return_value=[0.0]*4):
            with self.assertRaises(ValueError):
                p.measure([[]]*4, [0.0]*4, [], [],
                          {'used_preview_rows': 2, 'preview_width_blocks': 2}, [])


if __name__ == '__main__':
    unittest.main()
