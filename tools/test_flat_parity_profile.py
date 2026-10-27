"""Synthetic nominal parity profile controls."""
from array import array
import contextlib
import io
import json
import os
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flat_parity_profile as p


def checker(width, blocks):
    return array('B', (0 if (r + c) % 2 == 0 else 8
                       for r in range(blocks) for c in range(width)))


class Tests(unittest.TestCase):
    def test_literal_counts_and_stable_orientation(self):
        w=8; ss=checker(w,205); qs=array('H',[0]*len(ss))
        result=p.profile(qs,ss,w)
        self.assertEqual(result['training_numerator'],1600)
        self.assertEqual((result['eligible'],result['opposing'],result['zero_opposing']), (3,0,True))
        self.assertEqual((result['blocks'][202]['numerator'],result['blocks'][202]['denominator']),(8,8))

    def test_odd_and_even_token_insertion(self):
        w=8; original=checker(w,206)
        for count, expected in ((1,True),(2,False)):
            ss=original[:202*w]+array('B',[0]*count)+original[202*w:]
            result=p.profile(array('H',[0]*len(ss)),ss,w)
            self.assertEqual(result['opposing'] > 0, expected)
            self.assertEqual(result['partial_tokens'],count)

    def test_no_signal_and_tied_training_are_undefined(self):
        w=8; ss=checker(w,204); qs=array('H',[0]*len(ss))
        for i in range(202*w,len(ss)): ss[i]=3
        result=p.profile(qs,ss,w)
        self.assertEqual((result['eligible'],result['low_information'],result['zero_opposing']),(0,2,None))
        tied=p.profile(array('H',[0]*(204*w)),array('B',[3]*(204*w)),w)
        self.assertIsNone(tied['orientation'])
        self.assertIsNone(tied['zero_opposing'])

    def test_partial_and_short_input(self):
        ss=checker(8,10)+array('B',[0,8])
        result=p.profile(array('H',[0]*len(ss)),ss,8)
        self.assertFalse(result['complete'])
        self.assertEqual(result['partial_tokens'],2)
        self.assertIsNone(result['zero_opposing'])

    def test_coverage_and_contrast_boundaries(self):
        w=20; ss=checker(w,205); qs=array('H',[0]*len(ss))
        # 18 qualifying values, with 10 supporting and 8 opposing: exactly
        # 90% coverage and contrast 2/18, both above their fixed thresholds.
        base=202*w
        ss[base:base+w]=array('B',[0,8]*5+[8,0]*4+[3,3])
        # q != 0 excludes even an otherwise eligible suffix.
        qs[203*w]=1
        result=p.profile(qs,ss,w)
        self.assertEqual((result['blocks'][202]['numerator'],result['blocks'][202]['denominator']),(2,18))
        self.assertTrue(result['blocks'][202]['eligible'])
        self.assertEqual(result['blocks'][203]['denominator'],19)
        ss[base+18]=0; ss[base+19]=8
        # 11 supporting and 9 opposing => exactly 0.1 contrast.
        ss[base:base+w]=array('B',[0,8]*5+[8,0]*4+[0,8])
        self.assertTrue(p.profile(qs,ss,w)['blocks'][202]['eligible'])

    def test_cli_hash_failure_and_undefined_control(self):
        out=io.StringIO()
        with patch.object(sys,'argv',['profile','sample','--sha256','wrong']), \
             patch('builtins.open',return_value=io.BytesIO(b'data')), contextlib.redirect_stdout(out):
            self.assertEqual(p.main(),1)
        self.assertEqual(json.loads(out.getvalue())['error'],'ValueError')
        ss=checker(8,204); qs=array('H',[0]*len(ss))
        for i in range(202*8,len(ss)): ss[i]=3
        out=io.StringIO()
        with patch.object(sys,'argv',['profile','sample','--sha256',p.hashlib.sha256(b'data').hexdigest()]), \
             patch('builtins.open',return_value=io.BytesIO(b'data')), \
             patch.object(p.orf_tokens,'locate_data',return_value=(8,204,b'payload')), \
             patch.object(p.grid,'parse',return_value=(qs,ss,0)), \
             patch.object(p.grid,'shuffled',return_value=ss), contextlib.redirect_stdout(out):
            self.assertEqual(p.main(),0)
        report=json.loads(out.getvalue())
        self.assertIsNone(report['real']['zero_opposing'])
        self.assertEqual(report['shuffled']['orientation'],report['real']['orientation'])


if __name__ == '__main__': unittest.main()
