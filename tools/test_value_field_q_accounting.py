"""Synthetic quotient support, exact moment and decomposition checks."""
import os
import sys
import unittest
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_field_q_accounting as q
import value_field_independent_audit as old


def payload(bits):
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


class Tests(unittest.TestCase):
    def test_parser_reproduces_old_suffix_and_guard(self):
        data = payload('1' + '100001' + '0100010' + '0'*12 + '1'*12 + '1'*24)
        suffix, quotient = q.parse(data, 3)
        previous, reason = old.parse(data, 3)
        self.assertIsNone(reason)
        self.assertEqual(list(suffix), list(previous))
        self.assertEqual(list(quotient), [0, 1, 12])
        with self.assertRaisesRegex(ValueError, 'short_guarded_parse'):
            q.parse(payload('1100001'), 1)

    def test_strata_omission_and_term_sums(self):
        suffix = [0, 1, 2, -1, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        quotient = [0, 1, 0, 12, 2, 0, 0, 3, 0, 0, 1, 0, 0]
        out = q.accounting(suffix, quotient, 6, 0, 2, edge=1)
        self.assertEqual(out['omitted_escape'], 2)
        self.assertEqual(sum(map(sum, out['histograms'])), 6)
        self.assertEqual(sum(map(sum, out['current_by_partner_q'])), 6)
        values = sum((i-20)*sum(h[i] for h in out['histograms']) for i in range(32))
        self.assertEqual(sum(out['term_sums']), values)

    def test_exact_decomposition_and_moments(self):
        a, b = [[0]*32 for _ in range(2)], [[0]*32 for _ in range(2)]
        a[0][20], a[1][22] = 3, 1
        b[0][21], b[1][23] = 1, 3
        result = q.contrast(a, b)
        self.assertEqual(Fraction(result['delta_mean']), Fraction(2))
        self.assertEqual(Fraction(result['within']), Fraction(1))
        self.assertEqual(Fraction(result['composition']), Fraction(1))
        d = q.describe(a)
        self.assertEqual(Fraction(d['third_central']), Fraction(3, 4))
        self.assertEqual(sum(map(Fraction, d['third_central_terms'].values())), Fraction(3, 4))
        self.assertEqual(q.contrast(a, [[0]*32, b[1]])['reason'], 'empty_stratum')
        self.assertEqual(q.describe([[0]*32, [0]*32])['status'], 'empty')

    def test_all_third_moment_components_and_zero_variance(self):
        hist = [[0]*32 for _ in range(2)]
        hist[0][20], hist[0][21] = 2, 1
        hist[1][23], hist[1][24] = 1, 1
        result = q.describe(hist)
        parts = list(map(Fraction, result['third_central_terms'].values()))
        self.assertTrue(all(parts))
        self.assertEqual(sum(parts), Fraction(result['third_central']))
        self.assertEqual(result['eligible'], 5)
        self.assertEqual([s['count'] for s in result['strata']], [3, 2])
        constant = [[0]*32 for _ in range(2)]
        constant[0][20] = 3
        result = q.describe(constant)
        self.assertEqual(result['strata'][1]['status'], 'empty')
        self.assertEqual(result['skew_status'], 'zero_variance')
        self.assertIsNone(result['standardized_skew'])


if __name__ == '__main__':
    unittest.main()
