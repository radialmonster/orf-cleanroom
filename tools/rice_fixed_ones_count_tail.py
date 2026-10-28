#!/usr/bin/env python3
"""Exact synthetic count tail for uniformly ordered bits with fixed ones.

The fixed count includes all bits, including suffix bits. The effective unary
draws in the formula are not a literal prefix of the input bitstream.
"""
import argparse
from fractions import Fraction
import json
from math import comb


def count_tail(n, k, ones, count):
    """Return P(at least count complete Rice words) under the fixed-ones orbit."""
    if (type(n) is not int or not 0 <= n <= 4096 or
            type(k) is not int or not 0 <= k <= 8 or
            type(ones) is not int or not 0 <= ones <= n or
            type(count) is not int or count < 0):
        raise ValueError('require N=0..4096, k=0..8, K=0..N and nonnegative count')
    if count == 0:
        return Fraction(1)
    if count * (k + 1) > n or count > ones:
        return Fraction(0)
    draws = n - k * count
    lo = max(count, ones - (n - draws), 0)
    hi = min(draws, ones)
    favorable = sum(comb(draws, j) * comb(n - draws, ones - j)
                    for j in range(lo, hi + 1))
    return Fraction(favorable, comb(n, ones))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bits', type=int, required=True)
    parser.add_argument('--k', type=int, required=True)
    parser.add_argument('--ones', type=int, required=True)
    parser.add_argument('--count', type=int, required=True)
    args = parser.parse_args()
    try:
        value = count_tail(args.bits, args.k, args.ones, args.count)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps({'bits': args.bits, 'k': args.k, 'ones': args.ones,
                      'count_at_least': args.count,
                      'numerator': value.numerator, 'denominator': value.denominator}, indent=2))


if __name__ == '__main__':
    main()
