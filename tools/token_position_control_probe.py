#!/usr/bin/env python3
"""Fixed nominal-position controls for #29 item 9; aggregate output only.

W-token rows start at token zero, not established physical rows. Candidate
q>=17 tokens are omitted without compacting. Controls are fixed offsets, not
an exchangeable null or a reproduction of the unspecified historical measure.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_tokens import locate_data
from token_tail_distribution_probe import scan_tokens


def measure(payload, width, limit):
    if type(width) is not int or width < 96 or type(limit) is not int or limit <= 0:
        raise ValueError('width >=96 and positive token limit required')
    offsets = [0, width // 4, width // 2, 3 * width // 4]
    if any(a + 24 > b for a, b in zip(offsets, offsets[1:])) or offsets[-1] + 24 > width:
        raise ValueError('control windows must not overlap or cross nominal rows')
    cells = {str(o): {'window_n': 0, 'window_q': 0, 'window_suffix': 0,
                      'other_n': 0, 'other_q': 0, 'other_suffix': 0,
                      'paired_rows': 0, 'paired_q_sum': Fraction(),
                      'paired_suffix_sum': Fraction()} for o in offsets}
    row = []
    count = end = escapes = rows = 0
    identical_row_sets = True
    common_rows = 0
    common = {str(o): {'q': Fraction(), 'suffix': Fraction()} for o in offsets}
    for q, suffix, endpoint in scan_tokens(payload, limit):
        row.append((q, suffix))
        count += 1; end = endpoint; escapes += q >= 17
        if len(row) != width:
            continue
        ordinary = [(q, s) for q, s in row if q < 17]
        total_q = sum(q for q, _ in ordinary); total_s = sum(s for _, s in ordinary)
        row_valid = []
        row_contrasts = []
        for offset in offsets:
            window = [(q, s) for q, s in row[offset:offset + 24] if q < 17]
            wn = len(window); on = len(ordinary) - wn
            wq = sum(q for q, _ in window); ws = sum(s for _, s in window)
            oq = total_q - wq; osum = total_s - ws
            cell = cells[str(offset)]
            for name, value in (('window_n', wn), ('window_q', wq), ('window_suffix', ws),
                                ('other_n', on), ('other_q', oq), ('other_suffix', osum)):
                cell[name] += value
            if wn and on:
                cell['paired_rows'] += 1
                qdiff = Fraction(wq, wn) - Fraction(oq, on)
                sdiff = Fraction(ws, wn) - Fraction(osum, on)
                cell['paired_q_sum'] += qdiff
                cell['paired_suffix_sum'] += sdiff
                row_contrasts.append((qdiff, sdiff))
            else:
                row_contrasts.append(None)
            row_valid.append(bool(wn and on))
        identical_row_sets = identical_row_sets and len(set(row_valid)) == 1
        if all(row_valid):
            common_rows += 1
            for offset, (qdiff, sdiff) in zip(offsets, row_contrasts):
                common[str(offset)]['q'] += qdiff
                common[str(offset)]['suffix'] += sdiff
        rows += 1; row = []
    for cell in cells.values():
        for field in ('q', 'suffix'):
            value = cell.pop('paired_' + field + '_sum')
            n = cell['paired_rows']
            mean = value / n if n else None
            cell['paired_' + field + '_mean'] = ({'numerator': mean.numerator, 'denominator': mean.denominator}
                                                  if mean is not None else None)
        cell['undefined_rows'] = rows - cell['paired_rows']
    comparison = {}
    for field in ('q', 'suffix'):
        if not common_rows:
            comparison[field] = None
        else:
            x = [common[str(o)][field] / common_rows for o in offsets]
            comparison[field] = {'zero_exceeds_all_controls': all(x[0] > v for v in x[1:]),
                                 'zero_ties_controls': [o for o, v in zip(offsets[1:], x[1:]) if x[0] == v],
                                 'means': [{'numerator': v.numerator, 'denominator': v.denominator} for v in x]}
    return {'requested_tokens': limit, 'parsed_tokens': count, 'endpoint_bits': end,
            'complete_rows': rows, 'tail_tokens': len(row), 'parsed_escapes': escapes,
            'tail_escapes': sum(q >= 17 for q, _ in row), 'offsets': offsets, 'cells': cells,
            'identical_valid_row_sets': identical_row_sets, 'common_rows': common_rows,
            'common_excluded_rows': rows - common_rows, 'comparison': comparison}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sample', nargs=3, required=True, metavar=('PUBLIC_NAME', 'SHA256', 'FILE'))
    ap.add_argument('--tokens', type=int, required=True, choices=(262144, 524288))
    args = ap.parse_args(); name, digest, path = args.sample
    if not name or any(c in name for c in '/\\') or not re.fullmatch('[0-9a-f]{64}', digest):
        ap.error('invalid public identity or SHA-256')
    try:
        with open(path, 'rb') as f: data = f.read()
        if hashlib.sha256(data).hexdigest() != digest: raise ValueError('hash mismatch')
        w, h, payload = locate_data(data)
        result = measure(payload, w, args.tokens)
        print(json.dumps({'name': name, 'sha256': digest, 'width': w, 'height': h,
                          'payload_bytes': len(payload), 'result': result}, indent=2, allow_nan=False))
        return 0 if result['parsed_tokens'] == args.tokens else 1
    except (OSError, ValueError, TypeError, IndexError) as exc:
        print('measurement failed: ' + type(exc).__name__, file=sys.stderr); return 1


if __name__ == '__main__':
    sys.exit(main())
