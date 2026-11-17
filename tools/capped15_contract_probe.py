#!/usr/bin/env python3
"""Test one fixed A15/D12/k5 whole-strip contract; aggregate JSON only.

JP4468858B2 paragraphs 0055-0057 and 0071-0074 describe the branches and
second-embodiment marker. D12/A15, marker-at-zero, N and strict end are
post-hoc hypotheses, not established camera syntax. Timeout is unknown.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff

SAMPLES = {
    '1993': ('Olympus - E-M1MarkII - 16bit (4:3).ORF', '0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8'),
    '1995': ('Olympus - E-M1MarkII - 16bit (4:3).ORI', '8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f'),
    '1997': ('Olympus - E-M1MarkII - 16bit (4:3).ORI', '89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a'),
}
PHASES = {'discovery': ('1993', '1995'), 'verification': ('1993', '1995', '1997')}
N = 5240 * 3912


def locate(data):
    candidates = []
    for tags in Tiff(data).all_ifds():
        counts = tags.get(0x117)
        if 0x117 in tags and (not isinstance(counts, list) or not counts or
                              any(type(c) is not int or c <= 0 for c in counts)):
            raise ValueError('invalid strip counts')
        if counts:
            candidates.append((sum(counts), tags))
    if not candidates:
        raise ValueError('no strip IFD')
    maximum = max(size for size, _ in candidates)
    winners = [tags for size, tags in candidates if size == maximum]
    if len(winners) != 1:
        raise ValueError('ambiguous IFD')
    tags = winners[0]
    offsets, counts = tags.get(0x111), tags.get(0x117)
    if not isinstance(offsets, list) or len(offsets) != 1 or len(counts) != 1:
        raise ValueError('not one strip')
    if tags.get(0x100) != [5240] or tags.get(0x101) != [3912]:
        raise ValueError('unexpected dimensions')
    off, size = offsets[0], counts[0]
    if type(off) is not int or off < 0 or off + size > len(data):
        raise ValueError('invalid extent')
    return memoryview(data)[off:off + size], off


def scan(payload, n):
    if n < 0:
        raise ValueError('negative word count')
    size = len(payload) * 8
    if size < 40:
        return {'status': 'truncated_marker', 'payload_bits': size, 'completed': 0}
    if bytes(payload[:5]) != b'\x00\x00\x00\x00\x01':
        return {'status': 'marker_mismatch', 'payload_bits': size, 'completed': 0}
    data = bytes(payload) + b'\x00' * 5
    pos = 40
    ordinary = escapes = qsum = 0
    for i in range(n):
        start = pos
        word = (int.from_bytes(data[pos >> 3:(pos >> 3) + 5], 'big') << (pos & 7)) & ((1 << 40) - 1)
        q = min(15, 40 - word.bit_length())
        if q == 15 and size - start < 15:
            status, examined = 'truncated_ordinary', size
            break
        if q < 15:
            end = start + q + 6
            if end > size:
                status, examined = 'truncated_ordinary', size
                break
            ordinary += 1
            qsum += q
        else:
            end = start + 27
            if end > size:
                status, examined = 'truncated_escape', size
                break
            value = (word >> 13) & 4095
            if value >> 5 < 15:
                status, examined = 'invalid_escape', end
                break
            escapes += 1
        pos = end
    else:
        i = n
        status = 'strict_end' if pos == size else 'remaining_bits'
    if pos != 40 + 6 * i + qsum + 21 * escapes:
        raise AssertionError('completed endpoint invariant failed')
    out = {'status': status, 'payload_bits': size, 'N': n, 'completed': i,
           'ordinary': ordinary, 'escapes': escapes, 'ordinary_q_sum': qsum,
           'completed_endpoint': pos, 'unread_bits': size - pos}
    if i < n:
        out.update(word_start=start, examined_position=examined)
        if status == 'invalid_escape':
            out['invalid_value'] = value
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=sorted(PHASES), required=True)
    ap.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'))
    args = ap.parse_args()
    if tuple(x[0] for x in args.sample) != PHASES[args.phase]:
        ap.error('samples must match the frozen phase in order')
    results = []
    for sample_id, path in args.sample:
        name, digest = SAMPLES[sample_id]
        try:
            with open(path, 'rb') as f:
                data = f.read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('hash mismatch')
            payload, offset = locate(data)
            result = {'id': sample_id, 'name': name, 'sha256': digest,
                      'offset': offset, 'width': 5240, 'height': 3912,
                      'measurement': scan(payload, N)}
        except (ValueError, TypeError, IndexError, KeyError, OSError, struct.error) as exc:
            result = {'id': sample_id, 'name': name,
                      'measurement': {'status': 'unknown', 'error_type': type(exc).__name__}}
        results.append(result)
    print(json.dumps({'phase': args.phase, 'results': results}, sort_keys=True))
    return int(any(r['measurement']['status'] == 'unknown' for r in results))


if __name__ == '__main__':
    sys.exit(main())
