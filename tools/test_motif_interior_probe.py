"""Synthetic motif selection, edge ambiguity and bounded parse checks."""
import os
import sys
import unittest
from unittest import mock
import contextlib
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motif_interior_probe as p


def bits_bytes(bits):
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


class Tests(unittest.TestCase):
    def test_cohort_gates_before_sample_read(self):
        for argv in (['probe', '--sample', 'PA200011.ORF', 'private'],
                     ['probe', '--cohort', 'om3-repeat', '--sample', 'P1010009.ORF', 'private'],
                     ['probe', '--cohort', 'em5-repeat', '--sample', 'PA210010.ORF', 'private']):
            with mock.patch.object(sys, 'argv', argv), mock.patch('builtins.open') as opened, \
                 contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    p.main()
                opened.assert_not_called()
        self.assertEqual(len(p.COHORTS['discovery']), 3)
        self.assertEqual(len(p.COHORTS['om3-repeat']), 2)
        self.assertEqual(len(p.COHORTS['em5-repeat']), 6)

    def test_all_bit_phases_and_chunk_boundary(self):
        motif = '10000000'*6
        for phase in range(8):
            payload = bits_bytes('0'*(61+phase) + motif + '1'*80)
            expected = 61+phase
            self.assertIn(expected, p.motif_positions(payload, 0, len(payload)*8, 8))
            self.assertNotIn(expected, p.motif_positions(payload, 0, expected+47, 8))

    def test_edges_unique_and_ambiguous(self):
        self.assertEqual(p.unique_edges([0, 1000, 2000], 1000, 20), [(0, 1000), (1000, 2000)])
        self.assertEqual(p.unique_edges([0, 990, 1010, 2000], 1000, 20), [])
        self.assertTrue(all(a < b for a, b in p.unique_edges([0, 1, 2], 1, 10)))

    def test_literal_and_capped_end_and_overruns(self):
        payload = bits_bytes('10000'*4 + '0'*12 + '1'*12)
        a = p.interior(payload, 0, 20, 4, False)
        self.assertEqual((a['endpoint'], a['words']), (True, 4))
        self.assertEqual(p.interior(payload, 20, 44, 5, True)['escapes'], 1)
        self.assertEqual(p.interior(payload, 20, 43, 5, True)['reason'], 'escape_overrun')
        self.assertEqual(p.interior(bits_bytes('1'), 0, 3, 5, False)['reason'], 'suffix_overrun')
        self.assertEqual(p.interior(bits_bytes('000'), 0, 3, 5, False)['reason'], 'stop_overrun')

    def test_sparse_and_overlap_guard(self):
        self.assertEqual(p.measure(bytes(100), 100)['status'], 'sparse_no_edges')
        with self.assertRaisesRegex(ValueError, 'overlapping_motif_range'):
            p.measure(bytes(100), 7)

    def test_joint_masks_and_same_denominator(self):
        payload = bytes(200)
        def result(data, start, end, k, capped):
            success = (k == 4 and not capped) or (k == 5 and capped)
            return {'endpoint': success, 'reason': 'exact_end' if success else 'suffix_overrun',
                    'words': 94 if success else 3, 'escapes': 0}
        with mock.patch.object(p, 'motif_positions', return_value=[40, 652]), \
             mock.patch.object(p, 'interior', side_effect=result):
            report = p.measure(payload, 100)
        self.assertEqual(report['joint_success_masks'], {'1001': 1})
        self.assertEqual(report['eligible_directed_edges'], 1)
        self.assertTrue(all(c['candidate_edges'] == 1 for c in report['grammars'].values()))


if __name__ == '__main__':
    unittest.main()
