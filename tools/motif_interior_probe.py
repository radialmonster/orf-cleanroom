"""Fixed literal motif edges and candidate interior parses for #339.

Motifs are selected from bits alone. Candidate words and intervals do not
establish physical rows, token values, a codec, or calibrated significance.
"""
import argparse
import bisect
from collections import Counter
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_start_audit import independent_strips

SAMPLES = {
    'PA210010.ORF': 'd055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e',
    'PA200010.ORF': 'b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4',
    'PA200012.ORF': 'c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7',
    'PA200011.ORF': 'a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3',
    'PA200015.ORF': '84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278',
    'P1010009.ORF': 'ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c',
    'P1010011.ORF': 'd34532152c79ef24b22c60c6cf743cef41fe28196b40fe16b557c16b7a7ea03d',
    'P1010013.ORF': '81acdd3675c329b351a634cfb4e22228f2db8df94f36480690e04416ded0817d',
    'P1010017.ORF': '431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5',
    'P1010018.ORF': 'e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f',
    'P1010019.ORF': '5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75',
}
COHORTS = {
    'discovery': ('PA210010.ORF', 'PA200010.ORF', 'PA200012.ORF'),
    'om3-repeat': ('PA200011.ORF', 'PA200015.ORF'),
    'em5-repeat': ('P1010009.ORF', 'P1010011.ORF', 'P1010013.ORF',
                   'P1010017.ORF', 'P1010018.ORF', 'P1010019.ORF'),
}
OCTETS = tuple(format(i, '08b') for i in range(256))
MOTIF = re.compile(r'(?=(?:100[01]{5}){6})')


def motif_positions(payload, start, end, chunk_bytes=131072):
    """All complete motif starts in [start,end), preserving overlap at chunks."""
    if start < 0 or end > 8*len(payload) or end < start or chunk_bytes < 8:
        raise ValueError('invalid_interval')
    positions = []
    for base in range(start // 8, (end + 7)//8, chunk_bytes):
        stop = min(len(payload), base + chunk_bytes + 6)
        bits = ''.join(OCTETS[b] for b in payload[base:stop])
        low = max(start, 8*base)
        high = min(end-48, 8*(base+chunk_bytes)-1)
        if high >= low:
            positions.extend(8*base+m.start() for m in MOTIF.finditer(bits, low-8*base, high-8*base+48))
    return positions


def unique_edges(positions, pitch, tolerance):
    """Return edges whose source has one outgoing and target one incoming."""
    outgoing, incoming = [], []
    for i, p in enumerate(positions):
        a = max(i+1, bisect.bisect_left(positions, p + pitch - tolerance))
        b = max(a, bisect.bisect_right(positions, p + pitch + tolerance))
        outgoing.append((a, b))
        a = min(i, bisect.bisect_left(positions, p - pitch - tolerance))
        b = min(i, bisect.bisect_right(positions, p - pitch + tolerance))
        incoming.append((a, b))
    return [(positions[i], positions[a]) for i, (a, b) in enumerate(outgoing)
            if b-a == 1 and incoming[a] == (i, i+1)]


def interior(payload, start, end, k, capped):
    """Parse complete words exactly up to the fixed end, no read past it."""
    pos = start
    words = escapes = 0
    while pos < end:
        word = pos
        q = 0
        while pos < end and not (payload[pos//8] & (128 >> (pos%8))):
            q += 1
            pos += 1
            if capped and q == 12:
                break
        if capped and q == 12:
            if pos + 12 > end:
                return {'endpoint': False, 'reason': 'escape_overrun', 'words': words,
                        'escapes': escapes, 'word_start': word}
            pos += 12
            escapes += 1
        else:
            if pos == end:
                return {'endpoint': False, 'reason': 'stop_overrun', 'words': words,
                        'escapes': escapes, 'word_start': word}
            pos += 1
            if pos + k > end:
                return {'endpoint': False, 'reason': 'suffix_overrun', 'words': words,
                        'escapes': escapes, 'word_start': word}
            pos += k
        words += 1
    return {'endpoint': True, 'reason': 'exact_end', 'words': words, 'escapes': escapes}


def measure(payload, width):
    if width < 7:
        raise ValueError('unsupported_width')
    pitch = 6*width + 12
    tolerance = max(64, pitch//100)
    if pitch - tolerance < 48:
        raise ValueError('overlapping_motif_range')
    end = min(len(payload)*8, 40 + 400*pitch)
    if end < 40:
        raise ValueError('short_payload')
    positions = motif_positions(payload, 40, end)
    eligible = sum(bisect.bisect_right(positions, p+pitch+tolerance) -
                   bisect.bisect_left(positions, p+pitch-tolerance) for p in positions)
    edges = unique_edges(positions, pitch, tolerance)
    configs = [('literal_k4', 4, False), ('literal_k5', 5, False),
               ('capped_k4', 4, True), ('capped_k5', 5, True)]
    summaries = {name: {'candidate_edges': len(edges), 'exact_endpoint': 0,
                         'endpoint_and_target_words': 0, 'target_words': width-6,
                         'completed_words': 0, 'completed_escapes': 0, 'reasons': Counter()}
                 for name, _, _ in configs}
    joint = Counter()
    for a, b in edges:
        mask = ''
        for name, k, capped in configs:
            result = interior(payload, a+48, b, k, capped)
            cell = summaries[name]
            success = result['endpoint'] and result['words'] == width-6
            mask += '1' if success else '0'
            cell['reasons'][result['reason']] += 1
            cell['exact_endpoint'] += result['endpoint']
            cell['endpoint_and_target_words'] += success
            cell['completed_words'] += result['words']
            cell['completed_escapes'] += result['escapes']
        joint[mask] += 1
    return {'status': 'ok' if edges else 'sparse_no_edges', 'window_start': 40,
            'window_end': end, 'pitch': pitch, 'tolerance': tolerance,
            'motifs': len(positions), 'eligible_directed_edges': eligible,
            'mutual_unique_edges': len(edges),
            'joint_success_mask_order': [c[0] for c in configs],
            'joint_success_masks': dict(sorted(joint.items())), 'grammars': summaries}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'invalid arguments\n')


def main():
    parser = SafeParser(description=__doc__)
    parser.add_argument('--cohort', choices=tuple(COHORTS), default='discovery')
    parser.add_argument('--sample', action='append', nargs=2, required=True, metavar=('NAME', 'PATH'))
    args = parser.parse_args()
    if any(name not in COHORTS[args.cohort] for name, _ in args.sample) or len({s[0] for s in args.sample}) != len(args.sample):
        parser.error('identity')
    rows = []
    for name, path in args.sample:
        row = {'name': name, 'sha256': SAMPLES[name]}
        try:
            with open(path, 'rb') as f:
                data = f.read(128*1024*1024+1)
            if len(data) > 128*1024*1024 or hashlib.sha256(data).hexdigest() != SAMPLES[name]:
                raise ValueError('size_or_hash')
            geometry, payload = independent_strips(data)
            row.update(status='ok', width=geometry['width'], height=geometry['height'],
                       payload_bytes=len(payload), result=measure(payload, geometry['width']))
        except (OSError, ValueError, IndexError, KeyError, TypeError) as exc:
            row.update(status='unknown', reason=type(exc).__name__)
        rows.append(row)
    print(json.dumps({'samples': rows}, allow_nan=False))
    return int(any(r['status'] != 'ok' for r in rows))


if __name__ == '__main__':
    sys.exit(main())
