#!/usr/bin/env python3
"""Generated candidate-word and ambiguity controls; no sample pixels."""
import os
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from capped_prefix_counts import count, controls, word_end


class Tests(unittest.TestCase):
    def test_every_ordinary_prefix(self):
        for q in range(12):
            bits='0'*q+'1'+'10101'
            self.assertEqual(word_end(bits,0),len(bits))
            for n in range(len(bits)):
                self.assertIsNone(word_end(bits[:n],0))

    def test_escape_accepts_low_and_high_raw(self):
        for raw in (0,1,383,384,4095):
            bits='0'*12+format(raw,'012b')
            self.assertEqual(word_end(bits,0),24)
            self.assertEqual(count(bits,0)['complete']['low_raw_escapes'],int(raw<384))
            for n in range(24):
                self.assertIsNone(word_end(bits[:n],0))

    def test_guard_policy_is_explicit(self):
        result=count('100000'*4,0)
        self.assertEqual(result['guard24']['tokens'],1)
        self.assertEqual(result['complete']['tokens'],4)
        self.assertEqual(result['complete']['residual_bits'],0)

    def test_incomplete_suffix_is_residual(self):
        result=count('100000'+'100',0)['complete']
        self.assertEqual((result['tokens'],result['residual_bits']),(1,3))

    def test_length_histogram_and_non6(self):
        result=count('100000'+'00100000'+'0'*24,0)['complete']
        self.assertEqual(result['lengths'],{6:1,8:1,24:1})
        self.assertEqual((result['tokens'],result['non6'],result['escapes']),(3,2,1))

    def test_group_alone_makes_both_ends_exact(self):
        result=controls()
        self.assertEqual(result['pitch'],6*result['width']+12)
        self.assertEqual(result['plain_end'],result['pitch'])
        self.assertEqual(result['head_end'],result['pitch'])


if __name__=='__main__':
    unittest.main()
