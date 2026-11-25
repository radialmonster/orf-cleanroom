"""Compare four fixed candidate grammars on all near-pitch white-file motif edges.

Edges share motifs and are not independent physical boundaries. The adjacent
repeat band is explicit and does not reuse discovery counts as an expectation.
"""
import argparse
import bisect
from collections import Counter, defaultdict
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motif_interior_probe as old

NAME = 'PA210010.ORF'
SHA = old.SAMPLES[NAME]
CONFIGS = (('literal_k4', 4, False), ('literal_k5', 5, False),
           ('capped_k4', 4, True), ('capped_k5', 5, True))


def analyze(payload, width, repeat=False, expected=None):
    if width != 5220:
        raise ValueError('unsupported_width')
    pitch = 6 * width + 12
    tolerance = max(64, pitch // 100)
    start = 40 + (400 * pitch if repeat else 0)
    end = start + 400 * pitch
    if end > len(payload) * 8:
        raise ValueError('incomplete_window')
    positions = old.motif_positions(payload, start, end)
    edges = []
    incoming = Counter()
    for i, p in enumerate(positions):
        a = max(i + 1, bisect.bisect_left(positions, p + pitch - tolerance))
        b = bisect.bisect_right(positions, p + pitch + tolerance)
        for q in positions[a:b]:
            edges.append((p, q))
            incoming[q] += 1
    if expected is not None and (len(positions), len(edges)) != expected:
        raise ValueError('discovery_selector_mismatch')
    outgoing = Counter(a for a, _ in edges)
    summaries = {name: {'edges': len(edges), 'exact_endpoint': 0,
                         'endpoint_and_target_words': 0, 'completed_words': 0,
                         'completed_escapes': 0, 'reasons': Counter()}
                 for name, _, _ in CONFIGS}
    joint = Counter()
    strata = defaultdict(Counter)
    sources = {name: defaultdict(list) for name, _, _ in CONFIGS}
    for a, b in edges:
        mask = ''
        for name, k, capped in CONFIGS:
            r = old.interior(payload, a + 48, b, k, capped)
            success = r['endpoint'] and r['words'] == width - 6
            cell = summaries[name]
            cell['exact_endpoint'] += int(r['endpoint'])
            cell['endpoint_and_target_words'] += int(success)
            cell['completed_words'] += r['words']
            cell['completed_escapes'] += r['escapes']
            cell['reasons'][r['reason']] += 1
            sources[name][a].append(success)
            mask += '1' if success else '0'
        joint[mask] += 1
        strata['source_degree'][str(outgoing[a]) + ':' + mask] += 1
        strata['target_degree'][str(incoming[b]) + ':' + mask] += 1
        strata['gap_mod6'][str((b-a) % 6) + ':' + mask] += 1
    source_results = {}
    for name, _, _ in CONFIGS:
        c = Counter('all' if all(v) else 'some' if any(v) else 'none'
                    for v in sources[name].values())
        source_results[name] = {key: c[key] for key in ('all', 'some', 'none')}
    return {'status': 'ok' if edges else 'sparse_no_edges', 'window_start': start,
            'window_end': end, 'pitch': pitch, 'tolerance': tolerance,
            'motifs': len(positions), 'eligible_directed_edges': len(edges),
            'source_motifs_with_edges': len(outgoing), 'target_motifs_with_edges': len(incoming),
            'source_motifs_without_edges': len(positions) - len(outgoing),
            'target_motifs_without_edges': len(positions) - len(incoming),
            'target_words': width - 6, 'joint_success_mask_order': [x[0] for x in CONFIGS],
            'joint_success_masks': dict(sorted(joint.items())), 'grammars': summaries,
            'source_outcomes': source_results,
            'edge_strata_masks': {k: dict(sorted(v.items())) for k, v in strata.items()}}


def main():
    p = old.SafeParser(description=__doc__)
    p.add_argument('--sample', required=True, metavar='PATH')
    p.add_argument('--repeat', action='store_true')
    args = p.parse_args()
    report = {'name': NAME, 'sha256': SHA, 'band': 'repeat' if args.repeat else 'discovery'}
    try:
        with open(args.sample, 'rb') as f:
            data = f.read(128 * 1024 * 1024 + 1)
        if len(data) > 128 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != SHA:
            raise ValueError('size_or_hash')
        geometry, payload = old.independent_strips(data)
        report.update(width=geometry['width'], height=geometry['height'],
                      payload_bytes=len(payload))
        report['result'] = analyze(payload, geometry['width'], args.repeat,
                                   None if args.repeat else (791, 1568))
        report['status'] = 'ok'
    except (OSError, ValueError, IndexError, KeyError, TypeError) as exc:
        safe_reasons = {'size_or_hash', 'unsupported_width', 'incomplete_window',
                        'discovery_selector_mismatch'}
        reason = str(exc) if isinstance(exc, ValueError) and str(exc) in safe_reasons else type(exc).__name__
        report.update(status='unknown', reason=reason)
    print(json.dumps(report, allow_nan=False))
    return int(report['status'] != 'ok')


if __name__ == '__main__':
    sys.exit(main())
