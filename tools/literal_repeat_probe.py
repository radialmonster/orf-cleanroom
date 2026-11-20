#!/usr/bin/env python3
"""Bounded literal periodic-template description for #339, not a codec."""
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_tokens import locate_data
from strip_contiguity_audit import audit
from value_map_probe import PrivateArgumentParser

WINDOW = 65536
OFFSETS = {'discovery': (1048576, 2097152), 'verification': (1048576, 2097152, 3145728, 4194304)}
SAMPLES = {
    'PA210010.ORF': 'd055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e',
    'PA200010.ORF': 'b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4',
}
LOOKUP = tuple(format(i, '08b') for i in range(256))


def bit_string(data):
    return ''.join(map(LOOKUP.__getitem__, data))


def template_for(bits, start, period):
    template = ['0'] * period
    for offset in range(period):
        part = bits[offset::period]
        if part.count('1') * 2 > len(part):
            template[(start + offset) % period] = '1'
    return ''.join(template)


def description(data, start, template, chunk_bytes=65536):
    length = len(data) * 8
    p = len(template)
    if not 1 <= p <= 256 or start < 0 or start >= 2**64 or length >= 2**32:
        raise ValueError('descriptor bounds')
    previous, exceptions, gap_bits = -1, 0, 0
    for pos in range(0, len(data), chunk_bytes):
        bits = bit_string(data[pos:pos + chunk_bytes])
        shift = (start + 8 * pos) % p
        repeated = (template[shift:] + template * ((len(bits) + p - 1) // p))[:len(bits)]
        diff = format(int(bits, 2) ^ int(repeated, 2), '0%db' % len(bits))
        index = diff.find('1')
        while index >= 0:
            absolute = 8 * pos + index
            gap = absolute - previous
            gap_bits += 2 * gap.bit_length() - 1
            exceptions += 1
            previous = absolute
            index = diff.find('1', index + 1)
    if exceptions >= 2**32:
        raise ValueError('exception count overflow')
    unpadded = 136 + p + gap_bits
    return {'start_bit': start, 'length_bits': length, 'period': p,
            'exception_count': exceptions, 'gap_bits': gap_bits,
            'unpadded_bits': unpadded, 'padding_bits': (-unpadded) % 8,
            'charged_bits': unpadded + (-unpadded) % 8,
            'saves_bits': length - (unpadded + (-unpadded) % 8),
            'charged_over_raw': (unpadded + (-unpadded) % 8) / length if length else None}


def fit(data, start):
    bits = bit_string(data)
    records = []
    best = None
    for period in range(1, 257):
        template = template_for(bits, start, period)
        result = description(data, start, template)
        records.append(result['charged_bits'])
        key = (result['charged_bits'], period)
        if best is None or key < best[0]:
            best = (key, template)
    return best[1], records


def intervals(payload, template, phase):
    offsets = OFFSETS[phase]
    if len(payload) < max(offsets) + WINDOW:
        raise ValueError('short heldout interval')
    out = {'windows': [{'offset_bytes': x, **description(payload[x:x+WINDOW], x*8, template)} for x in offsets],
           'whole': description(payload, 0, template),
           'startup': description(payload[:WINDOW], 0, template),
           'tail': description(payload[-WINDOW:], (len(payload)-WINDOW)*8, template)}
    return out


def snapshot(name, path):
    with open(path, 'rb') as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != SAMPLES[name]:
        raise ValueError('identity mismatch')
    g = audit(data)
    if g['strip_count'] != 1:
        raise ValueError('single strip required')
    w, h, payload = locate_data(data)
    if (w, h, len(payload)) != (g['width'], g['height'], g['payload_bytes']):
        raise ValueError('locator disagreement')
    return w, h, payload


def main():
    ap = PrivateArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    ap.add_argument('--sample', nargs=2, action='append', required=True, metavar=('NAME', 'PATH'))
    args = ap.parse_args()
    names = tuple(SAMPLES) if args.phase == 'verification' else ('PA210010.ORF',)
    if tuple(x[0] for x in args.sample) != names:
        ap.error('samples must match frozen order')
    try:
        paths = dict(args.sample)
        w, h, white = snapshot('PA210010.ORF', paths['PA210010.ORF'])
        if len(white) < 2 * WINDOW:
            raise ValueError('short training interval')
        template, costs = fit(white[WINDOW:2*WINDOW], WINDOW*8)
        output = {'phase': args.phase, 'training': {'offset_bytes': WINDOW, 'length_bytes': WINDOW,
                  'costs_period_1_to_256': costs, 'selected_period': len(template),
                  'template_sha256_ascii_bits': hashlib.sha256(template.encode('ascii')).hexdigest()}, 'samples': []}
        for name in names:
            try:
                sw, sh, data = (w, h, white) if name == 'PA210010.ORF' else snapshot(name, paths[name])
                output['samples'].append({'name': name, 'sha256': SAMPLES[name], 'width': sw, 'height': sh,
                                          'payload_bytes': len(data), 'status': 'ok', 'records': intervals(data, template, args.phase)})
            except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
                output['samples'].append({'name': name, 'status': 'unknown', 'error_type': type(exc).__name__})
        white_result = output['samples'][0]
        output['discovery_window_decision'] = (
            all(row['charged_bits'] < row['length_bits']
                for row in white_result['records']['windows'][:2])
            if white_result['status'] == 'ok' else None)
        sources = {}
        for name in ('literal_repeat_probe.py', 'orf_tokens.py', 'orf_signature.py', 'strip_contiguity_audit.py', 'value_map_probe.py'):
            with open(os.path.join(os.path.dirname(__file__), name), 'rb') as f:
                sources[name] = hashlib.sha256(f.read()).hexdigest()
        output['source_sha256'] = sources
        print(json.dumps(output, allow_nan=False))
        return int(any(x['status'] != 'ok' for x in output['samples']))
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
        print(json.dumps({'status': 'unknown_training', 'error_type': type(exc).__name__}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
