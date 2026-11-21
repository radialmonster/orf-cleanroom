#!/usr/bin/env python3
"""Test one MakerNote-value-relative locator candidate, not tag semantics.

Candidate start tags are discovered only from the four fixed discovery files.
The previously observed 0x0102 length is fixed. Validation adds two other
files only after the saved discovery records and candidates have been checked.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_scalar_correspondence as scalar
from preview_ifd_extent_probe import validate_jpeg

SAMPLES = {sid: scalar.SAMPLES[sid] for sid in ('1994', '1995', '3800', '3802')}
SAMPLES.update({
    '6343': ('OM System - OM-5 - 16bit (4:3).ORF', 'ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7'),
    '5283': ('OM System - OM-1 - 16bit (4:3).ORF', 'bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b'),
})
DISCOVERY = ['1994', '1995', '3800', '3802']
EXTENSION = ['6343', '5283']


def metadata(data):
    screened = scalar.measure(data)
    start, length = screened['preview_offset'], screened['preview_length']
    paths, relation = scalar.literal_fields(data, start, length)
    camera = paths['camera_settings']
    if isinstance(camera, str):
        raise ValueError(camera)
    e = '<' if data[:2] == b'II' else '>'
    root = struct.unpack_from(e + 'I', data, 4)[0]
    outer = scalar.fields(data, root, e)
    exif = scalar.fields(data, outer[0x8769][2], e)
    _, size, base = exif[0x927c]
    if relation != 'contained':
        raise ValueError('preview_outside_maker_envelope')
    values = {tag: item[2] for tag, item in camera.items() if item[:2] == (4, 1)}
    return start, length, base, size, values


def discover(data, meta=None):
    start, length, base, _, values = metadata(data) if meta is None else meta
    return {'scanner_start': start, 'scanner_length': length,
            'relative_matches': sorted(k for k, v in values.items() if v == start - base),
            'absolute_matches': sorted(k for k, v in values.items() if v == start),
            'length_0102_matches': values.get(0x0102) == length if 0x0102 in values else None}


def check(data, tags, meta=None):
    try:
        scanner_start, scanner_length, base, size, values = metadata(data) if meta is None else meta
    except (ValueError, IndexError, KeyError, struct.error) as exc:
        return {'status': 'unknown', 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}
    results = []
    for tag in tags:
        row = {'tag': tag}
        if tag not in values or 0x0102 not in values:
            row.update(status='unknown', reason='missing_or_wrong_type')
        else:
            offset, length = base + values[tag], values[0x0102]
            if not length or offset < base or offset + length > base + size:
                row.update(status='contradiction', reason='outside_envelope',
                           derived_offset=offset, derived_length=length)
            else:
                same = (offset, length) == (scanner_start, scanner_length)
                row.update(derived_offset=offset, derived_length=length)
                try:
                    marker = validate_jpeg(data, offset, length)
                    if marker['marker_status'] != 'exact_eoi':
                        row.update(status='contradiction', reason='endpoint_mismatch')
                    else:
                        row.update(status='match' if same else 'contradiction',
                                   reason='exact_extent' if same else 'different_extent')
                except (ValueError, IndexError):
                    row.update(status='unknown' if same else 'contradiction',
                               reason='marker_unsupported' if same else 'different_extent',
                               marker_status='unknown')
        results.append(row)
    return {'status': 'ok', 'scanner_start': scanner_start, 'scanner_length': scanner_length,
            'candidates': results}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', required=True, choices=('discovery', 'verification'))
    ap.add_argument('--frozen')
    ap.add_argument('--sample', required=True, nargs=2, action='append', metavar=('ID', 'PATH'))
    args = ap.parse_args()
    ids = DISCOVERY + (EXTENSION if args.phase == 'verification' else [])
    if [sid for sid, _ in args.sample] != ids or bool(args.frozen) != (args.phase == 'verification'):
        ap.error('fixed sample order and frozen discovery required')
    frozen = None
    if args.frozen:
        with open(args.frozen, encoding='utf-8') as f:
            frozen = json.load(f)
        if frozen.get('phase') != 'discovery' or not isinstance(frozen.get('candidates'), list):
            raise ValueError('invalid_frozen')
        if not frozen['candidates']:
            raise ValueError('no_frozen_candidates')
    rows = []
    for sid, path in args.sample:
        if sid == EXTENSION[0]:
            restrict_checks(rows, candidates(rows))
            if rows != frozen.get('samples') or candidates(rows) != frozen['candidates']:
                raise ValueError('discovery_mismatch')
        name, digest = SAMPLES[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as f:
                data = f.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('size_or_hash')
            if sid in DISCOVERY:
                meta = metadata(data)
                row.update(status='ok', **discover(data, meta))
                row['locator'] = check(data, row['relative_matches'], meta)
            else:
                row['status'] = 'ok'
                row['locator'] = check(data, frozen['candidates'])
        except (OSError, ValueError, IndexError, KeyError, struct.error) as exc:
            row.update(status='unknown', reason=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        rows.append(row)
    common = candidates(rows[:4])
    restrict_checks(rows[:4], common)
    print(json.dumps({'phase': args.phase, 'samples': rows, 'candidates': common}, indent=2))
    return int(common is None or any(row['status'] != 'ok' or
                   row.get('locator', {}).get('status') == 'unknown' or
                   any(c['status'] == 'unknown' for c in row.get('locator', {}).get('candidates', []))
                   for row in rows))


def candidates(rows):
    if len(rows) != 4 or any(row.get('status') != 'ok' for row in rows):
        return None
    if any(row['length_0102_matches'] is not True for row in rows):
        return None
    return sorted(set.intersection(*(set(row['relative_matches']) for row in rows)))


def restrict_checks(rows, common):
    if common is not None:
        for row in rows:
            row['locator']['candidates'] = [item for item in row['locator'].get('candidates', [])
                                             if item['tag'] in common]


if __name__ == '__main__':
    sys.exit(main())
