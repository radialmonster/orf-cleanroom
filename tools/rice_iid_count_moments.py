#!/usr/bin/env python3
"""Synthetic finite-budget iid stop-1 Rice count mean and variance.

The stop probability is supplied independently, not fitted from input bits.
Floating point estimates are not a uniform error bound or a significance test.
"""
import argparse
from fractions import Fraction
import json


def mixture(items):
    """Merge weighted conditional means and central variances."""
    weight = mean = variance = 0.0
    for w, m, v in items:
        if not w:
            continue
        new = weight + w
        delta = m - mean
        variance = (weight * variance + w * v + delta * delta * weight * w / new) / new
        mean += delta * w / new
        weight = new
    return weight, mean, variance


def compose(a, b):
    size = len(a)
    out = [[None] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            out[i][j] = mixture((a[i][h][0] * b[h][j][0],
                                 a[i][h][1] + b[h][j][1],
                                 a[i][h][2] + b[h][j][2]) for h in range(size))
        # Each start-state row represents a distribution. Normalize its weight
        # after every composition to limit drift from repeated squaring.
        scale = sum(cell[0] for cell in out[i])
        out[i] = [(w / scale, m, v) for w, m, v in out[i]]
    return out


def moments(n, k, p):
    if (type(n) is not int or not 0 <= n <= 10**9 or type(k) is not int or
            not 0 <= k <= 8 or not isinstance(p, Fraction) or not 0 <= p <= 1 or
            p.denominator > 1000):
        raise ValueError('require N=0..1e9, k=0..8 and rational p in [0,1] with denominator <=1000')
    size = k + 1
    base = [[(0., 0., 0.) for _ in range(size)] for _ in range(size)]
    if k == 0:
        base[0][0] = (1., float(p), float(p * (1 - p)))
    else:
        base[0][0] = (float(1 - p), 0., 0.)
        base[0][k] = (float(p), 0., 0.)
        for j in range(1, size):
            base[j][j - 1] = (1., float(j == 1), 0.)
    result = [[(1., 0., 0.) if i == j else (0., 0., 0.)
               for j in range(size)] for i in range(size)]
    while n:
        if n & 1:
            result = compose(result, base)
        n //= 2
        if n:
            base = compose(base, base)
    return mixture(result[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bits', type=int, required=True)
    parser.add_argument('--k', type=int, required=True)
    parser.add_argument('--stop-probability', required=True, help='external rational, e.g. 1/3')
    args = parser.parse_args()
    try:
        p = Fraction(args.stop_probability)
        probability, mean, variance = moments(args.bits, args.k, p)
    except (ValueError, ZeroDivisionError) as exc:
        parser.error(str(exc))
    print(json.dumps({'bits': args.bits, 'k': args.k, 'stop_probability': str(p),
                      'total_probability': probability, 'mean': mean, 'variance': variance},
                     allow_nan=False, indent=2))


if __name__ == '__main__':
    main()
