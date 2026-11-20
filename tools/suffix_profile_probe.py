#!/usr/bin/env python3
"""Column-profile and vertical-residual decomposition of the fixed #155 table."""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_table_cross_body_probe as cross
from suffix_table_highres_probe import ADDITIONAL
from suffix_table_shift_probe import shift_scores

EXTRA = {
    '3804': ('Olympus - E-M1MarkIII - 16bit (4:3).ORI',
             'd831692b608471ad64667eb2485bab553de0ddb9366d384c4ecb731092b5dc42', 5240, 3912),
    '6347': ('OM System - OM-5 - 16bit (4:3).ORI',
             '062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9', 5240, 3912),
}
PHASES = {'discovery': ('3801', '3803', '6344'),
          'verification': ('3801', '3803', '6344', '3804', '6347')}


class UndefinedFullVariance(ValueError):
    """One of the full vectors is constant."""


def decomposition(target, prediction, rows, cols):
    n = rows * cols
    if rows < 2 or cols < 1 or len(target) != n or len(prediction) != n:
        raise ValueError('invalid grid')
    if not all(math.isfinite(v) for v in target + prediction):
        raise ValueError('nonfinite grid')
    a_mean, b_mean = math.fsum(target) / n, math.fsum(prediction) / n
    a = [v-a_mean for v in target]
    b = [v-b_mean for v in prediction]
    # Center each column relative to its first entry so constant columns
    # retain exactly zero residual for floating-point input.
    ao = [math.fsum(target[r*cols+c]-target[c] for r in range(rows))/rows for c in range(cols)]
    bo = [math.fsum(prediction[r*cols+c]-prediction[c] for r in range(rows))/rows for c in range(cols)]
    ac = [target[c]+ao[c]-a_mean for c in range(cols)]
    bc = [prediction[c]+bo[c]-b_mean for c in range(cols)]
    ar = [target[r*cols+c]-target[c]-ao[c] for r in range(rows) for c in range(cols)]
    br = [prediction[r*cols+c]-prediction[c]-bo[c] for r in range(rows) for c in range(cols)]
    ea, eb = math.fsum(v*v for v in a), math.fsum(v*v for v in b)
    va, vb = math.fsum(v*v for v in ar), math.fsum(v*v for v in br)
    ca, cb = rows*math.fsum(v*v for v in ac), rows*math.fsum(v*v for v in bc)
    if ea <= 0 or eb <= 0 or max(target) == min(target) or max(prediction) == min(prediction):
        raise UndefinedFullVariance('undefined full variance')
    if abs(ea-ca-va) > 1e-12*ea or abs(eb-cb-vb) > 1e-12*eb:
        raise ValueError('energy decomposition mismatch')
    denominator = math.sqrt(ea*eb)
    stationary = rows*math.fsum(x*y for x, y in zip(ac, bc))/denominator
    residual_numerator = math.fsum(x*y for x, y in zip(ar, br))
    residual = residual_numerator/denominator
    return {'full_target_energy': ea, 'full_prediction_energy': eb,
            'profile_target_energy': ca, 'profile_prediction_energy': cb,
            'residual_target_energy': va, 'residual_prediction_energy': vb,
            'profile_target_fraction': ca/ea, 'profile_prediction_fraction': cb/eb,
            'stationary_contribution': stationary, 'residual_contribution': residual,
            'residual_status': 'ok' if va > 0 and vb > 0 else 'undefined_variance',
            'residual_correlation': residual_numerator/math.sqrt(va*vb) if va > 0 and vb > 0 else None}


def measure(x, y, q, s, info, fit):
    prediction = cross.legacy.predict(x, fit)
    rows, cols = info['used_preview_rows'], info['preview_width_blocks']
    real = decomposition(y, prediction, rows, cols)
    shifts = shift_scores(y, prediction, rows, cols)
    if shifts['status'] != 'ok':
        raise ValueError('undefined shifts')
    mean = math.fsum(shifts['scores'])/len(shifts['scores'])
    if abs(mean-real['stationary_contribution']) > 1e-12:
        raise ValueError('curve mean mismatch')
    if abs(shifts['zero_r']-real['stationary_contribution']-real['residual_contribution']) > 1e-12:
        raise ValueError('zero score mismatch')
    rng = random.Random(20261021)
    shuffles = []
    for _ in range(4):
        qb, sb = cross.legacy.shuffle_pairs(q, s, cross.ROWS, info['width'], rng)
        sx = cross.legacy.features(qb, sb, cross.ROWS, info['width'], rows, cols, 's', intercept=False)
        try:
            shuffles.append({'status': 'ok', **decomposition(y, cross.legacy.predict(sx, fit), rows, cols)})
        except UndefinedFullVariance:
            shuffles.append({'status': 'unknown_variance'})
    return {'real': real, 'shift_mean': mean, 'zero_r': shifts['zero_r'],
            'shift_scores': shifts['scores'], 'shuffles': shuffles}


def main():
    parser = cross.SafeParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(PHASES), required=True)
    parser.add_argument('--train', required=True)
    parser.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'))
    args = parser.parse_args()
    if tuple(v[0] for v in args.sample) != PHASES[args.phase]:
        parser.error('frozen sample order required')
    samples = dict(cross.SAMPLES)
    samples.update(ADDITIONAL)
    samples.update(EXTRA)
    report, status = cross.run(args.phase, args.train, args.sample, samples, measure)
    print(json.dumps(report, allow_nan=False))
    return status


if __name__ == '__main__':
    sys.exit(main())
