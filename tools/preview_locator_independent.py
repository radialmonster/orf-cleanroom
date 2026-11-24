#!/usr/bin/env python3
"""Independent metadata and marker implementation of the fixed #920 rule.

No repository TIFF reader, preview scanner or JPEG checker is imported. This
checks a declared interval, not JPEG entropy conformance or physical geometry.
Retained CC0 records supply public identities; their prior verification remains
the caller's responsibility. The tool reads samples and prints metadata only.
"""
import argparse
import hashlib
import json
import sys


class View:
    """Bounded classic-TIFF directory reads with an explicit pointer origin."""
    def __init__(self, data, order):
        if order not in ('little', 'big'):
            raise ValueError('byte_order')
        self.data, self.order, self.spans = data, order, []

    def chunk(self, at, size):
        if at < 0 or size < 0 or at+size > len(self.data):
            raise ValueError('bounds')
        return self.data[at:at+size]

    def integer(self, at, size):
        return int.from_bytes(self.chunk(at, size), self.order)

    def directory(self, at):
        count = self.integer(at, 2)
        if count > 4096:
            raise ValueError('directory_limit')
        end = at+6+12*count
        self.chunk(at, end-at)
        if any(at < b and end > a for a, b in self.spans):
            raise ValueError('directory_overlap')
        self.spans.append((at, end))
        entries = {}
        for slot in range(at+2, end-4, 12):
            tag = self.integer(slot, 2)
            if tag in entries:
                raise ValueError('duplicate_tag')
            entries[tag] = (self.integer(slot+2, 2), self.integer(slot+4, 4), slot+8)
        return entries, self.integer(end-4, 4)

    def extent(self, entry, unit):
        _, count, slot = entry
        size = unit*count
        at = slot if size <= 4 else self.integer(slot, 4)
        self.chunk(at, size)
        return at, size

    def numbers(self, entry):
        typ, count, _ = entry
        unit = {3: 2, 4: 4, 13: 4}.get(typ)
        if unit is None or count < 1 or count > 65536:
            raise ValueError('numeric_shape')
        at, size = self.extent(entry, unit)
        if size > 4:
            if any(at < b and at+size > a for a, b in self.spans):
                raise ValueError('value_directory_overlap')
        return [self.integer(p, unit) for p in range(at, at+size, unit)]

    def scalar(self, tags, tag, typ=4):
        entry = tags.get(tag)
        if entry is None or entry[:2] != (typ, 1):
            raise ValueError('scalar_shape')
        return self.numbers(entry)[0]


def maker_context(data):
    if data[:2] not in (b'II', b'MM'):
        raise ValueError('tiff_order')
    view = View(data, 'little' if data[:2] == b'II' else 'big')
    if view.integer(2, 2) not in (42, 0x4f52, 0x5352):
        raise ValueError('tiff_magic')
    view.spans.append((0, 8))
    root = view.integer(4, 4)
    tags, _ = view.directory(root)
    exif, _ = view.directory(view.scalar(tags, 0x8769))
    entry = exif.get(0x927c)
    if entry is None or entry[0] != 7 or entry[1] < 18:
        raise ValueError('maker_shape')
    base, size = view.extent(entry, 1)
    if any(base < b and base+size > a for a, b in view.spans):
        raise ValueError('maker_directory_overlap')
    blob = view.chunk(base, size)
    if blob[:8] != b'OLYMPUS\0' or blob[8:10] not in (b'II', b'MM'):
        raise ValueError('unsupported_maker_header')
    maker = View(blob, 'little' if blob[8:10] == b'II' else 'big')
    maker.spans.append((0, 12))
    top, _ = maker.directory(12)
    return view, exif, maker, top, base, size


def jpeg_geometry(blob):
    """Independent single baseline-scan marker walk over the exact interval."""
    if blob[:2] != b'\xff\xd8':
        raise ValueError('jpeg_soi')
    pos, frame, scanning = 2, None, False
    while pos < len(blob):
        if scanning:
            pos = blob.find(b'\xff', pos)
            if pos < 0:
                break
        if blob[pos] != 255:
            raise ValueError('jpeg_marker')
        while pos < len(blob) and blob[pos] == 255:
            pos += 1
        if pos == len(blob):
            break
        code, pos = blob[pos], pos+1
        if scanning and (code == 0 or 208 <= code <= 215):
            continue
        if code == 217:
            if not scanning or frame is None or pos != len(blob):
                raise ValueError('jpeg_endpoint')
            return frame[:2]
        if scanning or code in (0, 216) or 208 <= code <= 215:
            raise ValueError('jpeg_unsupported')
        length = int.from_bytes(blob[pos:pos+2], 'big')
        if length < 2 or pos+length > len(blob):
            raise ValueError('jpeg_segment')
        body = blob[pos+2:pos+length]
        if code == 192:
            if frame is not None or len(body) < 9 or body[0] != 8:
                raise ValueError('jpeg_frame')
            h, w, n = int.from_bytes(body[1:3], 'big'), int.from_bytes(body[3:5], 'big'), body[5]
            ids = list(body[6::3])
            if not w or not h or not n or len(body) != 6+3*n or len(set(ids)) != n:
                raise ValueError('jpeg_frame')
            frame = (w, h, ids)
        elif code == 218:
            if frame is None or not body:
                raise ValueError('jpeg_scan')
            n = body[0]
            if (not n or len(body) != 4+2*n or body[-3:] != b'\0\x3f\0'
                    or sorted(body[1:1+2*n:2]) != sorted(frame[2])):
                raise ValueError('jpeg_scan')
            scanning = True
        pos += length
    raise ValueError('jpeg_no_eoi')


def candidate(data):
    outer, _, maker, top, base, size = maker_context(data)
    settings, _ = maker.directory(maker.scalar(top, 0x2020, 13))
    relative = maker.scalar(settings, 0x0101)
    length = maker.scalar(settings, 0x0102)
    if not length or relative+length > size:
        raise ValueError('outside_maker')
    spans = outer.spans + [(base+a, base+b) for a, b in maker.spans]
    start = base+relative
    if any(start < b and start+length > a for a, b in spans):
        raise ValueError('preview_metadata_overlap')
    width, height = jpeg_geometry(data[start:start+length])
    return {'status': 'ok', 'offset': start, 'length': length, 'width': width, 'height': height}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', required=True, help='retained verified public CC0 JSON records')
    parser.add_argument('--sample', action='append', nargs=2, required=True, metavar=('ID', 'PATH'))
    args = parser.parse_args()
    with open(args.records, encoding='utf-8') as stream:
        records = json.load(stream)
    if isinstance(records, dict):
        records = records['files']
    rows = []
    for sid, path in args.sample:
        hits = [r for r in records if str(r.get('id')) == sid]
        if len(hits) != 1 or hits[0].get('licence') != 'CC0':
            raise ValueError('identity_record')
        record = hits[0]
        row = {k: record[k] for k in ('id', 'name', 'sha256')}
        try:
            with open(path, 'rb') as stream:
                data = stream.read(128*1024*1024+1)
            if len(data) > 128*1024*1024 or hashlib.sha256(data).hexdigest() != record['sha256']:
                raise ValueError('size_or_hash')
            row['candidate'] = candidate(data)
        except (OSError, ValueError) as exc:
            row['candidate'] = {'status': 'unknown', 'reason':
                                str(exc) if isinstance(exc, ValueError) else type(exc).__name__}
        rows.append(row)
    print(json.dumps({'samples': rows}, indent=2))
    return int(any(r['candidate']['status'] != 'ok' for r in rows))


if __name__ == '__main__':
    sys.exit(main())
