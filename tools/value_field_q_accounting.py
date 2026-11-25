"""Account for #961's candidate field by partner quotient, not sensor meaning."""
import argparse
from array import array
from fractions import Fraction
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_start_audit import independent_strips
from value_field_independent_audit import OCTETS

WINDOWS = {'original': (20, 600), 'later': (620, 1200)}


def parse(payload, need):
    bits = ''.join(OCTETS[b] for b in payload[:3 * need + 16])
    first = bits.find('1')
    if first < 0:
        raise ValueError('missing_marker')
    pos = first + 1
    suffix, quotient = array('b'), array('b')
    while len(suffix) < need and pos + 24 <= len(bits):
        q = 0
        while q < 12 and bits[pos + q] == '0':
            q += 1
        quotient.append(q)
        if q == 12:
            suffix.append(-1)
            pos += 24
        else:
            at = pos + q + 1
            suffix.append(int(bits[at:at + 5], 2))
            pos = at + 5
    if len(suffix) != need:
        raise ValueError('short_guarded_parse')
    return suffix, quotient


def accounting(suffix, quotient, width, start, end, edge=20):
    if width <= 2 * edge or len(suffix) < end * width + 1 or len(quotient) != len(suffix):
        raise ValueError('insufficient_support')
    hist = [[0] * 32 for _ in range(2)]
    cross = [[0, 0], [0, 0]]
    terms = [0] * 6
    omitted = 0
    for row in range(start, end):
        for col in range(edge, width - edge):
            i = row * width + col
            a, b = suffix[i], suffix[i+1]
            if a < 0 or b < 0:
                omitted += 1
                continue
            x, y, n = (a >> 2) & 1, (b >> 4) & 1, 1 - ((b >> 3) & 1)
            pieces = (a & 3, 8*y, -4*n, -16*x*y, 8*x*n, -12*x)
            for k, v in enumerate(pieces):
                terms[k] += v
            value = (a & 3) + (1 - 2*x)*(8*y - 4*n) - 12*x
            g, h = int(quotient[i+1] > 0), int(quotient[i] > 0)
            hist[g][value + 20] += 1
            cross[h][g] += 1
    if sum(terms) != sum((i-20) * sum(h[i] for h in hist) for i in range(32)):
        raise ValueError('sum_invariant')
    return {'eligible': sum(map(sum, hist)), 'histograms': hist,
            'current_by_partner_q': cross, 'term_sums': terms,
            'omitted_escape': omitted}


def pooled(rows):
    return [[sum(row['histograms'][g][i] for row in rows) for i in range(32)] for g in range(2)]


def describe(hist):
    counts = [sum(h) for h in hist]
    total = sum(counts)
    if not total:
        return {'status': 'empty'}
    raw = [sum(Fraction((i-20)**k * sum(h[i] for h in hist), total) for i in range(32)) for k in (1, 2, 3)]
    mean, second, third = raw
    variance = second - mean*mean
    parts = [Fraction(0), Fraction(0), Fraction(0)]
    strata = []
    for h, count in zip(hist, counts):
        if not count:
            strata.append({'status': 'empty', 'count': 0})
            continue
        moments = [Fraction(sum((i-20)**k * v for i, v in enumerate(h)), count) for k in (1, 2, 3)]
        m, s, t = moments
        v = s - m*m
        central = t - 3*m*s + 2*m**3
        weight, offset = Fraction(count, total), m - mean
        parts[0] += weight*central
        parts[1] += weight*3*offset*v
        parts[2] += weight*offset**3
        strata.append({'status': 'ok', 'count': count, 'mean': str(m), 'variance': str(v),
                       'third_central': str(central)})
    central = third - 3*mean*second + 2*mean**3
    if sum(parts) != central:
        raise ValueError('third_moment_invariant')
    return {'status': 'ok', 'eligible': total, 'strata': strata,
            'raw_moments': list(map(str, raw)), 'variance': str(variance),
            'third_central_terms': {'within': str(parts[0]), 'interaction': str(parts[1]),
                                    'mean_offsets': str(parts[2])},
            'third_central': str(central),
            'standardized_skew': float(central) / (float(variance)**1.5) if variance else None,
            'skew_status': 'ok' if variance else 'zero_variance'}


def contrast(a, b):
    na, nb = [sum(x) for x in a], [sum(x) for x in b]
    if not all(na + nb):
        return {'status': 'unknown', 'reason': 'empty_stratum'}
    pa, pb = [Fraction(n, sum(na)) for n in na], [Fraction(n, sum(nb)) for n in nb]
    ma = [Fraction(sum((i-20)*v for i, v in enumerate(h)), n) for h, n in zip(a, na)]
    mb = [Fraction(sum((i-20)*v for i, v in enumerate(h)), n) for h, n in zip(b, nb)]
    within = sum((pa[i]+pb[i])*(mb[i]-ma[i])/2 for i in range(2))
    composition = sum((ma[i]+mb[i])*(pb[i]-pa[i])/2 for i in range(2))
    delta = sum(pb[i]*mb[i] - pa[i]*ma[i] for i in range(2))
    if within + composition != delta:
        raise ValueError('decomposition_invariant')
    return {'status': 'ok', 'delta_mean': str(delta), 'within': str(within), 'composition': str(composition)}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'invalid arguments\n')


def main():
    parser = SafeParser(description=__doc__)
    parser.add_argument('--window', required=True, choices=tuple(WINDOWS))
    parser.add_argument('--sample', nargs=4, action='append', required=True, metavar=('GROUP', 'NAME', 'SHA256', 'PATH'))
    args = parser.parse_args()
    if any(g not in ('200', '800') or not name or not name.isprintable() or '/' in name or '\\' in name or
           len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest)
           for g, name, digest, path in args.sample):
        parser.error('identity')
    if len({x[2] for x in args.sample}) != len(args.sample):
        parser.error('duplicate')
    rows = []
    for group, name, digest, path in args.sample:
        row = {'group': group, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as f:
                data = f.read(128*1024*1024+1)
            if len(data) > 128*1024*1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('size_or_hash')
            geometry, payload = independent_strips(data)
            width = geometry['width']
            start, end = WINDOWS[args.window]
            suffix, q = parse(payload, (end+1)*width)
            row.update(status='ok', width=width, height=geometry['height'],
                       result=accounting(suffix, q, width, start, end))
        except (OSError, ValueError, IndexError, KeyError, TypeError) as exc:
            row.update(status='unknown', reason=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        rows.append(row)
    valid = all(row['status'] == 'ok' for row in rows)
    groups = {g: [r['result'] for r in rows if r['group'] == g and r['status'] == 'ok'] for g in ('200', '800')}
    if valid and all(groups.values()):
        a, b = pooled(groups['200']), pooled(groups['800'])
        summary = {'200': describe(a), '800': describe(b), 'contrast_800_minus_200': contrast(a, b)}
    else:
        summary = {'status': 'unknown', 'reason': 'missing_or_incomplete_group'}
    print(json.dumps({'window': args.window, 'samples': rows, 'summary': summary}, allow_nan=False))
    return int(not valid or not all(groups.values()))


if __name__ == '__main__':
    sys.exit(main())
