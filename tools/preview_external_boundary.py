#!/usr/bin/env python3
"""Compare fixed scalar-derived extents with declared TIFF intervals.

No scanner, JPEG-marker parsing or entropy decoding is used. The known leading
MakerNote path and literal 0x0101/0x0102 are fixed hypotheses, not tag semantics.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preview_scalar_correspondence import fields

SAMPLES = {
    '792': ('Olympus - SH-2 - 12bit (4:3).ORF', '6e6b9b7dd9ded7c4b364b83116c817ca2d6daac15f2e9ef7796159b08c3288a1'),
    '1432': ('Olympus - XZ-2 - 12bit (4:3).orf', '675fefe7c9e99281783b987889d723b5f46692f5c20e19fed5e422c7c6d2636b'),
    '1759': ('Olympus - XZ-1 - 16bit (4:3).orf', '3f5fb6f36ad4132323cab790e30b0bc10217aa7fb703518005a5800c908ba8a3'),
    '2431': ('Olympus - XZ-10 - 12bit (4:3).ORF', 'a25383acad9b5bb0bb404715e0957f2eb80aa1aaad6c448a71025c03cfa631be'),
}
DISCOVERY = ['792', '1432', '1759']
EXTENSION = ['2431']


def header(data):
    if len(data) < 8 or data[:2] not in (b'II', b'MM'):
        raise ValueError('header')
    endian = '<' if data[:2] == b'II' else '>'
    magic, root = struct.unpack_from(endian + 'HI', data, 2)
    if magic not in (42, 0x4f52, 0x5352) or root < 8:
        raise ValueError('header')
    return endian, root


def scalar_interval(data):
    endian, root = header(data)
    occupied = [(0, 8)]
    outer = fields(data, root, endian, occupied=occupied)
    exif = outer.get(0x8769)
    if exif is None or exif[:2] != (4, 1) or exif[2] < 8:
        raise ValueError('exif_pointer')
    tags = fields(data, exif[2], endian, occupied=occupied)
    maker = tags.get(0x927c)
    if maker is None or maker[0] != 7 or maker[1] < 18:
        raise ValueError('maker_envelope')
    _, size, base = maker
    end = base + size
    if base < 8 or end > len(data) or any(base < b and end > a for a, b in occupied):
        raise ValueError('maker_envelope')
    if data[base:base+8] != b'OLYMPUS\0' or data[base+8:base+10] not in (b'II', b'MM'):
        raise ValueError('maker_header')
    inner_endian = '<' if data[base+8:base+10] == b'II' else '>'
    blob = data[base:end]
    inner = [(0, 12)]
    top = fields(blob, 12, inner_endian, occupied=inner)
    child = top.get(0x2020)
    if child is None or child[:2] != (13, 1) or child[2] < 12:
        raise ValueError('camera_settings')
    entries = fields(blob, child[2], inner_endian, occupied=inner)
    offset, length = entries.get(0x0101), entries.get(0x0102)
    if offset is None or length is None or offset[:2] != (4, 1) or length[:2] != (4, 1):
        raise ValueError('missing_scalar')
    start, stop = base + offset[2], base + offset[2] + length[2]
    if not length[2] or start < base or stop > len(data):
        raise ValueError('candidate_bounds')
    if any(start < b and stop > a for a, b in occupied + [(base+a, base+b) for a, b in inner]):
        raise ValueError('candidate_metadata_overlap')
    return {'status': 'ok', 'maker_start': base, 'maker_end': end,
            'candidate_start': start, 'candidate_end': stop,
            'start_minus_maker_end': start - end, 'end_minus_maker_end': stop - end,
            'contained': start >= base and stop <= end}


def outer_graph(data, forbidden=None):
    endian, root = header(data)
    seen, pending, occupied, directories, link_arrays = set(), [root], [(0, 8)], [], []
    while pending:
        off = pending.pop()
        if not off:
            continue
        if off in seen or off < 8 or len(seen) >= 128:
            raise ValueError('ifd_graph')
        seen.add(off)
        tags = fields(data, off, endian, forbidden=forbidden, occupied=occupied)
        directories.append((off, tags))
        count = struct.unpack_from(endian + 'H', data, off)[0]
        pending.append(struct.unpack_from(endian + 'I', data, off + 2 + 12 * count)[0])
        if 330 in tags:
            typ, n, value = tags[330]
            if typ not in (4, 13) or not 1 <= n <= 128:
                raise ValueError('subifd_link')
            if n == 1:
                targets = (value,)
            else:
                if value < 8 or value + 4 * n > len(data):
                    raise ValueError('subifd_link')
                if forbidden is not None and value < forbidden[1] and value + 4*n > forbidden[0]:
                    raise ValueError('subifd_candidate_overlap')
                link_arrays.append((value, value + 4*n))
                targets = struct.unpack_from(endian + str(n) + 'I', data, value)
            if not all(targets):
                raise ValueError('subifd_link')
            pending.extend(targets)
    if any(a < d and b > c for a, b in link_arrays for c, d in occupied):
        raise ValueError('subifd_table_overlap')
    if any(a[1] > b[0] for a, b in zip(sorted(link_arrays), sorted(link_arrays)[1:])):
        raise ValueError('subifd_table_overlap')
    return endian, directories


def declarations(data, dirs):
    spans, disabled, orphan = [], 0, 0
    for off, tags in dirs:
        a, b = tags.get(513), tags.get(514)
        if a is None:
            orphan += b is not None
            continue
        if a[:2] != (4, 1):
            raise ValueError('declaration_type')
        if not a[2]:
            disabled += 1
            continue
        if b is None or b[:2] != (4, 1) or not b[2] or a[2] < 8 or a[2] + b[2] > len(data):
            raise ValueError('declaration_bounds')
        spans.append({'ifd_offset': off, 'start': a[2], 'end': a[2] + b[2]})
    return spans, disabled, orphan


def strip_spans(data, endian, dirs, forbidden=None):
    def values(entry):
        typ, n, value = entry
        if typ not in (3, 4) or not 1 <= n <= 65536:
            raise ValueError('strip_table')
        unit = 2 if typ == 3 else 4
        if unit * n <= 4:
            raw = struct.pack(endian + 'I', value)[:unit*n]
        else:
            if value < 8 or value + unit*n > len(data):
                raise ValueError('strip_table')
            if forbidden is not None and value < forbidden[1] and value + unit*n > forbidden[0]:
                raise ValueError('strip_table_candidate_overlap')
            raw = data[value:value+unit*n]
        return struct.unpack(endian + str(n) + ('H' if typ == 3 else 'I'), raw)
    options = []
    for off, tags in dirs:
        if 279 in tags:
            counts = values(tags[279])
            if not all(counts):
                raise ValueError('strip_counts')
            options.append((sum(counts), off, tags, counts))
    if not options:
        raise ValueError('no_strip_ifd')
    largest = max(x[0] for x in options)
    winners = [x for x in options if x[0] == largest]
    if len(winners) != 1:
        raise ValueError('ambiguous_strip_ifd')
    _, off, tags, counts = winners[0]
    if 273 not in tags:
        raise ValueError('strip_offsets')
    offsets = values(tags[273])
    if len(offsets) != len(counts):
        raise ValueError('strip_offsets')
    spans = sorted((a, a+b) for a, b in zip(offsets, counts))
    if any(a < 8 or b > len(data) for a, b in spans) or any(x[1] > y[0] for x, y in zip(spans, spans[1:])):
        raise ValueError('strip_bounds')
    return off, spans


def measure(data):
    try:
        interval = scalar_interval(data)
    except (ValueError, IndexError, struct.error) as exc:
        interval = {'status': 'unknown', 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}
    try:
        forbidden = ((interval['candidate_start'], interval['candidate_end'])
                     if interval['status'] == 'ok' else None)
        endian, dirs = outer_graph(data, forbidden)
    except (ValueError, IndexError, struct.error) as exc:
        reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        return {'interval': interval, 'declarations': {'status': 'unknown', 'reason': reason},
                'strips': {'status': 'unknown', 'reason': reason}}
    try:
        spans, disabled, orphan = declarations(data, dirs)
        starts = {}
        for span in spans:
            starts.setdefault(span['start'], set()).add(span['end'])
        dec = {'status': 'ok', 'declared': spans, 'disabled': disabled, 'orphan': orphan,
               'conflicting_start_count': sum(len(ends) > 1 for ends in starts.values())}
        if interval['status'] == 'ok':
            p, q = interval['candidate_start'], interval['candidate_end']
            exact = sum(s['start'] == p and s['end'] == q for s in spans)
            different = sum(s['start'] == p and s['end'] != q for s in spans)
            if exact and different:
                relation = 'exact_with_conflict'
            elif exact > 1:
                relation = 'exact_aliases'
            elif exact:
                relation = 'unique_exact'
            elif different:
                relation = 'same_start_different_end'
            elif spans:
                relation = 'other_declarations'
            else:
                relation = 'no_positive_declaration'
            dec.update(exact_count=exact, same_start_different_end_count=different, relation=relation)
    except (ValueError, IndexError, struct.error) as exc:
        dec = {'status': 'unknown', 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}
    try:
        selected, spans = strip_spans(data, endian, dirs, forbidden)
        strips = {'status': 'ok', 'ifd_offset': selected, 'spans': spans}
        if interval['status'] == 'ok':
            p, q = interval['candidate_start'], interval['candidate_end']
            strips.update(exact_count=sum((a, b) == (p, q) for a, b in spans),
                          start_boundary_count=sum(p in (a, b) for a, b in spans),
                          end_boundary_count=sum(q in (a, b) for a, b in spans),
                          overlap_count=sum(p < b and q > a for a, b in spans))
    except (ValueError, IndexError, struct.error) as exc:
        strips = {'status': 'unknown', 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}
    return {'interval': interval, 'declarations': dec, 'strips': strips}


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
        try:
            with open(args.frozen, encoding='utf-8') as f:
                previous = json.load(f)
        except (OSError, ValueError):
            raise SystemExit('invalid_frozen') from None
        if not isinstance(previous, dict) or previous.get('phase') != 'discovery':
            raise SystemExit('invalid_frozen')
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
            reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            row.update({name: {'status': 'unknown', 'reason': reason} for name in ('interval', 'declarations', 'strips')})
        rows.append(row)
    print(json.dumps({'phase': args.phase, 'samples': rows}, indent=2))
    return int(any(row[k]['status'] != 'ok' for row in rows for k in ('interval', 'declarations', 'strips')))


if __name__ == '__main__':
    sys.exit(main())
