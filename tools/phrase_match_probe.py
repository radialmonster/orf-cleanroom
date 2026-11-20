#!/usr/bin/env python3
"""Fixed two-suffix phrase comparison on nominal blocks; no codec inference."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_tokens import locate_data
from suffix_joint_probe import scan_prefix

LIMIT = 262144
SAMPLES = {
    '3800': ('Olympus - E-M1MarkIII - 16bit (4:3).ORF', '1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f'),
    '1331': ('Olympus - E-M10 - 16bit (4:3).ORF', 'd7f6ac99ee1f824e81ec0e71599f0f87f9b2e2675f7ddfdb21202281b8bdc5e0'),
    '3210': ('Olympus - TG-6 - 16bit (4:3).ORF', 'edd6f928bc790c79852a17fce56718d26563c7a593894d22970ef0fdb86ba45f'),
    '3573': ('Olympus - E-M5 Mark III - 16bit (4:3).ORF', '391f2f6ba712a517212cae53bfc9a313fc4d106d0b04d3b9af68a4ed2d5d944e'),
    '3970': ('Olympus - E-PL10 - 16bit (4:3).ORF', '6911f11810545cc2c55882ef6fa6aa2f25d34674865f8ade15e47990865e37ed'),
    '4126': ('Olympus - E-M10 Mark IV - 16bit (4:3).ORF', 'ce03e936cb2e8131343e7045a3249f78477bd2ae944e121ace72058b89fef509'),
}
PHASES = {'discovery': ('3800', '1331', '3210'),
          'verification': ('3800', '1331', '3210', '3573', '3970', '4126')}


def rational(value):
    return None if value is None else {'numerator': value.numerator, 'denominator': value.denominator}


def measure(tokens, width, phase):
    if width <= 2 or width % 2 or phase not in (0, 1):
        raise ValueError('invalid geometry')
    blocks, tail = divmod(len(tokens), width)
    usable = blocks * width
    lags = (2, width, 2 * width)
    slots, hist = {}, []
    for block in range(blocks):
        counts = Counter()
        for col in range(phase, width - 1, 2):
            t = block * width + col
            a, b = tokens[t], tokens[t + 1]
            if a[0] < 17 and b[0] < 17:
                label = (a[1], b[1])
                slots[t] = label
                counts[label] += 1
        hist.append(counts)
    totals = [sum(h.values()) for h in hist]

    def valid_slot(t):
        column = t % width
        return 0 <= t < usable and column < width - 1 and column % 2 == phase

    candidates = [t for t in range(2 * width + phase, usable - 1, 2)
                  if valid_slot(t) and all(valid_slot(t - lag) for lag in lags)]
    retained = [t for t in candidates if t in slots and all(t - lag in slots for lag in lags)]
    rows = []
    for lag in lags:
        groups = Counter()
        match = first = second = 0
        for t in retained:
            u = t - lag
            a, b = slots[t], slots[u]
            match += a == b
            first += a[0] == b[0]
            second += a[1] == b[1]
            groups[(t // width, u // width)] += 1
        expected = Fraction()
        same = cross = 0
        for (a, b), count in groups.items():
            ha, hb = hist[a], hist[b]
            if a == b:
                n = totals[a]
                if n < 2:
                    raise ValueError('inconsistent same-block support')
                probability = Fraction(sum(x * (x - 1) for x in ha.values()), n * (n - 1))
                same += count
            else:
                if not totals[a] or not totals[b]:
                    raise ValueError('inconsistent cross-block support')
                probability = Fraction(sum(n * hb.get(label, 0) for label, n in ha.items()), totals[a] * totals[b])
                cross += count
            expected += count * probability
        n = len(retained)
        rows.append({'lag': lag, 'P': n, 'M': match, 'first_equal': first, 'second_equal': second,
                     'same_block_pairs': same, 'cross_block_pairs': cross,
                     'target_bounds': [retained[0], retained[-1] + 2] if n else None,
                     'donor_bounds': [retained[0] - lag, retained[-1] - lag + 2] if n else None,
                     'E': rational(expected) if n else None,
                     'observed_rate': rational(Fraction(match, n)) if n else None,
                     'expected_rate': rational(expected / n) if n else None,
                     'difference': rational((match - expected) / n) if n else None})
    return {'phase': phase, 'status': 'ok' if retained else 'empty_support', 'complete_blocks': blocks,
            'excluded_tail_tokens': tail, 'block_spans': [[i * width, (i + 1) * width] for i in range(blocks)],
            'eligible_slots_per_block': totals, 'candidate_targets': len(candidates),
            'omitted_targets': len(candidates) - len(retained), 'retained_targets': len(retained), 'lags': rows}


def report(sid, path):
    name, expected = SAMPLES[sid]
    with open(path, 'rb') as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != expected:
        return {'id': sid, 'name': name, 'status': 'unknown', 'reason': 'identity_mismatch'}
    w, h, payload = locate_data(data)
    if w <= 2 or w % 2 or h <= 0:
        return {'id': sid, 'name': name, 'status': 'unknown', 'reason': 'incompatible_geometry'}
    tokens, end = scan_prefix(payload, LIMIT)
    base = {'id': sid, 'name': name, 'sha256': expected, 'width': w, 'height': h,
            'payload_bytes': len(payload), 'requested_tokens': LIMIT, 'returned_tokens': len(tokens), 'bits_consumed': end}
    if len(tokens) != LIMIT:
        base.update(status='unknown', reason='short_input')
        return base
    phases = [measure(tokens, w, p) for p in (0, 1)]
    base.update(status='ok' if all(p['status'] == 'ok' for p in phases) else 'unknown', phases=phases)
    return base


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=sorted(PHASES), required=True)
    ap.add_argument('--sample', nargs=2, action='append', metavar=('ID', 'PATH'), required=True)
    args = ap.parse_args()
    if tuple(x[0] for x in args.sample) != PHASES[args.phase]:
        ap.error('sample order must match frozen phase')
    results = []
    for sid, path in args.sample:
        try:
            results.append(report(sid, path))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            results.append({'id': sid, 'name': SAMPLES[sid][0], 'status': 'unknown', 'error_type': type(exc).__name__})
    sources = {}
    for name in ('phrase_match_probe.py', 'suffix_joint_probe.py', 'orf_tokens.py', 'orf_signature.py'):
        with open(os.path.join(os.path.dirname(__file__), name), 'rb') as f:
            sources[name] = hashlib.sha256(f.read()).hexdigest()
    print(json.dumps({'phase': args.phase, 'python_version': sys.version.split()[0],
                      'source_sha256': sources, 'samples': results}, allow_nan=False))
    return int(any(r['status'] != 'ok' for r in results))


if __name__ == '__main__':
    sys.exit(main())
