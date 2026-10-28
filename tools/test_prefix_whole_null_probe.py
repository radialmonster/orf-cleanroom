#!/usr/bin/env python3
"""Synthetic bounded parsing and integer-moment controls; no sample files."""
import os,sys,unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import prefix_whole_null_probe as p

class Tests(unittest.TestCase):
    def test_prefix_whole_and_tail(self):
        # q = 0,1,0, followed by incomplete zero-run and byte fill.
        bits='1'+'00000'+'01'+'00000'+'1'+'00000'+'00000'
        payload=int(bits,2).to_bytes(len(bits)//8,'big')
        result=p.measure(payload,1,1,prefix=2)
        self.assertEqual(result['prefix_status'],'complete')
        self.assertEqual((result['prefix']['tokens'],result['prefix']['endpoint_bits']),(2,13))
        self.assertEqual((result['whole']['tokens'],result['whole']['endpoint_bits'],result['whole']['residual_bits']),(3,19,5))
        self.assertEqual(result['whole']['lags']['1'],{'n':2,'sx':1,'sy':1,'sxx':1,'syy':1,'sxy':0,'pearson':-1.0})
        self.assertEqual(result['whole']['lags']['2']['pearson'],None)
        self.assertEqual((result['prefix']['complete_byte_bits'],result['prefix']['ones']),(8,2))
    def test_shortfall_and_escape(self):
        bits='0'*17+'1'+'00000'+'0'
        r=p.measure(int(bits,2).to_bytes(3,'big'),1,1,prefix=2)
        self.assertEqual(r['prefix_status'],'shortfall')
        self.assertIsNone(r['prefix'])
        self.assertEqual((r['whole']['tokens'],r['whole']['endpoint_bits'],r['whole']['escapes']),(1,23,1))
        self.assertIsNone(r['whole']['lags']['1']['pearson'])
    def test_extreme_density_matches_historical_undefined(self):
        for payload, expected in ((b'\xff\xff', (8,8)), (b'\x00\x80', (8,0))):
            result=p.measure(payload,1,1,prefix=1)['whole']
            self.assertEqual((result['complete_byte_bits'],result['ones']),expected)
            self.assertIsNone(result['null_projection'])
            self.assertIsNone(result['null_printed'])
    def test_no_complete_word_and_invalid(self):
        r=p.measure(b'\x00',1,1,prefix=1)
        self.assertEqual((r['whole']['tokens'],r['whole']['residual_bits']),(0,8))
        self.assertIsNone(r['whole']['real_projection'])
        self.assertIsNone(r['whole']['null_projection'])
        with self.assertRaises(ValueError):p.measure(b'',0,1)

if __name__=='__main__':unittest.main()
