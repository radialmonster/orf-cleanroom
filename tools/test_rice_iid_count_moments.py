import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rice_finite_count_null import joint_distribution
from rice_iid_count_moments import moments


class CountMomentsTest(unittest.TestCase):
    def test_small_exact_pmf(self):
        for n in range(13):
            for k in range(9):
                for p in (Fraction(0), Fraction(1, 3), Fraction(1, 2), Fraction(1)):
                    d = joint_distribution(n, k, p)
                    mean = sum((c * w for (c, _), w in d.items()), Fraction())
                    variance = sum(((c - mean) ** 2 * w for (c, _), w in d.items()), Fraction())
                    total, actual_mean, actual_var = moments(n, k, p)
                    self.assertAlmostEqual(total, 1., places=12)
                    self.assertAlmostEqual(actual_mean, float(mean), places=10)
                    self.assertAlmostEqual(actual_var, float(variance), places=10)

    def test_large_analytic_edges(self):
        n = 10**9
        for k in range(9):
            self.assertEqual(moments(n, k, Fraction(0)), (1., 0., 0.))
            self.assertEqual(moments(n, k, Fraction(1)), (1., float(n // (k + 1)), 0.))
        for p in (Fraction(1, 1000), Fraction(1, 2), Fraction(999, 1000)):
            total, mean, variance = moments(n, 0, p)
            self.assertAlmostEqual(total, 1.)
            self.assertAlmostEqual(mean / float(n * p), 1., places=12)
            self.assertAlmostEqual(variance / float(n * p * (1 - p)), 1., places=12)

    def test_bounds(self):
        for n, k, p in ((-1, 0, Fraction(1, 2)), (10**9+1, 0, Fraction(1, 2)),
                        (1, 9, Fraction(1, 2)), (1, 0, Fraction(1, 1001))):
            with self.assertRaises(ValueError):
                moments(n, k, p)


if __name__ == '__main__':
    unittest.main()
