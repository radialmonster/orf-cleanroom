#!/usr/bin/env python3
"""Fixed #155 learned-suffix-table circular registration sensitivity.

Uses the existing table fit and candidate/preview helpers; shifts are vertical
by default or horizontal with --axis horizontal. Circular shifts are descriptive,
not physical registration, p-values, sensor values or a codec. Aggregate JSON
only. Match retained CC0 provenance independently. Python 3.8+ stdlib only.
"""
import argparse
import hashlib
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_value_probe as legacy

TOL = 1e-12
ROWS = 600
SAMPLES = {
    '1995': ('Olympus - E-M1MarkII - 16bit (4:3).ORI', '8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f', 5240, 3912),
    '1997': ('Olympus - E-M1MarkII - 16bit (4:3).ORI', '89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a', 5240, 3912),
    '1998': ('Olympus - E-M1MarkII - 16bit (4:3).ORF', '4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71', 5240, 3912),
    '1993': ('Olympus - E-M1MarkII - 16bit (4:3).ORF', '0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8', 5240, 3912),
    '1994': ('Olympus - E-M1MarkII - 16bit (4:3).ORF', 'f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23', 10400, 7792),
}
PHASES = {'discovery': ('1997', '1998'), 'verification': ('1997', '1998', '1993', '1994')}


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def features_from_file(sample_id, path):
    name, expected, width, height = SAMPLES[sample_id]
    if digest(path) != expected:
        raise ValueError('input identity mismatch')
    w, h, q, s, rows = legacy.read_tokens(path, ROWS)
    if (w, h) != (width, height) or rows != ROWS:
        raise ValueError('geometry or complete-row mismatch')
    wb, hb, dc, nd = legacy.read_preview(path, rows, h)
    if wb < 1 or hb < nd or len(dc) != wb * hb:
        raise ValueError('preview geometry mismatch')
    y = legacy.row_center([dc[r * wb + c] for r in range(nd) for c in range(wb)], nd, wb)
    x = legacy.features(q, s, rows, w, nd, wb, 's', intercept=False)
    if digest(path) != expected:
        raise ValueError('input changed during legacy reads')
    return x, y, {'id': sample_id, 'name': name, 'sha256': expected,
                  'width': w, 'height': h, 'candidate_rows': rows,
                  'preview_width_blocks': wb, 'preview_height_blocks': hb,
                  'used_preview_rows': nd}


def shift_scores(target, prediction, rows, cols, axis='vertical'):
    if axis not in ('vertical', 'horizontal'):
        raise ValueError('invalid axis')
    if axis == 'horizontal' and cols != 400:
        raise ValueError('horizontal grid width mismatch')
    if rows < 2 or cols < 1 or len(target) != rows * cols or len(prediction) != rows * cols:
        raise ValueError('incompatible dimensions')
    if not all(math.isfinite(x) for x in target + prediction):
        return {'status': 'undefined_nonfinite'}
    n = rows * cols
    tm, pm = math.fsum(target) / n, math.fsum(prediction) / n
    t, p = [x - tm for x in target], [x - pm for x in prediction]
    vt, vp = math.fsum(x * x for x in t), math.fsum(x * x for x in p)
    if vt <= 0 or vp <= 0:
        return {'status': 'undefined_variance'}
    denominator = math.sqrt(vt * vp)
    if axis == 'vertical':
        scores = [math.fsum(t[r * cols + c] * p[((r + k) % rows) * cols + c]
                            for r in range(rows) for c in range(cols)) / denominator
                  for k in range(rows)]
    else:
        scores = [math.fsum(t[r * cols + c] * p[r * cols + ((c + k) % cols)]
                            for r in range(rows) for c in range(cols)) / denominator
                  for k in range(cols)]
        if not all(math.isfinite(x) for x in scores):
            return {'status': 'undefined_nonfinite'}
    best, zero = max(scores), scores[0]
    greater = [i for i, x in enumerate(scores[1:], 1) if x > zero + TOL]
    ties = [i for i, x in enumerate(scores) if abs(x - zero) <= TOL]
    return {'status': 'ok', 'scores': scores, 'zero_r': zero,
            'best_r': best, 'best_shifts_within_tolerance': [i for i, x in enumerate(scores) if best - x <= TOL],
            'zero_min_rank': 1 + len(greater), 'zero_ties': ties, 'shift_count': len(scores),
            'operationally_specific': zero > 0 and all(zero > x + TOL for x in scores[1:]),
            'tolerance': TOL}


def fitted_table(x, y, rows, cols):
    mask = [(r % 2 == 0) for r in range(rows) for _ in range(cols)]
    return legacy.solve([a for a, keep in zip(x, mask) if keep],
                        [a for a, keep in zip(y, mask) if keep],
                        1.0, 10.0, 32, intercept=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=sorted(PHASES), required=True)
    ap.add_argument('--train', required=True)
    ap.add_argument('--axis', choices=('vertical', 'horizontal'), default='vertical')
    ap.add_argument('--sample', nargs=2, action='append', metavar=('ID', 'PATH'), required=True)
    args = ap.parse_args()
    if tuple(item[0] for item in args.sample) != PHASES[args.phase]:
        ap.error('samples must match the frozen phase in order')
    try:
        x, y, train_info = features_from_file('1995', args.train)
        fit = fitted_table(x, y, train_info['used_preview_rows'], train_info['preview_width_blocks'])
        if len(fit) != 32 or not all(math.isfinite(v) for v in fit):
            raise ValueError('invalid fitted table')
        train_info['table_sha256_binary64_be'] = hashlib.sha256(struct.pack('>32d', *fit)).hexdigest()
    except (ValueError, IndexError, KeyError, OSError, TypeError, ZeroDivisionError, struct.error) as exc:
        print(json.dumps({'status': 'unknown_training', 'error_type': type(exc).__name__}))
        return 1
    results = []
    for sample_id, path in args.sample:
        try:
            x, y, info = features_from_file(sample_id, path)
            p = legacy.predict(x, fit)
            result = shift_scores(y, p, info['used_preview_rows'], info['preview_width_blocks'], args.axis)
            if result['status'] == 'ok':
                legacy_r, _ = legacy.stats(y, p)
                if not math.isfinite(legacy_r) or abs(result['zero_r'] - legacy_r) > 1e-12:
                    raise ValueError('legacy zero-shift mismatch')
                result['legacy_zero_r'] = legacy_r
            results.append({'sample': info, 'measurement': result})
        except (ValueError, IndexError, KeyError, OSError, TypeError, ZeroDivisionError, struct.error) as exc:
            results.append({'sample': {'id': sample_id, 'name': SAMPLES[sample_id][0]},
                            'measurement': {'status': 'unknown', 'error_type': type(exc).__name__}})
    output = {'phase': args.phase, 'train': train_info, 'results': results}
    if args.axis == 'horizontal':
        output['axis'] = 'horizontal'
    print(json.dumps(output, allow_nan=False))
    return int(any(r['measurement']['status'] != 'ok' for r in results))


if __name__ == '__main__':
    sys.exit(main())
