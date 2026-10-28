#!/usr/bin/env python3
"""Test two fixed capped-prefix hypotheses from US7259698B2; aggregate only.

A marker is required at payload bit zero: 47 zeros then 1 for D=15,
39 zeros then 1 for exploratory D=12. Both use k=5 and max_prefix=12.
The marker ends at the 1; it is not a k=5 token. No interior marker,
resynchronization, padding interpretation, image reconstruction or adaptive
parameter fitting is attempted. An invalid escape rejects only this fixed
parse. Input identity and expected SHA-256 must be verified CC0 before use.
"""
import argparse
import hashlib
import json
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_tokens import locate_data


def parse(payload, width, limit=None):
    if width not in (12, 15) or (limit is not None and limit < 1):
        raise ValueError('unsupported parameter')
    nbits = len(payload) * 8
    marker_zeros = 8 * ((12 + 2 * width) // 8) + 7
    marker_len = marker_zeros + 1
    def bit(i):
        return (payload[i >> 3] >> (7 - (i & 7))) & 1
    def value(start, count):
        v = 0
        for i in range(start, start + count):
            v = (v << 1) | bit(i)
        return v
    out = {'D': width, 'k': 5, 'max_prefix': 12, 'payload_bits': nbits,
           'marker_bits': marker_len, 'marker_matches': False, 'words': 0,
           'ordinary_words': 0, 'escape_words': 0, 'consumed_bits': 0,
           'residual_bits': nbits, 'stop': 'marker_missing',
           'stop_at_bits': 0, 'invalid_escape_value': None}
    if nbits < marker_len or any(bit(i) for i in range(marker_zeros)) or not bit(marker_zeros):
        return out
    out['marker_matches'] = True
    pos = marker_len
    out['consumed_bits'] = pos
    while pos < nbits and (limit is None or out['words'] < limit):
        q = 0
        while q < 12 and pos < nbits and bit(pos) == 0:
            q += 1
            pos += 1
        if q < 12:
            if pos >= nbits or pos + 1 + 5 > nbits:
                out['stop'] = 'truncated_ordinary'
                break
            pos += 1 + 5
            out['ordinary_words'] += 1
        else:
            if pos + width > nbits:
                out['stop'] = 'truncated_escape'
                break
            v = value(pos, width)
            if v >> 5 < 12:
                out['invalid_escape_value'] = v
                out['stop'] = 'invalid_escape'
                break
            pos += width
            out['escape_words'] += 1
        out['words'] += 1
        out['consumed_bits'] = pos
    else:
        out['stop'] = 'end' if pos == nbits else 'limit'
    out['stop_at_bits'] = out['consumed_bits']
    out['residual_bits'] = nbits - out['consumed_bits']
    return out


def shuffled_tail(payload, width, seed):
    """Keep the fixed marker bytes and shuffle all following bytes once."""
    marker_bytes = (8 * ((12 + 2 * width) // 8) + 8) // 8
    prefix = payload[:marker_bytes]
    tail = bytearray(payload[marker_bytes:])
    random.Random(seed).shuffle(tail)
    return prefix + bytes(tail)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sample', nargs=4, action='append', required=True,
                    metavar=('PUBLIC_ID', 'PUBLIC_NAME', 'SHA256', 'PATH'))
    ap.add_argument('--width', required=True, type=int, choices=(12, 15))
    ap.add_argument('--max-words', type=int)
    ap.add_argument('--tail-shuffle', action='store_true',
                    help='preserve marker bytes and shuffle all remaining payload bytes')
    ap.add_argument('--seed', type=int, default=20261022)
    args = ap.parse_args(argv)
    if args.max_words is not None and args.max_words < 1:
        ap.error('--max-words must be positive')
    ids, hashes, results = set(), set(), []
    for ident, name, digest, path in args.sample:
        if (not ident or not name or any(c in name for c in '/\\') or
            not all(c.isprintable() for c in ident + name) or
            len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest) or
            ident in ids or digest in hashes):
            ap.error('invalid or duplicate public identity/hash')
        ids.add(ident); hashes.add(digest)
        row = {'id': ident, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as f:
                data = f.read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('hash_mismatch')
            w, h, payload = locate_data(data)
            measured = shuffled_tail(payload, args.width, args.seed) if args.tail_shuffle else payload
            row.update(status='ok', width=w, height=h, mode='tail_shuffle' if args.tail_shuffle else 'real',
                       seed=args.seed if args.tail_shuffle else None,
                       measured_payload_sha256=hashlib.sha256(measured).hexdigest(),
                       parse=parse(measured, args.width, args.max_words))
        except (OSError, ValueError, TypeError, IndexError, KeyError, struct.error) as e:
            row.update(status='error', error=type(e).__name__)
        results.append(row)
    complete = all(row['status'] == 'ok' for row in results)
    print(json.dumps({'complete': complete, 'results': results}, indent=2))
    return 0 if complete else 1


if __name__ == '__main__':
    sys.exit(main())
