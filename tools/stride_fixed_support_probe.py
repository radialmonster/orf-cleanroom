#!/usr/bin/env python3
"""Nested fold extents with one fixed-support #734 surrogate; aggregate only."""
import argparse
import array
import collections
import hashlib
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stride_harmonics as old
from token_row_stride import stride_scores

LO, HI, HEAD, N = 5220, 6420, 32, 600 * 6420
SEED = 20261112
SAMPLES = {
    '7262': ('OM System - OM-1 Mark II - 16bit (4:3).orf',
             'd0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd', 5566, (-48, 48)),
    '7264': ('OM System - OM-1 Mark II - 16bit (4:3).ori',
             'd7fea34029b9926e7d9cf6ecdfef9de90cbda41ff6eea009cc1a4f5b1813b8df', 5578, (-49, 42)),
    '7266': ('OM System - OM-1 Mark II - 16bit (4:3).ori',
             '1c994e4bf5aa4e48d6ec97a1f83558184a866f71bca2b5b1bf914a159927e199', 5631, (-45, 63)),
}
PHASES = {'discovery': ('7262',), 'verification': ('7262', '7264', '7266')}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'invalid command line; use --help\n')


def histogram(q, period):
    head, rest = collections.Counter(), collections.Counter()
    for start in range(0, len(q), period):
        head.update(q[start:start + HEAD])
        rest.update(q[start + HEAD:start + period])
    return {'head': dict(sorted(head.items())), 'rest': dict(sorted(rest.items())),
            'head_count': sum(head.values()), 'rest_count': sum(rest.values())}


def summarize(q, rows, period, offsets):
    scores = stride_scores(q, LO, HI, rows, HEAD)
    if (len(scores) != HI - LO + 1 or
            any(nrow != rows or not math.isfinite(z) or not math.isfinite(e)
                for z, e, _, nrow in scores)):
        return {'status': 'unknown_nonfinite_or_empty'}
    accepted_best, secondary = old.picks(scores, 4.0, 32, 8)
    ranks = {item[2]: i + 1 for i, item in enumerate(scores)}
    best = scores[0]
    peaks = [{'stride': s, 'z': z, 'rank': ranks[s]} for s, z in secondary]
    bands = []
    for off in offsets:
        candidates = [item for item in scores if abs(item[2] - (period + off)) <= 2]
        if not candidates:
            return {'status': 'unknown_target_band'}
        best_band = candidates[0]
        bands.append({'offset': off, 'stride': best_band[2], 'z': best_band[0],
                      'rank': ranks[best_band[2]]})
    match = (accepted_best is not None and abs(accepted_best - period) <= 2 and
             all(any(abs(p['stride'] - (period + off)) <= 2 for p in peaks) for off in offsets))
    return {'status': 'ok', 'best': {'stride': best[2], 'z': best[0],
                                     'elevation': best[1], 'rows': best[3]},
            'accepted_primary': accepted_best, 'secondary': peaks, 'pair_match': match,
            'scored_count': len(scores), 'target_bands': bands}


def experiment(q, period, offsets):
    if len(q) != N:
        raise ValueError('short candidate prefix')
    fixed = old.synthetic(q, period, HEAD, SEED, N)
    shuffled = old.shuffled(q, SEED)
    reports = []
    for rows in (150, 300, 600):
        length = rows * HI
        real = q[:length]
        resampled = old.synthetic(real, period, HEAD, SEED, length)
        streams = {'real': real, 'fixed_support': fixed[:length],
                   'fixed_shuffle': shuffled[:length], 'old_refit': resampled}
        report = {'rows': rows, 'tokens': length,
                  'results': {key: summarize(value, rows, period, offsets)
                              for key, value in streams.items()}}
        if rows == 600:
            report['full_support_surrogate_equals_old_refit'] = fixed == resampled
        reports.append(report)
    return {'support': histogram(q, period), 'extents': reports}


def main():
    ap = SafeParser(description=__doc__)
    ap.add_argument('--phase', choices=tuple(PHASES), required=True,
                    help='verification adds 7264 and 7266')
    ap.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'),
                    help='path to a verified CC0 file; supply 7262 first')
    args = ap.parse_args()
    if tuple(x[0] for x in args.sample) != PHASES[args.phase]:
        ap.error('frozen sample order required')
    results = []
    for sid, path in args.sample:
        name, digest, period, offsets = SAMPLES[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as stream:
                data = stream.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('identity mismatch')
            w, h, payload = old.T.locate_data(data)
            if (w, h) != (5220, 3912):
                raise ValueError('geometry mismatch')
            q = array.array('B')
            marks, endpoint = old.T.scan(payload, N, 150 * HI, 0, None, q, array.array('B'), 40)
            if len(q) != N:
                raise ValueError('short candidate prefix')
            if len(marks) != 4 or marks[0] != 0:
                raise ValueError('missing candidate endpoints')
            row.update(status='ok', payload_bytes=len(payload), bits_consumed=endpoint,
                       extent_endpoints={'150': marks[1], '300': marks[2], '600': endpoint},
                       period=period, offsets=offsets, **experiment(q, period, offsets))
            if any(cell['status'] != 'ok' for extent in row['extents']
                   for cell in extent['results'].values()):
                row['status'] = 'unknown_nonfinite_or_empty'
            if not row['extents'][-1]['full_support_surrogate_equals_old_refit']:
                row['status'] = 'unknown_surrogate_mismatch'
        except (OSError, ValueError, IndexError, KeyError, struct.error) as exc:
            row.update(status='unknown', error_type=type(exc).__name__)
        results.append(row)
    print(json.dumps({'phase': args.phase, 'results': results}, allow_nan=False))
    return int(any(row['status'] != 'ok' for row in results))


if __name__ == '__main__':
    sys.exit(main())
