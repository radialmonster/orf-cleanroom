"""Synthetic exact permutation and candidate-pair accounting controls."""
import itertools
import os
import sys
import unittest
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_field_partner_null as p


def brute(s, q, width, start, end):
    total = Fraction()
    for row in range(start, end):
        for group in (0, 1):
            pairs = [(s[i], s[i+1]) for i in range(row*width, (row+1)*width)
                     if s[i] >= 0 and s[i+1] >= 0 and int(q[i+1] > 0) == group]
            if not pairs:
                continue
            signs = [1-2*((a>>2)&1) for a,b in pairs]
            bs = [8*((b>>4)&1)-4*(1-((b>>3)&1)) for a,b in pairs]
            scores = [sum(x*y for x,y in zip(signs, perm)) for perm in itertools.permutations(bs)]
            total += Fraction(sum(scores), len(scores))
    return total


class Tests(unittest.TestCase):
    def test_exact_permutation_empty_singleton_and_escape(self):
        suffix = [4, 16, -1, 7, 24, 0, 4, 16, 8]
        quotient = [0, 0, 1, 0, 1, 0, 0, 0, 0]
        r = p.accounting(suffix, quotient, 4, 0, 2, 0)
        self.assertEqual(Fraction(r['permuted_partner_sum']), brute(suffix, quotient, 4, 0, 2))
        self.assertEqual(r['omitted_escape'], 2)
        self.assertGreater(r['singleton_row_q_cells'], 0)
        self.assertLess(r['nonempty_row_q_cells'], 4)

    def test_changed_pairing_with_same_marginals(self):
        q = [0]*7
        a = p.accounting([0,16,-1,4,24,-1,0], q, 6, 0, 1, 0)
        b = p.accounting([0,24,-1,4,16,-1,0], q, 6, 0, 1, 0)
        result = p.compare(p.summarize([a]), p.summarize([b]))
        self.assertEqual(Fraction(result['current_mean']), 0)
        self.assertEqual(Fraction(result['permuted_partner_mean']), 0)
        self.assertEqual(Fraction(result['pairing_remainder_mean']), 4)

    def test_marginal_change_without_pairing_remainder(self):
        q = [0]*7
        a = p.accounting([0,16,-1,0,24,-1,0], q, 6, 0, 1, 0)
        b = p.accounting([0,0,-1,0,8,-1,0], q, 6, 0, 1, 0)
        result = p.compare(p.summarize([a]), p.summarize([b]))
        self.assertNotEqual(Fraction(result['permuted_partner_mean']), 0)
        self.assertEqual(Fraction(result['pairing_remainder_mean']), 0)
        self.assertEqual(p.summarize([])['status'], 'empty')

if __name__ == '__main__':
    unittest.main()
