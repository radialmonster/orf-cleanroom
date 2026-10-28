#!/usr/bin/env python3
"""Exact small synthetic Rice count/residual null, extending #87.

A word is q zero bits, one stop bit (1), then k arbitrary suffix bits.
Inputs are a fixed bit budget N and an externally specified iid stop
probability, not a camera payload or an estimated-density significance test.
This rational-arithmetic demonstration is intentionally limited to N <= 32.
"""
import argparse
from fractions import Fraction
import json
import math

MAX_N = 32
MAX_K = 8
MAX_DENOMINATOR = 1000


def joint_distribution(n, k, p):
    """Return exact joint (completed-word count, unconsumed-tail bits) PMF."""
    if type(n) is not int or not 0 <= n <= MAX_N:
        raise ValueError('N must be an integer from 0 to 32')
    if type(k) is not int or not 0 <= k <= MAX_K:
        raise ValueError('k must be an integer from 0 to 8')
    if not isinstance(p, Fraction) or not 0 <= p <= 1 or p.denominator > MAX_DENOMINATOR:
        raise ValueError('p must be a rational from 0 to 1 with denominator at most 1000')
    z = 1 - p
    # B[t][s]: probability that exactly t complete words end at bit s.
    boundary = [[Fraction(0) for _ in range(n + 1)] for _ in range(n + 1)]
    boundary[0][0] = Fraction(1)
    for count in range(1, n + 1):
        for end in range(k + 1, n + 1):
            boundary[count][end] = sum(
                (boundary[count-1][end-(q+k+1)] * p * z**q
                 for q in range(end-k)), Fraction(0))
    joint = {}
    for count in range(n + 1):
        for tail in range(n + 1):
            survival = Fraction(1) if tail <= k else z**(tail-k)
            mass = boundary[count][n-tail] * survival
            if mass:
                joint[(count, tail)] = mass
    assert sum(joint.values(), Fraction(0)) == 1
    return joint


def fixed_ones_counts(n, k, ones):
    """Exact joint string counts conditional on all N bits containing K ones."""
    if type(n) is not int or not 0 <= n <= MAX_N:
        raise ValueError('N must be an integer from 0 to 32')
    if type(k) is not int or not 0 <= k <= MAX_K:
        raise ValueError('k must be an integer from 0 to 8')
    if type(ones) is not int or not 0 <= ones <= n:
        raise ValueError('ones must be an integer from 0 to N')
    result = {}
    for count in range(n + 1):
        for tail in range(n + 1):
            end = n - tail
            zeros = end - count * (k + 1)
            if count == 0:
                unary_ways = int(end == 0)
            elif zeros < 0:
                continue
            else:
                unary_ways = math.comb(zeros + count - 1, count - 1)
            free_bits = count * k + min(tail, k)
            free_ones = ones - count
            if unary_ways and 0 <= free_ones <= free_bits:
                value = unary_ways * math.comb(free_bits, free_ones)
                if value:
                    result[(count, tail)] = value
    if sum(result.values()) != math.comb(n, ones):
        raise ArithmeticError('fixed-ones counts do not normalize')
    return result

def fraction_json(x):
    return {'numerator': x.numerator, 'denominator': x.denominator}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bits', type=int, required=True)
    ap.add_argument('--k', type=int, required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--stop-probability', help='externally fixed rational, e.g. 1/2')
    mode.add_argument('--ones', type=int, help='fixed number of ones in all N bits')
    args = ap.parse_args(argv)
    try:
        if args.ones is None:
            p = Fraction(args.stop_probability)
            joint = joint_distribution(args.bits, args.k, p)
        else:
            raw_counts = fixed_ones_counts(args.bits, args.k, args.ones)
            total = math.comb(args.bits, args.ones)
            joint = {key: Fraction(value, total) for key, value in raw_counts.items()}
    except (ValueError, ZeroDivisionError) as e:
        ap.error(str(e))
    counts, tails = {}, {}
    for (count, tail), mass in sorted(joint.items()):
        counts[count] = counts.get(count, Fraction(0)) + mass
        tails[tail] = tails.get(tail, Fraction(0)) + mass
    result = {'bits': args.bits, 'k': args.k,
              **({'stop_probability': fraction_json(p)} if args.ones is None else
                 {'ones': args.ones, 'total_strings': total}),
              'joint': [{'count': c, 'tail_bits': r, 'probability': fraction_json(v)}
                        for (c, r), v in sorted(joint.items())],
              'count_marginal': {str(c): fraction_json(v) for c, v in sorted(counts.items())},
              'tail_marginal': {str(r): fraction_json(v) for r, v in sorted(tails.items())},
              'scope': ('synthetic iid fixed-p null; no camera inference or fitted-p calibration'
                        if args.ones is None else
                        'synthetic uniform fixed-ones null; exchangeability assumed, no camera inference')}
    if args.ones is not None:
        for row in result['joint']:
            row['strings'] = raw_counts[(row['count'], row['tail_bits'])]
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
