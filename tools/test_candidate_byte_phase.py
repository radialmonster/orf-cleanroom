"""Generated candidate cursor, rotation, eligibility and exact tie controls."""
import os
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import candidate_byte_phase as p


def pack(bits):
    bits+='0'*(-len(bits)%8)
    return bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8))


class Tests(unittest.TestCase):
    def test_nonzero_start_and_no_skip_long_q(self):
        qs=[0,20,1]; ss=[0,31,4]
        r=p.window(qs,ss,3)
        self.assertEqual((r['start_bit'],r['end_bit']),(3,42))
        self.assertEqual(r['occupancy'],[0,1,0,2,0,0,0,0])
        self.assertEqual(sum(map(sum,r['tables']['0']['b4'])),2)

    def test_scanner_long_and_incomplete_suffix(self):
        bits='1'+'10101'+'0'*20+'1'+'11100'+'0'*3+'1'+'10'
        q=[];s=[]
        _,end=p.orf_tokens.scan(pack(bits),3,0,0,None,q,s,1<<62)
        self.assertEqual(q,[0,20])
        self.assertEqual(s,[21,28])
        self.assertEqual(end,32)

    def test_rotation_preserves_original_eligibility(self):
        q=[0,17,1,2]; s=[16,31,4,0]; phases=[0,1,2,3]
        tables=p.joint(phases,q,s,1)
        self.assertEqual(tables['q'][2][5],1)
        self.assertEqual(sum(tables['b4'][2]),0)
        self.assertEqual(tables['b4'][1][1],1)

    def test_mutual_information_sanity(self):
        self.assertAlmostEqual(p.mutual([[5,0],[0,5]]),1.0)
        self.assertAlmostEqual(p.mutual([[2,2],[3,3]]),0.0)
        self.assertIsNone(p.mutual([[0,0],[0,0]]))
    def test_exact_ties_and_equal_rates(self):
        table=[[0,0] for _ in range(8)]
        table[1]=[1,1];table[2]=[2,2];table[3]=[0,2];table[4]=[0,4]
        self.assertEqual(p.choose(table,1),{'high':3,'low':1})
        self.assertIsNone(p.choose([[2,2],[1,1]],1))


if __name__=='__main__':unittest.main()
