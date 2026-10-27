#!/usr/bin/env python3
"""Audit public sample capture-time metadata without printing timestamps or paths.

Supports: lead #318's remaining capture-group metadata question.
Use retained, previously verified licence records; no catalogue is queried.
Equal model and DateTimeOriginal are metadata coincidences only: they do not
establish the same physical body, capture independence, scene, mode, or cause.
Timezone, subsecond timing and camera clock accuracy are not evaluated.
The caller remains responsible for the original licence verification.
"""
import argparse
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capture_pair_calibration import file_meta
from manifest_rows import licence_records
from orf_signature import signature
from pixls_samples import by_hash, sha256_file


def audit(record_path, samples):
    records = list(licence_records(record_path))
    identities = {r['id']: r for r in records}
    restrictions = by_hash(records)
    selected, seen_ids, seen_hashes = [], set(), set()
    for rid, path in samples:
        if not re.fullmatch(r'[1-9][0-9]*', rid) or rid in seen_ids:
            raise ValueError('invalid or duplicate sample ID')
        seen_ids.add(rid)
        record = identities.get(rid)
        if record is None:
            raise ValueError('sample ID absent from retained records')
        digest = sha256_file(path)
        if digest != record['sha256'] or restrictions[digest]['licence'] != 'CC0':
            raise ValueError('sample hash or licence does not match retained records')
        if digest in seen_hashes:
            raise ValueError('duplicate sample content')
        seen_hashes.add(digest)
        selected.append((record, path, digest))

    rows, groups = [], {}
    for record, path, digest in selected:
        measured_hash, meta = file_meta(path)
        sig = signature(path)
        if measured_hash != digest or sig['sha256'] != digest:
            raise ValueError('sample changed while reading metadata')
        make, model = sig['make'], sig['model']
        valid_body = bool(make and model)
        available = meta['time'] is not None
        rows.append({'id': record['id'], 'name': record['name'], 'sha256': digest,
                     'make': make, 'model': model, 'datetime_original_available': available})
        if valid_body and available:
            groups.setdefault((make, model, meta['time']), []).append(record['id'])
    rows.sort(key=lambda row: int(row['id']))
    coincidences = [{'make': make, 'model': model, 'ids': sorted(ids, key=int)}
                    for (make, model, _), ids in groups.items() if len(ids) > 1]
    coincidences.sort(key=lambda group: tuple(map(int, group['ids'])))
    return {'schema_version': 1, 'samples': rows, 'summary': {'total': len(rows),
            'datetime_original_available': sum(r['datetime_original_available'] for r in rows),
            'camera_model_available': sum(bool(r['make'] and r['model']) for r in rows),
            'model_and_time_available': sum(len(ids) for ids in groups.values()),
            'distinct_model_time_groups': len(groups), 'repeated_model_time_groups': len(coincidences)},
            'same_model_time_groups': coincidences,
            'interpretation': 'Metadata coincidences only; same physical body, independent captures, scenes, modes, and causes are not established. Timezone, subseconds, and clock accuracy are not evaluated.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--licence-records', required=True, metavar='JSON')
    parser.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'))
    args = parser.parse_args(argv)
    try:
        report = audit(args.licence_records, args.sample)
    except (OSError, UnicodeError, ValueError, TypeError, IndexError, KeyError, struct.error):
        parser.error('invalid or unreadable records or sample metadata')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
