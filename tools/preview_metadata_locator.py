#!/usr/bin/env python3
"""Compare a frozen metadata-first JPEG locator with the byte scanner.

Only the leading Olympus MakerNote header and fixed 0x2020/0x0101/0x0102
layout are tested. Unknown layouts receive no fallback. Marker checks do not
decode entropy or establish JPEG conformance or preview-to-raw registration.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc
from preview_scalar_correspondence import fields, SAMPLES as PRIOR_SAMPLES
from preview_ifd_extent_probe import validate_jpeg

SAMPLES = {sid: PRIOR_SAMPLES[sid] for sid in ('1994', '1995', '3800', '3802')}
SAMPLES.update({
    '1051': ('Olympus - E-M1 - 16bit (4:3).orf', '19ba17e778ae802d4039f0e88bb1cd68825780788b8058c479067e32b9a63eda'),
    '3588': ('OLYMPUS - E-M5 Mark III - 16bit (4:3).ORF', '24de6ac3bd5e668ee22fd0dbf2e344608949eb85f7342f28470ce709c9d51226'),
})
DISCOVERY = ['1994', '1995', '3800', '3802']
EXTENSION = ['1051', '3588']


def candidate(data):
    if len(data) < 8 or data[:2] not in (b'II', b'MM'):
        raise ValueError('tiff_header')
    endian = '<' if data[:2] == b'II' else '>'
    magic, root = struct.unpack_from(endian + 'HI', data, 2)
    if magic not in (42, 0x4f52, 0x5352) or root < 8:
        raise ValueError('tiff_header')
    spans = [(0, 8)]
    outer = fields(data, root, endian, occupied=spans)
    exif = outer.get(0x8769)
    if exif is None or exif[:2] != (4, 1) or exif[2] < 8:
        raise ValueError('exif_pointer')
    exif_tags = fields(data, exif[2], endian, occupied=spans)
    maker = exif_tags.get(0x927c)
    if maker is None or maker[0] != 7 or maker[1] < 18:
        raise ValueError('maker_envelope')
    _, size, base = maker
    if base < 8 or base + size > len(data):
        raise ValueError('maker_envelope')
    if any(base < b and base + size > a for a, b in spans):
        raise ValueError('maker_directory_overlap')
    if data[base:base+8] != b'OLYMPUS\0':
        raise ValueError('nonleading_header')
    if data[base+8:base+10] not in (b'II', b'MM'):
        raise ValueError('maker_endian')
    inner_endian = '<' if data[base+8:base+10] == b'II' else '>'
    blob = data[base:base+size]
    inner_spans = [(0, 12)]
    top = fields(blob, 12, inner_endian, occupied=inner_spans)
    settings = top.get(0x2020)
    if settings is None or settings[:2] != (13, 1) or settings[2] < 12:
        raise ValueError('camera_settings')
    entries = fields(blob, settings[2], inner_endian, occupied=inner_spans)
    start_tag, length_tag = entries.get(0x0101), entries.get(0x0102)
    if (start_tag is None or length_tag is None or start_tag[:2] != (4, 1)
            or length_tag[:2] != (4, 1)):
        raise ValueError('missing_scalar')
    start, length = base + start_tag[2], length_tag[2]
    if not length or start < base or start + length > base + size:
        return {'status': 'contradiction', 'reason': 'outside_envelope',
                'offset': start, 'length': length}
    occupied = spans + [(base+a, base+b) for a, b in inner_spans]
    if any(start < b and start + length > a for a, b in occupied):
        raise ValueError('jpeg_metadata_overlap')
    if length < 4 or data[start:start+2] != b'\xff\xd8':
        return {'status': 'contradiction', 'reason': 'missing_soi',
                'offset': start, 'length': length}
    try:
        marker = validate_jpeg(data, start, length)
    except (ValueError, IndexError):
        return {'status': 'unknown', 'reason': 'marker_unsupported',
                'offset': start, 'length': length}
    if marker['marker_status'] != 'exact_eoi':
        return {'status': 'contradiction', 'reason': 'endpoint_mismatch',
                'offset': start, 'length': length}
    return {'status': 'ok', 'offset': start, 'length': length,
            'width': marker['width'], 'height': marker['height']}


def measure(data):
    try:
        metadata = candidate(data)
    except (ValueError, IndexError, KeyError, struct.error) as exc:
        metadata = {'status': 'unknown', 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}
    try:
        selected = jpeg_dc.find_preview(data)
        if selected is None:
            raise ValueError('no_preview')
        area, start, length, width, height = selected
        # The legacy selector keeps the first greatest-area result; any tied
        # candidate must therefore occur later in its SOI scan order.
        later = jpeg_dc.find_preview(data[start+3:])
        if later is not None and later[0] == area:
            raise ValueError('scanner_tie')
        marker = validate_jpeg(data, start, length)
        if marker['marker_status'] != 'exact_eoi' or (width, height) != (marker['width'], marker['height']):
            raise ValueError('scanner_marker')
        scanner = {'status': 'ok', 'offset': start, 'length': length, 'width': width, 'height': height}
    except (ValueError, IndexError) as exc:
        scanner = {'status': 'unknown', 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}
    if metadata['status'] == 'ok' and scanner['status'] == 'ok':
        relation = 'match' if all(metadata[k] == scanner[k] for k in ('offset', 'length', 'width', 'height')) else 'mismatch'
    else:
        relation = 'unknown'
    return {'candidate': metadata, 'scanner': scanner, 'relation': relation}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    ap.add_argument('--frozen')
    ap.add_argument('--sample', action='append', nargs=2, required=True, metavar=('ID', 'PATH'))
    args = ap.parse_args()
    expected = DISCOVERY + (EXTENSION if args.phase == 'verification' else [])
    if [sid for sid, _ in args.sample] != expected or bool(args.frozen) != (args.phase == 'verification'):
        ap.error('fixed phase order and frozen discovery required')
    previous = None
    if args.frozen:
        with open(args.frozen, encoding='utf-8') as f:
            previous = json.load(f)
        if previous.get('phase') != 'discovery':
            raise ValueError('invalid_frozen')
    rows = []
    for sid, path in args.sample:
        if sid == EXTENSION[0] and rows != previous.get('samples'):
            raise ValueError('discovery_mismatch')
        name, digest = SAMPLES[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as f:
                data = f.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('size_or_hash')
            row.update(measure(data))
        except (OSError, ValueError, IndexError, struct.error) as exc:
            row.update(candidate={'status': 'unknown', 'reason': type(exc).__name__},
                       scanner={'status': 'unknown', 'reason': type(exc).__name__}, relation='unknown')
        rows.append(row)
    print(json.dumps({'phase': args.phase, 'samples': rows}, indent=2))
    return int(any(r['candidate']['status'] == 'unknown' or r['scanner']['status'] == 'unknown' for r in rows))


if __name__ == '__main__':
    sys.exit(main())
