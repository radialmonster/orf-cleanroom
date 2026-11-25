"""Test two fixed legacy extent bases and one inner IFD shape (#949).

This is a bounded structural hypothesis, not a private tag interpretation.
No offset, signature or alternative inner-layout search is performed.
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from makernote_prefix_audit import Reader
from strip_start_audit import independent_strips

SAMPLES = {
    '1800': ('Olympus - E-1 - 16bit (4:3).ORF', '042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c'),
    '2878': ('Olympus - E-300 - 16bit (4:3).ORF', '6d818dbff78b3e2efa4835f568d04733052b9211e6bc65b0a3748a841170e95b'),
    '1799': ('Olympus - C5060WZ - 12bit (4:3).ORF', '3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd'),
    '780': ('Olympus - C7070WZ - 12bit (4:3).ORF', '9d55506f9d6ee31d2d4c4b6df0dcd1d016d358b3e5eb4ed31edd7227dfefd5f8'),
    '3540': ('Olympus - E-500 - 16bit (4:3).ORF', 'fa5a4759b2de2b573f59629ad1baf64ad04a85fb8fe1fb3cbf68e08a42fff4f0'),
}
COHORTS = {'discovery': ('1800', '2878', '1799', '780'), 'reserved': ('3540',)}
TYPES = {1:1, 2:1, 3:2, 4:4, 5:8, 6:1, 7:1, 8:2, 9:4, 10:8, 11:4, 12:8}


def shape(data, order):
    """One nonempty IFD at block offset zero, block-relative values only."""
    def u(pos, size):
        if pos < 0 or pos + size > len(data):
            raise ValueError('bounds')
        return int.from_bytes(data[pos:pos+size], order)
    count = None
    end = None
    failed_entry = None
    try:
        count = u(0, 2)
        if not 1 <= count <= 4096:
            raise ValueError('entry_count')
        end = 2 + 12*count + 4
        if end > len(data):
            raise ValueError('table_bounds')
        previous = -1
        for i in range(count):
            failed_entry = i
            at = 2 + 12*i
            tag, typ, n = u(at, 2), u(at+2, 2), u(at+4, 4)
            if tag <= previous:
                raise ValueError('tag_order')
            previous = tag
            if typ not in TYPES or n == 0:
                raise ValueError('field_shape')
            size = TYPES[typ] * n
            if size > 4:
                offset = u(at+8, 4)
                if offset < end or offset + size > len(data):
                    raise ValueError('value_bounds')
        failed_entry = None
        if u(end-4, 4) != 0:
            raise ValueError('next_ifd')
        return {'status': 'match', 'entries': count, 'table_bytes': end}
    except ValueError as exc:
        return {'status': 'mismatch', 'reason': str(exc), 'entry_count': count,
                'required_table_bytes': end, 'failed_entry': failed_entry}


def bases(base, size, top_end, entries, strips):
    """Interpret type-7 slots under file-absolute and MakerNote-relative bases."""
    if any(tag not in entries for tag in (0x2040, 0x2050)):
        return {'status': 'unavailable', 'reason': 'top_entry_absent'}
    if any(entries[tag][0] != 7 or entries[tag][1] <= 4 for tag in (0x2040, 0x2050)):
        return {'status': 'unavailable', 'reason': 'unsupported_entry_shape'}
    out = {}
    for label, origin in (('absolute', 0), ('makernote_relative', base)):
        spans = [(origin + entries[t][2], origin + entries[t][2] + entries[t][1]) for t in (0x2040, 0x2050)]
        reasons = []
        if any(a < base or b > base + size for a, b in spans):
            reasons.append('outside_envelope')
        if any(a < base+top_end and b > base for a, b in spans):
            reasons.append('header_or_top_overlap')
        if any(a < d and b > c for a, b in spans for c, d in strips):
            reasons.append('strip_overlap')
        if spans[0][0] < spans[1][1] and spans[0][1] > spans[1][0]:
            reasons.append('block_overlap')
        out[label] = {'status': 'valid' if not reasons else 'invalid',
                      'spans': [list(x) for x in spans], 'reasons': reasons}
    valid = [k for k, v in out.items() if v['status'] == 'valid']
    return {'status': 'unique' if len(valid) == 1 else ('ambiguous' if valid else 'no_common_base'),
            'selected': valid[0] if len(valid) == 1 else None, 'candidates': out}


def measure(data):
    geometry, _ = independent_strips(data)
    strips = [(a, a+n) for a, n in zip(geometry['strip_offsets'], geometry['strip_byte_counts'])]
    order = 'little' if data[:2] == b'II' else 'big'
    outer = Reader(data, order, strips)
    if outer.uint(2, 2) not in (42, 0x4f52, 0x5352):
        raise ValueError('magic')
    outer.spans = [(0, 8)]
    root = outer.directory(outer.uint(4, 4))
    exif = outer.directory(outer.pointer(root, 0x8769))
    note = exif.get(0x927c)
    if note is None or note[0] != 7 or note[1] < 14:
        raise ValueError('maker_envelope')
    size, base = note[1], outer.uint(note[2], 4)
    if any(base < b and base+size > a for a, b in outer.spans):
        raise ValueError('maker_directory_overlap')
    blob = outer.block(base, size)
    if blob[:8] not in (b'OLYMP\0\x01\0', b'OLYMP\0\x02\0'):
        return {'status': 'unsupported_header'}
    reader = Reader(blob, order)
    reader.spans = [(0, 8)]
    top = reader.directory(8)
    top_end = 8 + 6 + 12*len(top)
    entries = {tag: (top[tag][0], top[tag][1], reader.uint(top[tag][2], 4))
               for tag in (0x2040, 0x2050) if tag in top}
    decision = bases(base, size, top_end, entries, strips)
    if decision['status'] == 'unique':
        spans = decision['candidates'][decision['selected']]['spans']
        decision['inner'] = {format(tag, '04x'): shape(data[a:b], order)
                             for tag, (a, b) in zip((0x2040, 0x2050), spans)}
    return {'status': 'ok', 'width': geometry['width'], 'height': geometry['height'],
            'maker_start': base, 'maker_bytes': size, 'top_end_relative': top_end,
            'entries': {format(t, '04x'): {'type': v[0], 'count': v[1]} for t, v in entries.items()},
            'extent_comparison': decision}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'invalid arguments\n')


def main():
    parser = SafeParser(description=__doc__)
    parser.add_argument('--cohort', choices=tuple(COHORTS), default='discovery')
    parser.add_argument('--sample', action='append', nargs=2, required=True, metavar=('ID', 'PATH'))
    args = parser.parse_args()
    if any(sid not in COHORTS[args.cohort] for sid, _ in args.sample) or len({x[0] for x in args.sample}) != len(args.sample):
        parser.error('identity')
    rows = []
    for sid, path in args.sample:
        name, digest = SAMPLES[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            with open(path, 'rb') as f:
                data = f.read(160*1024*1024+1)
            if len(data) > 160*1024*1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('size_or_hash')
            row['result'] = measure(data)
        except (OSError, ValueError, IndexError, KeyError, TypeError) as exc:
            row['result'] = {'status': 'unknown', 'reason': str(exc) if isinstance(exc, ValueError) else type(exc).__name__}
        rows.append(row)
    print(json.dumps({'cohort': args.cohort, 'samples': rows}, allow_nan=False))
    return int(any(row['result']['status'] == 'unknown' for row in rows))


if __name__ == '__main__':
    sys.exit(main())
