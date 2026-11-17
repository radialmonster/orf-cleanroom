"""Reduce suffix_balance_windows aggregate JSON to exact conditional ordering (#29 item 3).

Input is printed aggregate JSON, not a raw file. P(b2=1 | b1b0=j) is
C[j+4]/(C[j]+C[j+4]), where C is the four-row H marginal of L. Report
every comparison, including ties; incomplete and empty windows are undefined.
"""
import argparse
import hashlib
from fractions import Fraction
import json


def reduce_window(window):
    table = window['joint_h_rows_l_columns']
    if len(table) != 4 or any(len(row) != 8 for row in table):
        raise ValueError('expected 4x8 table')
    if any(type(x) is not int or x < 0 for row in table for x in row):
        raise ValueError('counts must be nonnegative integers')
    cols = [sum(table[h][l] for h in range(4)) for l in range(8)]
    if sum(cols) != window['retained_tokens']:
        raise ValueError('retained count mismatch')
    identity = {'start_token': window['start_token'],
                'requested_tokens': window['requested_tokens'],
                'returned_tokens': window['returned_tokens'],
                'retained_tokens': window['retained_tokens'],
                'escape_tokens': window['escape_tokens']}
    if window['returned_tokens'] != window['requested_tokens'] or not sum(cols):
        return {**identity, 'counts': None, 'fractions': None,
                'adjacent': None, 'strictly_increasing': None, 'nondecreasing': None}
    counts = [[cols[j + 4], cols[j] + cols[j + 4]] for j in range(4)]
    fractions = [str(Fraction(n, d)) if d else None for n, d in counts]
    adjacent = []
    for (a, b), (c, d) in zip(counts, counts[1:]):
        if not b or not d:
            adjacent.append(None)
        else:
            left, right = a * d, c * b
            adjacent.append('<' if left < right else '>' if left > right else '=')
    defined = all(d for _, d in counts)
    return {**identity, 'counts': counts, 'fractions': fractions,
            'adjacent': adjacent, 'strictly_increasing': all(x == '<' for x in adjacent) if defined else None,
            'nondecreasing': all(x in ('<', '=') for x in adjacent) if defined else None}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('aggregate_json')
    args = ap.parse_args()
    with open(args.aggregate_json, 'rb') as f:
        raw = f.read()
    source = json.loads(raw)
    with open(__file__, 'rb') as f:
        tool_sha = hashlib.sha256(f.read()).hexdigest()
    sample = source['sample']
    print(json.dumps({'input_report_sha256': hashlib.sha256(raw).hexdigest(),
                      'tool_sha256': tool_sha, 'mode': source['mode'],
                      'pixls_id': sample['pixls_id'], 'pixls_name': sample['pixls_name'],
                      'sample_sha256': sample['sha256'],
                      'windows': [reduce_window(w) for w in sample['windows']]}, indent=2))


if __name__ == '__main__':
    main()
