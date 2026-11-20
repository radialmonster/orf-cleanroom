#!/usr/bin/env python3
"""Compare an independent TIFF strip reader with existing clean-room locators.

Supports specs/V2.md G4 and lead #246. Select the unique IFD with the largest
sum of StripByteCounts, without changing any declared offset. Report container
geometry, literal startup zero bits and full extracted-byte agreement. This
does not establish where coded samples begin, what a prefix means or a codec.

Verify CC0 provenance separately. --sample takes PUBLIC_ID PUBLIC_NAME SHA256
PATH, may repeat, and prints only identities and aggregates. A failed input is
reported as unknown and gives exit status 1; other inputs still run. No writes,
network, image output, offset search or candidate-token parsing are performed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import signature
from orf_tokens import locate_data
from payload_zero_run_probe import census
from strip_contiguity_audit import audit as existing_geometry


class ContainerError(ValueError):
    pass


def independent_strips(data):
    """Read TIFF directories directly; do not use an existing TIFF reader."""
    if data[:2] not in (b'II', b'MM'):
        raise ContainerError('unsupported_byte_order')
    order = 'little' if data[:2] == b'II' else 'big'

    def integer(offset, size):
        if offset < 0 or offset + size > len(data):
            raise ContainerError('truncated_directory_or_value')
        return int.from_bytes(data[offset:offset + size], order)

    magic = integer(2, 2)
    if magic not in (42, 0x4f52, 0x5352):
        raise ContainerError('unsupported_magic')
    root = integer(4, 4)
    pending, seen, directories = [root], set(), []
    needed = {0x100, 0x101, 0x102, 0x103, 0x10f, 0x110,
              0x111, 0x117, 0x14a}
    while pending:
        offset = pending.pop(0)
        if offset == 0 or offset in seen:
            continue
        seen.add(offset)
        count = integer(offset, 2)
        end = offset + 2 + 12 * count
        following = integer(end, 4)
        tags, entries = {}, {}
        for index in range(count):
            entry = offset + 2 + 12 * index
            tag, kind, length = (integer(entry, 2), integer(entry + 2, 2),
                                 integer(entry + 4, 4))
            if tag not in needed:
                continue
            if tag in entries:
                raise ContainerError('duplicate_relevant_tag')
            entries[tag] = entry
            if kind not in (2, 3, 4, 13):
                raise ContainerError('unsupported_relevant_tag_type')
            size = {2: 1, 3: 2, 4: 4, 13: 4}[kind]
            total = size * length
            position = entry + 8 if total <= 4 else integer(entry + 8, 4)
            if position + total > len(data):
                raise ContainerError('tag_value_outside_file')
            if kind == 2:
                tags[tag] = data[position:position + total].split(b'\0', 1)[0].decode('ascii').strip()
            else:
                tags[tag] = [integer(position + size * i, size) for i in range(length)]
        directories.append((offset, tags, entries))
        pending.append(following)
        pending.extend(tags.get(0x14a, []))
    candidates = []
    for offset, tags, entries in directories:
        if 0x117 not in tags:
            continue
        counts = tags[0x117]
        if not isinstance(counts, list) or not counts or any(c <= 0 for c in counts):
            raise ContainerError('invalid_strip_counts')
        candidates.append((sum(counts), offset, tags, entries))
    if not candidates:
        raise ContainerError('no_strip_ifd')
    largest = max(c[0] for c in candidates)
    winners = [c for c in candidates if c[0] == largest]
    if len(winners) != 1:
        raise ContainerError('ambiguous_largest_ifd')
    _, offset, tags, entries = winners[0]
    offsets, counts = tags.get(0x111), tags[0x117]
    if not isinstance(offsets, list) or not offsets or len(offsets) != len(counts):
        raise ContainerError('mismatched_strip_tables')
    for tag in (0x100, 0x101):
        if not isinstance(tags.get(tag), list) or len(tags[tag]) != 1 or tags[tag][0] <= 0:
            raise ContainerError('invalid_dimensions')
    if any(o + c > len(data) for o, c in zip(offsets, counts)):
        raise ContainerError('strip_outside_file')
    spans = sorted(zip(offsets, counts))
    if any(o + c > next_o for (o, c), (next_o, _) in zip(spans, spans[1:])):
        raise ContainerError('overlapping_strips')
    payload = b''.join(data[o:o + c] for o, c in zip(offsets, counts))
    result = {
        'header': data[:4].hex(), 'root_ifd': root, 'selected_ifd': offset,
        'ifds_visited': len(directories), 'file_bytes': len(data),
        'width': tags[0x100][0], 'height': tags[0x101][0],
        'bits_per_sample': tags.get(0x102), 'compression': tags.get(0x103),
        'strip_count': len(counts), 'strip_offsets': offsets,
        'strip_byte_counts': counts, 'payload_bytes': len(payload),
        'offsets_mod16': [o % 16 for o in offsets],
        'bytes_after_last_physical_strip': len(data) - max(o + c for o, c in spans),
        'strip_offsets_entry': entries[0x111], 'strip_counts_entry': entries[0x117],
    }
    return result, payload


def startup_zeros(payload):
    """Count literal leading zero bits, independently of any candidate words."""
    zeros = 0
    for value in payload:
        if value:
            return zeros + 8 - value.bit_length()
        zeros += 8
    return None  # no one bit found


def compare_snapshot(data):
    result, payload = independent_strips(data)
    geometry = existing_geometry(data)
    width, height, located = locate_data(data)
    zeros = startup_zeros(payload)
    prefix = census(payload[:64])
    startup = prefix['terminated']['startup']
    checks = {
        'geometry': all(result[k] == geometry[k] for k in
                        ('width', 'height', 'strip_count', 'payload_bytes')),
        'locator_dimensions': (width, height) == (result['width'], result['height']),
        'full_payload_bytes': located == payload,
        'literal_prefix_census': (zeros is not None and zeros < min(64, len(payload)) * 8
                                  and startup['exact39'] == int(zeros == 39)
                                  and startup['exact47'] == int(zeros == 47)
                                  and startup['at_least39'] == int(zeros >= 39)),
    }
    result.update(initial_zero_bits=zeros, agreements=checks,
                  geometry_summary=geometry)
    return result


def measure(path, digest):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ContainerError('hash_mismatch')
    result = compare_snapshot(data)
    s = signature(path)
    if s['sha256'] != digest:
        raise ContainerError('input_changed_between_reads')
    result['make'], result['model'] = s['make'], s['model']
    result['size_class'], result['bpp'] = s['size_class'], s['bpp']
    result['agreements']['signature'] = (
        (s['payload_w'], s['payload_h'], s['payload_offset'], s['payload_bytes']) ==
        (result['width'], result['height'], result['strip_offsets'][0], result['payload_bytes']))
    result['status'] = 'agree' if all(result['agreements'].values()) else 'disagree'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', nargs=4, action='append', required=True,
                        metavar=('PUBLIC_ID', 'PUBLIC_NAME', 'SHA256', 'PATH'))
    args = parser.parse_args(argv)
    seen = set()
    for sid, name, digest, _ in args.sample:
        if (not re.fullmatch(r'[1-9][0-9]*', sid) or not name or not name.isprintable()
                or any(c in name for c in '/\\') or not re.fullmatch(r'[0-9a-f]{64}', digest)):
            parser.error('invalid public sample identity')
        if sid in seen or digest in seen:
            parser.error('duplicate public identity or content')
        seen.update((sid, digest))
    results = []
    for sid, name, digest, path in args.sample:
        record = {'id': sid, 'name': name, 'sha256': digest}
        try:
            record.update(measure(path, digest))
        except ContainerError as exc:
            record.update(status='unknown', error=str(exc))
        except (OSError, ValueError, TypeError, IndexError, KeyError, struct.error) as exc:
            record.update(status='unknown', error=type(exc).__name__)
        results.append(record)
    source_names = ('strip_start_audit.py', 'strip_contiguity_audit.py',
                    'orf_signature.py', 'orf_tokens.py', 'payload_zero_run_probe.py')
    sources = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
               for name in source_names}
    complete = all(r['status'] == 'agree' for r in results)
    print(json.dumps({'results': results, 'all_agree': complete, 'source_sha256': sources}, indent=2))
    return int(not complete)


if __name__ == '__main__':
    sys.exit(main())
