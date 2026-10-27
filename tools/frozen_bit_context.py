#!/usr/bin/env python3
"""Frozen binary-context likelihood baseline for #298, NOT an ORF codec.

Preregistered family: orders 0..8, MSB-first supplied strip bytes, context zero
at each window start; all bits including the first order bits are scored.
Discovery fits one Laplace-smoothed probability per context, quantized to a
numerator 1..4095 over 4096 (nearest, ties upward). Each numerator costs 12
bits; order costs 4 bits. Select lowest discovery NLL plus model cost, ties
by order; no validation fitting. Charge that model once for the validation
cohort. This is normalized predictive NLL plus parameter cost, NOT serialized
packet size: no arithmetic coder, packet framing, padding or termination is
implemented, and there is no claimed round trip or sensor reconstruction.

Default windows: 65536 bytes starting at logical strip byte 65536, fixed before
measurement. --validation-offset can move only the heldout windows, keeping
discovery fitting and selection at --offset for frozen-table band transfer.
Choose both offsets before examining results. Concatenate raw strips in tag order; reject invalid
strip bounds/count tables, short windows and duplicate input hashes. Files
must match CC0 entries in the supplied public manifest. External retained
licence verification remains required. Signature fields are copied prior
manifest measurements, not newly measured. Output contains aggregates only.
A control shuffles each validation window's bits preserving its exact count,
using MT19937 seed 298, getrandbits rejection Fisher-Yates in input order.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from orf_signature import Tiff

ORDERS = tuple(range(9))
DENOMINATOR = 4096


def counts(data, order):
    """Data is an iterable of integer bits; no sample arrays are returned."""
    table = [[0, 0] for _ in range(1 << order)]
    state, mask = 0, (1 << order) - 1
    for bit in data:
        if bit not in (0, 1):
            raise ValueError('nonbinary input')
        table[state][bit] += 1
        state = ((state << 1) | bit) & mask
    return table


def bits(data):
    return [((value >> shift) & 1) for value in data for shift in range(7, -1, -1)]


def fit(table):
    # Round positive rational to nearest, ties upward; exact integer arithmetic.
    return [max(1, min(4095, ((one + 1) * 8192 + zero + one + 2)
                             // (2 * (zero + one + 2)))) for zero, one in table]


def nll(table, probabilities):
    if len(table) != len(probabilities):
        raise ValueError('table length mismatch')
    return math.fsum(-zero * math.log2((4096 - p) / 4096)
                     - one * math.log2(p / 4096)
                     for (zero, one), p in zip(table, probabilities))


def model_cost(order):
    return 4 + 12 * (1 << order)


def experiment(discovery, validation, seed=298):
    if not discovery or not validation or any(not x for x in discovery + validation):
        raise ValueError('nonempty windows required')
    shuffled = [list(x) for x in validation]
    rng = random.Random(seed)
    for window in shuffled:
        for i in range(len(window) - 1, 0, -1):
            j = rng.getrandbits((i + 1).bit_length())
            while j > i:
                j = rng.getrandbits((i + 1).bit_length())
            window[i], window[j] = window[j], window[i]
    ledger = []
    for order in ORDERS:
        discovery_tables = [counts(window, order) for window in discovery]
        train = [[sum(table[c][b] for table in discovery_tables) for b in (0, 1)]
                 for c in range(1 << order)]
        probability = fit(train)
        train_nll = nll(train, probability)
        test_nll = [nll(counts(window, order), probability) for window in validation]
        null_nll = [nll(counts(window, order), probability) for window in shuffled]
        ledger.append({'order': order, 'model_bits': model_cost(order),
                       'discovery_nll': train_nll,
                       'discovery_score': train_nll + model_cost(order),
                       'validation_nll_by_file': test_nll,
                       'validation_score': math.fsum(test_nll) + model_cost(order),
                       'shuffled_validation_score': math.fsum(null_nll) + model_cost(order),
                       'discovery_count_total': sum(sum(pair) for pair in train),
                       'discovery_table_sha256': hashlib.sha256(
                           json.dumps(train, separators=(',', ':')).encode('ascii')).hexdigest()})
    selected = min(ledger, key=lambda row: (row['discovery_score'], row['order']))['order']
    return {'frozen_order': selected, 'ledger': ledger,
            'validation_literal_bits': sum(map(len, validation)),
            'discovery_literal_bits': sum(map(len, discovery)),
            'control': 'exact-count bit shuffle, MT19937/getrandbits Fisher-Yates, seed %d' % seed}


def load_window(path, manifest, offset, size):
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    rows = [row for row in manifest if row['sha256'] == digest and row['licence'] == 'CC0']
    if not rows:
        raise ValueError('input hash absent from CC0 manifest')
    tags = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    starts, lengths = tags.get(0x111) or [], tags.get(0x117) or []
    if not starts or len(starts) != len(lengths):
        raise ValueError('invalid strip table')
    if any(start < 0 or length <= 0 or start + length > len(data)
           for start, length in zip(starts, lengths)):
        raise ValueError('strip outside file')
    extents = sorted(zip(starts, lengths))
    if any(left + length > right for (left, length), (right, _)
           in zip(extents, extents[1:])):
        raise ValueError('overlapping strips')
    payload = b''.join(data[start:start + length] for start, length in zip(starts, lengths))
    if offset + size > len(payload):
        raise ValueError('short fixed window')
    row = rows[0]
    return bits(payload[offset:offset + size]), {
        'pixls_id': row['pixls_id'], 'pixls_name': row['pixls_name'], 'sha256': digest,
        'payload_bytes': len(payload), 'strip_count': len(starts),
        'window_offset': offset, 'window_bytes': size,
        'manifest_signature': {key: row[key] for key in ('payload_w', 'payload_h', 'size_class', 'variant')}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--discovery', nargs='+', required=True)
    parser.add_argument('--validation', nargs='+', required=True)
    parser.add_argument('--offset', type=int, default=65536)
    parser.add_argument('--validation-offset', type=int, default=None,
                        help='heldout logical-strip byte offset; defaults to --offset')
    parser.add_argument('--bytes', type=int, default=65536, dest='size')
    args = parser.parse_args(argv)
    validation_offset = args.offset if args.validation_offset is None else args.validation_offset
    if args.offset < 0 or validation_offset < 0 or not 1 <= args.size <= 1048576:
        parser.error('offsets >= 0 and bytes 1..1048576 required')
    try:
        with open(args.manifest, newline='', encoding='utf-8') as stream:
            reader = csv.DictReader(stream, strict=True)
            fields = ('sha256', 'licence', 'pixls_id', 'pixls_name', 'payload_w', 'payload_h', 'size_class', 'variant')
            if any((reader.fieldnames or []).count(field) != 1 for field in fields):
                raise ValueError('missing or duplicate consumed manifest column')
            manifest = list(reader)
            if any(row[field] is None for row in manifest for field in fields):
                raise ValueError('truncated manifest row')
        started = time.perf_counter()
        loaded = ([load_window(path, manifest, args.offset, args.size) for path in args.discovery]
                  + [load_window(path, manifest, validation_offset, args.size)
                     for path in args.validation])
        identities = [identity for _, identity in loaded]
        if len({row['sha256'] for row in identities}) != len(identities):
            parser.error('duplicate content or train/test overlap')
        split = len(args.discovery)
        result = experiment([x[0] for x in loaded[:split]], [x[0] for x in loaded[split:]])
        result.update({'inputs_discovery': identities[:split], 'inputs_validation': identities[split:],
                       'scope': 'compressed-bit predictive baseline only; no codec/reconstruction',
                       'cpu_seconds': time.perf_counter() - started,
                       'backend': 'stdlib CPU; fixed tiny campaign, no GPU claim'})
    except (OSError, UnicodeError, ValueError, KeyError, IndexError, TypeError, struct.error, csv.Error):
        print('invalid input: unreadable manifest/sample or invalid hash/strip/window', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
