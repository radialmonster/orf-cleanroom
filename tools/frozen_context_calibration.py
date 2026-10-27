#!/usr/bin/env python3
"""Finite-grid per-file calibration of frozen context models for #298/#362.

Discovery fits orders 0..8 at offset 65536; a separate per-file calibration
window at 196608 selects an odds multiplier, then windows 262144 and 327680
are scored without refitting. All windows contain 65536 bytes. Scores include
model and three-bit index costs but exclude calibration-data transmission;
they are predictive NLL, not serialized size or a codec. A single seeded
exact-count shuffle per window is descriptive. Previously studied inputs are
not independent captures. Missing or invalid inputs produce an incomplete run.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frozen_bit_context as base

GRID = ((1, 4), (1, 2), (3, 4), (1, 1), (4, 3), (2, 1), (4, 1))
SIZE = 65536
EXPECTED = '1f395ec3446c96b3c7415e2ff5e6d11ad79684695410315132a1e19584bbdc71'


def transform(probabilities, multiplier):
    a, b = multiplier
    out, clamps = [], 0
    for p in probabilities:
        numerator = 4096 * a * p
        denominator = b * (4096 - p) + a * p
        rounded = (2 * numerator + denominator) // (2 * denominator)
        value = max(1, min(4095, rounded))
        clamps += value != rounded
        out.append(value)
    return out, clamps


def choose(probabilities, calibration, order):
    table = base.counts(calibration, order)
    candidates = []
    adjusted = []
    for multiplier in GRID:
        probabilities2, clamps = transform(probabilities, multiplier)
        adjusted.append(probabilities2)
        candidates.append(dict(multiplier=list(multiplier), nll=base.nll(table, probabilities2),
                               clamps=clamps, table_sha256=hashlib.sha256(
                                   json.dumps(probabilities2, separators=(',', ':')).encode('ascii')).hexdigest()))
    winner = min(range(len(GRID)), key=lambda i: (candidates[i]['nll'], i))
    best = candidates[winner]['nll']
    return adjusted[winner], dict(candidates=candidates, selected_index=winner,
                                  tied_indices=[i for i, c in enumerate(candidates) if c['nll'] == best])


def shuffled(bits):
    result = list(bits)
    rng = random.Random(298)
    for i in range(len(result)-1, 0, -1):
        j = rng.getrandbits((i+1).bit_length())
        while j > i:
            j = rng.getrandbits((i+1).bit_length())
        result[i], result[j] = result[j], result[i]
    return result


def models(discovery):
    ledger = []
    for order in range(9):
        tables = [base.counts(window, order) for window in discovery]
        table = [[sum(t[i][b] for t in tables) for b in (0, 1)] for i in range(1 << order)]
        p = base.fit(table)
        digest = hashlib.sha256(json.dumps(table, separators=(',', ':')).encode('ascii')).hexdigest()
        ledger.append((base.nll(table, p) + base.model_cost(order), p, digest))
    if min(range(9), key=lambda i: (ledger[i][0], i)) != 8 or ledger[8][2] != EXPECTED:
        raise ValueError('frozen model mismatch')
    return ledger


def evaluate(ledger, calibration, windows):
    selected = {}
    result = {'calibration': {}, 'evaluation': []}
    for order in (0, 8):
        selected[order], details = choose(ledger[order][1], calibration, order)
        result['calibration'][str(order)] = details
    for window in windows:
        control = shuffled(window)
        entry = {}
        for order in (0, 8):
            table, null = base.counts(window, order), base.counts(control, order)
            cost = base.model_cost(order)
            entry[str(order)] = dict(frozen=base.nll(table, ledger[order][1]) + cost,
                                     adjusted=base.nll(table, selected[order]) + cost + 3,
                                     shuffled=base.nll(null, selected[order]) + cost + 3)
        result['evaluation'].append(entry)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--discovery', nargs=2, required=True)
    parser.add_argument('--validation', nargs='+', required=True)
    args = parser.parse_args(argv)
    try:
        with open(args.manifest, encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream, strict=True)
            fields = ('sha256','licence','pixls_id','pixls_name','payload_w','payload_h','size_class','variant')
            if any((reader.fieldnames or []).count(field) != 1 for field in fields):
                raise ValueError('manifest columns')
            manifest = list(reader)
            if any(row[field] is None for row in manifest for field in fields):
                raise ValueError('truncated manifest')
        failures = []
        def load(path, role, ordinal, offset):
            try:
                return base.load_window(path, manifest, offset, SIZE)
            except (OSError, UnicodeError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
                failures.append(dict(role=role, ordinal=ordinal, offset=offset, error=type(exc).__name__))
                return None
        discovery = [load(path, 'discovery', i, 65536) for i, path in enumerate(args.discovery, 1)]
        loaded = [[load(path, 'validation', i, offset) for offset in (196608,262144,327680)]
                  for i, path in enumerate(args.validation, 1)]
        if failures:
            print(json.dumps(dict(complete=False, failures=failures)))
            return 1
        ids = [v[1]['sha256'] for v in discovery] + [group[0][1]['sha256'] for group in loaded]
        if len(ids) != len(set(ids)) or any(len({v[1]['sha256'] for v in group}) != 1 for group in loaded):
            raise ValueError('duplicate or changed sample')
        ledger = models([v[0] for v in discovery])
        reports = []
        for group in loaded:
            report = evaluate(ledger, group[0][0], [group[1][0], group[2][0]])
            report['input'] = group[0][1]
            report['evaluation_offsets'] = [262144,327680]
            reports.append(report)
        print(json.dumps(dict(complete=True, grid=GRID, index_bits=3, frozen_table_sha256=EXPECTED,
                              calibration_offset=196608, evaluation_offsets=[262144,327680],
                              window_bytes=SIZE, control='exact-count bit shuffle, MT19937/getrandbits Fisher-Yates, seed 298 reset per window',
                              inputs_discovery=[v[1] for v in discovery], samples=reports),
                         indent=2, allow_nan=False))
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, IndexError, TypeError, struct.error, csv.Error):
        print(json.dumps(dict(complete=False, error='invalid input or frozen model')))
        return 1


if __name__ == '__main__':
    sys.exit(main())
