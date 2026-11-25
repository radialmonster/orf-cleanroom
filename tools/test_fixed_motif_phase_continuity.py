"""Generated coverage, gate, gap and terminal-boundary checks."""
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fixed_motif_phase_continuity as p


class Tests(unittest.TestCase):
    def test_gaps_ties_and_half_open_ranges(self):
        r=p.summarize(['present','present','absent','present','present','out_of_bounds'])
        self.assertEqual(r['longest_present_run'],[0,2])
        self.assertEqual(r['present_run_count'],2)
        self.assertEqual(r['absent_ranges'],[[2,3]])
        self.assertEqual(r['out_of_bounds_ranges'],[[5,6]])
        self.assertEqual((r['first_absent'],r['last_out_of_bounds']),(2,5))

    def test_prior_gate_before_farther_access(self):
        payload=bytes((40+801*31332+7)//8)
        with mock.patch.object(p,'motif',return_value=False) as m:
            with self.assertRaisesRegex(ValueError,'prior_coverage_mismatch'):
                p.analyze(payload,0,(1,0))
        self.assertEqual(m.call_count,800)

    def test_nominal_incomplete_never_reads_clipped_motif(self):
        pitch=31332
        cutoff=40+801*pitch+40
        payload=bytes(cutoff//8)
        with mock.patch.object(p,'motif',return_value=True) as m:
            r=p.analyze(payload,0,(400,400))
        self.assertTrue(all(call.args[1]+48 <= len(payload)*8 for call in m.call_args_list))
        self.assertEqual(r['nominal']['out_of_bounds'],3912-801)
        self.assertEqual(r['beyond_nominal']['complete_starts'],0)
    def test_complete_terminal_motif_and_clipping(self):
        pitch=31332
        first=40+3912*pitch
        payload=bytes((first+48+7)//8)
        with mock.patch.object(p,'motif',return_value=True):
            r=p.analyze(payload,0,(400,400))
        self.assertEqual(r['nominal']['present'],3912)
        self.assertEqual(r['beyond_nominal']['complete_starts'],1)
        self.assertEqual(r['beyond_nominal']['matched_starts'],1)
        payload=bytes((first+40)//8)
        with mock.patch.object(p,'motif',return_value=True) as m:
            r=p.analyze(payload,0,(400,400))
        self.assertTrue(all(call.args[1]+48 <= len(payload)*8 for call in m.call_args_list))
        self.assertEqual(r['beyond_nominal']['complete_starts'],0)
        self.assertEqual(r['beyond_nominal']['eof_minus_first_expected_start_bits'],40)


if __name__=='__main__':
    unittest.main()
