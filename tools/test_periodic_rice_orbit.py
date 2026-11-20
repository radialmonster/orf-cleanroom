"""Exhaustive synthetic finite-state checks."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import periodic_rice_orbit as p


class Tests(unittest.TestCase):
    def test_six_nonconstant_all_starts(self):
        for n in range(1, 63):
            bits = format(n, '06b')
            for start in range(6):
                for k, maximum in ((4, 5), (5, 1)):
                    result = p.orbit(bits, k, start)
                    idx = result['cycle_start']
                    self.assertLessEqual(idx, maximum)
                    self.assertEqual(len(result['words']) - idx, 1)
                    self.assertEqual(result['words'][idx], {'q': 5-k, 'bits': 6})
    def test_constants_and_neighbors(self):
        for n in (5, 6, 7):
            for k in (4, 5):
                self.assertEqual(p.orbit('0'*n, k, 0)['status'], 'no_stop')
                for value in range(1, 2**n):
                    for start in range(n):
                        result = p.orbit(format(value, '0%db' % n), k, start)
                        idx = result['cycle_start']
                        for word in result['words']:
                            if word['bits'] == n:
                                self.assertEqual(word['q'], n-k-1)
                        if n < k+1:
                            self.assertTrue(all(word['bits'] > n for word in result['words']))
                        self.assertLess(idx, n)
        self.assertEqual(len(p.orbit('111111', 4, 0)['states']), 6)
        self.assertEqual(p.orbit('111111', 5, 0)['words'], [{'q': 0, 'bits': 6}])


if __name__ == '__main__':
    unittest.main()
