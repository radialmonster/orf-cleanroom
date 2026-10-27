#!/usr/bin/env python3
"""Conditional block-rotation control for #144, building on #508.

Full joint and fixed-period training searches precede common-interval scoring.
References are descriptive, not calibrated significance or physical rows.
Block seams and the 5240-token partition affect the reference distribution.
Prints aggregate JSON only; checks the supplied hash before parsing.
"""
import argparse
from array import array
from fractions import Fraction
import hashlib
import json
import random
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_band_profile as B

ANCHOR, CENTER, RADIUS, ROWS, HEAD = 10480000, 5240, 64, 100, 32
SEED = 20261027


def draw(rng, n):
    bits = n.bit_length()
    while True:
        value = rng.getrandbits(bits)
        if value < n:
            return value


def rotate(qs, start, barrier, end, block, rng):
    result = array('B', qs)
    shifts = []
    for left, right in ((start, barrier), (barrier, end)):
        for pos in range(left, right, block):
            n = min(block, right - pos)
            shift = draw(rng, n)
            segment = qs[pos:pos + n]
            result[pos:pos + n] = segment[shift:] + segment[:shift]
            shifts.append({'start': pos, 'length': n, 'shift': shift})
    return result, shifts


def fit(qs, anchor, center, radius, rows, head):
    lo, hi = center - radius, center + radius
    barrier = anchor + (rows + 2) * hi
    end = barrier + rows * lo
    if lo <= head or head < 1 or rows < 1 or anchor < 0 or len(qs) < end:
        raise ValueError('incomplete or invalid design')
    prefix = array('Q', [0])
    total = 0
    for q in memoryview(qs)[anchor:end]:
        total += q
        prefix.append(total)
    joint = fixed = None
    for stride in range(lo, hi + 1):
        best = None
        for phase in range(stride):
            hs = rs = 0
            for row in range(rows):
                i = phase + row * stride
                hs += prefix[i + head] - prefix[i]
                rs += prefix[i + stride] - prefix[i]
            num = stride * hs - head * rs
            if best is None or num > best[0]:
                best = (num, rows * head * (stride - head), stride, phase)
        if stride == center:
            fixed = best
        if joint is None or best[0] * joint[1] > joint[0] * best[1]:
            joint = best

    def score(choice):
        num, den, stride, phase = choice
        start = anchor + phase + ((barrier - anchor - phase) // stride) * stride
        hs = hc = 0
        while start < end:
            left, right = max(start, barrier), min(start + head, end)
            if right > left:
                hs += prefix[right - anchor] - prefix[left - anchor]
                hc += right - left
            start += stride
        rc = end - barrier - hc
        rs = prefix[end - anchor] - prefix[barrier - anchor] - hs
        contrast = Fraction(hs, hc) - Fraction(rs, rc) if hc and rc else None
        return {'stride': stride, 'phase': phase, 'training_numerator': num,
                'training_denominator': den, 'head_sum': hs, 'head_count': hc,
                'rest_sum': rs, 'rest_count': rc, 'contrast': rational(contrast)}, contrast
    j, jscore = score(joint)
    f, fscore = score(fixed)
    difference = jscore - fscore if jscore is not None and fscore is not None else None
    return j, f, difference


def rational(value):
    return None if value is None else {'numerator': value.numerator, 'denominator': value.denominator}


def control(qs, anchor, center, radius, rows, head, replicates, seed=SEED):
    barrier = anchor + (rows + 2) * (center + radius)
    end = barrier + rows * (center - radius)
    joint, fixed, observed = fit(qs, anchor, center, radius, rows, head)
    rng = random.Random(seed)
    out = []
    for index in range(replicates):
        rotated, shifts = rotate(qs, anchor, barrier, end, center, rng)
        j, f, diff = fit(rotated, anchor, center, radius, rows, head)
        out.append({'index': index, 'shifts': shifts, 'joint': j, 'fixed': f,
                    'difference': rational(diff), 'comparison': None if diff is None or observed is None
                    else ('greater' if diff > observed else 'equal' if diff == observed else 'less')})
    return {'anchor': anchor, 'barrier': barrier, 'end_exclusive': end,
            'center': center, 'radius': radius, 'rows': rows, 'head': head,
            'seed': seed, 'draw_algorithm': 'Random.getrandbits(n.bit_length()), reject >= n',
            'draw_order': 'replicate, training blocks, test blocks; increasing start',
            'observed': {'joint': joint, 'fixed': fixed, 'difference': rational(observed)},
            'replicates': out, 'undefined_count': sum(r['difference'] is None for r in out),
            'greater_equal_count': (sum(r['comparison'] in ('greater', 'equal') for r in out)
                                    if observed is not None else None),
            'equal_count': (sum(r['comparison'] == 'equal' for r in out)
                            if observed is not None else None)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sample', nargs=4, required=True, metavar=('ID', 'PUBLIC_NAME', 'SHA256', 'FILE'))
    ap.add_argument('--replicates', type=int, default=16)
    a = ap.parse_args(argv)
    sid, name, digest, path = a.sample
    if (not sid.isascii() or not sid.isdecimal() or not sid.strip('0') or not name or
            not name.isprintable() or any(c in name for c in '/\\') or len(digest) != 64 or
            any(c not in '0123456789abcdef' for c in digest) or a.replicates < 1):
        ap.error('invalid public identity, hash or replicate count')
    try:
        with open(path, 'rb') as f:
            data = f.read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('hash mismatch')
        best = max(B.Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
        width, height = best[0x100][0], best[0x101][0]
        offsets, sizes = best[0x111], best[0x117]
        if (width <= 0 or height <= 0 or len(offsets) != 1 or len(sizes) != 1 or
                offsets[0] < 0 or sizes[0] <= 0 or offsets[0] + sizes[0] > len(data) or
                B.size_class(sizes[0], width, height) != 'variable'):
            raise ValueError('unsupported container')
        end = ANCHOR + (ROWS + 2) * (CENTER + RADIUS) + ROWS * (CENTER - RADIUS)
        qs, bits = B.scan_q(data[offsets[0]:offsets[0] + sizes[0]], end)
        result = control(qs, ANCHOR, CENTER, RADIUS, ROWS, HEAD, a.replicates)
        result.update(pixls_id=sid, pixls_name=name, sha256=digest, parsed_tokens=len(qs),
                      consumed_bits=bits, python_version=sys.version.split()[0])
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
        print(json.dumps({'pixls_id': sid, 'complete': False, 'error': type(exc).__name__}))
        return 1
    result['complete'] = True
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
