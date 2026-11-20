"""Synthetic ordered residual matrix and undefined-cell checks."""
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_cross_preview_probe as p


class Tests(unittest.TestCase):
    def test_ordered_matrix_reuses_shuffles(self):
        first = [1., -1., -1., 1.]
        second = [-1., 1., 1., -1.]
        base = {'width': 2, 'used_preview_rows': 2, 'preview_width_blocks': 2}
        records = [('A', first, [], [], dict(base, target=first)),
                   ('B', second, [], [], dict(base, target=second))]
        with mock.patch.object(p.cross.legacy, 'predict', side_effect=lambda x, fit: x), \
             mock.patch.object(p.cross.legacy, 'shuffle_pairs', return_value=([], [])) as shuffle, \
             mock.patch.object(p.cross.legacy, 'features', return_value=first):
            rows = p.matrix(records, [])
        self.assertEqual(shuffle.call_count, 8)
        self.assertEqual([row['source_id'] for row in rows], ['A', 'B'])
        self.assertEqual([cell['target_id'] for cell in rows[0]['cells']], ['A', 'B'])
        self.assertAlmostEqual(rows[0]['cells'][0]['real']['r'], 1.)
        self.assertAlmostEqual(rows[0]['cells'][1]['real']['r'], -1.)
        self.assertTrue(rows[0]['decision']['positive_unique'])
        self.assertTrue(rows[1]['decision']['positive_unique'])
        self.assertEqual(rows[0]['cells'][0]['shuffles'][0]['r'], 1.)
        self.assertEqual(rows[0]['cells'][1]['shuffles'][0]['r'], -1.)

    def test_undefined_residual(self):
        result = p.residual_score([0.1, 0.3]*3, [1., 2.]*3, 3, 2)
        self.assertEqual(result['status'], 'undefined_residual_variance')


if __name__ == '__main__':
    unittest.main()
