#!/usr/bin/env python3
"""Compare fixed preview extents with selected literal metadata scalars.

The only offset convention is the existing active-area tool's MakerNote-relative
IFD offsets. MakerNote paths are limited to 0x2020 and 0x2040. Unsupported or
incomplete path scope is unknown, not a negative observation.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc
from preview_ifd_extent_probe import validate_jpeg


def fields(data, off, endian, forbidden=None, occupied=None):
    if off < 0 or off + 2 > len(data):
        raise ValueError('ifd_bounds')
    count = struct.unpack_from(endian + 'H', data, off)[0]
    end = off + 2 + 12 * count
    if end + 4 > len(data):
        raise ValueError('ifd_bounds')
    if forbidden is not None and off < forbidden[1] and end + 4 > forbidden[0]:
        raise ValueError('ifd_preview_overlap')
    if occupied is not None:
        if any(off < b and end + 4 > a for a, b in occupied):
            raise ValueError('overlapping_directories')
        occupied.append((off, end + 4))
    result = {}
    for i in range(count):
        tag, typ, n, val = struct.unpack_from(endian + 'HHII', data, off + 2 + i * 12)
        if tag in result:
            raise ValueError('duplicate_tag')
        result[tag] = (typ, n, val)
    return result


def literal_fields(data, preview_start=None, preview_length=None):
    if len(data) < 8 or data[:2] not in (b'II', b'MM'):
        raise ValueError('header')
    endian = '<' if data[:2] == b'II' else '>'
    magic, root = struct.unpack_from(endian + 'HI', data, 2)
    if magic not in (42, 0x4f52, 0x5352) or root < 8:
        raise ValueError('header')
    forbidden = ((preview_start, preview_start + preview_length)
                 if preview_start is not None else None)
    occupied = []
    outer = fields(data, root, endian, forbidden, occupied)
    paths = {'ifd0': outer}
    try:
        exif = outer.get(0x8769)
        if exif is None or exif[:2] != (4, 1) or exif[2] < 8:
            raise ValueError('exif_pointer')
        exif_tags = fields(data, exif[2], endian, forbidden, occupied)
        maker = exif_tags.get(0x927c)
        if maker is None or maker[0] != 7 or maker[1] < 13:
            raise ValueError('maker_envelope')
        _, size, start = maker
        if start < 8 or start + size > len(data):
            raise ValueError('maker_envelope')
        if (preview_start is not None and start < preview_start + preview_length
                and start + size > preview_start):
            raise ValueError('maker_preview_overlap')
        if any(start < b and start + size > a for a, b in occupied):
            raise ValueError('maker_directory_overlap')
        blob = data[start:start + size]
        if blob.count(b'OLYMPUS\0') != 1:
            raise ValueError('maker_header')
        base = blob.find(b'OLYMPUS\0') + 8
        if blob[base:base+2] not in (b'II', b'MM'):
            raise ValueError('maker_endian')
        inner_endian = '<' if blob[base:base+2] == b'II' else '>'
        inner_occupied = [(base - 8, base + 4)]
        top = fields(blob, base + 4, inner_endian, occupied=inner_occupied)
    except (ValueError, struct.error) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else 'bounds'
        paths.update(camera_settings=reason, image_processing=reason)
        return paths
    for tag, name in ((0x2020, 'camera_settings'), (0x2040, 'image_processing')):
        try:
            ref = top.get(tag)
            if ref is None or ref[:2] != (13, 1) or ref[2] < base + 4:
                raise ValueError('maker_path')
            paths[name] = fields(blob, ref[2], inner_endian, occupied=inner_occupied)
        except (ValueError, struct.error) as exc:
            paths[name] = str(exc) if isinstance(exc, ValueError) else 'bounds'
            if paths[name] == 'overlapping_directories':
                paths['camera_settings'] = 'overlapping_directories'
                paths['image_processing'] = 'overlapping_directories'
                break
    return paths


def measure(data):
    preview = jpeg_dc.find_preview(data)
    if preview is None:
        raise ValueError('no_preview')
    _, start, length, width, height = preview
    masked = bytearray(data)
    masked[start:start+2] = b'\x00\x00'
    other = jpeg_dc.find_preview(masked)
    if other is not None and other[0] == preview[0]:
        raise ValueError('preview_tie')
    marker = validate_jpeg(data, start, length)
    if marker['marker_status'] != 'exact_eoi' or (width, height) != (marker['width'], marker['height']):
        raise ValueError('preview_marker')
    paths = literal_fields(data, start, length)
    matches = {}
    for path, tags in paths.items():
        if isinstance(tags, str):
            matches[path] = {'status': 'unknown', 'reason': tags}
            continue
        tags = {tag: item[2] for tag, item in tags.items() if item[:2] == (4, 1)}
        matches[path] = {'length': sorted(t for t, v in tags.items() if v == length),
                         'offset': sorted(t for t, v in tags.items() if v == start),
                         'scalar_count': len(tags), 'status': 'ok'}
    return {'preview_length': length, 'preview_offset': start, 'matches': matches}


def intersection(rows):
    if not rows:
        raise ValueError('empty_rows')
    if len({row['preview_length'] for row in rows}) != len(rows):
        raise ValueError('lengths_not_distinct')
    return {path: (sorted(set.intersection(*(set(row['matches'][path]['length']) for row in rows)))
                   if all(row['matches'][path]['status'] == 'ok' for row in rows) else None)
            for path in ('ifd0', 'camera_settings', 'image_processing')}


SAMPLES = {
    '1994': ('Olympus - E-M1MarkII - 16bit (4:3).ORF', 'f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23'),
    '1995': ('Olympus - E-M1MarkII - 16bit (4:3).ORI', '8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f'),
    '3800': ('Olympus - E-M1MarkIII - 16bit (4:3).ORF', '1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f'),
    '3802': ('Olympus - E-M1MarkIII - 16bit (4:3).ORI', '83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46'),
    '1998': ('Olympus - E-M1MarkII - 16bit (4:3).ORF', '4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71'),
    '3801': ('Olympus - E-M1MarkIII - 16bit (4:3).ORF', 'e9a21175493e9d9e5653aa91f1bd6fbf421aba42b59b4ffe7cd1f7cac2de385c'),
}
DISCOVERY = ['1994', '1995', '3800', '3802']
EXTENSION = ['1998', '3801']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    ap.add_argument('--frozen', help='saved discovery aggregate JSON for verification')
    ap.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'))
    args = ap.parse_args()
    ids = DISCOVERY + (EXTENSION if args.phase == 'verification' else [])
    if [sid for sid, path in args.sample] != ids or bool(args.frozen) != (args.phase == 'verification'):
        ap.error('phase requires fixed ordered sample IDs and verification requires --frozen')
    frozen = None
    previous_samples = None
    if args.frozen:
        with open(args.frozen, 'r', encoding='utf-8') as f:
            previous = json.load(f)
        if previous.get('phase') != 'discovery':
            raise ValueError('frozen_phase')
        frozen = previous['candidates']
        if not isinstance(frozen, dict):
            raise ValueError('frozen_candidates')
        previous_samples = previous.get('samples')
        if (not isinstance(previous_samples, list)
                or not all(isinstance(row, dict) for row in previous_samples)
                or [row.get('id') for row in previous_samples] != DISCOVERY
                or any(row.get('name') != SAMPLES[row['id']][0]
                       or row.get('sha256') != SAMPLES[row['id']][1]
                       or row.get('status') != 'ok' for row in previous_samples)):
            raise ValueError('frozen_samples')
    rows = []
    for sid, path in args.sample:
        if sid == EXTENSION[0]:
            good = [row for row in rows[:4] if row.get('status') == 'ok']
            if len(good) != 4 or rows[:4] != previous_samples or intersection(good) != frozen:
                raise ValueError('discovery_mismatch')
        name, digest = SAMPLES[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as f:
                data = f.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024:
                raise ValueError('size_limit')
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('hash_mismatch')
            row.update(status='ok', **measure(data))
        except (OSError, ValueError, IndexError, struct.error) as exc:
            row.update(status='unknown', reason=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        rows.append(row)
    good = [row for row in rows[:4] if row.get('status') == 'ok']
    candidates = intersection(good) if len(good) == 4 else None
    check = []
    if args.phase == 'verification' and frozen is not None:
        for row in rows[4:]:
            for path, ids_for_path in frozen.items():
                if ids_for_path is None or row.get('status') != 'ok' or row['matches'][path]['status'] != 'ok':
                    check.append({'id': row['id'], 'path': path, 'status': 'unknown'})
                else:
                    found = set(row['matches'][path]['length'])
                    check.append({'id': row['id'], 'path': path, 'status': 'ok',
                                  'matched': [i for i in ids_for_path if i in found],
                                  'lost': [i for i in ids_for_path if i not in found]})
    print(json.dumps({'phase': args.phase, 'samples': rows, 'candidates': candidates,
                      'verification': check}, indent=2))
    return int(any(row.get('status') != 'ok' or any(
        p['status'] != 'ok' for p in row.get('matches', {}).values()) for row in rows))


if __name__ == '__main__':
    sys.exit(main())
