import sys
import unittest
from fractions import Fraction
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rice_finite_count_null import fixed_ones_counts
from rice_fixed_ones_count_tail import count_tail


class FixedOnesCountTailTest(unittest.TestCase):
    def test_joint_marginal(self):
        for n in range(17):
            for k in range(9):
                for ones in range(n + 1):
                    joint = fixed_ones_counts(n, k, ones)
                    for c in range(n + 2):
                        expected = Fraction(sum(v for (count, _), v in joint.items() if count >= c),
                                            comb(n, ones))
                        self.assertEqual(count_tail(n, k, ones, c), expected)

    def test_boundaries(self):
        self.assertEqual(count_tail(4, 1, 2, 2), Fraction(1, 6))
        self.assertEqual(count_tail(0, 0, 0, 0), 1)
        self.assertEqual(count_tail(4096, 0, 2048, 2048), 1)
        self.assertEqual(count_tail(4096, 0, 2048, 2049), 0)
        self.assertEqual(count_tail(4096, 8, 4096, 455), 1)
        self.assertEqual(count_tail(4096, 8, 0, 1), 0)
        self.assertEqual(count_tail(4096, 8, 4096, 456), 0)

    def test_invalid_inputs(self):
        for args in ((4097, 0, 0, 0), (0, 9, 0, 0), (1, 0, 2, 0), (1, 0, 0, -1)):
            with self.assertRaises(ValueError):
                count_tail(*args)


if __name__ == '__main__':
    unittest.main()
