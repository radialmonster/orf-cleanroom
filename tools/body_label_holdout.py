#!/usr/bin/env python3
"""File-holdout body-label confounding diagnostic for #299; not variant discovery.

Input is aggregate output of payload_feature_probe.py plus public manifest.
File means use three declared equal-byte windows. Compare bpp, three raw-bit
features, and their union. Training-fold population variances standardize each
coordinate; zero-variance coordinates are omitted. Nearest standardized body
centroid wins (squared Euclidean distance); exact ties choose lexicographic
(make, model). No fitting uses the held-out file. All folds/distances remain
visible. File holdout is NOT capture/scene holdout: captures may be related.
No significance, causal attribution, clustering, independent-capture accuracy,
codec identity or variants follow. Neither windows nor bits are replication.
Reads inputs and prints aggregate JSON only; no raw files or previews are read.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
import re
import sys

FEATURES = ('bpp', 'one_fraction', 'transition_fraction', 'byte_entropy_bits')
ABLATIONS = {'bpp': (0,), 'bits': (1, 2, 3), 'union': (0, 1, 2, 3)}


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('expected finite numeric aggregate')
    return value


def cohort(report, manifest, ids):
    if not isinstance(report, dict):
        raise ValueError('feature report must be an object')
    if (len(ids) < 3 or len(set(ids)) != len(ids) or
            any(not isinstance(i, str) or not re.fullmatch(r'[0-9]+', i) for i in ids)):
        raise ValueError('need at least three unique numeric public IDs')
    if report.get('schema') not in ('raw-bit-window-features-v1', 'raw-bit-window-features-v2'):
        raise ValueError('unsupported feature schema')
    if report.get('window_count') != 3 or report.get('window_bytes') != 65536:
        raise ValueError('protocol requires three 65536-byte windows')
    measured = {}
    for row in report['samples']:
        key = row['pixls_id']
        if key in measured:
            raise ValueError('duplicate feature ID')
        measured[key] = row
    if any(row['pixls_id'] in ids for row in report.get('errors', [])):
        raise ValueError('selected feature error')
    rows = []
    for key in ids:
        sample = measured[key]
        candidates = {(row['sha256'], row['pixls_name'], row['make'], row['model'],
                       row['licence'], row['source']) for row in manifest if row['pixls_id'] == key}
        if len(candidates) != 1:
            raise ValueError('missing or conflicting manifest identity')
        digest, name, make, model, licence, source = candidates.pop()
        if (not re.fullmatch(r'[0-9a-f]{64}', digest) or
                digest != sample['sha256'] or name != sample['pixls_name'] or
                licence != 'CC0' or source != 'pixls' or not make or not model):
            raise ValueError('identity/provenance mismatch')
        if sample['size_class'] != 'variable':
            raise ValueError('compressed subset only')
        windows = sample['windows']
        if len(windows) != 3 or any(w['features']['bytes'] != 65536 for w in windows):
            raise ValueError('missing or unequal windows')
        width, height = sample['payload_width'], sample['payload_height']
        count = sample['payload_bytes']
        if any(type(x) is not int or x < 1 for x in (width, height, count)):
            raise ValueError('invalid geometry')
        for row in manifest:
            if row['pixls_id'] == key:
                for field, actual in (('payload_w', width), ('payload_h', height)):
                    declared = row.get(field)
                    if declared and int(declared) != actual:
                        raise ValueError('feature geometry conflicts with manifest')
        starts = [w['payload_byte_start'] for w in windows]
        if starts != [i * (count - 65536) // 2 for i in range(3)] or count < 3 * 65536:
            raise ValueError('window coordinates disagree with frozen protocol')
        values = [finite(sample['payload_bits_per_pixel'])]
        if values[0] != count * 8 / (width * height):
            raise ValueError('bpp disagrees with geometry')
        for feature in FEATURES[1:]:
            observations = [finite(w['features'][feature]) for w in windows]
            maximum = 8 if feature == 'byte_entropy_bits' else 1
            if any(not 0 <= x <= maximum for x in observations):
                raise ValueError('aggregate outside range')
            values.append(math.fsum(observations) / 3)
        rows.append({'pixls_id': key, 'pixls_name': name, 'sha256': digest,
                     'body': (make, model), 'features': values})
    if len({r['sha256'] for r in rows}) != len(rows):
        raise ValueError('identical-content ID aliases')
    return rows


def classify(rows, indices):
    folds = []
    for held, target in enumerate(rows):
        train = [r for i, r in enumerate(rows) if i != held]
        labels = sorted({tuple(r['body']) for r in train})
        means = [math.fsum(r['features'][j] for r in train) / len(train) for j in indices]
        variances = [math.fsum((r['features'][j] - means[k]) ** 2 for r in train) / len(train)
                     for k, j in enumerate(indices)]
        distances = []
        for label in labels:
            members = [r for r in train if tuple(r['body']) == label]
            centroid = [math.fsum(r['features'][j] for r in members) / len(members) for j in indices]
            distance = math.fsum((target['features'][j] - centroid[k]) ** 2 / variances[k]
                                 for k, j in enumerate(indices) if variances[k] > 0)
            distances.append({'body': label, 'training_files': len(members),
                              'squared_distance': distance, 'centroid_unscaled': centroid})
        winner = min(distances, key=lambda d: (d['squared_distance'], d['body']))['body']
        folds.append({'pixls_id': target['pixls_id'], 'actual': target['body'],
                      'predicted': winner, 'correct': tuple(target['body']) == winner,
                      'target_present_in_training': tuple(target['body']) in labels,
                      'training_means': means, 'training_population_variances': variances,
                      'active_features': [FEATURES[j] for k, j in enumerate(indices) if variances[k] > 0],
                      'distances': distances})
    confusion = Counter((tuple(f['actual']), f['predicted']) for f in folds)
    return {'features': [FEATURES[j] for j in indices], 'files': len(folds),
            'correct': sum(f['correct'] for f in folds),
            'target_absent_folds': sum(not f['target_present_in_training'] for f in folds),
            'confusion': [{'actual': a, 'predicted': b, 'files': n}
                          for (a, b), n in sorted(confusion.items())], 'folds': folds}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--features', required=True, help='aggregate feature JSON')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--ids', nargs='+', required=True)
    args = parser.parse_args(argv)
    try:
        with open(args.features, 'rb') as stream:
            raw_features = stream.read()
        with open(args.manifest, 'rb') as stream:
            raw_manifest = stream.read()
        rows = cohort(json.loads(raw_features), list(csv.DictReader(raw_manifest.decode('utf-8').splitlines())), args.ids)
        with open(__file__, 'rb') as stream:
            source_hash = hashlib.sha256(stream.read()).hexdigest()
        result = {'schema': 'body-label-file-holdout-v1', 'scope': __doc__,
                  'diagnostic_source_sha256': source_hash,
                  'feature_sources_sha256': json.loads(raw_features).get('sources_sha256', {}),
                  'feature_json_sha256': hashlib.sha256(raw_features).hexdigest(),
                  'manifest_sha256': hashlib.sha256(raw_manifest).hexdigest(),
                  'cohort': rows, 'ablations': {key: classify(rows, indices) for key, indices in ABLATIONS.items()}}
        print(json.dumps(result, sort_keys=True, indent=2))
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        print('invalid diagnostic input: ' + type(exc).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
