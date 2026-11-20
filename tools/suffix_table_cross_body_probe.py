#!/usr/bin/env python3
"""Frozen #155 suffix-table transfer to other bodies; aggregate only."""
import argparse
import array
import hashlib
import json
import math
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_value_probe as legacy
import jpeg_dc
from suffix_table_shift_probe import fitted_table

ROWS = 600
MAX_BYTES = 128 * 1024 * 1024
SAMPLES = {
    '1995': ('Olympus - E-M1MarkII - 16bit (4:3).ORI',
             '8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f', 5240, 3912),
    '1997': ('Olympus - E-M1MarkII - 16bit (4:3).ORI',
             '89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a', 5240, 3912),
    '3800': ('Olympus - E-M1MarkIII - 16bit (4:3).ORF',
             '1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f', 5240, 3912),
    '6343': ('OM System - OM-5 - 16bit (4:3).ORF',
             'ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7', 5240, 3912),
    '3801': ('Olympus - E-M1MarkIII - 16bit (4:3).ORF',
             'e9a21175493e9d9e5653aa91f1bd6fbf421aba42b59b4ffe7cd1f7cac2de385c', 8200, 6132),
    '5283': ('OM System - OM-1 - 16bit (4:3).ORF',
             'bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b', 5220, 3912),
}
PHASES = {'discovery': ('1997', '3800', '6343'),
          'verification': ('1997', '3800', '6343', '3801', '5283')}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'invalid command line; use --help\n')


def validate_preview_sampling(data):
    """Check that the selected JPEG can use the repository's DC grid order."""
    if data[:2] != b'\xff\xd8' or data[-2:] != b'\xff\xd9':
        raise ValueError('incomplete JPEG')
    i = 2
    frame = None
    quantizers = {}
    while i + 4 <= len(data):
        if data[i] != 255:
            raise ValueError('invalid JPEG marker')
        while i < len(data) and data[i] == 255:
            i += 1
        if i >= len(data):
            break
        marker = data[i]
        i += 1
        if marker in (0xd8, 0xd9) or 0xd0 <= marker <= 0xd7:
            break
        if i + 2 > len(data):
            break
        size = int.from_bytes(data[i:i + 2], 'big')
        if size < 2 or i + size > len(data):
            break
        segment = data[i + 2:i + size]
        if marker == 0xc0:
            if len(segment) < 6 or segment[5] < 1 or len(segment) != 6 + 3 * segment[5]:
                break
            sampling = [segment[7 + 3 * j] for j in range(segment[5])]
            pairs = [(v >> 4, v & 15) for v in sampling]
            if any(h == 0 or v == 0 for h, v in pairs):
                break
            if pairs[0][0] != max(h for h, _ in pairs) or pairs[0][1] != max(v for _, v in pairs):
                raise ValueError('first component is not full sampling')
            if frame is not None or segment[0] != 8:
                raise ValueError('unsupported frame')
            frame = {'pixel_width': (segment[3] << 8) | segment[4],
                     'pixel_height': (segment[1] << 8) | segment[2],
                     'component_ids': [segment[6 + 3 * j] for j in range(segment[5])],
                     'sampling': pairs, 'first_quantizer': segment[8]}
            if (not frame['pixel_width'] or not frame['pixel_height'] or
                    len(set(frame['component_ids'])) != len(frame['component_ids'])):
                raise ValueError('invalid frame geometry or components')
        elif marker == 0xdb:
            pos = 0
            while pos < len(segment):
                descriptor = segment[pos]
                precision = descriptor >> 4
                if precision not in (0, 1):
                    raise ValueError('unsupported quantizer')
                n = 1 if precision == 0 else 2
                end = pos + 1 + 64 * n
                if end > len(segment):
                    raise ValueError('truncated quantizer')
                quantizers[descriptor & 15] = int.from_bytes(segment[pos + 1:pos + 1 + n], 'big')
                pos = end
        elif marker == 0xda:
            if frame is None or not segment or len(segment) != 4 + 2 * segment[0]:
                break
            scan_ids = list(segment[1:-3:2])
            if scan_ids != frame['component_ids'] or segment[-3:] != bytes((0, 63, 0)):
                raise ValueError('unsupported component scan')
            dc_quantizer = quantizers.get(frame['first_quantizer'])
            if not dc_quantizer:
                raise ValueError('missing DC quantizer')
            frame['dc_quantizer_value'] = dc_quantizer
            frame['convention'] = 'un-dequantized first-component DC'
            return frame
        i += size
    raise ValueError('invalid baseline frame')


