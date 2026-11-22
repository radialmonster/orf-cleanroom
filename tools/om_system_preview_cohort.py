#!/usr/bin/env python3
"""Measure two unchanged metadata locators on the frozen 104-file roster.

96 discovery records must replay before eight reserved records are measured.
The scanner never selects or repairs the combined metadata result. Exit 1
with a complete report includes unsupported scope or locator contradictions;
input_status distinguishes those cases from identity/read/hash failures.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import om_system_preview_locator as locator
import preview_locator_cohort as cohort

RESERVED = {'1432', '5284', '5424', '6347', '6946', '7269', '7803', '8553'}
KEYS = ('offset', 'length', 'width', 'height')


def combine(old, new):
    choices = [('olympus', old), ('om_system', new)]
    valid = [(name, row) for name, row in choices if row['status'] == 'ok']
    contradictions = [name for name, row in choices if row['status'] == 'contradiction']
    if contradictions:
        return {'status': 'contradiction', 'reason': 'candidate_contradiction', 'rules': contradictions}
    if len(valid) > 1:
        return {'status': 'contradiction', 'reason': 'rule_overlap'}
    if not valid:
        return {'status': 'unknown', 'reason': 'no_supported_layout'}
    name, row = valid[0]
    return dict(status='ok', rule=name, **{key: row[key] for key in KEYS})


def relation(metadata, scanner):
    if metadata['status'] != 'ok' or scanner['status'] != 'ok':
        return 'unknown'
    return 'match' if all(metadata[key] == scanner[key] for key in KEYS) else 'mismatch'


def measure(data):
    # This function computes both metadata candidates before invoking the scanner.
    measured = locator.measure(data)
    old, new, scanned = measured['previous'], measured['candidate'], measured['scanner']
    combined = combine(old, new)
    return {'olympus': old, 'om_system': new, 'combined': combined, 'scanner': scanned,
            'relations': {name: relation(value, scanned) for name, value in
                          (('olympus', old), ('om_system', new), ('combined', combined))}}


def unknown(reason):
    return {**{key: {'status': 'unknown', 'reason': reason}
               for key in ('olympus', 'om_system', 'combined', 'scanner')},
            'relations': {key: 'unknown' for key in ('olympus', 'om_system', 'combined')}}


def run_one(record, inventory, manifest, corpus):
    sid, name, digest = record
    row = {'id': sid, 'name': name, 'sha256': digest, 'input_status': 'unknown'}
    local, size_class, reason = cohort.identity(record, inventory, manifest)
    row['size_class'] = size_class
    if reason:
        row.update(unknown(reason))
        return row
    try:
        root = Path(corpus).resolve(strict=True)
        target = (root/local).resolve(strict=True)
        if target.parent != root:
            row.update(unknown('outside_corpus'))
            return row
        with open(target, 'rb') as stream:
            data = stream.read(128*1024*1024+1)
        if len(data) > 128*1024*1024 or hashlib.sha256(data).hexdigest() != digest:
            row.update(unknown('size_or_hash'))
        else:
            row.update(input_status='ok', **measure(data))
    except (OSError, ValueError) as exc:
        row.update(unknown(type(exc).__name__))
    return row


def counts(rows):
    result = {}
    for key in ('olympus', 'om_system', 'combined'):
        counter = Counter((row[key]['status'], row['scanner']['status'], row['relations'][key]) for row in rows)
        result[key] = [{'metadata': a, 'scanner': b, 'relation': c, 'count': n}
                       for (a, b, c), n in sorted(counter.items())]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    parser.add_argument('--frozen')
    parser.add_argument('--inventory', required=True)
    parser.add_argument('--corpus', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--roster', required=True)
    args = parser.parse_args()
    if bool(args.frozen) != (args.phase == 'verification'):
        parser.error('verification requires frozen discovery report')
    with open(args.roster, encoding='utf-8') as stream:
        roster = cohort.roster(stream.read())
    if not RESERVED.issubset({r[0] for r in roster}):
        raise ValueError('reserved_roster')
    with open(args.inventory, encoding='utf-8') as stream:
        inventory = json.load(stream)
    if isinstance(inventory, dict):
        inventory = inventory['files']
    with open(args.manifest, 'rb') as stream:
        manifest_bytes = stream.read()
    manifest = list(csv.DictReader(io.StringIO(manifest_bytes.decode('utf-8-sig'), newline='')))
    config = {'roster_sha256': cohort.ROSTER_DIGEST,
              'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
              'reserved': sorted(RESERVED, key=int)}
    frozen = None
    if args.frozen:
        with open(args.frozen, encoding='utf-8') as stream:
            frozen = json.load(stream)
        if frozen.get('phase') != 'discovery' or frozen.get('config') != config:
            raise ValueError('invalid_frozen')
    discovery = [r for r in roster if r[0] not in RESERVED]
    reserved = [r for r in roster if r[0] in RESERVED]
    rows = [run_one(record, inventory, manifest, args.corpus) for record in discovery]
    if frozen is not None:
        if rows != frozen.get('samples'):
            raise ValueError('discovery_mismatch')
        rows.extend(run_one(record, inventory, manifest, args.corpus) for record in reserved)
    print(json.dumps({'phase': args.phase, 'config': config, 'samples': rows,
                      'counts': counts(rows), 'input_counts': dict(Counter(r['input_status'] for r in rows))}, indent=2))
    return int(any(row['input_status'] != 'ok' or row['combined']['status'] != 'ok'
                   or row['scanner']['status'] != 'ok' or row['relations']['combined'] == 'mismatch' for row in rows))


if __name__ == '__main__':
    sys.exit(main())
