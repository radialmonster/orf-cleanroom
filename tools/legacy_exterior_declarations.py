"""Audit fixed exterior intervals against bounded outer TIFF declarations.

No target contents are interpreted. An inaccessible traversal branch is unknown.
"""
import argparse
import hashlib
import json
import struct

SAMPLES = {
    '1800': ('Olympus - E-1 - 16bit (4:3).ORF', '042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c', (3826, 3862)),
    '2878': ('Olympus - E-300 - 16bit (4:3).ORF', '6d818dbff78b3e2efa4835f568d04733052b9211e6bc65b0a3748a841170e95b', (4078, 4114)),
}
EXTENSION = {'3540': ('Olympus - E-500 - 16bit (4:3).ORF',
                      'fa5a4759b2de2b573f59629ad1baf64ad04a85fb8fe1fb3cbf68e08a42fff4f0',
                      (3982, 4018))}
SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}


def audit(data, target):
    """Return declaration intersections, retaining evidence on incomplete traversal."""
    lo, hi = target
    result = {'status': 'ok', 'target': [lo, hi], 'overlaps': [],
              'union_overlap_bytes': 0, 'visited_ifds': 0, 'issues': []}
    def issue(code):
        result['status'] = 'unknown'
        result['issues'].append(code)
    def intersects(a, b):
        return a < hi and lo < b
    def read(a, n):
        if a < 0 or n < 0 or a + n > len(data):
            raise ValueError('out_of_bounds')
        if intersects(a, a + n):
            raise ValueError('target_overlap')
        return data[a:a + n]
    def record(kind, start, end, ifd, tag=None, typ=None, count=None):
        if intersects(start, end):
            result['overlaps'].append({'kind': kind, 'ifd_offset': ifd, 'tag': tag,
                                       'start': start, 'end': end, 'type': typ, 'count': count,
                                       'overlap_bytes': min(end, hi) - max(start, lo)})
    if lo < 0 or hi <= lo or hi > len(data):
        issue('invalid_target')
        return result
    if intersects(0, 8):
        record('header', 0, 8, None)
        result['union_overlap_bytes'] = min(hi, 8) - lo
        issue('header_target_overlap')
        return result
    try:
        header = read(0, 8)
        endian = {b'II': '<', b'MM': '>'}.get(header[:2])
        if endian is None or struct.unpack(endian + 'H', header[2:4])[0] not in (42, 0x4f52, 0x5352):
            raise ValueError('unsupported_tiff')
        first = struct.unpack(endian + 'I', header[4:8])[0]
        if first < 8:
            raise ValueError('invalid_ifd0')
    except (ValueError, struct.error) as exc:
        issue(str(exc))
        return result
    pending = [first]
    visited = set()
    def values(entry, allowed):
        typ, count, slot, pos = entry
        if typ not in allowed or count < 1 or count > 65536:
            raise ValueError('unsupported_pointer_field')
        size = SIZES[typ] * count
        if size > 4 and pos < 8:
            raise ValueError('invalid_value_offset')
        raw = slot[:size] if size <= 4 else read(pos, size)
        fmt = {3: 'H', 4: 'I', 13: 'I'}[typ]
        return struct.unpack(endian + str(count) + fmt, raw)
    while pending:
        off = pending.pop(0)
        if off in visited:
            issue('duplicate_directory_reference')
            continue
        if len(visited) >= 128:
            issue('directory_limit')
            break
        visited.add(off)
        if off < 8:
            issue('invalid_directory_offset')
            continue
        try:
            count = struct.unpack(endian + 'H', read(off, 2))[0]
            end = off + 6 + 12 * count
            if end > len(data):
                raise ValueError('directory_out_of_bounds')
            record('directory', off, end, off)
            table = read(off, end - off)
        except (ValueError, struct.error) as exc:
            issue('directory_' + str(exc))
            continue
        result['visited_ifds'] += 1
        fields = {}
        for i in range(count):
            chunk = table[2 + 12*i:14 + 12*i]
            tag, typ, n = struct.unpack(endian + 'HHI', chunk[:8])
            slot = chunk[8:12]
            if tag in fields:
                issue('duplicate_tag')
                continue
            if typ not in SIZES or n == 0:
                issue('unsupported_field')
                continue
            size = SIZES[typ] * n
            pos = struct.unpack(endian + 'I', slot)[0] if size > 4 else None
            fields[tag] = (typ, n, slot, pos)
            if size > 4 and tag != 0x927c:
                if pos < 8 or pos + size > len(data):
                    issue('value_out_of_bounds')
                else:
                    record('value', pos, pos + size, off, tag, typ, n)
        nxt = struct.unpack(endian + 'I', table[-4:])[0]
        if nxt:
            pending.append(nxt)
        for tag in (330, 34665):
            if tag not in fields:
                continue
            try:
                entry = fields[tag]
                if tag == 34665 and (entry[0] != 4 or entry[1] != 1):
                    raise ValueError('unsupported_exif_pointer')
                ptrs = values(entry, (4, 13) if tag == 330 else (4,))
                if any(p < 8 for p in ptrs):
                    raise ValueError('invalid_pointer')
                pending.extend(ptrs)
            except (ValueError, struct.error) as exc:
                issue('link_' + str(exc))
        for a, b, kind in ((273, 279, 'strip'), (513, 514, 'jpeg')):
            if a not in fields:
                if b in fields:
                    issue('incomplete_' + kind + '_pair')
                continue
            try:
                av = values(fields[a], (3, 4) if kind == 'strip' else (4,))
                if kind == 'jpeg' and (len(av) != 1 or av[0] == 0):
                    if len(av) != 1:
                        raise ValueError('invalid_jpeg_offset')
                    continue
                if b not in fields:
                    raise ValueError('missing_extent_length')
                bv = values(fields[b], (3, 4) if kind == 'strip' else (4,))
                if len(av) != len(bv) or (kind == 'jpeg' and len(bv) != 1):
                    raise ValueError('extent_count_mismatch')
                for start, size in zip(av, bv):
                    if start < 8 or size == 0 or start + size > len(data):
                        raise ValueError('invalid_extent')
                    record(kind, start, start + size, off, a, fields[a][0], fields[a][1])
            except (ValueError, struct.error) as exc:
                issue(kind + '_' + str(exc))
    intervals = sorted((max(lo, x['start']), min(hi, x['end'])) for x in result['overlaps'])
    last = lo
    for start, end in intervals:
        result['union_overlap_bytes'] += max(0, end - max(last, start))
        last = max(last, end)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extension', action='store_true')
    parser.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'))
    args = parser.parse_args()
    ids = [x[0] for x in args.sample]
    cohort = EXTENSION if args.extension else SAMPLES
    if len(ids) != len(set(ids)) or any(x not in cohort for x in ids):
        parser.error('IDs must be distinct and drawn from the selected cohort')
    rows = []
    for ident, path in args.sample:
        name, expected, target = cohort[ident]
        row = {'id': ident, 'name': name, 'sha256': expected}
        try:
            with open(path, 'rb') as f:
                data = f.read(128 * 1024 * 1024 + 1)
            if len(data) > 128 * 1024 * 1024:
                raise ValueError('size_limit')
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('hash_mismatch')
            row.update(audit(data, target))
        except (OSError, ValueError) as exc:
            row.update(status='unknown', issues=[type(exc).__name__ if isinstance(exc, OSError) else str(exc)])
        rows.append(row)
    print(json.dumps({'samples': rows}, indent=2))
    return 0 if all(r['status'] == 'ok' for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
