#!/usr/bin/env python3
"""Synthetic exhaustive checks of the finite Rice count/tail null."""
import itertools
import os
import sys
import unittest
from collections import defaultdict
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rice_finite_count_null import joint_distribution
from terminal_residual_null_probe import residual_null


def brute(n, k, p):
    result = defaultdict(Fraction)
    for bits in itertools.product((0, 1), repeat=n):
        ones = sum(bits)
        weight = p**ones * (1-p)**(n-ones)
        cursor = count = 0
        while cursor < n:
            stop = cursor
            while stop < n and bits[stop] == 0:
                stop += 1
            if stop + 1 + k > n:
                break
            cursor = stop + 1 + k
            count += 1
        result[(count,n-cursor)] += weight
    return {key:value for key,value in result.items() if value}


class Tests(unittest.TestCase):
    def test_exhaustive(self):
        for n in range(9):
            for k in range(9):
                for p in (Fraction(0),Fraction(1,3),Fraction(1,2),Fraction(1)):
                    self.assertEqual(joint_distribution(n,k,p),brute(n,k,p))

    def test_existing_k5_tail_marginal(self):
        for n in range(33):
            for p in (Fraction(0),Fraction(1,3),Fraction(1,2),Fraction(1)):
                joint = joint_distribution(n,5,p)
                actual = [sum((v for (c,t),v in joint.items() if t == r),Fraction(0)) for r in range(n+1)]
                expected = residual_null(n,float(p))['residual_length_pmf']
                for a,b in zip(actual,expected): self.assertAlmostEqual(float(a),b,places=12)

    def test_extremes_and_bounds(self):
        self.assertEqual(joint_distribution(0,0,Fraction(1,2)),{(0,0):Fraction(1)})
        self.assertEqual(joint_distribution(5,0,Fraction(1)),{(5,0):Fraction(1)})
        self.assertEqual(joint_distribution(5,0,Fraction(0)),{(0,5):Fraction(1)})
        for n,k,p in ((33,0,Fraction(1,2)),(1,9,Fraction(1,2)),(1,0,Fraction(1,1001)),(1,0,Fraction(-1,2))):
            with self.assertRaises(ValueError): joint_distribution(n,k,p)

if __name__ == '__main__': unittest.main()