#!/usr/bin/env python3
"""Exact synthetic conditional-null change-point control for #296.

Eight bits, four ones, period-two fixed phase versus one fixed split at four.
All unique orderings are equiprobable ONLY under the declared synthetic null.
Same-data fitting is not a held-out prediction and does not imply camera framing.
"""
import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations
import json


def valid(bits):
    return len(bits) == 8 and all(x in (0, 1) for x in bits) and sum(bits) == 4


def mismatch(bits, first, second):
    return sum(x != int(i % 2 == (first if i < 4 else second)) for i, x in enumerate(bits))


def fit(bits):
    if not valid(bits):
        raise ValueError('exactly eight binary values and four ones required')
    fixed = min((mismatch(bits, p, p), p) for p in (0, 1))
    changed = min((mismatch(bits, p, q), p, q) for p in (0, 1) for q in (0, 1))
    return {'fixed_mismatches':fixed[0], 'fixed_phase':fixed[1],
            'changed_mismatches':changed[0], 'changed_phases':[changed[1],changed[2]],
            'gain':fixed[0]-changed[0]}


def orbit():
    for ones in combinations(range(8), 4):
        positions = set(ones)
        yield tuple(int(i in positions) for i in range(8))


def analyze(bits):
    observed = fit(bits)
    gains = [fit(candidate)['gain'] for candidate in orbit()]
    assert len(gains) == 70 and min(gains) >= 0
    rank = sum(g >= observed['gain'] for g in gains)
    p = Fraction(rank, len(gains))
    histogram = dict(sorted(Counter(gains).items()))
    # Verify superuniformity at all attainable p thresholds, by exact counts.
    ranks = [Fraction(sum(h >= g for h in gains), len(gains)) for g in gains]
    calibration = all(sum(r <= t for r in ranks) <= t * len(ranks) for t in set(ranks))
    return {'observed':observed, 'null_orderings':len(gains),
            'gain_histogram':histogram, 'tail_count_including_ties':rank,
            'tail_fraction':{'numerator':p.numerator,'denominator':p.denominator},
            'exact_superuniform':calibration,
            'limits':'synthetic uniform conditional null; no held-out or camera inference'}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--observed', required=True, help='eight synthetic bits with exactly four ones')
    args=ap.parse_args(argv)
    if len(args.observed)!=8 or any(x not in '01' for x in args.observed):
        ap.error('expected eight binary characters')
    try:
        result=analyze(tuple(int(x) for x in args.observed))
    except ValueError as e:
        ap.error(str(e))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
