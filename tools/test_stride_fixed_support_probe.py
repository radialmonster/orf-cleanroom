"""Synthetic-only support, nesting and score controls."""
import array
import os
import random
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stride_fixed_support_probe as p


class Tests(unittest.TestCase):
    def test_candidate_endpoint_marks(self):
        payload = bytes([0xff]) * 45
        q, s = array.array('B'), array.array('B')
        marks, end = p.old.T.scan(payload, 60, 15, 0, None, q, s, 40)
        self.assertEqual(marks, [0, 90, 180, 270])
        self.assertEqual((len(q), end), (60, 360))

    def test_fixed_support_and_refit(self):
        rng = random.Random(42)
        q = array.array('B', (rng.randrange(5) for _ in range(600 * 70)))
        with mock.patch.object(p, 'LO', 60), mock.patch.object(p, 'HI', 70), \
             mock.patch.object(p, 'HEAD', 4), mock.patch.object(p, 'N', len(q)):
            result = p.experiment(q, 63, (-2, 2))
            self.assertEqual(result['support']['head_count'] + result['support']['rest_count'], len(q))
            self.assertTrue(result['extents'][-1]['full_support_surrogate_equals_old_refit'])
            self.assertEqual([e['tokens'] for e in result['extents']], [10500, 21000, 42000])
            fixed = p.old.synthetic(q, 63, 4, p.SEED, len(q))
            for extent in result['extents']:
                rows = extent['rows']
                expected = p.summarize(fixed[:rows*70], rows, 63, (-2, 2))
                self.assertEqual(expected, extent['results']['fixed_support'])
            with self.assertRaises(ValueError):
                p.experiment(q[:-1], 63, (-2, 2))

    def test_empty_and_nonfinite(self):
        with mock.patch.object(p, 'stride_scores', return_value=[]):
            self.assertEqual(p.summarize([], 150, 63, (-2, 2))['status'], 'unknown_nonfinite_or_empty')

    def test_pair_decision(self):
        scores = [(8., 1., 5566, 300), (7., 1., 5614, 300), (6., 1., 5518, 300)]
        scores.extend((1., 0., s, 300) for s in range(5518, 5615)
                      if s not in (5518, 5566, 5614))
        with mock.patch.object(p, 'LO', 5518), mock.patch.object(p, 'HI', 5614), \
             mock.patch.object(p, 'stride_scores', return_value=scores):
            result = p.summarize([], 300, 5566, (-48, 48))
        self.assertTrue(result['pair_match'])
        self.assertEqual([row['rank'] for row in result['secondary']], [2, 3])
        self.assertEqual([row['stride'] for row in result['target_bands']], [5518, 5614])
        with mock.patch.object(p, 'stride_scores', return_value=[(float('inf'), 1., 63, 150)]):
            self.assertEqual(p.summarize([], 150, 63, (-2, 2))['status'], 'unknown_nonfinite_or_empty')


if __name__ == '__main__':
    unittest.main()
