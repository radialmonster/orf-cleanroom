"""Matched-anchor candidate boundary coalescence (#30, building on #634).

Freeze a stop-1/k5 prefix. For each q>=17 candidate choose the nearest earlier
same-suffix q=0 candidate whose two 24-word control horizons complete no later
than the escape start. Compare boundaries at offsets 0 and 12 after each anchor.
Each horizon includes its start plus 24 ends; the earliest shared absolute bit
position is reported. A bounded shared boundary does not establish physical
framing, escape syntax, independence or hidden state. Inputs are read only;
output consists of aggregate counts and histograms, never raw/pixel data.
"""
import argparse
from bisect import bisect_right
import hashlib
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class

HORIZON = 24
SKIP = 12


def scan(buf, start, end, count):
    """Complete candidate words as (q, suffix, start, end); stop if short."""
    pos = start
    result = []
    while len(result) < count:
        begin = pos
        while pos < end and not ((buf[pos >> 3] >> (7 - (pos & 7))) & 1):
            pos += 1
        if pos + 6 > end:
            break
        suffix = 0
        for bit in range(pos + 1, pos + 6):
            suffix = (suffix << 1) | ((buf[bit >> 3] >> (7 - (bit & 7))) & 1)
        pos += 6
        result.append((pos - begin - 6, suffix, begin, pos))
    return result


def horizons(buf, start, end):
    first = scan(buf, start, end, HORIZON)
    second = scan(buf, start + SKIP, end, HORIZON)
    return (first, second) if len(first) == len(second) == HORIZON else None


def first_shared(start, pair):
    left = [start] + [word[3] for word in pair[0]]
    right = [start + SKIP] + [word[3] for word in pair[1]]
    shared = set(left).intersection(right)
    if not shared:
        return None
    position = min(shared)
    return (position - start, left.index(position), right.index(position))


