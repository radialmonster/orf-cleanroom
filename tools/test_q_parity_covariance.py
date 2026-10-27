import contextlib
import io
import json
import math
import os
import sys
import unittest
from unittest import mock
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import q_parity_covariance as t

class Tests(unittest.TestCase):
    def test_alternating(self):
        r=t.summarize([0,1]*8)
        self.assertAlmostEqual(r['lags'][0]['r'],-1)
        self.assertAlmostEqual(r['lags'][1]['r'],1)
        self.assertAlmostEqual(r['lags'][0]['within'],0)
        self.assertAlmostEqual(r['lags'][1]['within'],0)
        self.assertAlmostEqual(r['between_delta_share'],1)
        self.assertTrue(r['at_least_half'])

    def test_equal_parity_means(self):
        r=t.decompose([0,0,2,2,0,0,2,2,0,0],2)
        self.assertAlmostEqual(r['between'],0)
        self.assertNotEqual(r['r'],0)
        self.assertAlmostEqual(r['r'],r['within'])
        self.assertEqual([g['n'] for g in r['groups']],[4,4])

    def test_empty_parity_and_pearson(self):
        r=t.decompose([0,1,2],2)
        self.assertEqual(r['groups'][1]['n'],0)
        self.assertIsNone(r['r'])
        for xs in ([0,1,4,2,8,0,3],[0,1,4,2,8,0,3,6]):
            for lag in (1,2):
                self.assertAlmostEqual(t.decompose(xs,lag)['r'],t.orf_tokens.pearson(xs[:-lag],xs[lag:]))

    def test_odd_counts_independent_moments(self):
        xs=[0,1,4,2,8,0,3]
        for lag in (1,2):
            r=t.decompose(xs,lag); a=xs[:-lag];b=xs[lag:]; n=len(a)
            sx=sum(a);sy=sum(b);sxy=sum(x*y for x,y in zip(a,b))
            den=math.sqrt((sum(x*x for x in a)-sx*sx/n)*(sum(y*y for y in b)-sy*sy/n))
            self.assertAlmostEqual(r['r'],(sxy-sx*sy/n)/den)
            self.assertAlmostEqual(r['r'],r['within']+r['between'])
        self.assertEqual([g['n'] for g in t.decompose(xs,2)['groups']],[3,2])

    def test_undefined(self):
        self.assertIsNone(t.summarize([3]*8)['at_least_half'])
        self.assertIsNone(t.decompose([],1)['r'])
        self.assertIsNone(t.summarize([0,1,2])['at_least_half'])

    def test_measure_caps_and_shortfall(self):
        def scan(payload,limit,w,extra,esc,q,s,cap):
            for x in (47,1,0): q.append(min(x,cap));s.append(0)
            return [],100
        with mock.patch('builtins.open',mock.mock_open(read_data=b'container')), \
             mock.patch.object(t.orf_tokens,'locate_data',return_value=(1,1,b'p')), \
             mock.patch.object(t.orf_tokens,'scan',side_effect=scan):
            self.assertEqual(t.measure('file',3)['first_q_capped'],8)
            with self.assertRaises(ValueError): t.measure('file',4)

if __name__=='__main__': unittest.main()
