"""Generated exact centered-bridge and block-control checks."""
from array import array
import os
import random
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_field_order_bridge as p


class Tests(unittest.TestCase):
    def test_drift_and_center(self):
        values=[1,3,-2,4,0,-3]
        x=p.bridge(values)
        self.assertEqual(sum(x),0)
        self.assertEqual(x,p.bridge([v+7 for v in values]))

    def test_signal_and_permutation(self):
        pattern=[((i//32)*3+(i%7))%17-8 for i in range(128)]
        row=[v for x in pattern for v in (x,x)]
        r=p.analyze(array('b',row*5),5,256)
        self.assertAlmostEqual(r['lanes']['real']['r'],1.0)
        self.assertTrue(r['decision']['strict_above_both'])
        self.assertEqual(r['lanes']['real']['complete_pairs'],6)
        self.assertEqual(r['lanes']['real']['paired_values'],6*128)
        tail=list(range(65))
        shuffled=p.shuffled_blocks(tail,random.Random(1))
        self.assertEqual(shuffled[-1],64)
        self.assertEqual(sorted(shuffled[:32]),list(range(32,64)))

    def test_exact_signed_near_tie_order(self):
        def moment(c, e):
            return {'cross': c, 'energy_x': e, 'energy_y': e}
        a=moment(10**20+1,10**20+2)
        b=moment(10**20,10**20+1)
        self.assertTrue(p.correlation_greater(a,b))
        self.assertFalse(p.correlation_greater(a,a))
        self.assertTrue(p.correlation_greater(moment(-1,3),moment(-1,2)))
        self.assertTrue(p.correlation_greater(moment(0,1),moment(-1,2)))
    def test_zero_energy_and_missing_shared_mask(self):
        r=p.analyze(array('b',[1]*24),3,8)
        self.assertEqual(r['lanes']['real']['status'],'zero_energy')
        self.assertIsNone(r['decision']['strict_above_both'])
        grid=array('b',[0]*32)
        grid[0]=p.old.MISSING
        r=p.analyze(grid,4,8)
        for lane in r['lanes'].values():
            self.assertEqual((lane['complete_pairs'],lane['skipped_pairs']),(3,1))


if __name__=='__main__':
    unittest.main()