def load(sample_id, path, samples=None):
    if samples is None:
        samples = SAMPLES
    name, expected, width, height = samples[sample_id]
    with open(path, 'rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('input too large')
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('identity mismatch')
    selected = jpeg_dc.find_preview(data)
    if selected is None:
        raise ValueError('no baseline preview')
    _, start, length, _, _ = selected
    selected_bytes = data[start:start + length]
    preview = validate_preview_sampling(selected_bytes)
    w, h, payload = legacy.T.locate_data(data)
    if (w, h) != (width, height):
        raise ValueError('geometry mismatch')
    q, s = array.array('B'), array.array('B')
    _, consumed = legacy.T.scan(payload, ROWS * w, w, 0, None, q, s, 40, None, 32)
    rows = len(s) // w
    if rows != ROWS:
        raise ValueError('row count mismatch')
    wb, hb, dc = jpeg_dc.decode(selected_bytes, 0)
    nd = max(2, min(hb, round(rows * hb / h)))
    expected_grid = ((preview['pixel_width'] + 7) // 8, (preview['pixel_height'] + 7) // 8)
    if (wb, hb) != expected_grid or nd < 2 or hb < nd or len(dc) != wb * hb:
        raise ValueError('preview geometry mismatch')
    y = legacy.row_center(dc[:nd * wb], nd, wb)
    x = legacy.features(q, s, rows, w, nd, wb, 's', intercept=False)
    info = {'id': sample_id, 'name': name, 'sha256': expected, 'width': w, 'height': h,
            'candidate_rows': rows, 'payload_bytes': len(payload), 'bits_consumed': consumed,
            'preview_width_blocks': wb,
            'preview_height_blocks': hb, 'used_preview_rows': nd, 'preview': preview}
    return x, y, q, s, info


def score(x, y, q, s, info, fit):
    r, r2 = legacy.stats(y, legacy.predict(x, fit))
    rng = random.Random(20261021)
    shuffles = []
    for _ in range(4):
        qb, sb = legacy.shuffle_pairs(q, s, ROWS, info['width'], rng)
        features = legacy.features(qb, sb, ROWS, info['width'], info['used_preview_rows'],
                                   info['preview_width_blocks'], 's', intercept=False)
        sr, sr2 = legacy.stats(y, legacy.predict(features, fit))
        shuffles.append({'r': sr, 'r2': sr2})
    if not all(math.isfinite(v) for v in [r, r2] + [z for item in shuffles for z in item.values()]):
        raise ValueError('undefined score')
    return {'r': r, 'r2': r2, 'shuffles': shuffles,
            'r_minus_shuffles': [r - item['r'] for item in shuffles],
            'positive_above_all_four': r > 0 and all(r > item['r'] for item in shuffles)}


def run(phase, train_path, sample_paths, samples, measure):
    try:
        x, y, _, _, info = load('1995', train_path, samples)
        cols = info['preview_width_blocks']
        fit_y = [v for i, v in enumerate(y) if (i // cols) % 2 == 0]
        if not all(math.isfinite(v) for v in fit_y) or len(set(fit_y)) < 2:
            raise ValueError('undefined training variance')
        fit = fitted_table(x, y, info['used_preview_rows'], info['preview_width_blocks'])
        if len(fit) != 32 or not all(math.isfinite(v) for v in fit):
            raise ValueError('invalid table')
        info['table_sha256_binary64_be'] = hashlib.sha256(struct.pack('>32d', *fit)).hexdigest()
    except (OSError, ValueError, IndexError, KeyError, TypeError, ZeroDivisionError, struct.error) as exc:
        return {'status': 'unknown_training', 'error_type': type(exc).__name__}, 1
    results = []
    for sid, path in sample_paths:
        try:
            x, y, q, s, target = load(sid, path, samples)
            result = measure(x, y, q, s, target, fit)
            results.append({'sample': target, 'status': 'ok', 'measurement': result})
        except (OSError, ValueError, IndexError, KeyError, TypeError, ZeroDivisionError, struct.error) as exc:
            results.append({'sample': {'id': sid, 'name': samples[sid][0], 'sha256': samples[sid][1]},
                            'status': 'unknown', 'error_type': type(exc).__name__})
    return {'phase': phase, 'train': info, 'results': results}, int(
        any(row['status'] != 'ok' for row in results))


def main():
    ap = SafeParser(description=__doc__)
    ap.add_argument('--phase', choices=tuple(PHASES), required=True,
                    help='verification adds 3801 and 5283')
    ap.add_argument('--train', required=True, help='path to the verified CC0 training file 1995')
    ap.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'),
                    help='verified CC0 file; first supply 1997, 3800 and 6343 in that order')
    args = ap.parse_args()
    if tuple(x[0] for x in args.sample) != PHASES[args.phase]:
        ap.error('frozen sample order required')
    report, status = run(args.phase, args.train, args.sample, SAMPLES, score)
    print(json.dumps(report, allow_nan=False))
    return status


if __name__ == '__main__':
    sys.exit(main())
