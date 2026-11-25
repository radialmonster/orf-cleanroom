"""Generated exact range and omission/permutation controls."""
from array import array
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_field_predictor_range as p


class Tests(unittest.TestCase):
    def test_exact_4095_4096_and_initial_zero(self):
        for value, expected in ((4095,'not_rejected'),(4096,'rejected')):
            n=value//117
            vals=[117]*n
            if value-117*n:
                vals.append(value-117*n)
            grid=array('b', [x for v in vals for x in (v,0)])
            r=p.ranges(grid,1,len(grid),'H')
            self.assertEqual(r['max_complete_span'],value)
            self.assertEqual(r['decision'],expected)
        r=p.ranges(array('b',[-10,0,5,0]),1,4,'H')
        self.assertEqual(r['max_complete_span'],10)

    def test_missing_chain_and_rejection_precedence(self):
        g=array('b',[p.MISSING,117]+[0,117]*34+[0,1])
        r=p.ranges(g,1,len(g),'H')
        self.assertEqual(r['unknown_chains'],1)
        self.assertEqual(r['decision'],'rejected')
        self.assertEqual(r['max_complete_span'],4096)
        self.assertEqual(p.ranges(array('b',[p.MISSING,0]),1,2,'H')['decision'],'unknown')

    def test_horizontal_vertical_orientation(self):
        grid = array('b', [10,0,-8,0, 0,0,0,0, 10,0,-8,0])
        h = p.ranges(grid, 3, 4, 'H')
        v = p.ranges(grid, 3, 4, 'V')
        self.assertEqual((h['total_chains'], h['max_complete_span']), (6, 10))
        self.assertEqual((v['total_chains'], v['max_complete_span']), (8, 20))
    def test_row_parity_permutation_preserves_mask_and_sums(self):
        g=array('b',[1,2,p.MISSING,4,5,6,7,8,9,10,11,12])
        for seed in (1,2):
            x=p.shuffled(g,2,6,seed)
            for row in range(2):
                for parity in (0,1):
                    ix=list(range(row*6+parity,row*6+6,2))
                    self.assertEqual([i for i in ix if g[i]==p.MISSING],
                                     [i for i in ix if x[i]==p.MISSING])
                    self.assertEqual(sorted(g[i] for i in ix), sorted(x[i] for i in ix))
            out=p.analyze(g,2,6)
            self.assertEqual(out['shuffle_'+str(seed)]['H'],p.ranges(x,2,6,'H'))
            self.assertEqual(out['shuffle_'+str(seed)]['V'],p.ranges(x,2,6,'V'))


if __name__=='__main__':
    unittest.main()
