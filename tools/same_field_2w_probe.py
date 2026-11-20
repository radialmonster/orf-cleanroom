#!/usr/bin/env python3
"""Fixed disjoint-band same-field 2W comparison; descriptive, not framing."""
import argparse
import hashlib
import json
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_tokens import locate_data
from suffix_joint_probe import scan_prefix
from token_width_context_probe import score_tables

BAND = 262144
SAMPLES = {
    '1993': ('Olympus - E-M1MarkII - 16bit (4:3).ORF', '0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8', 5240, 3912),
    '5283': ('OM System - OM-1 - 16bit (4:3).ORF', 'bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b', 5220, 3912),
    '1995': ('Olympus - E-M1MarkII - 16bit (4:3).ORI', '8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f', 5240, 3912),
    '6343': ('OM System - OM-5 - 16bit (4:3).ORF', 'ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7', 5240, 3912),
}
PHASES = {'discovery': ('1993', '5283'), 'verification': ('1993', '5283', '1995', '6343')}


def measure(tokens, width, band_index, band_size=BAND):
    if width <= 128 or 2 * width + 128 >= band_size:
        raise ValueError('incompatible width')
    start, end = band_index * band_size, (band_index + 1) * band_size
    if len(tokens) < end:
        raise ValueError('short input')
    donors = (2 * width, 2 * width - 128, 2 * width + 128)
    offsets = (0, 1, 2, 3, 4, 5) + donors
    counts = {field: [[[0, 0] for _ in range(n)] for n in (32, 64, 64, 64)]
              for field in ('q_positive', 'suffix_b0')}
    omitted = 0
    candidate = band_size - (2 * width + 128)
    for t in range(start + 2 * width + 128, end):
        if any(tokens[t - lag][0] >= 17 for lag in offsets):
            omitted += 1
            continue
        for field in counts:
            def bit(idx):
                q, s = tokens[idx]
                return int(q > 0) if field == 'q_positive' else s & 1
            ctx = 0
            for lag in (1, 2, 3, 4, 5):
                ctx = (ctx << 1) | bit(t - lag)
            y = bit(t)
            counts[field][0][ctx][y] += 1
            for j, lag in enumerate(donors, 1):
                counts[field][j][(ctx << 1) | bit(t - lag)][y] += 1
    return {'band': band_index, 'start': start, 'end': end,
            'target_start': start + 2 * width + 128, 'candidate': candidate,
            'omitted': omitted, 'retained': candidate - omitted,
            'required_offsets': list(offsets), 'duplicate_offsets': len(set(offsets)) != len(offsets),
            'tables': counts}


def pair(train, test, width):
    rows = []
    donors = (2 * width, 2 * width - 128, 2 * width + 128)
    for field in ('q_positive', 'suffix_b0'):
        baseline = None
        for idx, name in enumerate(('local', '2w', '2w_minus_128', '2w_plus_128')):
            a, b = train['tables'][field][idx], test['tables'][field][idx]
            scored = score_tables(a, b)
            valid = bool(scored['training_targets'] and scored['test_targets'])
            if not valid:
                scored['heldout_log_loss_bits'] = None
            if idx == 0 and valid:
                baseline = scored['heldout_log_loss_bits']
            scored.update(field=field, model=name, taps=[1, 2, 3, 4, 5] + ([] if idx == 0 else [donors[idx - 1]]),
                          train_context_by_outcome=a, test_context_by_outcome=b,
                          status='ok' if valid else 'unknown',
                          gain_vs_local_bits=(baseline - scored['heldout_log_loss_bits']) if valid and baseline is not None else None)
            rows.append(scored)
    return rows


def report(sample_id, path, phase):
    name, expected, width, height = SAMPLES[sample_id]
    t0 = time.monotonic()
    with open(path, 'rb') as handle:
        data = handle.read()
    if hashlib.sha256(data).hexdigest() != expected:
        return {'id': sample_id, 'name': name, 'status': 'unknown', 'reason': 'identity_mismatch'}
    w, h, payload = locate_data(data)
    if (w, h) != (width, height):
        return {'id': sample_id, 'name': name, 'status': 'unknown', 'reason': 'geometry_mismatch'}
    bands = 3 if phase == 'verification' else 2
    tokens, end = scan_prefix(payload, bands * BAND)
    if len(tokens) != bands * BAND:
        return {'id': sample_id, 'name': name, 'sha256': expected, 'width': w, 'height': h,
                'payload_bytes': len(payload),
                'requested_tokens': bands * BAND, 'returned_tokens': len(tokens),
                'bits_consumed': end, 'status': 'unknown', 'reason': 'short_input'}
    endpoints, offset = [], 0
    for i in range(bands):
        offset += sum(q + 6 for q, _ in tokens[i * BAND:(i + 1) * BAND])
        endpoints.append(offset)
    if offset != end:
        raise ValueError('scanner endpoint mismatch')
    results = {str(i): measure(tokens, w, i, BAND) for i in range(bands)}
    for i in range(bands):
        results[str(i)]['end_bit_exclusive'] = endpoints[i]
    indices = (1,) if phase == 'discovery' else ((1, 2) if sample_id in ('1993', '5283') else (2,))
    pairs = {str(i): pair(results['0'], results[str(i)], w) for i in indices}
    for item in results.values():
        del item['tables']
    return {'id': sample_id, 'name': name, 'sha256': expected, 'width': w, 'height': h,
            'payload_bytes': len(payload),
            'requested_tokens': bands * BAND, 'returned_tokens': len(tokens), 'bits_consumed': end,
            'bands': results, 'pairs': pairs, 'runtime_seconds': time.monotonic() - t0}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=sorted(PHASES), required=True)
    ap.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'))
    args = ap.parse_args()
    if tuple(x[0] for x in args.sample) != PHASES[args.phase]:
        ap.error('sample order must match phase')
    results = []
    for sid, path in args.sample:
        try:
            r = report(sid, path, args.phase)
            if 'status' not in r:
                r['status'] = 'ok' if all(row['status'] == 'ok' for rows in r['pairs'].values() for row in rows) else 'unknown'
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            r = {'id': sid, 'name': SAMPLES[sid][0], 'status': 'unknown', 'error_type': type(exc).__name__}
        results.append(r)
    names = ('same_field_2w_probe.py', 'suffix_joint_probe.py', 'token_width_context_probe.py', 'orf_tokens.py', 'orf_signature.py')
    sources = {}
    for name in names:
        with open(os.path.join(os.path.dirname(__file__), name), 'rb') as handle:
            sources[name] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({'phase': args.phase, 'python_version': sys.version.split()[0],
                      'source_sha256': sources, 'samples': results}, allow_nan=False))
    return int(any(r['status'] != 'ok' for r in results))


if __name__ == '__main__':
    sys.exit(main())
