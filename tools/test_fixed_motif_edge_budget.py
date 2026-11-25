"""Generated fixed-lattice budget, missing-anchor and truncation checks."""
import os
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fixed_motif_edge_budget as p


def fixture():
    bits=['1']*256
    motif='10000000'*6
    for at in (40,112,184):
        bits[at:at+48]=motif
    return bits


def packed(bits):
    return bytes(int(''.join(bits[i:i+8]),2) for i in range(0,len(bits),8))


class Tests(unittest.TestCase):
    def test_minimum_and_predicate(self):
        r=p.analyze(packed(fixture()),10,0,first=0,count=3)
        self.assertEqual((r['present_anchors'],r['available_edges']),(3,2))
        self.assertEqual(r['predicate'],{'true':2})
        self.assertEqual(r['predicate_agreement'],{'both_agree':2})
        self.assertEqual(r['joint_success_masks']['0101'],2)

    def test_longer_and_missing_no_bridge(self):
        bits=fixture(); bits[88]='0'
        r=p.analyze(packed(bits),10,0,first=0,count=3)
        self.assertEqual(r['predicate'],{'false':1,'true':1})
        self.assertEqual(r['predicate_agreement'],{'both_agree':2})
        bits=fixture(); bits[112]='0'
        r=p.analyze(packed(bits),10,0,first=0,count=3)
        self.assertEqual((r['present_anchors'],r['available_edges'],r['unavailable_edges']),(2,0,2))
        self.assertEqual(r['status'],'no_available_edges')

    def test_truncated_window_unknown(self):
        with self.assertRaisesRegex(ValueError,'incomplete_window'):
            p.analyze(packed(fixture())[:-1],10,0,first=0,count=3)


if __name__=='__main__':
    unittest.main()
