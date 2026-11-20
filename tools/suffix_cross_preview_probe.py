#!/usr/bin/env python3
"""Fixed suffix-table residual predictions against a same-geometry preview matrix."""
import hashlib
import json
import math
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_table_cross_body_probe as cross
from suffix_profile_probe import decomposition, UndefinedFullVariance
from suffix_table_shift_probe import fitted_table

EXTRA = {
    '3804': ('Olympus - E-M1MarkIII - 16bit (4:3).ORI',
             'd831692b608471ad64667eb2485bab553de0ddb9366d384c4ecb731092b5dc42', 5240, 3912),
    '3802': ('Olympus - E-M1MarkIII - 16bit (4:3).ORI',
             '83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46', 5240, 3912),
}
PHASES = {'discovery': ('3800', '3804'), 'verification': ('3800', '3804', '3802')}
TOL = 1e-12


def residual_score(target, prediction, rows, cols):
    try:
        result = decomposition(target, prediction, rows, cols)
    except UndefinedFullVariance:
        return {'status': 'undefined_full_variance'}
    if result['residual_status'] != 'ok':
        return {'status': 'undefined_residual_variance'}
    return {'status': 'ok', 'r': result['residual_correlation'],
            'target_residual_energy': result['residual_target_energy'],
            'prediction_residual_energy': result['residual_prediction_energy']}


def matrix(records, fit):
    result = []
    for sid, x, q, s, info in records:
        rows, cols = info['used_preview_rows'], info['preview_width_blocks']
        prediction = cross.legacy.predict(x, fit)
        rng = random.Random(20261021)
        nulls = []
        for _ in range(4):
            qb, sb = cross.legacy.shuffle_pairs(q, s, cross.ROWS, info['width'], rng)
            sx = cross.legacy.features(qb, sb, cross.ROWS, info['width'], rows, cols, 's', intercept=False)
            nulls.append(cross.legacy.predict(sx, fit))
        cells = []
        for tid, _, _, _, target in records:
            y = target['target']
            cells.append({'target_id': tid, 'real': residual_score(y, prediction, rows, cols),
                          'shuffles': [residual_score(y, candidate, rows, cols) for candidate in nulls]})
        values = [cell['real'].get('r') for cell in cells]
        own_index = next(i for i, item in enumerate(cells) if item['target_id'] == sid)
        if any(value is None for value in values):
            decision = {'status': 'unknown'}
        else:
            own = values[own_index]
            other = max(value for i, value in enumerate(values) if i != own_index)
            decision = {'status': 'ok', 'diagonal': own, 'maximum_off_diagonal': other,
                        'margin': own-other, 'positive_unique': own > 0 and own > other + TOL}
        result.append({'source_id': sid, 'cells': cells, 'decision': decision})
    return result


def main():
    parser = cross.SafeParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(PHASES), required=True)
    parser.add_argument('--train', required=True)
    parser.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'))
    args = parser.parse_args()
    if tuple(item[0] for item in args.sample) != PHASES[args.phase]:
        parser.error('frozen sample order required')
    samples = dict(cross.SAMPLES)
    samples.update(EXTRA)
    try:
        x, y, _, _, train = cross.load('1995', args.train, samples)
        cols = train['preview_width_blocks']
        fit_y = [v for i, v in enumerate(y) if (i // cols) % 2 == 0]
        if not all(math.isfinite(v) for v in fit_y) or len(set(fit_y)) < 2:
            raise ValueError('undefined training variance')
        fit = fitted_table(x, y, train['used_preview_rows'], cols)
        if len(fit) != 32 or not all(math.isfinite(v) for v in fit):
            raise ValueError('invalid table')
        train['table_sha256_binary64_be'] = hashlib.sha256(struct.pack('>32d', *fit)).hexdigest()
    except (OSError, ValueError, IndexError, KeyError, TypeError, ZeroDivisionError, struct.error) as exc:
        print(json.dumps({'status': 'unknown_training', 'error_type': type(exc).__name__}))
        return 1
    records, unknown = [], []
    for sid, path in args.sample:
        try:
            x, y, q, s, info = cross.load(sid, path, samples)
            preview = info['preview']
            if ((info['width'], info['height'], info['used_preview_rows'], info['preview_width_blocks']) !=
                    (5240, 3912, 46, 400) or
                    (preview['pixel_width'], preview['pixel_height']) != (3200, 2400)):
                raise ValueError('grid mismatch')
            records.append((sid, x, q, s, dict(info, target=y)))
        except (OSError, ValueError, IndexError, KeyError, TypeError, ZeroDivisionError, struct.error) as exc:
            unknown.append({'id': sid, 'name': samples[sid][0], 'sha256': samples[sid][1],
                            'status': 'unknown', 'error_type': type(exc).__name__})
    if unknown:
        print(json.dumps({'phase': args.phase, 'train': train, 'status': 'unknown_inputs', 'unknown': unknown}))
        return 1
    sampling = records[0][4]['preview']['sampling']
    if any(record[4]['preview']['sampling'] != sampling for record in records[1:]):
        print(json.dumps({'phase': args.phase, 'train': train, 'status': 'unknown_sampling_mismatch'}))
        return 1
    try:
        result = matrix(records, fit)
    except (ValueError, IndexError, KeyError, TypeError, ZeroDivisionError) as exc:
        print(json.dumps({'phase': args.phase, 'train': train, 'status': 'unknown_matrix',
                          'error_type': type(exc).__name__}))
        return 1
    public_info = [{key: value for key, value in record[4].items() if key != 'target'} for record in records]
    output = {'phase': args.phase, 'train': train, 'samples': public_info,
              'matrix_convention': 'row=prediction source; column=preview target', 'matrix': result}
    print(json.dumps(output, allow_nan=False))
    return int(any(row['decision']['status'] != 'ok' or
                   any(shuffle['status'] != 'ok' for cell in row['cells'] for shuffle in cell['shuffles'])
                   for row in result))


if __name__ == '__main__':
    sys.exit(main())
