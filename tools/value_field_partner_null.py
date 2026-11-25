"""Exact row-and-partner-q permutation accounting for the fixed #961 field."""
from fractions import Fraction
import hashlib
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_field_q_accounting as old

SAMPLES = {
 'PA200010.ORF': ('200','b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4'),
 'PA200011.ORF': ('200','a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3'),
 'PA200012.ORF': ('800','c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7'),
 'PA200013.ORF': ('800','b714b28697a94081b83d7dd6127ed295f3ffbf6045b098a93381e373f8e3b946'),
 'PA200014.ORF': ('800','49d1719d4120da07911488060c35f8d47dd76b9fc03c328d3cea8a190e298fca'),
 'PA200015.ORF': ('800','84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278'),
 'P1010009.ORF': ('200','ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c'),
 'P1010011.ORF': ('200','d34532152c79ef24b22c60c6cf743cef41fe28196b40fe16b557c16b7a7ea03d'),
 'P1010013.ORF': ('200','81acdd3675c329b351a634cfb4e22228f2db8df94f36480690e04416ded0817d'),
 'P1010017.ORF': ('800','431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5'),
 'P1010018.ORF': ('800','e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f'),
 'P1010019.ORF': ('800','5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75'),
}
COHORTS = {'discovery': tuple(list(SAMPLES)[:6]), 'repeat': tuple(list(SAMPLES)[6:])}


def accounting(suffix, quotient, width, start=20, end=600, edge=20):
    if width <= 2*edge or len(suffix) < end*width+1 or len(quotient) != len(suffix):
        raise ValueError('insufficient_support')
    count = [0, 0]
    omitted = current = observed = 0
    expectation = Fraction(0)
    nonempty = singleton = 0
    for row in range(start, end):
        cells = [[0, 0, 0], [0, 0, 0]]
        for i in range(row*width+edge, row*width+width-edge):
            a, b = suffix[i], suffix[i+1]
            if a < 0 or b < 0:
                omitted += 1
                continue
            q = int(quotient[i+1] > 0)
            x = (a >> 2) & 1
            sign = 1 - 2*x
            partner = 8*((b >> 4) & 1) - 4*(1-((b >> 3) & 1))
            current += (a & 3) - 12*x
            observed += sign * partner
            count[q] += 1
            cells[q][0] += 1
            cells[q][1] += sign
            cells[q][2] += partner
        for n, signs, partners in cells:
            if n:
                nonempty += 1
                singleton += int(n == 1)
                expectation += Fraction(signs*partners, n)
    return {'eligible': sum(count), 'omitted_escape': omitted, 'partner_q_support': count,
            'nonempty_row_q_cells': nonempty, 'singleton_row_q_cells': singleton,
            'current_sum': current, 'observed_partner_sum': observed,
            'permuted_partner_sum': str(expectation)}


def summarize(rows):
    n = sum(r['eligible'] for r in rows)
    if not n:
        return {'status': 'empty'}
    current = Fraction(sum(r['current_sum'] for r in rows), n)
    actual = Fraction(sum(r['observed_partner_sum'] for r in rows), n)
    expected = sum((Fraction(r['permuted_partner_sum']) for r in rows), Fraction()) / n
    remainder = actual - expected
    return {'status': 'ok', 'eligible': n,
            'partner_q_support': [sum(r['partner_q_support'][i] for r in rows) for i in range(2)],
            'current_mean': str(current), 'permuted_partner_mean': str(expected),
            'pairing_remainder_mean': str(remainder), 'field_mean': str(current+actual)}


def compare(a, b):
    if a['status'] != 'ok' or b['status'] != 'ok':
        return {'status': 'unknown', 'reason': 'empty_group'}
    keys = ('current_mean', 'permuted_partner_mean', 'pairing_remainder_mean')
    terms = {k: Fraction(b[k])-Fraction(a[k]) for k in keys}
    delta = Fraction(b['field_mean'])-Fraction(a['field_mean'])
    if sum(terms.values(), Fraction()) != delta:
        raise ValueError('contrast_invariant')
    return {'status': 'ok', 'delta_mean': str(delta), **{k: str(v) for k,v in terms.items()}}


def main():
    p = old.SafeParser(description=__doc__)
    p.add_argument('--cohort', choices=tuple(COHORTS), default='discovery')
    p.add_argument('--sample', nargs=2, action='append', required=True, metavar=('NAME','PATH'))
    args = p.parse_args()
    names = [n for n, _ in args.sample]
    if tuple(names) != COHORTS[args.cohort]:
        p.error('fixed cohort order required')
    rows = []
    for name, path in args.sample:
        group, pin = SAMPLES[name]
        row = {'name': name, 'sha256': pin, 'group': group}
        try:
            with open(path, 'rb') as f:
                data = f.read(128*1024*1024+1)
            if len(data) > 128*1024*1024 or hashlib.sha256(data).hexdigest() != pin:
                raise ValueError('size_or_hash')
            geo, payload = old.independent_strips(data)
            width = geo['width']
            expected_width = 5220 if args.cohort == 'discovery' else 4640
            if width != expected_width:
                raise ValueError('unexpected_width')
            suffix, quotient = old.parse(payload, 601*width)
            row.update(status='ok', width=width, height=geo['height'],
                       result=accounting(suffix, quotient, width))
        except (OSError, ValueError, IndexError, KeyError, TypeError) as exc:
            row.update(status='unknown', reason=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        rows.append(row)
    if all(r['status'] == 'ok' for r in rows):
        groups = {g: summarize([r['result'] for r in rows if r['group'] == g]) for g in ('200','800')}
        summary = {'groups': groups, 'contrast_800_minus_200': compare(groups['200'], groups['800'])}
    else:
        summary = {'status': 'unknown', 'reason': 'input_failure'}
    print(json.dumps({'cohort': args.cohort, 'window': [20,600], 'samples': rows, 'summary': summary}))
    return int(any(r['status'] != 'ok' for r in rows))


if __name__ == '__main__':
    sys.exit(main())
