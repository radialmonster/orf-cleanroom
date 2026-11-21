#!/usr/bin/env python3
"""Inventory literal declared geometry on the fixed public V0 cohort.

TIFF IFD0/next/SubIFD graph and largest-strip selection follow the existing
external-boundary probe. DNG type/order comparisons do not imply ORF semantics
or a relationship between raw coordinates and a camera preview. An `ok` tag
has the supported literal type and count, not a validated geometric transform.
"""
import argparse
import bisect
import csv
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_external_boundary as boundary

DISCOVERY = ['1800', '8609', '2151', '1799', '3438', '1432', '2878',
             '792', '780', '3624', '5491', '2420', '2977', '3540']
EXTENSION = ['2431', '2856', '5424']
ROSTER_SHA256 = '2cdbe99693defed1e0d846c29886ca1bf64e07e4547b39f315e694c50541aad0'
GEOMETRY_ROSTER_SHA256 = '27bba849e69a0a73502448cdbbe550a2432c56cb80ee7792a4027703b25e0484'
SHAPES = {256: ((3, 4), 1), 257: ((3, 4), 1), 274: ((3,), 1), 50706: ((1,), 4), 50718: ((5,), 2),
          50719: ((3, 4, 5), 2), 50720: ((3, 4, 5), 2), 50829: ((3, 4), 4)}
UNITS = {1: 1, 3: 2, 4: 4, 5: 8}


def declared(data, offset, endian, wanted, forbidden=()):
    count = struct.unpack_from(endian + 'H', data, offset)[0]
    entries = {}
    for i in range(count):
        pos = offset + 2 + 12 * i
        tag, typ, n = struct.unpack_from(endian + 'HHI', data, pos)
        if tag not in wanted:
            continue
        if tag in entries:
            raise ValueError('duplicate_tag')
        result = {'type': typ, 'count': n}
        expected, expected_n = SHAPES[tag]
        if typ not in expected or n != expected_n:
            result['status'] = 'unsupported_shape'
        else:
            size = n * UNITS[typ]
            loc = pos + 8 if size <= 4 else struct.unpack_from(endian + 'I', data, pos + 8)[0]
            if loc < 8 or loc + size > len(data):
                result['status'] = 'out_of_bounds'
            elif size > 4 and any(loc < b and loc + size > a for a, b in forbidden):
                result['status'] = 'strip_overlap'
            else:
                formats = {1: 'B', 3: 'H', 4: 'I', 5: 'I'}
                values = struct.unpack_from(endian + str(n * (2 if typ == 5 else 1)) + formats[typ], data, loc)
                if typ == 5:
                    values = [list(values[i:i+2]) for i in range(0, len(values), 2)]
                    result['status'] = 'ok' if all(v[1] for v in values) else 'zero_denominator'
                else:
                    result['status'] = 'ok'
                result['values'] = list(values)
                if tag == 274 and values[0] not in range(1, 9):
                    result['status'] = 'invalid_orientation'
        entries[tag] = result
    return {str(tag): entries.get(tag, {'status': 'absent'}) for tag in wanted}


def measure(data, expected):
    endian, dirs = boundary.outer_graph(data)
    selected, spans = boundary.strip_spans(data, endian, dirs)
    starts = [a for a, _ in spans]
    def overlaps(start, end):
        i = bisect.bisect_left(starts, end) - 1
        return i >= 0 and spans[i][1] > start
    for offset, tags in dirs:
        count = struct.unpack_from(endian + 'H', data, offset)[0]
        end = offset + 2 + 12 * count + 4
        if overlaps(offset, end):
            raise ValueError('ifd_strip_overlap')
        for tag in (273, 279, 330):
            if tag not in tags:
                continue
            typ, n, value = tags[tag]
            unit = {3: 2, 4: 4, 13: 4}.get(typ)
            if unit is not None and n * unit > 4 and overlaps(value, value + n * unit):
                raise ValueError('table_strip_overlap')
    root = boundary.header(data)[1]
    tags = dict(dirs)[selected]
    dimensions = []
    for tag in (256, 257):
        if tag not in tags or tags[tag][:2] not in ((3, 1), (4, 1)):
            raise ValueError('invalid_dimensions')
        values = declared(data, selected, endian, [tag])
        dimensions.append(values[str(tag)]['values'][0])
    width, height = dimensions
    total = sum(b - a for a, b in spans)
    packing = ('packed-12' if 2*total == 3*width*height else
               'packed-12.8' if 5*total == 8*width*height else
               'packed-16' if total == 2*width*height else 'other')
    if (str(width), str(height), packing) != expected:
        raise ValueError('geometry_mismatch')
    raw = declared(data, selected, endian, [274, 50718, 50719, 50720, 50829], spans)
    version = declared(data, root, endian, [274, 50706], spans)
    return {'status': 'ok', 'raw_ifd': selected, 'ifd_count': len(dirs),
            'strip_count': len(spans), 'width': width, 'height': height,
            'packing': packing, 'raw_tags': raw, 'ifd0_tags': version}


