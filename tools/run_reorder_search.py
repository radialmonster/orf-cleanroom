#!/usr/bin/env python3
"""Run-reordering full-search surrogate diagnostic, Part of #297/#231.

Frozen pilot: logical strip bytes [4096,4608), split into two 256-byte windows;
widths 2..12, every phase (154 candidates), 127 full-search replicates.
The statistic is squared pooled-binomial standardized phase density contrast.
Run reorder preserves global per-symbol maximal-run multisets, endpoints,
density and all four adjacent-transition counts. It does NOT preserve local
window densities, byte histograms, or run positions. Invariants are checked on
every replicate. This is a surrogate-model diagnostic, NOT a camera p-value,
codec grammar, or established framing detector. Public samples are development
inputs; no untouched validation or independent-capture replication is asserted.

Read-only stdlib tool. Prints aggregates only, never payloads or local paths.
File mode requires an expected previously licence-verified SHA256. The caller
must retain the licence record: a hash alone does not establish licence.
Builds on #231's run-preservation definition and #297's full-search protocol;
distinct from #308's synthetic byte-shuffle harness. No findings are asserted.
File mode requires a positive ASCII decimal ID and a printable public basename.
"""
import argparse
import fractions
import hashlib
import itertools
import json
import math
import os
import platform
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, first, size_class

SEED = 20261022
REPLICATES = 127
SPAN_BYTES = 512
OFFSET_BYTES = 4096
WINDOW_BITS = 2048


def bits_of(buf):
    return [(byte >> shift) & 1 for byte in buf for shift in range(7, -1, -1)]


def invariants(bits):
    """Exact global invariants, including no-wrap adjacent transitions."""
    runs = [(v, sum(1 for _ in group)) for v, group in itertools.groupby(bits)]
    transitions = [[0, 0], [0, 0]]
    for a, b in zip(bits, bits[1:]):
        transitions[a][b] += 1
    return {'bits': len(bits), 'ones': sum(bits),
            'endpoints': [bits[0], bits[-1]] if bits else [],
            'runs_by_symbol': [[length for v, length in sorted(runs) if v == symbol]
                               for symbol in (0, 1)],
            'transition_counts': transitions}


def reorder_runs(bits, rng):
    runs = [(v, sum(1 for _ in group)) for v, group in itertools.groupby(bits)]
    lengths = [[length for v, length in runs if v == symbol] for symbol in (0, 1)]
    for values in lengths:
        rng.shuffle(values)
    cursors = [iter(values) for values in lengths]
    return [v for v, _ in runs for _ in range(next(cursors[v]))]


def candidates(bits):
    """Every candidate, stable order; no data-dependent family truncation."""
    if len(bits) != 2 * WINDOW_BITS:
        raise ValueError('requires exactly 4096 bits')
    rows = []
    for window in range(2):
        xs = bits[window * WINDOW_BITS:(window + 1) * WINDOW_BITS]
        total = sum(xs)
        for width in range(2, 13):
            counts = [len(xs[phase::width]) for phase in range(width)]
            ones = [sum(xs[phase::width]) for phase in range(width)]
            for phase in range(width):
                n, a = counts[phase], ones[phase]
                m, b = len(xs) - n, total - a
                contrast = a / n - b / m
                numerator = (a * m - b * n) ** 2 * len(xs)
                denominator = n * m * total * (len(xs) - total)
                exact = fractions.Fraction(numerator, denominator) if denominator else fractions.Fraction(0)
                score = float(exact)
                rows.append({'window': window, 'width': width, 'phase': phase,
                             'selected_n': n, 'selected_ones': a,
                             'other_n': m, 'other_ones': b,
                             'density_difference': contrast, 'score': score,
                             'score_numerator': exact.numerator, 'score_denominator': exact.denominator})
    return rows


def exact_score(row):
    return fractions.Fraction(row['score_numerator'], row['score_denominator'])


def summarize_winner(rows):
    top = max(rows, key=exact_score)
    tied = [row for row in rows if exact_score(row) == exact_score(top)]
    return dict(top, tie_count=len(tied), winner_width_boundary=top['width'] in (2, 12),
                any_tied_width_boundary=any(row['width'] in (2, 12) for row in tied))


def wilson(k, n):
    z = 1.959963984540054
    p = k / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0.0, centre - half), min(1.0, centre + half)]


