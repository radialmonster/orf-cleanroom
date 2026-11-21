#!/usr/bin/env python3
"""Apply the fixed metadata-first JPEG locator to the 104-file #438 roster.

The seven TG/XZ identities are reserved for verification. The input inventory
must be previously verified CC0 provenance, not a new catalogue assertion.
No local paths, image bytes, or private identifiers are emitted.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_metadata_locator as locator

ROSTER_DIGEST = 'efa234dec110ced00a181296cb3ac316f4aee695aa6741e1d372c29c23accbf0'
RESERVED = {'1135', '1432', '1723', '1759', '2431', '3210', '6946'}


def roster(text):
    entries = re.findall(r'(?m)^- (\d+); ([^;]+); ([0-9a-f]{64})\s*$', text)
    entries.sort(key=lambda x: int(x[0]))
    canonical = ''.join('|'.join(x) + '\n' for x in entries).encode('utf-8')
    if (len(entries) != 104 or len({x[0] for x in entries}) != 104
            or len({x[2] for x in entries}) != 104
            or hashlib.sha256(canonical).hexdigest() != ROSTER_DIGEST
            or not RESERVED.issubset({x[0] for x in entries})):
        raise ValueError('roster_mismatch')
    return entries


def identity(record, inventory, manifest):
    sid, name, digest = record
    hits = [r for r in inventory if str(r.get('id')) == sid and r.get('name') == name
            and r.get('sha256') == digest and r.get('licence') == 'CC0']
    if (len(hits) != 1 or any(r.get('licence') != 'CC0' for r in inventory
                              if r.get('sha256') == digest)):
        return None, 'unknown', 'inventory_identity'
    local = (hits[0]['local_name'] if 'local_name' in hits[0] else
             sid + '_' + re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name))
    if (not isinstance(local, str) or local in ('', '.', '..')
            or not local.isprintable() or '/' in local or '\\' in local or ':' in local
            or os.path.basename(local) != local):
        return None, 'unknown', 'inventory_local_name'
    matches = [r for r in manifest if r.get('source') == 'pixls' and r.get('pixls_id') == sid
               and r.get('pixls_name') == name and r.get('sha256') == digest and r.get('licence') == 'CC0']
    if not matches:
        return None, 'unknown', 'manifest_identity'
    classes = {r.get('size_class') for r in matches}
    allowed = {'variable', 'packed-12', 'packed-12.8', 'packed-16'}
    size_class = next(iter(classes)) if len(classes) == 1 and next(iter(classes)) in allowed else 'unknown'
    return local, size_class, None


def summarize(rows):
    counter = Counter((r['candidate']['status'], r['scanner']['status'], r['relation']) for r in rows)
    return [{'candidate': a, 'scanner': b, 'relation': c, 'count': n}
            for (a, b, c), n in sorted(counter.items())]


def unknown(reason):
    return {'candidate': {'status': 'unknown', 'reason': reason},
            'scanner': {'status': 'unknown', 'reason': reason}, 'relation': 'unknown'}


def run_one(record, inventory, manifest, corpus):
    sid, name, digest = record
    row = {'id': sid, 'name': name, 'sha256': digest}
    local, size_class, reason = identity(record, inventory, manifest)
    row['size_class'] = size_class
    if reason:
        row.update(unknown(reason))
        return row
    try:
        root = Path(corpus).resolve(strict=True)
        target = (root / local).resolve(strict=True)
        if target.parent != root:
            row.update(unknown('outside_corpus'))
            return row
        with open(target, 'rb') as f:
            data = f.read(128 * 1024 * 1024 + 1)
        if len(data) > 128 * 1024 * 1024:
            row.update(unknown('size_limit'))
        elif hashlib.sha256(data).hexdigest() != digest:
            row.update(unknown('hash_mismatch'))
        else:
            row.update(locator.measure(data))
    except (OSError, ValueError) as exc:
        row.update(unknown(type(exc).__name__))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=('discovery', 'verification'), required=True)
    ap.add_argument('--inventory', required=True)
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--roster', required=True)
    ap.add_argument('--frozen')
    args = ap.parse_args()
    if bool(args.frozen) != (args.phase == 'verification'):
        ap.error('verification requires frozen discovery report')
    with open(args.roster, encoding='utf-8') as f:
        all_entries = roster(f.read())
    with open(args.inventory, 'rb') as f:
        inventory_bytes = f.read()
    loaded = json.loads(inventory_bytes)
    inventory = loaded.get('files') if isinstance(loaded, dict) else loaded
    if not isinstance(inventory, list) or not all(isinstance(r, dict) for r in inventory):
        raise ValueError('invalid_inventory')
    with open(args.manifest, 'rb') as f:
        manifest_bytes = f.read()
    manifest = list(csv.DictReader(io.StringIO(manifest_bytes.decode('utf-8-sig'), newline='')))
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    previous = None
    if args.frozen:
        with open(args.frozen, encoding='utf-8') as f:
            previous = json.load(f)
        if (previous.get('phase') != 'discovery' or previous.get('roster_sha256') != ROSTER_DIGEST
                or previous.get('manifest_sha256') != manifest_hash):
            raise ValueError('invalid_frozen')
    discover = [r for r in all_entries if r[0] not in RESERVED]
    reserved = [r for r in all_entries if r[0] in RESERVED]
    rows = [run_one(r, inventory, manifest, args.corpus) for r in discover]
    if previous is not None:
        if rows != previous.get('samples'):
            raise ValueError('discovery_mismatch')
        rows.extend(run_one(r, inventory, manifest, args.corpus) for r in reserved)
    result = {'phase': args.phase, 'roster_sha256': ROSTER_DIGEST,
              'manifest_sha256': manifest_hash,
              'samples': rows, 'counts': summarize(rows)}
    print(json.dumps(result, indent=2))
    return int(any(r['candidate']['status'] == 'unknown' or r['scanner']['status'] == 'unknown' for r in rows))


if __name__ == '__main__':
    sys.exit(main())
