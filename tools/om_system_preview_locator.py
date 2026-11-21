#!/usr/bin/env python3
"""Test a fixed leading OM SYSTEM MakerNote JPEG locator (#155/#924).

The 16-byte header and MakerNote-relative 0x2020/0x0101/0x0102 path are
file-derived candidates, not official tag semantics. No header or JPEG scan
is used to choose the metadata interval. The existing Olympus rule is unchanged.
Only aggregate metadata is emitted; JPEG entropy and raw samples are not decoded.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc
import preview_metadata_locator as previous
from preview_ifd_extent_probe import validate_jpeg
from preview_scalar_correspondence import fields

HEADER = b'OM SYSTEM\0\0\0II\x04\0'
DISCOVERY = ['6343', '5283']
EXTENSION = ['7262', '7796', '8552']
SAMPLES = {
    '6343': ('OM System - OM-5 - 16bit (4:3).ORF',
             'ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7'),
    '5283': ('OM System - OM-1 - 16bit (4:3).ORF',
             'bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b'),
    '7262': ('OM System - OM-1 Mark II - 16bit (4:3).orf',
             'd0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd'),
    '7796': ('OM System - OM-3 - 16bit (4:3).ORF',
             '1cee7deb661e45101ab3ca6c4240d24ed949b167ed423703fca15c09dd8ec176'),
    '8552': ('OM System - OM-5 Mark II - 16bit (4:3).ORF',
             '4d79adadf1f736cdbd666bc5f750ee75235b365ecb5fa8dcbc6cd7ca461343ed'),
}


def candidate(data):
    if len(data) < 8 or data[:2] not in (b'II', b'MM'):
        raise ValueError('tiff_header')
    endian = '<' if data[:2] == b'II' else '>'
    magic, root = struct.unpack_from(endian + 'HI', data, 2)
    if magic not in (42, 0x4f52, 0x5352) or root < 8:
        raise ValueError('tiff_header')
    occupied = [(0, 8)]
    outer = fields(data, root, endian, occupied=occupied)
    exif = outer.get(0x8769)
    if exif is None or exif[:2] != (4, 1) or exif[2] < 8:
        raise ValueError('exif_pointer')
    exif_tags = fields(data, exif[2], endian, occupied=occupied)
    maker = exif_tags.get(0x927c)
    if maker is None or maker[0] != 7 or maker[1] < 22:
        raise ValueError('maker_envelope')
    _, size, base = maker
    if base < 8 or base + size > len(data):
        raise ValueError('maker_envelope')
    if any(base < b and base + size > a for a, b in occupied):
        raise ValueError('maker_directory_overlap')
    blob = data[base:base+size]
    if blob[:16] != HEADER:
        raise ValueError('unsupported_leading_header')
    inner_spans = [(0, 16)]
    top = fields(blob, 16, '<', occupied=inner_spans)
    settings = top.get(0x2020)
    if settings is None or settings[:2] != (13, 1) or settings[2] < 16:
        raise ValueError('camera_settings')
    entries = fields(blob, settings[2], '<', occupied=inner_spans)
    first, count = entries.get(0x0101), entries.get(0x0102)
    if first is None or count is None or first[:2] != (4, 1) or count[:2] != (4, 1):
        raise ValueError('missing_scalar')
    start, length = base + first[2], count[2]
    result = {'maker_offset': base, 'maker_length': size,
              'header_hex': HEADER.hex(), 'top_entries': len(top),
              'settings_relative': settings[2], 'settings_entries': len(entries),
              'preview_relative': first[2], 'offset': start, 'length': length}
    if not length or start < base or start + length > base + size:
        return dict(result, status='contradiction', reason='outside_envelope')
    spans = occupied + [(base+a, base+b) for a, b in inner_spans]
    if any(start < b and start + length > a for a, b in spans):
        raise ValueError('jpeg_metadata_overlap')
    if length < 4 or data[start:start+2] != b'\xff\xd8':
        return dict(result, status='contradiction', reason='missing_soi')
    try:
        marker = validate_jpeg(data, start, length)
    except (ValueError, IndexError):
        return dict(result, status='unknown', reason='marker_unsupported')
    if marker['marker_status'] != 'exact_eoi':
        return dict(result, status='contradiction', reason='endpoint_mismatch')
    return dict(result, status='ok', width=marker['width'], height=marker['height'])


def checked(function, data):
    try:
        return function(data)
    except (ValueError, IndexError, KeyError, struct.error) as exc:
        return {'status': 'unknown',
                'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}


def scanner(data):
    selected = jpeg_dc.find_preview(data)
    if selected is None:
        raise ValueError('no_preview')
    area, start, length, width, height = selected
    later = jpeg_dc.find_preview(data[start+3:])
    if later is not None and later[0] == area:
        raise ValueError('scanner_tie')
    marker = validate_jpeg(data, start, length)
    if marker['marker_status'] != 'exact_eoi' or (width, height) != (marker['width'], marker['height']):
        raise ValueError('scanner_marker')
    return {'status': 'ok', 'offset': start, 'length': length, 'width': width, 'height': height}


def measure(data):
    metadata = checked(candidate, data)
    baseline = checked(previous.candidate, data)
    scanned = checked(scanner, data)
    relation = 'unknown'
    if metadata['status'] == scanned['status'] == 'ok':
        relation = ('match' if all(metadata[k] == scanned[k]
                    for k in ('offset', 'length', 'width', 'height')) else 'mismatch')
    return {'candidate': metadata, 'previous': baseline, 'scanner': scanned, 'relation': relation}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    ap.add_argument('--frozen', help='saved discovery aggregate JSON')
    ap.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'))
    args = ap.parse_args()
    expected = DISCOVERY + (EXTENSION if args.phase == 'verification' else [])
    if [sid for sid, _ in args.sample] != expected or bool(args.frozen) != (args.phase == 'verification'):
        ap.error('fixed phase order and verification discovery report required')
    frozen = None
    if args.frozen:
        with open(args.frozen, encoding='utf-8') as f:
            frozen = json.load(f)
        if frozen.get('phase') != 'discovery' or frozen.get('rule_header_hex') != HEADER.hex():
            raise ValueError('invalid_frozen')
    rows = []
    for sid, path in args.sample:
        if sid == EXTENSION[0] and rows != frozen.get('samples'):
            raise ValueError('discovery_mismatch')
        name, digest = SAMPLES[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as f:
                data = f.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('size_or_hash')
            row.update(measure(data))
        except (OSError, ValueError) as exc:
            row.update(candidate={'status': 'unknown', 'reason': type(exc).__name__},
                       previous={'status': 'unknown'}, scanner={'status': 'unknown'}, relation='unknown')
        rows.append(row)
    print(json.dumps({'phase': args.phase, 'rule_header_hex': HEADER.hex(), 'samples': rows}, indent=2))
    return int(any(r['candidate']['status'] == 'unknown' or r['scanner']['status'] == 'unknown' for r in rows))


if __name__ == '__main__':
    sys.exit(main())