def measure(buf, limit, pair_callback=None):
    rows = scan(buf, 0, len(buf) * 8, limit)
    result = {'requested_tokens': limit, 'parsed_tokens': len(rows),
              'endpoint_bits': rows[-1][3] if rows else 0, 'prefix_complete': len(rows) == limit,
              'anchors': None, 'no_match': None, 'short_horizon': None, 'matched_pairs': None,
              'unique_controls': None, 'reused_control_pairs': None, 'escape': None,
              'control': None, 'paired': None, 'q0_denominator': None,
              'paired_q0_difference_sum': None}
    if len(rows) != limit:
        return result
    boundary = rows[-1][3]
    buckets = [[] for _ in range(32)]
    for index, (q, suffix, _, end) in enumerate(rows):
        if q != 0:
            continue
        pair = horizons(buf, end, boundary)
        if pair is not None:
            buckets[suffix].append((max(pair[0][-1][3], pair[1][-1][3]), index))
    indexes = []
    for bucket in buckets:
        bucket.sort()
        best = []
        latest = -1
        for _, ordinal in bucket:
            latest = max(latest, ordinal)
            best.append(latest)
        indexes.append(([end for end, _ in bucket], best))
    stats = lambda: {'found': 0, 'not_found': 0, 'distance_bits': {}, 'index0': {}, 'index12': {},
                     'shared_words': {}, 'immediate_later_start': 0, 'q0_0': 0, 'q0_12': 0, 'q0_difference': 0,
                     'found_pre_difference': 0, 'found_tail_difference': 0,
                     'not_found_difference': 0}
    escape_stats, control_stats = stats(), stats()
    paired = {'both': 0, 'escape_only': 0, 'control_only': 0, 'neither': 0,
              'both_pre_difference': 0, 'both_tail_difference': 0, 'other_difference': 0}
    anchors = no_match = short = 0
    uses = {}
    def record(target, value, pair):
        q0 = lambda words: sum(word[0] == 0 for word in words)
        difference = q0(pair[1]) - q0(pair[0])
        target['q0_0'] += q0(pair[0])
        target['q0_12'] += q0(pair[1])
        target['q0_difference'] += difference
        if value is None:
            target['not_found'] += 1
            target['not_found_difference'] += difference
            return (difference, None, None)
        target['found'] += 1
        _, left, right = value
        shared = min(HORIZON - left, HORIZON - right)
        assert pair[0][left:left + shared] == pair[1][right:right + shared]
        target['immediate_later_start'] += int(right == 0)
        pre = q0(pair[1][:right]) - q0(pair[0][:left])
        tail = q0(pair[1][right + shared:]) - q0(pair[0][left + shared:])
        assert difference == pre + tail
        target['found_pre_difference'] += pre
        target['found_tail_difference'] += tail
        label = str(shared)
        target['shared_words'][label] = target['shared_words'].get(label, 0) + 1
        for key, number in zip(('distance_bits', 'index0', 'index12'), value):
            label = str(number)
            target[key][label] = target[key].get(label, 0) + 1
        return (difference, pre, tail)
    for q, suffix, start, end in rows:
        if q < 17:
            continue
        anchors += 1
        ends, best = indexes[suffix]
        i = bisect_right(ends, start) - 1
        if i < 0:
            no_match += 1
            continue
        ordinal = best[i]
        epair = horizons(buf, end, boundary)
        if epair is None:
            short += 1
            continue
        control_end = rows[ordinal][3]
        cpair = horizons(buf, control_end, boundary)
        if cpair is None:
            raise AssertionError('selected control horizon became incomplete')
        if pair_callback is not None:
            pair_callback(end, control_end, boundary)
        evalue, cvalue = first_shared(end, epair), first_shared(control_end, cpair)
        ediff, epre, etail = record(escape_stats, evalue, epair)
        cdiff, cpre, ctail = record(control_stats, cvalue, cpair)
        key = ('both' if evalue is not None and cvalue is not None else
               'escape_only' if evalue is not None else 'control_only' if cvalue is not None else 'neither')
        paired[key] += 1
        if key == 'both':
            paired['both_pre_difference'] += epre - cpre
            paired['both_tail_difference'] += etail - ctail
        else:
            paired['other_difference'] += ediff - cdiff
        uses[ordinal] = uses.get(ordinal, 0) + 1
    result.update(anchors=anchors, no_match=no_match, short_horizon=short,
                  matched_pairs=sum(paired[key] for key in ('both', 'escape_only', 'control_only', 'neither')), unique_controls=len(uses),
                  reused_control_pairs=sum(count - 1 for count in uses.values()),
                  escape=escape_stats, control=control_stats, paired=paired,
                  paired_q0_difference_sum=escape_stats['q0_difference'] - control_stats['q0_difference'])
    result['q0_denominator'] = result['matched_pairs'] * HORIZON
    for stats in (escape_stats, control_stats):
        assert stats['q0_difference'] == stats['found_pre_difference'] + stats['found_tail_difference'] + stats['not_found_difference']
        assert all(sum(stats[key].values()) == stats['found'] for key in ('distance_bits', 'index0', 'index12', 'shared_words'))
    assert result['paired_q0_difference_sum'] == paired['both_pre_difference'] + paired['both_tail_difference'] + paired['other_difference']
    assert anchors == no_match + short + result['matched_pairs']
    return result


def locate_snapshot(data):
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError('one contiguous strip required')
    off, length = offsets[0], lengths[0]
    w, h = best[0x100][0], best[0x101][0]
    if off < 0 or length <= 0 or off + length > len(data) or w <= 0 or h <= 0:
        raise ValueError('invalid payload bounds or dimensions')
    if size_class(length, w, h) != 'variable' or best.get(0x103) != [1]:
        raise ValueError('variable-size compression-tag-1 payload required')
    return w, h, data[off:off + length]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sample', nargs=3, required=True, metavar=('PUBLIC_NAME', 'SHA256', 'FILE'))
    ap.add_argument('--tokens', type=int, required=True, choices=(262144, 524288))
    args = ap.parse_args()
    name, digest, path = args.sample
    if not name or not name.isprintable() or any(c in name for c in '/\\') or not re.fullmatch('[0-9a-f]{64}', digest):
        ap.error('invalid public identity or SHA-256')
    try:
        with open(path, 'rb') as handle:
            data = handle.read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('hash mismatch')
        w, h, payload = locate_snapshot(data)
        length = len(payload)
        result = measure(payload, args.tokens)
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
        ap.exit(1, 'measurement failed: %s\n' % type(exc).__name__)
    hashes = {}
    for filename in ('matched_boundary_coalescence.py', 'orf_signature.py'):
        with open(os.path.join(os.path.dirname(__file__), filename), 'rb') as handle:
            hashes[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({'name': name, 'sha256': digest, 'width': w, 'height': h,
                      'payload_bytes': length, 'source_sha256': hashes, 'result': result}, indent=2))
    return int(not result['prefix_complete'])


if __name__ == '__main__':
    sys.exit(main())
