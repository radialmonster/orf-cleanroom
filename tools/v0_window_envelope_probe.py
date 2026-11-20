#!/usr/bin/env python3
"""Fixed and refitted toy envelopes on V0 windows; aggregate diagnostics only."""
import json
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sensor_rejection_controls as c
import sensor_window_scale_probe as scale
from v0_sensor_controls import SafeParser, geometry, read_verified

SAMPLES = {
    '1800': (
        'Olympus - E-1 - 16bit (4:3).ORF',
        '042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c',
    ),
    '2151': (
        'Olympus - E-400 - 16bit (4:3).ORF',
        '1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b',
    ),
    '5424': (
        'Olympus - E-10 - 16bit (4:3).ORF',
        '2bfdade72439017a60a47aad1e5bbcb1aca36f2be7a21e94a4257a678fb6f4da',
    ),
}


def training(multiplier):
    width, height = scale.scale_dimensions(multiplier)
    rows, bounds = [], []
    for scene in c.SCENES:
        for noise in c.NOISE:
            for seed in c.DEVELOPMENT_SEEDS:
                values = c.synthetic(scene, noise, seed, width, height)
                rows.append({'features': c.features(values, width, height)})
                bounds.append({'scene': scene, 'noise': noise, 'seed': seed,
                               'zero': values.count(0), 'max_code': values.count(c.MAX_CODE)})
    return {'limits': c.envelope(rows), 'training_bound_counts': bounds}


def measure(data, multipliers, fixed, refitted):
    info = geometry(data)
    reports, counts = [], {}
    for multiplier in multipliers:
        width, height = scale.scale_dimensions(multiplier)
        windows = scale.extract_v0_windows(data, info, width, height)
        counts[multiplier] = {
            rule: {mapping: {'accepted': 0, 'rejected': 0} for mapping in c.MAPPINGS}
            for rule in ('fixed', 'refitted')
        }
        for label in ('top', 'middle', 'bottom'):
            window = windows[label]
            stored = window['raw_words']
            shifted = window['shifted_words']
            trials = []
            for mapping in c.MAPPINGS:
                values = c.transform(shifted, mapping)
                features = c.features(values, width, height)
                fixed_reasons = c.classify(features, fixed)
                refitted_reasons = c.classify(features, refitted[multiplier]['limits'])
                for rule, reasons in (('fixed', fixed_reasons), ('refitted', refitted_reasons)):
                    counts[multiplier][rule][mapping]['rejected' if reasons else 'accepted'] += 1
                trials.append({'mapping': mapping, 'features': features,
                               'changed_values': sum(a != b for a, b in zip(shifted, values)),
                               'fixed_rejected_by': fixed_reasons,
                               'refitted_rejected_by': refitted_reasons})
            reports.append({'scale': multiplier, 'width': width, 'height': height,
                            'window': label, 'x': window['x'], 'y': window['y'],
                            'stored_word_features': c.features(stored, width, height),
                            'stored_min': min(stored), 'stored_max': max(stored),
                            'nonzero_low_nibbles': sum(bool(v & 15) for v in stored),
                            'shift4_min': min(shifted), 'shift4_max': max(shifted),
                            'trials': trials})
    return {'geometry': info, 'windows': reports, 'counts': counts}


def main(argv=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument('--phase', choices=('discovery', 'verification'), required=True,
                        help='use scales 1, 2, 4, adding scale 8 in verification')
    parser.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'FILE'),
                        help='verified CC0 file; supply IDs 1800, 2151, 5424 in that order')
    args = parser.parse_args(argv)
    if tuple(x[0] for x in args.sample) != tuple(SAMPLES):
        parser.error('fixed sample order required')
    multipliers = (1, 2, 4) if args.phase == 'discovery' else (1, 2, 4, 8)
    refitted = {m: training(m) for m in multipliers}
    fixed = refitted[1]['limits']
    output = {'phase': args.phase, 'fixed_limits': fixed, 'training': refitted, 'samples': []}
    failed = False
    for sid, path in args.sample:
        name, digest = SAMPLES[sid]
        row = {'id': sid, 'name': name, 'sha256': digest}
        try:
            row.update(measure(read_verified(Path(path), digest), multipliers, fixed, refitted), status='ok')
        except (OSError, ValueError, struct.error) as exc:
            row.update(status='unknown', error_type=type(exc).__name__)
            failed = True
        output['samples'].append(row)
    print(json.dumps(output, allow_nan=False))
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
