"""Synthetic alternative phase selection and tile-boundary tests."""
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import alternate_motif_phase as p


class Tests(unittest.TestCase):
    def test_shifted_phase_fit_and_scores(self):
        windows=((0,2),(2,4),(4,6)); pitch=128
        positions=[[40+j*pitch+7 for j in range(a,b)] for a,b in windows]
        r=p.select_and_score(positions,3,pitch,40,windows)
        self.assertEqual(r['selected'],{'phase':7,'fit_matches':2,'tie_count':1,'phase_difference':4})
        self.assertTrue(r['full_phase_recovery'])

    def test_fit_tie_and_no_reselect(self):
        windows=((0,2),(2,4),(4,6)); pitch=128
        a=[40+4,40+8]; b=[40+2*pitch+8,40+3*pitch+8]
        r=p.select_and_score([a,b,[]],0,pitch,40,windows)
        self.assertEqual((r['selected']['phase'],r['selected']['tie_count']),(4,2))
        self.assertEqual(r['windows'][1]['selected_phase_matches'],0)
        self.assertFalse(r['full_phase_recovery'])

    def test_no_alternative(self):
        windows=((0,1),(1,2),(2,3))
        r=p.select_and_score([[40],[168],[296]],0,128,40,windows)
        self.assertIsNone(r['selected'])
        self.assertIsNone(r['full_phase_recovery'])

    def test_prior_mismatch_blocks_alternative_scan(self):
        fake={'windows':[{'present':x} for x in (1,2,3,5)]}
        with mock.patch.object(p.prior,'analyze',return_value=fake), \
             mock.patch.object(p,'motif_positions') as scan:
            with self.assertRaisesRegex(ValueError,'prior_coverage_mismatch'):
                p.analyze(b'',0,(1,2,3,4),5220,3912)
        scan.assert_not_called()
    def test_cross_tile_motif_retained_in_source_tile(self):
        data=bytearray(60)
        start=40+128-5
        for i,bit in enumerate('10000000'*6):
            if bit=='1':
                pos=start+i
                data[pos//8] |= 128 >> (pos%8)
        fake={'windows':[{'present':x} for x in (1,2,3,4)]}
        with mock.patch.object(p.prior,'analyze',return_value=fake), \
             mock.patch.object(p,'PITCH',128), \
             mock.patch.object(p,'WINDOWS',((0,1),(1,2),(2,3))):
            r=p.analyze(bytes(data),0,(1,2,3,4),5220,3912)
        self.assertEqual(r['windows'][0]['motif_starts'],1)
        self.assertEqual(r['windows'][0]['indices'],[0,1])
        self.assertEqual(r['windows'][0]['tiles_with_motif'],1)
        self.assertEqual(r['selected']['phase'],123)
        self.assertEqual(r['windows'][1]['motif_starts'],0)


if __name__=='__main__':
    unittest.main()
