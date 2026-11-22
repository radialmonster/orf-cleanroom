#!/usr/bin/env python3
"""Inventory literal V0 Exif and fixed-path MakerNote geometry (#77/#933).

No coordinate order, crop origin, orientation transform or pixel mapping is
inferred. Unsupported metadata scope is unknown, never a negative tag result.
No preview scanner, entropy decoder or image output is used.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v0_declared_geometry as baseline
from preview_locator_independent import View

DISCOVERY = list(baseline.DISCOVERY)
EXTENSION = list(baseline.EXTENSION)


class GuardedView(View):
    def __init__(self, data, order, forbidden=()):
        super().__init__(data, order)
        self.forbidden = list(forbidden)

    def chunk(self, at, size):
        if any(at < b and at+size > a for a, b in self.forbidden):
            raise ValueError('forbidden_metadata_read')
        return super().chunk(at, size)


def literal(view, tags, tag, count):
    entry = tags.get(tag)
    if entry is None:
        return {'status': 'absent'}
    typ, n, _ = entry
    result = {'type': typ, 'count': n}
    if typ not in (3, 4) or n != count:
        return dict(result, status='unsupported_shape')
    try:
        return dict(result, status='ok', values=view.numbers(entry))
    except ValueError as exc:
        return dict(result, status='unknown', reason=str(exc))


def maker_fields(data, outer, exif):
    entry = exif.get(0x927c)
    if entry is None or entry[0] != 7 or entry[1] < 18:
        raise ValueError('maker_envelope')
    base, size = outer.extent(entry, 1)
    if any(base < b and base+size > a for a, b in outer.spans):
        raise ValueError('maker_directory_overlap')
    blob = outer.chunk(base, size)
    if blob[:8] != b'OLYMPUS\0' or blob[8:10] not in (b'II', b'MM'):
        raise ValueError('unsupported_leading_header')
    maker = GuardedView(blob, 'little' if blob[8:10] == b'II' else 'big')
    maker.spans = [(0, 12)]
    top, _ = maker.directory(12)
    settings, _ = maker.directory(maker.scalar(top, 0x2020, 13))
    start = maker.scalar(settings, 0x0101)
    length = maker.scalar(settings, 0x0102)
    if not length or base+start < 8 or base+start+length > len(data):
        raise ValueError('preview_boundary_unknown')
    if any(start < b and start+length > a for a, b in maker.spans):
        raise ValueError('preview_metadata_overlap')
    maker.forbidden.append((start, start+length))
    processing_at = maker.scalar(top, 0x2040, 13)
    processing, _ = maker.directory(processing_at)
    values = {str(tag): literal(maker, processing, tag, count)
              for tag, count in ((0x0614, 1), (0x0615, 1), (0x0637, 4))}
    return {'status': 'ok', 'maker_start': base, 'maker_length': size,
            'processing_relative': processing_at, 'tags': values}


def measure(data, expected):
    geometry = baseline.measure(data, expected)
    endian, dirs = baseline.boundary.outer_graph(data)
    _, strips = baseline.boundary.strip_spans(data, endian, dirs)
    outer = GuardedView(data, 'little' if endian == '<' else 'big', strips)
    outer.spans = [(0, 8)]
    root, _ = outer.directory(outer.integer(4, 4))
    result = {'status': 'ok', 'raw_ifd': geometry['raw_ifd'],
              'width': geometry['width'], 'height': geometry['height'],
              'packing': geometry['packing'], 'orientation': geometry['raw_tags']['274']}
    try:
        exif, _ = outer.directory(outer.scalar(root, 0x8769))
        dimensions = {str(tag): literal(outer, exif, tag, 1) for tag in (0xa002, 0xa003)}
        result['exif'] = {'status': 'ok', 'tags': dimensions}
    except ValueError as exc:
        result.update(exif={'status': 'unknown', 'reason': str(exc)},
                      maker={'status': 'unknown', 'reason': 'exif_scope_unknown'})
        return result
    try:
        result['maker'] = maker_fields(data, outer, exif)
    except ValueError as exc:
        result['maker'] = {'status': 'unknown', 'reason': str(exc)}
    if result['maker']['status'] == 'ok':
        tags = result['maker']['tags']
        pair = [tags[str(tag)] for tag in (0x0614, 0x0615)]
        if all(item['status'] == 'ok' for item in pair):
            values = [item['values'][0] for item in pair]
            result['raw_minus_maker'] = [geometry['width']-values[0], geometry['height']-values[1]]
            if all(item['status'] == 'ok' for item in dimensions.values()):
                result['maker_equals_exif'] = values == [dimensions[str(t)]['values'][0] for t in (0xa002, 0xa003)]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    parser.add_argument('--frozen')
    parser.add_argument('--sample', action='append', nargs=2, required=True, metavar=('ID', 'PATH'))
    args = parser.parse_args()
    expected_ids = DISCOVERY + (EXTENSION if args.phase == 'verification' else [])
    if [sid for sid, _ in args.sample] != expected_ids or bool(args.frozen) != (args.phase == 'verification'):
        parser.error('fixed phase roster and replay report required')
    frozen = None
    if args.frozen:
        with open(args.frozen, encoding='utf-8') as stream:
            frozen = json.load(stream)
        if frozen.get('phase') != 'discovery':
            raise ValueError('invalid_frozen')
    roster = baseline.roster()
    rows = []
    for sid, path in args.sample:
        if sid == EXTENSION[0] and rows != frozen.get('samples'):
            raise ValueError('discovery_mismatch')
        name, digest, width, height, packing = roster[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as stream:
                data = stream.read(160*1024*1024+1)
            if len(data) > 160*1024*1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('size_or_hash')
            row.update(measure(data, (width, height, packing)))
        except (OSError, ValueError, IndexError, struct.error) as exc:
            row.update(status='unknown', reason=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'phase': args.phase, 'samples': rows}, indent=2))
    return int(any(row['status'] != 'ok' for row in rows))


if __name__ == '__main__':
    sys.exit(main())
