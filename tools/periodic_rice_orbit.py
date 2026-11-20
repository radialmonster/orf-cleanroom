#!/usr/bin/env python3
"""Enumerate synthetic literal stop-1 Rice phase orbits; no file inputs."""
import argparse
import collections
import json


def orbit(bits, k, start):
    period = len(bits)
    if '1' not in bits:
        return {'status': 'no_stop', 'states': [], 'words': [], 'cycle_start': None}
    seen, states, words = {}, [], []
    state = start
    while state not in seen:
        seen[state] = len(states)
        states.append(state)
        q = 0
        while bits[(state + q) % period] != '1':
            q += 1
        length = q + 1 + k
        words.append({'q': q, 'bits': length})
        state = (state + length) % period
    return {'status': 'cycle', 'states': states, 'words': words, 'cycle_start': seen[state]}


def enumerate_period(period):
    cases = []
    summary = {str(k): collections.Counter() for k in (4, 5)}
    for n in range(2 ** period):
        bits = format(n, '0%db' % period)
        for k in (4, 5):
            for phase in range(period):
                result = orbit(bits, k, phase)
                if result['status'] == 'no_stop':
                    key = 'no_stop'
                else:
                    index = result['cycle_start']
                    cycle = result['words'][index:]
                    key = '%d:%d:%d' % (index, len(cycle), sum(x['bits'] for x in cycle))
                summary[str(k)][key] += 1
                cases.append({'template': bits, 'k': k, 'start_phase': phase, **result})
    return {'period': period, 'summary_transient_words_cycle_words_cycle_bits': {k: dict(sorted(v.items())) for k, v in summary.items()}, 'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    args = parser.parse_args()
    periods = (6,) if args.phase == 'discovery' else (6, 5, 7)
    print(json.dumps({'phase': args.phase, 'periods': [enumerate_period(p) for p in periods]}))


if __name__ == '__main__':
    main()