def analyse(buf):
    bits = bits_of(buf)
    reference = invariants(bits)
    observed = candidates(bits)
    winner = summarize_winner(observed)
    rng = random.Random(SEED)
    maxima = []
    for replicate in range(REPLICATES):
        surrogate = reorder_runs(bits, rng)
        if invariants(surrogate) != reference:
            raise AssertionError('surrogate invariant failure')
        rows = candidates(surrogate)
        top = summarize_winner(rows)
        maxima.append(dict(replicate=replicate, **top))
    exceedances = sum(exact_score(row) >= exact_score(winner) for row in maxima)
    # Run lists themselves are aggregate histograms, but only their counts are
    # needed in the public output; never emit the original run order.
    return {'bits': reference['bits'], 'ones': reference['ones'],
            'endpoints': reference['endpoints'],
            'run_counts_by_symbol': [len(x) for x in reference['runs_by_symbol']],
            'transition_counts': reference['transition_counts'],
            'candidate_count': len(observed), 'observed_candidates': observed,
            'winner': winner, 'replicate_maxima': maxima,
            'invariants_checked_replicates': REPLICATES,
            'exceedances_ge': exceedances,
            'surrogate_tail_fraction': exceedances / REPLICATES,
            'surrogate_tail_wilson95': wilson(exceedances, REPLICATES),
            'plus_one_rank_diagnostic': (exceedances + 1) / (REPLICATES + 1)}


def read_window(path, expected_sha256):
    with open(path, 'rb') as source:
        data = source.read()
    return read_data(data, expected_sha256)


def read_data(data, expected_sha256):
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise ValueError('input hash mismatch')
    tags = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    offsets, counts = tags.get(0x111) or [], tags.get(0x117) or []
    if not offsets or len(offsets) != len(counts):
        raise ValueError('invalid strip tables')
    ranges = sorted(zip(offsets, counts))
    for i, (offset, count) in enumerate(ranges):
        if offset < 0 or count <= 0 or offset + count > len(data):
            raise ValueError('invalid strip bounds')
        if i and ranges[i - 1][0] + ranges[i - 1][1] > offset:
            raise ValueError('overlapping strips')
    w, h = first(tags, 0x100), first(tags, 0x101)
    if not isinstance(w, int) or not isinstance(h, int) or min(w, h) <= 0:
        raise ValueError('invalid dimensions')
    payload = b''.join(data[o:o + n] for o, n in zip(offsets, counts))
    if len(payload) < OFFSET_BYTES + SPAN_BYTES:
        raise ValueError('short payload window')
    return payload[OFFSET_BYTES:OFFSET_BYTES + SPAN_BYTES], {
        'sha256': digest, 'payload_width': w, 'payload_height': h,
        'payload_bytes': len(payload), 'compression_tag': first(tags, 0x103),
        'size_class': size_class(len(payload), w, h)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', nargs=4, metavar=('ID', 'PUBLIC_NAME', 'SHA256', 'PATH'))
    args = parser.parse_args(argv)
    if args.sample:
        sid, name, expected, path = args.sample
        try:
            invalid_id = not sid.isascii() or not sid.isdigit() or int(sid) <= 0
        except ValueError:
            invalid_id = True
        if invalid_id:
            parser.error('sample ID must be a positive ASCII integer')
        if not name or not name.isprintable() or any(c in name for c in '/\\'):
            parser.error('sample public name must be a printable basename')
        if len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
            parser.error('expected SHA256 must be 64 lowercase hexadecimal digits')
    records = []
    rng = random.Random(611)
    uniform = bytes(rng.getrandbits(8) for _ in range(SPAN_BYTES))
    for synthetic_name, buf in [('constant_zero', bytes(SPAN_BYTES)), ('uniform', uniform),
                                ('forced_byte_lsb', bytes(value | 1 for value in uniform))]:
        records.append(dict(name=synthetic_name, input_kind='synthetic_development', **analyse(buf)))
    if args.sample:
        try:
            window, metadata = read_window(path, expected)
            records.append(dict(pixls_id=sid, pixls_name=name,
                                input_kind='public_development', **metadata, **analyse(window)))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error):
            print(json.dumps({'complete': False, 'error': 'invalid input/hash/payload'}))
            return 1
    print(json.dumps({'complete': True, 'lead': 297, 'seed': SEED,
                      'python_version': platform.python_version(),
                      'rng': 'Python random.Random MT19937; sequential 0 then 1 run shuffles',
                      'replicates': REPLICATES, 'offset_bytes': OFFSET_BYTES,
                      'span_bytes': SPAN_BYTES, 'window_bits': WINDOW_BITS,
                      'widths': list(range(2, 13)), 'phase_rule': 'all phases for each width',
                      'validation': 'none; all inputs development',
                      'interpretation': 'surrogate diagnostic; no camera p-value',
                      'records': records}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
