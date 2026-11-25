"""Test literal zero-run support before comparing two fixed k=5 traversals."""
from bisect import bisect_left, bisect_right
from collections import Counter
from hashlib import sha256
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motif_interior_probe import OCTETS, SafeParser, independent_strips, interior, motif_positions

PINS = {
    '1993': '0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8',
    '1997': '89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a',
    'P1010019.ORF': '5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75',
    'P1010017.ORF': '431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5',
}


def runs(bits, offset):
    return [(offset + m.start(), offset + m.end())
            for m in re.finditer(r'(?<=1)0{12,}(?=1)', bits)]


def supported(raw_runs, starts, a, b):
    """Require both flanking ones to be strictly inside the tested interior."""
    return [u for u, v in raw_runs[bisect_right(starts, a):bisect_left(starts, b)] if v < b]


def measure(payload, width, em5=False):
    if width != (4640 if em5 else 5240):
        raise ValueError('unexpected_width')
    pitch = 6 * width + 12
    tolerance = max(64, pitch // 100)
    start = 40 + (620 * pitch if em5 else 0)
    end = 40 + (1200 if em5 else 400) * pitch
    if len(payload) * 8 < end:
        raise ValueError('incomplete_window')
    motifs = motif_positions(payload, start, end)
    bits = ''.join(OCTETS[x] for x in payload[start//8:(end+7)//8])[:end-start]
    raw_runs = runs(bits, start)
    starts = [u for u, _ in raw_runs]
    edges = qualified = escaped_edges = coincident = 0
    outcomes = [Counter(), Counter()]
    joint = Counter()
    joint_endpoint = Counter()
    cap_only_coincident = 0
    for a in motifs:
        left = bisect_left(motifs, a + pitch - tolerance)
        right = bisect_right(motifs, a + pitch + tolerance)
        for b in motifs[left:right]:
            edges += 1
            found = supported(raw_runs, starts, a+48, b)
            if not found:
                continue
            qualified += 1
            escape_starts = []
            l = interior(payload, a+48, b, 5, False)
            c = interior(payload, a+48, b, 5, True, escape_starts)
            escaped_edges += bool(escape_starts)
            coincident += sum(x in found for x in escape_starts)
            paired = []
            endpoints = []
            for totals, r in zip(outcomes, (l, c)):
                success = r['endpoint'] and r['words'] == width - 6
                totals['endpoint'] += r['endpoint']
                totals['endpoint_and_target_words'] += success
                totals['completed_escapes'] += r['escapes']
                totals[r['reason']] += 1
                paired.append(str(int(success)))
                endpoints.append(str(int(r['endpoint'])))
            cap_only_coincident += int(paired == ['0', '1'] and any(x in found for x in escape_starts))
            joint[''.join(paired)] += 1
            joint_endpoint[''.join(endpoints)] += 1
    result = dict(window=[start, end], pitch=pitch, tolerance=tolerance, width=width,
                target_words=width-6, motifs=len(motifs), eligible_edges=edges,
                window_flanked_runs=len(raw_runs), run_bearing_edges=qualified,
                edges_with_completed_escape=escaped_edges, escapes_at_supported_run_start=coincident,
                joint_success=dict(joint), joint_endpoint=dict(joint_endpoint),
                literal=dict(outcomes[0]), capped=dict(outcomes[1]),
                status=('escape_support' if escaped_edges else
                        'no_completed_escape' if qualified else
                        'no_run_bearing_edge' if edges else 'no_motif_edge'))
    if em5:
        result['cap_only_success_with_coincident_escape'] = cap_only_coincident
    return result


def main():
    p = SafeParser(description=__doc__)
    p.add_argument('--sample', required=True, metavar='PATH')
    p.add_argument('--repeat', action='store_true')
    p.add_argument('--em5', action='store_true')
    a = p.parse_args()
    ident = ('P1010017.ORF' if a.repeat else 'P1010019.ORF') if a.em5 else ('1997' if a.repeat else '1993')
    pin = PINS[ident]
    try:
        with open(a.sample, 'rb') as f:
            data = f.read(128 * 1024 * 1024 + 1)
        if len(data) > 128 * 1024 * 1024 or sha256(data).hexdigest() != pin:
            raise ValueError('size_or_hash')
        geo, payload = independent_strips(data)
        result = measure(payload, geo['width'], a.em5)
    except (OSError, ValueError, IndexError, KeyError, TypeError) as exc:
        safe = {'unexpected_width', 'incomplete_window', 'size_or_hash'}
        reason = str(exc) if isinstance(exc, ValueError) and str(exc) in safe else type(exc).__name__
        result = {'status': 'unknown', 'reason': reason}
    print(json.dumps({'id': ident, 'sha256': pin, 'result': result}, allow_nan=False))
    return int(result['status'] == 'unknown')


if __name__ == '__main__':
    sys.exit(main())
