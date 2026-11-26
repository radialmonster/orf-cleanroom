"""Independent aggregate checker for #961. Candidate coordinates only."""
import argparse
from array import array
from collections import Counter
import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_start_audit import independent_strips

OCTETS = tuple(format(i, '08b') for i in range(256))
MISSING = -128


def assembled(a, b):
    x, y, n = (a >> 2) & 1, (b >> 4) & 1, 1 - ((b >> 3) & 1)
    return (a & 3) + (1 - 2*x) * (8*y - 4*n) - 12*x


def parse(payload, need):
    bits = ''.join(OCTETS[b] for b in payload[:3 * need + 16])
    start = bits.find('1')
    if start < 0:
        return None, 'missing_marker'
    pos = start + 1
    words = array('b')
    while len(words) < need and pos + 24 <= len(bits):
        q = 0
        while q < 12 and bits[pos + q] == '0':
            q += 1
        if q == 12:
            words.append(-1)
            pos += 24
        else:
            at = pos + q + 1
            words.append(int(bits[at:at + 5], 2))
            pos = at + 5
    if len(words) != need:
        return None, 'short_guarded_parse'
    return words, None


def evaluate(words, width, rows=600, null=False, top=20, edge=20):
    need = (rows + 1) * width
    if len(words) < need or width <= 2 * edge or rows <= top:
        return {'status': 'unknown', 'reason': 'insufficient_support'}
    values = array('b', [MISSING]) * need
    step = width + 1 if null else 1
    counts = Counter()
    total = total2 = total3 = skipped = 0
    class_sum, class_n = [0, 0], [0, 0]
    class_hist = [Counter(), Counter()]
    for r in range(top, rows):
        for c in range(edge, width - edge):
            i = r * width + c
            a, b = words[i], words[i + step]
            if a < 0 or b < 0:
                skipped += 1
                continue
            v = assembled(a, b)
            values[i] = v
            counts[v] += 1
            total += v
            total2 += v*v
            total3 += v*v*v
            parity = (r + c) % 2
            class_sum[parity] += v
            class_n[parity] += 1
            class_hist[parity][v] += 1
    n = sum(counts.values())
    mean = total / n if n else None
    variance = (total2 / n - mean * mean) if n else None
    sd = math.sqrt(max(0, variance)) if variance is not None else None
    skew = ((total3 / n - 3*mean*total2/n + 2*mean**3) / sd**3) if sd else None
    lags = {}
    for label, lag in [('1',1), ('2',2), ('3',3), ('4',4), ('W',width),
                       ('2W',2*width), ('2W-2',2*width-2), ('2W+2',2*width+2)]:
        pn = sx = sy = xx = yy = xy = 0
        for i in range(top * width, rows * width - lag):
            a, b = values[i], values[i + lag]
            if a == MISSING or b == MISSING:
                continue
            pn += 1; sx += a; sy += b; xx += a*a; yy += b*b; xy += a*b
        vx, vy = pn*xx-sx*sx, pn*yy-sy*sy
        lags[label] = {'pairs': pn, 'r': ((pn*xy-sx*sy)/math.sqrt(vx*vy)) if pn >= 2 and vx > 0 and vy > 0 else None,
                       'status': ('empty' if pn == 0 else 'insufficient_pairs' if pn == 1 else
                                  'ok' if vx > 0 and vy > 0 else 'zero_variance')}
    return {'status': 'ok' if n and sd else 'unknown', 'reason': None if n and sd else ('empty' if not n else 'zero_variance'),
            'valued': n, 'skipped': skipped, 'mean': mean, 'sd': sd, 'skew': skew,
            'classes': [{'count': class_n[i], 'mean': class_sum[i]/class_n[i] if class_n[i] else None,
                         'histogram': {str(v): class_hist[i][v] for v in range(-20, 12)}} for i in range(2)],
            'histogram': {str(i): counts[i] for i in range(-20, 12)}, 'lags': lags}


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, 'invalid arguments\n')
    p = SafeParser(description=__doc__)
    p.add_argument('--sample', nargs=3, required=True, metavar=('NAME', 'SHA256', 'PATH'))
    p.add_argument('--null', action='store_true')
    p.add_argument('--rows', type=int, default=600,
                   help='exclusive stop row; starts at row 20 (default 600)')
    a = p.parse_args()
    if a.rows <= 20:
        p.error('rows must exceed 20')
    name, expected, path = a.sample
    if (not name or not name.isprintable() or '/' in name or '\\' in name or
            len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected)):
        p.error('invalid public identity')
    try:
        with open(path, 'rb') as f:
            data = f.read(128 * 1024 * 1024 + 1)
        if len(data) > 128 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('size_or_hash')
        geometry, payload = independent_strips(data)
        width, height = geometry['width'], geometry['height']
        if a.rows >= height:
            raise ValueError('rows_need_partner_row')
        words, reason = parse(payload, (a.rows + 1) * width)
        result = evaluate(words, width, rows=a.rows, null=a.null) if words is not None else {'status': 'unknown', 'reason': reason}
        print(json.dumps({'name': name, 'sha256': expected, 'width': width, 'height': height,
                          'payload_bytes': len(payload), 'null': a.null, 'rows': [20, a.rows],
                          'result': result}, allow_nan=False))
        return int(result['status'] != 'ok')
    except (OSError, ValueError, IndexError, KeyError, TypeError) as exc:
        print(json.dumps({'name': name, 'sha256': expected, 'status': 'unknown', 'reason': type(exc).__name__}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
