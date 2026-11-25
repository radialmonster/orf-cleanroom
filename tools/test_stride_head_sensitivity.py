"""Synthetic head comparison and fixed later support controls."""
from array import array
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stride_head_sensitivity as probe


class Tests(unittest.TestCase):
    def test_real_candidate_scanner(self):
        words, bits = probe.scan_payload(bytes([0b10000010, 0b00000000]), 2)
        self.assertEqual(list(words), [0, 0])
        self.assertEqual(bits, 12)

    def test_all_heads_reuse_prefix_and_fixed_later(self):
        width = 140
        q = array('B', [0]) * (1300 * (width + 1200))
        calls = []
        def scores(prefix, lo, hi, rows, head):
            calls.append((len(prefix), lo, hi, rows, head))
            return [(3.0, 0.2, width + head, 300), (1.0, 0.1, width, 300)]
        with mock.patch.object(probe.token_row_stride, 'stride_scores', side_effect=scores), \
             mock.patch.object(probe, 'later', side_effect=lambda data, s, h: {'status': 'ok', 'stride': s, 'head': h}):
            result = probe.compare(q, width)
        self.assertEqual([x[-1] for x in calls], list(probe.HEADS))
        self.assertTrue(all(c[0] == 300*(width+1200) for c in calls))
        self.assertEqual(result['legacy_head32_winner'], width+32)
        self.assertEqual([x['winner_later']['stride'] for x in result['heads']], [width+h for h in probe.HEADS])
        self.assertTrue(all(x['head32_winner_later']['stride'] == width+32 for x in result['heads']))

    def test_insufficient_and_undefined(self):
        self.assertEqual(probe.compare(array('B'), 140)['status'], 'insufficient_prefix')
        self.assertEqual(probe.later(array('B', [0])*100, 140, 8)['status'], 'insufficient')
        q = array('B', [0]) * (1300 * 140)
        self.assertEqual(probe.later(q, 140, 8)['status'], 'undefined')

    def test_exact_tie_retains_legacy_order(self):
        width = 140
        q = array('B', [0]) * (300 * (width+1200))
        def scores(prefix, lo, hi, rows, head):
            return [(1.0, 0.1, width+1, 300), (1.0, 0.1, width, 300)]
        with mock.patch.object(probe.token_row_stride, 'stride_scores', side_effect=scores), \
             mock.patch.object(probe, 'later', return_value={'status': 'insufficient'}):
            result = probe.compare(q, width)
        self.assertEqual(result['heads'][0]['winner'], width+1)
        self.assertEqual(result['heads'][0]['ties_exact'], [width, width+1])

    def test_nonfinite_winner_is_retained(self):
        width = 140
        q = array('B', [0]) * (300 * (width+1200))
        def scores(prefix, lo, hi, rows, head):
            return [(float('inf'), 0.1, width+1, 300), (1.0, 0.1, width, 300)]
        with mock.patch.object(probe.token_row_stride, 'stride_scores', side_effect=scores), \
             mock.patch.object(probe, 'later', return_value={'status': 'insufficient'}):
            result = probe.compare(q, width)
        self.assertEqual(result['heads'][0]['winner'], width+1)
        self.assertIsNone(result['heads'][0]['z'])
        self.assertEqual(result['heads'][0]['z_sign'], 'positive_infinity')


if __name__ == '__main__':
    unittest.main()
