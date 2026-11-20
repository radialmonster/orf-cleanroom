#!/usr/bin/env python3
"""Inventory one hypothetical JP4493551B2 direct BYTE-tag packaging.

This does not identify a codec, tag meaning, or payload boundaries. MakerNotes
and other private structures are outside the traversed scope. The phase fixes
the public identities and expected hashes. Output contains no paths or bytes.
Declared directory links may point into strip bytes; overlapping directories
and candidates are rejected before candidate value classification.
"""
import argparse
import hashlib
import json
import struct
import sys

SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1,
         8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}
LINKS = {0x14a, 0x8769, 0x8825, 0xa005}
SAMPLES = {
    '1993': ('0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8',
             (5240, 3912), 'Olympus - E-M1MarkII - 16bit (4:3).ORF'),
    '1994': ('f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23',
             (10400, 7792), 'Olympus - E-M1MarkII - 16bit (4:3).ORF'),
    '1997': ('89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a',
             (5240, 3912), 'Olympus - E-M1MarkII - 16bit (4:3).ORI'),
    '7265': ('c7bd43b29ed89542058534b867fa894b8550d1960503cf4b4cb9f5912fd242b3',
             (10400, 7792), 'OM System - OM-1 Mark II - 16bit (4:3).orf'),
}


def inventory(data):
    if data[:2] not in (b'II', b'MM'):
        raise ValueError('header')
    e = '<' if data[:2] == b'II' else '>'

    def unpack(fmt, off):
        return struct.unpack_from(e + fmt, data, off)

    if len(data) < 8 or unpack('H', 2)[0] not in (42, 0x4f52, 0x5352):
        raise ValueError('header')
    todo = [unpack('I', 4)[0]]
    seen, directories, entries, directory_spans, link_spans = set(), [], [], [], []
    maker_notes = 0
    while todo:
        off = todo.pop()
        if not off:
            continue
        if off in seen or len(seen) >= 128:
            raise ValueError('repeated_or_excessive_ifd')
        seen.add(off)
        if off < 8 or off + 2 > len(data):
            raise ValueError('ifd_bounds')
        count = unpack('H', off)[0]
        end = off + 2 + count * 12
        if end + 4 > len(data):
            raise ValueError('ifd_bounds')
        directory_spans.append((off, end + 4))
        tags = {}
        for i in range(count):
            p = off + 2 + 12 * i
            tag, typ, n = unpack('HHI', p)
            if tag in tags or typ not in SIZES:
                raise ValueError('duplicate_or_unknown_type')
            size = SIZES[typ] * n
            start = p + 8 if size <= 4 else unpack('I', p + 8)[0]
            valid = 8 <= start <= len(data) and size <= len(data) - start
            entry = (tag, typ, n, start, size, valid, len(directories))
            tags[tag] = entry
            entries.append(entry)
            if tag == 0x927c:
                maker_notes += 1
            if tag in LINKS:
                if (typ not in (4, 13) or not valid or not n or n > 128
                        or (tag != 0x14a and n != 1)):
                    raise ValueError('unresolved_ifd_link')
                targets = unpack(str(n) + 'I', start)
                if not all(targets):
                    raise ValueError('unresolved_ifd_link')
                if size > 4:
                    link_spans.append((start, start + size))
                todo.extend(targets)
        todo.append(unpack('I', end)[0])
        directories.append(tags)

    def integers(entry):
        _, typ, n, start, _, valid, _ = entry
        if not valid or typ not in (3, 4) or not n:
            raise ValueError('invalid_geometry')
        return unpack(str(n) + ('H' if typ == 3 else 'I'), start)

    candidates = []
    for tags in directories:
        if 0x117 not in tags:
            continue
        counts = integers(tags[0x117])
        if not all(counts):
            raise ValueError('invalid_geometry')
        candidates.append((sum(counts), tags, counts))
    if not candidates:
        raise ValueError('no_strip_ifd')
    highest = max(x[0] for x in candidates)
    selected = [x for x in candidates if x[0] == highest]
    if len(selected) != 1:
        raise ValueError('ambiguous_strip_ifd')
    _, tags, counts = selected[0]
    try:
        width, = integers(tags[0x100])
        height, = integers(tags[0x101])
        offsets = integers(tags[0x111])
    except (KeyError, ValueError):
        raise ValueError('invalid_geometry')
    if not width or not height or width % 8 or height % 8 or len(offsets) != len(counts):
        raise ValueError('incompatible_geometry')
    spans = sorted((o, o + n) for o, n in zip(offsets, counts))
    if any(a < 8 or b > len(data) for a, b in spans) or any(y[0] < x[1] for x, y in zip(spans, spans[1:])):
        raise ValueError('invalid_strip_extent')
    if any(a < d and b > c for a, b in directory_spans for c, d in spans):
        raise ValueError('ifd_overlaps_strip')
    if any(a < d and b > c for a, b in link_spans for c, d in spans):
        raise ValueError('ifd_link_overlaps_strip')
    nblocks = (width // 8) * (height // 8)
    packed = nblocks // 4 + 1
    found = []
    for tag, typ, n, start, size, valid, ordinal in entries:
        if typ != 1 or n not in (nblocks, packed):
            continue
        row = {'ifd_ordinal': ordinal, 'tag': tag, 'count': n, 'in_bounds': valid}
        if valid:
            overlap = any(start < b and start + size > a for a, b in spans)
            row['strip_overlap'] = overlap
            if not overlap:
                values = data[start:start + size]
                if n == nblocks:
                    row['byte_choices_0_2'] = all(v <= 2 for v in values)
                if n == packed:
                    row['packed_choices_0_2'] = {
                        order: all(((values[i // 4] >> shift[i % 4]) & 3) != 3
                                   for i in range(nblocks))
                        for order, shift in (('msb_first', (6, 4, 2, 0)),
                                             ('lsb_first', (0, 2, 4, 6)))
                    }
        found.append(row)
    unresolved = any(not x['in_bounds'] or x.get('strip_overlap', False) for x in found)
    compatible = any(x.get('byte_choices_0_2') or
                     any(x.get('packed_choices_0_2', {}).values()) for x in found)
    outcome = 'unresolved' if unresolved else ('compatible' if compatible else 'no_compatible')
    byte_entries = [x for x in entries if x[1] == 1]
    return {'status': 'ok', 'outcome': outcome, 'width': width, 'height': height,
            'blocks': nblocks, 'packed_count': packed, 'ifds_visited': len(seen),
            'maker_notes_unvisited': maker_notes, 'byte_entries': len(byte_entries),
            'byte_entries_out_of_bounds': sum(not x[5] for x in byte_entries),
            'candidates': found}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=('discovery', 'verification'), default='discovery')
    ap.add_argument('--sample', nargs=2, action='append', required=True,
                    metavar=('ID', 'PATH'))
    args = ap.parse_args(argv)
    ids = ['1993', '1994'] + (['1997', '7265'] if args.phase == 'verification' else [])
    if [x[0] for x in args.sample] != ids:
        ap.error('sample IDs must match the fixed phase order')
    rows = []
    for sid, path in args.sample:
        digest, geometry, name = SAMPLES[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as f:
                data = f.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024:
                raise ValueError('size_limit')
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('hash_mismatch')
            result = inventory(data)
            if (result['width'], result['height']) != geometry:
                raise ValueError('geometry_mismatch')
            row.update(result)
        except (OSError, ValueError, struct.error) as exc:
            row.update(status='unknown', reason=(str(exc) if isinstance(exc, ValueError) else type(exc).__name__))
        rows.append(row)
    print(json.dumps({'results': rows}, indent=2))
    return int(any(r['status'] != 'ok' or r.get('outcome') == 'unresolved' for r in rows))


if __name__ == '__main__':
    sys.exit(main())