def roster():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, 'samples', 'conformance-V0.csv'), encoding='utf-8', newline='') as f:
        conformance = {row['input_sha256']: row for row in csv.DictReader(f)}
    with open(os.path.join(base, 'samples', 'manifest.csv'), encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    result = {}
    for row in rows:
        if row['source'] == 'pixls' and row['pixls_id'] in DISCOVERY + EXTENSION and row['licence'] == 'CC0' and row['sha256'] in conformance and conformance[row['sha256']]['variant'] == 'V0':
            c = conformance[row['sha256']]
            pair = (row['pixls_name'], row['sha256'], c['width'], c['height'], c['packing'])
            if row['pixls_id'] in result and result[row['pixls_id']] != pair:
                raise ValueError('ambiguous_roster')
            result[row['pixls_id']] = pair
    if set(result) != set(DISCOVERY + EXTENSION) or len(conformance) != 17:
        raise ValueError('invalid_roster')
    canonical = ''.join(f'{sid}|{result[sid][0]}|{result[sid][1]}|{result[sid][4]}\n'
                        for sid in sorted(result, key=int)).encode('utf-8')
    if hashlib.sha256(canonical).hexdigest() != ROSTER_SHA256:
        raise ValueError('invalid_roster_digest')
    geometry = ''.join(f'{sid}|{result[sid][0]}|{result[sid][1]}|{result[sid][4]}|{result[sid][2]}|{result[sid][3]}\n'
                       for sid in sorted(result, key=int)).encode('utf-8')
    if hashlib.sha256(geometry).hexdigest() != GEOMETRY_ROSTER_SHA256:
        raise ValueError('invalid_geometry_digest')
    return result


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'invalid arguments\n')


def main():
    parser = SafeParser()
    parser.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    parser.add_argument('--frozen')
    parser.add_argument('--sample', action='append', nargs=2, required=True)
    args = parser.parse_args()
    ids = DISCOVERY + (EXTENSION if args.phase == 'verification' else [])
    if [x[0] for x in args.sample] != ids or bool(args.frozen) != (args.phase == 'verification'):
        parser.error('phase')
    previous = None
    if args.frozen:
        try:
            with open(args.frozen, encoding='utf-8') as f:
                previous = json.load(f)
            if not isinstance(previous, dict) or previous.get('phase') != 'discovery':
                raise ValueError('invalid_frozen')
        except (OSError, ValueError):
            raise SystemExit('invalid_frozen') from None
    identities = roster()
    rows = []
    for sid, path in args.sample:
        if sid == EXTENSION[0] and rows != previous.get('samples'):
            raise SystemExit('discovery_mismatch')
        name, digest, width, height, packing = identities[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as f:
                data = f.read(160 * 1024 * 1024 + 1)
            if len(data) > 160 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('size_or_hash')
            row.update(measure(data, (width, height, packing)))
        except (OSError, ValueError, struct.error, IndexError) as exc:
            row.update(status='unknown', reason=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'phase': args.phase, 'samples': rows}, indent=2))
    return int(any(r['status'] != 'ok' for r in rows))


if __name__ == '__main__':
    sys.exit(main())
