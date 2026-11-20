#!/usr/bin/env python3
"""Compare scanner-selected JPEG extent with TIFF tags 513/514.

Only IFD0, next IFDs and SubIFDs are traversed. MakerNotes and JPEG-nested
metadata are excluded. Comparisons are descriptive, not conformance claims.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc

HASHES = {
    '1994': 'f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23',
    '1995': '8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f',
    '1996': 'eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2',
    '3800': '1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f',
    '3802': '83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46',
    '3804': 'd831692b608471ad64667eb2485bab553de0ddb9366d384c4ecb731092b5dc42',
}
NAMES = {sid: ('Olympus - E-M1MarkII - 16bit (4:3).' if sid.startswith('19')
               else 'Olympus - E-M1MarkIII - 16bit (4:3).') +
         ('ORI' if sid in ('1995', '3802', '3804') else 'ORF') for sid in HASHES}


def validate_jpeg(data, start, length):
    end = start + length
    if start < 0 or end > len(data) or data[start:start+2] != b'\xff\xd8':
        raise ValueError('jpeg_bounds')
    p, scan, frame = start + 2, False, None
    while p < end:
        if scan and data[p] != 0xff:
            p += 1
            continue
        if data[p] != 0xff:
            raise ValueError('marker_structure')
        while p < end and data[p] == 0xff:
            p += 1
        if p >= end:
            raise ValueError('marker_truncated')
        marker = data[p]
        p += 1
        if scan and (marker == 0 or 0xd0 <= marker <= 0xd7):
            continue
        if marker == 0xd9:
            if not scan or frame is None:
                raise ValueError('eoi')
            return {'marker_status': 'exact_eoi' if p == end else 'trailing_after_eoi',
                    'width': frame[0], 'height': frame[1], 'eoi_length': p - start}
        if scan or marker in (0, 0xd8) or 0xd0 <= marker <= 0xd7:
            raise ValueError('unsupported_marker')
        if p + 2 > end:
            raise ValueError('segment_bounds')
        size = int.from_bytes(data[p:p+2], 'big')
        if size < 2 or p + size > end:
            raise ValueError('segment_bounds')
        if marker == 0xc0:
            if frame is not None or size < 11:
                raise ValueError('sof0_shape')
            height = int.from_bytes(data[p+3:p+5], 'big')
            width = int.from_bytes(data[p+5:p+7], 'big')
            components = data[p+7]
            ids = [data[p + 8 + 3 * i] for i in range(components)] if size == 8 + 3 * components else []
            if (data[p+2] != 8 or not width or not height or not components
                    or len(ids) != components or len(set(ids)) != components):
                raise ValueError('sof0_shape')
            frame = (width, height, ids)
        if marker == 0xda:
            if frame is None or size < 8:
                raise ValueError('sos_shape')
            components = data[p+2]
            if not components or size != 6 + 2 * components:
                raise ValueError('sos_shape')
            scan_ids = [data[p+3+2*i] for i in range(components)]
            if (len(set(scan_ids)) != components or set(scan_ids) != set(frame[2])
                    or data[p+3+2*components:p+6+2*components] != b'\x00\x3f\x00'):
                raise ValueError('sos_shape')
        p += size
        if marker == 0xda:
            scan = True
    raise ValueError('missing_eoi')


def declared(data):
    if len(data) < 8 or data[:2] not in (b'II', b'MM'):
        raise ValueError('tiff_header')
    e = '<' if data[:2] == b'II' else '>'

    def read(fmt, pos):
        return struct.unpack_from(e + fmt, data, pos)

    if read('H', 2)[0] not in (42, 0x4f52, 0x5352):
        raise ValueError('tiff_magic')
    root = read('I', 4)[0]
    if not root:
        raise ValueError('missing_ifd0')
    pending, seen, declarations = [root], set(), []
    disabled = orphan_length = 0
    while pending:
        off = pending.pop()
        if not off:
            continue
        if off < 8 or off in seen or len(seen) >= 128 or off + 2 > len(data):
            raise ValueError('ifd_graph')
        seen.add(off)
        n = read('H', off)[0]
        end = off + 2 + 12 * n
        if end + 4 > len(data):
            raise ValueError('ifd_bounds')
        tags = {}
        for i in range(n):
            pos = off + 2 + 12 * i
            tag, typ, count, value = read('HHII', pos)
            if tag in tags:
                raise ValueError('duplicate_tag')
            tags[tag] = (typ, count, value)
        pending.append(read('I', end)[0])
        if 330 in tags:
            typ, count, value = tags[330]
            if typ not in (4, 13) or count < 1 or count > 128:
                raise ValueError('subifd_link')
            if count == 1:
                targets = (value,)
            else:
                if value < 8 or value + count * 4 > len(data):
                    raise ValueError('subifd_link')
                targets = read(str(count) + 'I', value)
            if not all(targets):
                raise ValueError('subifd_link')
            pending.extend(targets)
        has_offset, has_length = 513 in tags, 514 in tags
        if not has_offset and not has_length:
            continue
        if not has_offset:
            orphan_length += 1
            continue
        if tags[513][:2] != (4, 1):
            raise ValueError('pair_type')
        start = tags[513][2]
        if not start:
            disabled += 1
            continue
        if not has_length:
            raise ValueError('incomplete_pair')
        if tags[514][:2] != (4, 1):
            raise ValueError('pair_type')
        length = tags[514][2]
        if start < 8 or not length:
            raise ValueError('incomplete_pair')
        try:
            marker = validate_jpeg(data, start, length)
        except ValueError as exc:
            marker = {'marker_status': 'unknown', 'marker_reason': str(exc)}
        declarations.append({'ifd_offset': off, 'offset': start, 'length': length, **marker})
    return len(seen), declarations, disabled, orphan_length


def measure(data):
    selected = jpeg_dc.find_preview(data)
    if selected is None:
        raise ValueError('no_scanned_preview')
    _, start, length, width, height = selected
    scanned = validate_jpeg(data, start, length)
    if scanned['marker_status'] != 'exact_eoi':
        raise ValueError('scanner_trailing')
    if (scanned['width'], scanned['height']) != (width, height):
        raise ValueError('scanner_geometry')
    n_ifds, rows, disabled, orphan_length = declared(data)
    by_start = {}
    for row in rows:
        by_start.setdefault(row['offset'], set()).add(row['length'])
    if any(len(lengths) > 1 for lengths in by_start.values()):
        status = 'conflicting_declared_lengths'
    elif any(x['marker_status'] == 'unknown' for x in rows):
        status = 'unknown_declared_marker'
    elif any(x['offset'] == start and x['length'] == length for x in rows):
        status = 'exact_match'
    elif any(x['offset'] == start for x in rows):
        status = 'same_start_different_length'
    elif rows:
        status = 'other_declared_jpeg_only'
    else:
        status = 'no_declared_pair'
    return {'classification': status, 'ifds_visited': n_ifds,
            'disabled_offsets': disabled, 'orphan_lengths': orphan_length,
            'scanner': {'offset': start, 'length': length,
                        'width': width, 'height': height}, 'declared': rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    ap.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'))
    args = ap.parse_args()
    order = ['1994', '1995', '3800', '3802']
    if args.phase == 'verification':
        order += ['1996', '3804']
    if [s[0] for s in args.sample] != order:
        ap.error('sample IDs must match fixed phase order')
    rows = []
    for sid, path in args.sample:
        row = {'id': sid, 'name': NAMES[sid], 'sha256': HASHES[sid]}
        try:
            with open(path, 'rb') as f:
                data = f.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024:
                raise ValueError('size_limit')
            if hashlib.sha256(data).hexdigest() != HASHES[sid]:
                raise ValueError('hash_mismatch')
            result = measure(data)
            unknown = result['classification'] in ('unknown_declared_marker', 'conflicting_declared_lengths')
            row.update(status='unknown' if unknown else 'ok', **result)
        except (OSError, ValueError, IndexError, struct.error) as exc:
            row.update(status='unknown', reason=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'phase': args.phase, 'samples': rows}, indent=2))
    return int(any(r['status'] != 'ok' for r in rows))


if __name__ == '__main__':
    sys.exit(main())
