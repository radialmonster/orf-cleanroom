#!/usr/bin/env python3
"""Exact small synthetic Rice count/residual null, extending #87.

A word is q non-stop bits, one stop bit, then k arbitrary suffix bits.
Inputs are a fixed bit budget N and an externally specified iid stop
probability, not a camera payload or an estimated-density significance test.
This rational-arithmetic demonstration is intentionally limited to N <= 32.
"""
import argparse
from fractions import Fraction
import json

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


def fraction_json(x):
    return {'numerator': x.numerator, 'denominator': x.denominator}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bits', type=int, required=True)
    ap.add_argument('--k', type=int, required=True)
    ap.add_argument('--stop-probability', required=True, help='externally fixed rational, e.g. 1/2')
    args = ap.parse_args(argv)
    try:
        p = Fraction(args.stop_probability)
        joint = joint_distribution(args.bits, args.k, p)
    except (ValueError, ZeroDivisionError) as e:
        ap.error(str(e))
    counts, tails = {}, {}
    for (count, tail), mass in sorted(joint.items()):
        counts[count] = counts.get(count, Fraction(0)) + mass
        tails[tail] = tails.get(tail, Fraction(0)) + mass
    result = {'bits': args.bits, 'k': args.k, 'stop_probability': fraction_json(p),
              'joint': [{'count': c, 'tail_bits': r, 'probability': fraction_json(v)}
                        for (c, r), v in sorted(joint.items())],
              'count_marginal': {str(c): fraction_json(v) for c, v in sorted(counts.items())},
              'tail_marginal': {str(r): fraction_json(v) for r, v in sorted(tails.items())},
              'scope': 'synthetic iid fixed-p null; no camera inference or fitted-p calibration'}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()