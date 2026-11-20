#!/usr/bin/env python3
"""Common absolute bit-budget sensitivity for the fixed #781 pairs.

Candidate parser coalescence is not independent physical framing or evidence
of escape syntax; shared post-meet words agree by deterministic parsing.
"""
import hashlib
import json
import os
import struct
import sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matched_boundary_coalescence as old
from value_map_probe import PrivateArgumentParser

BUDGETS = (36, 60, 84, 156)
SAMPLES = {
    '5283': ('OM System - OM-1 - 16bit (4:3).ORF', 'bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b'),
    '5286': ('OM System - OM-1 - 16bit (4:3).ORI', '2fd8bd46e2644fe28092fd921d9647007afd6d1e879c5ff19b1e3df50c578df1'),
    '6343': ('OM System - OM-5 - 16bit (4:3).ORF', 'ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7'),
    '6347': ('OM System - OM-5 - 16bit (4:3).ORI', '062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9'),
}
PHASES = {'discovery': (('5283', 262144), ('5286', 262144)),
          'verification': (('5283', 262144), ('5286', 262144), ('5283', 524288), ('5286', 524288), ('6343', 524288), ('6347', 524288))}


def side(buf, start, prefix_end, budget):
    cutoff = start + budget
    if cutoff > prefix_end:
        return {'status': 'censored'}
    left = old.scan(buf, start, cutoff, budget // 6 + 1)
    right = old.scan(buf, start + 12, cutoff, budget // 6 + 1)
    left_ends = [start] + [w[3] for w in left]
    right_ends = [start + 12] + [w[3] for w in right]
    common = sorted(set(left_ends) & set(right_ends))
    result = {'status': 'eligible', 'category': 'none', 'words0': len(left), 'words12': len(right),
              'q0_0': sum(w[0] == 0 for w in left), 'q0_12': sum(w[0] == 0 for w in right),
              'residual0': cutoff - left_ends[-1], 'residual12': cutoff - right_ends[-1],
              'shared_words': 0, 'shared_bits': 0, 'pre_difference': None, 'tail_difference': None}
    if common:
        meet = common[0]
        i, j = left_ends.index(meet), right_ends.index(meet)
        assert left[i:] == right[j:]
        shared = len(left) - i
        pre = sum(w[0] == 0 for w in right[:j]) - sum(w[0] == 0 for w in left[:i])
        tail = 0
        assert result['q0_12'] - result['q0_0'] == pre + tail
        result.update(category='immediate' if meet == start + 12 else 'later',
                      first_distance=meet-start, index0=i, index12=j,
                      shared_words=shared, shared_bits=sum(w[3]-w[2] for w in left[i:i+shared]),
                      pre_difference=pre, tail_difference=tail)
    return result


def measure(buf, limit):
    totals = {str(b): {'eligibility': Counter(), 'joint': Counter(), 'escape': Counter(), 'control': Counter()}
              for b in BUDGETS}
    def pair(escape_start, control_start, end):
        # Selection already requires 24 complete words after both starts.
        assert escape_start + max(BUDGETS) <= end and control_start + max(BUDGETS) <= end
        for budget in BUDGETS:
            e, c = side(buf, escape_start, end, budget), side(buf, control_start, end, budget)
            cell = totals[str(budget)]
            cell['eligibility'][e['status'] + '/' + c['status']] += 1
            if e['status'] == c['status'] == 'eligible':
                cell['joint'][e['category'] + '/' + c['category']] += 1
                for name, value in (('escape', e), ('control', c)):
                    cell[name][value['category']] += 1
                    for key in ('words0', 'words12', 'q0_0', 'q0_12', 'shared_words', 'shared_bits', 'residual0', 'residual12'):
                        cell[name][key] += value[key]
                    if value['category'] != 'none':
                        cell[name]['boundary_only'] += value['shared_words'] == 0
                        cell[name]['first_distance_' + str(value['first_distance'])] += 1
                        cell[name]['pre_difference'] += value['pre_difference']
                        cell[name]['tail_difference'] += value['tail_difference']
                    else:
                        cell[name]['no_find_difference'] += value['q0_12'] - value['q0_0']
    baseline = old.measure(buf, limit, pair_callback=pair)
    return {'baseline_781': baseline, 'budgets': totals}


def report(sid, path, limit):
    name, expected = SAMPLES[sid]
    with open(path, 'rb') as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != expected:
        return {'id': sid, 'name': name, 'status': 'unknown', 'reason': 'identity_mismatch'}
    w, h, payload = old.locate_snapshot(data)
    result = measure(payload, limit)
    return {'id': sid, 'name': name, 'sha256': expected, 'width': w, 'height': h,
            'payload_bytes': len(payload), 'status': 'ok' if result['baseline_781']['prefix_complete'] and result['baseline_781']['matched_pairs'] else 'unknown', 'result': result}


def main():
    ap = PrivateArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=sorted(PHASES), required=True)
    ap.add_argument('--sample', nargs=2, action='append', metavar=('ID', 'PATH'), required=True)
    args = ap.parse_args()
    required_ids = tuple(dict.fromkeys(sid for sid, _ in PHASES[args.phase]))
    if tuple(sid for sid, _ in args.sample) != required_ids:
        ap.error('sample order must match phase')
    paths = dict(args.sample)
    results = []
    for sid, limit in PHASES[args.phase]:
        try:
            result = report(sid, paths[sid], limit)
            result['requested_tokens'] = limit
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            result = {'id': sid, 'name': SAMPLES[sid][0], 'requested_tokens': limit,
                      'status': 'unknown', 'error_type': type(exc).__name__}
        results.append(result)
    names = ('equal_bit_coalescence.py', 'matched_boundary_coalescence.py', 'orf_tokens.py',
             'orf_signature.py', 'value_map_probe.py')
    sources = {}
    for name in names:
        with open(os.path.join(os.path.dirname(__file__), name), 'rb') as f:
            sources[name] = hashlib.sha256(f.read()).hexdigest()
    print(json.dumps({'phase': args.phase, 'source_sha256': sources, 'samples': results}, allow_nan=False))
    return int(any(x['status'] != 'ok' for x in results))


if __name__ == '__main__':
    sys.exit(main())
