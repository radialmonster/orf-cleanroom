"""Synthetic candidate-state and reporting checks for the #31 bounded screen."""
import os
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import flat_predictor_screen as s


class Tests(unittest.TestCase):
    def test_frozen_grid_counts_and_signed_maps(self):
        self.assertEqual(len(s.search_configs()),2640)
        self.assertEqual(len(s.cross_configs()),360)
        self.assertEqual([s.signed(u,'zz+') for u in range(5)],[0,-1,1,-2,2])
        self.assertEqual([s.signed(u,'zz-') for u in range(5)],[0,1,-1,2,-2])
        self.assertEqual([s.signed(u,'sl') for u in range(5)],[0,0,1,-1,2])

    def test_constant_zero_residual_and_short_input(self):
        cfg=('W','zz+',1,0,0,('fixed',0,0,0))
        report,error=s.candidate('1'*(16*4),4,cfg)
        self.assertIsNone(error)
        self.assertEqual(report['sites'],[(0.0,0.0)]*4)
        self.assertEqual(report['consumed_bits'],64)
        report,error=s.candidate('1'*10,4,cfg)
        self.assertIsNone(report)
        self.assertEqual(error,'missing_stop')

    def test_fixed_six_bit_skip_and_cross_zero(self):
        cfg=('W','zz+',1,1,0,('fixed',0,0,0))
        report,error=s.candidate('1'*70,4,cfg)
        self.assertIsNone(error)
        self.assertEqual(report['consumed_bits'],70)
        cross=('zz+',0,0,0,'W','L')
        report,error=s.candidate('100000'*(16*4),4,cross,True)
        self.assertIsNone(error)
        self.assertEqual(report['sites'],[(0.0,0.0)]*4)

    def test_predictors(self):
        self.assertEqual([s.predictor(k,5,9,7) for k in ('W','N','avg','planar','med')],[5,9,7,7,7])
        self.assertEqual(s.predictor('med',5,9,20),5)
        self.assertEqual(s.predictor('med',5,9,1),9)

    def test_adaptive_zero_updates_change_code_width(self):
        # A=4,N=1 starts k=2, then k=1 twice, then k=0.
        cfg=('W','zz+',1,0,0,('jls',0,4,1))
        bits='100'+'10'+'10'+'1'*61
        report,error=s.candidate(bits,4,cfg)
        self.assertIsNone(error)
        self.assertEqual(report['consumed_bits'],68)
        self.assertEqual(report['sites'],[(0.0,0.0)]*4)

    def test_previous_error_changes_next_code_width(self):
        # First q=1,k=0 gives -1; next k=1 reads zero, then k returns to 0.
        cfg=('W','zz+',1,0,0,('prev',0,0,1))
        report,error=s.candidate('01'+'10'+'1'*62,4,cfg)
        self.assertIsNone(error)
        self.assertEqual(report['consumed_bits'],66)
        self.assertEqual(report['sites'],[(-1.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0)])

    def test_nonzero_cross_l_ld_u(self):
        bits='100010'+'100000'*63  # first u=2 (+1), then zero residuals
        for other, expected in (('L',[(1.0,0.0),(0.5,0.5),(0.0,0.0),(0.0,0.0)]),
                                ('LD',[(1.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0)]),
                                ('U',[(1.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0)])):
            with self.subTest(other=other):
                report,error=s.candidate(bits,4,('zz+',0,0,0,'W',other),True)
                self.assertIsNone(error)
                self.assertEqual(report['consumed_bits'],384)
                self.assertEqual(report['sites'],expected)

    def test_activity_requires_suffix_after_nonzero_neighbour(self):
        bits='1'*14+'01'+'1'*12
        active=('W','zz+',1,0,0,('act',0,0,1))
        fixed=('W','zz+',1,0,0,('fixed',0,0,0))
        self.assertEqual(s.candidate(bits,6,active)[1],'incomplete_word')
        self.assertEqual(s.candidate(bits,6,fixed)[1],'missing_stop')


if __name__=='__main__': unittest.main()
