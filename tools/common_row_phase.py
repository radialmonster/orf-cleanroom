"""Common row-phase necessary condition for fixed candidate family (#31).

Assumes one candidate per site and a single row phase per file. Fixed family:
signed_digit(s)-3, B16, stride two. Free anchors are independent per segment
and window. Lane cuts share a row boundary; a surviving phase is permissive and
does not establish framing, predictor, values or a decode. Escaped/short windows
are unknown and never eliminate a phase. Reads files and prints aggregates only.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from free_anchor_second_order import mapped, STARTS, WINDOW
from orf_signature import Tiff, size_class
from suffix_joint_probe import scan_prefix

MAXIMUM = 65535
WINDOW_SECONDS = 20
FILE_SECONDS = 570


def prefix_length(values, maximum, deadline=None):
    """Maximal feasible prefix with two free starting values, exact integers."""
    if not values:
        return 0
    sums = [0]
    low, high = -maximum, maximum
    for j in range(1, len(values)):
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError('window deadline reached')
        current = 0 if j == 1 else 2 * sums[-1] - sums[-2] + values[j]
        next_low, next_high = low, high
        for i, previous in enumerate(sums):
            distance = j - i
            difference = current - previous
            next_low = max(next_low, -((maximum + difference) // distance))
            next_high = min(next_high, (maximum - difference) // distance)
            if next_low > next_high:
                return j
        sums.append(current)
        low, high = next_low, next_high
    return len(values)


def lane_limits(values, maximum, deadline=None):
    reverse = [0, 0] + list(reversed(values[2:])) if len(values) >= 2 else list(values)
    prefix = prefix_length(values, maximum, deadline)
    suffix = len(values) - prefix_length(reverse, maximum, deadline)
    return prefix, suffix


def phase_set(values, width, start, maximum=MAXIMUM, deadline=None):
    """Return possible phases and aggregate cut details, resetting before b."""
    n = len(values)
    lanes = (values[0::2], values[1::2])
    limits = []
    for lane in lanes:
        try:
            limits.append(lane_limits(lane, maximum, deadline))
        except TimeoutError:
            if any(s > p for p, s in limits):
                return set(), {'lane_lengths': [len(x) for x in lanes],
                               'prefix_lengths': [x[0] for x in limits] + [None] * (2 - len(limits)),
                               'suffix_starts': [x[1] for x in limits] + [None] * (2 - len(limits)),
                               'cut_lo': None, 'cut_hi': None, 'whole_window_feasible': False,
                               'partial_rejection': True}
            raise
    (p0, s0), (p1, s1) = limits
    lo = max(0, 2 * s0 - 1, 2 * s1)
    hi = min(n, 2 * p0, 2 * p1 + 1)
    full = p0 == len(lanes[0]) and p1 == len(lanes[1])
    if full:
        phases = set(range(width))
    else:
        phases = {(start + b) % width for b in range(max(1, lo), min(n - 1, hi) + 1)}
    return phases, {'lane_lengths': [len(lane) for lane in lanes],
                    'prefix_lengths': [p0, p1], 'suffix_starts': [s0, s1],
                    'cut_lo': lo, 'cut_hi': hi, 'whole_window_feasible': full,
                    'partial_rejection': False}


def measure(tokens, width, starts=STARTS, requested=WINDOW, file_deadline=None):
    """Intersect phases across defined windows; unknowns cannot eliminate."""
    if width <= requested or width % 2:
        raise ValueError('even width greater than window required')
    possible = set(range(width))
    windows = []
    for start in starts:
        selected = tokens[start:start + requested]
        escapes = sum(q >= 17 for q, _ in selected)
        details, phase_count = None, None
        if len(selected) != requested or not selected:
            status = 'short'
        elif escapes:
            status = 'escape'
        elif file_deadline is not None and time.monotonic() >= file_deadline:
            status = 'file_budget_not_run'
        else:
            values = [mapped(suffix, 'signed_digit') - 3 for _, suffix in selected]
            deadline = time.monotonic() + WINDOW_SECONDS
            if file_deadline is not None:
                deadline = min(deadline, file_deadline)
            try:
                phases, details = phase_set(values, width, start, deadline=deadline)
                phase_count = len(phases)
                possible.intersection_update(phases)
                if details['partial_rejection']:
                    status = ('partial_reject_file_timeout' if file_deadline is not None and
                              time.monotonic() >= file_deadline else 'partial_reject_timeout')
                else:
                    status = 'ok'
            except TimeoutError:
                status = 'file_timeout' if file_deadline is not None and time.monotonic() >= file_deadline else 'timeout'
        windows.append({'start_token': start, 'requested_tokens': requested,
                        'returned_tokens': len(selected), 'escape_tokens': escapes,
                        'status': status, 'details': details, 'phase_count': phase_count,
                        'cumulative_possible_count': len(possible)})
    defined = sum(w['status'] == 'ok' for w in windows)
    unknown = len(windows) - defined
    conclusion = 'rejected' if not possible else 'undefined' if not defined else 'not_rejected'
    return {'windows': windows, 'intended_windows': len(windows), 'defined_windows': defined,
            'unknown_windows': unknown, 'possible_phase_count': len(possible),
            'conclusion': conclusion, 'complete_survival': bool(possible) and not unknown}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', nargs=3, required=True, metavar=('ID', 'PUBLIC_NAME', 'FILE'))
    args = parser.parse_args()
    sample_id, name, path = args.sample
    if not sample_id.isascii() or not sample_id.isdecimal() or int(sample_id) <= 0:
        parser.error('sample ID must be a positive ASCII decimal')
    if not name or not name.isprintable() or any(c in name for c in '/\\'):
        parser.error('public name must be a printable basename')
    deadline = time.monotonic() + FILE_SECONDS
    try:
        with open(path, 'rb') as handle:
            data = handle.read()
        best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
        offsets, lengths = best[0x111], best[0x117]
        if len(offsets) != 1 or len(lengths) != 1:
            raise ValueError('one contiguous strip required')
        off, length = offsets[0], lengths[0]
        width, height = best[0x100][0], best[0x101][0]
        if off < 0 or length <= 0 or off + length > len(data) or width <= WINDOW or width % 2 or height <= 0:
            raise ValueError('invalid bounds or ineligible width')
        if size_class(length, width, height) != 'variable' or best.get(0x103) != [1]:
            raise ValueError('variable-size compression-tag-1 payload required')
        tokens, end = scan_prefix(data[off:off + length], STARTS[-1] + WINDOW)
        result = measure(tokens, width, starts=STARTS, requested=WINDOW, file_deadline=deadline)
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
        parser.exit(1, 'measurement failed: %s\n' % type(exc).__name__)
    sources = {}
    for filename in ('common_row_phase.py', 'free_anchor_second_order.py', 'suffix_joint_probe.py', 'orf_signature.py'):
        with open(os.path.join(os.path.dirname(__file__), filename), 'rb') as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({'pixls_id': sample_id, 'pixls_name': name, 'sha256': hashlib.sha256(data).hexdigest(),
                      'variant': 'unassigned', 'payload_w': width, 'payload_h': height,
                      'payload_offset': off, 'payload_bytes': length, 'returned_tokens': len(tokens),
                      'bits_consumed': end, 'source_sha256': sources, 'python_version': sys.version.split()[0],
                      'window_seconds': WINDOW_SECONDS, 'file_seconds': FILE_SECONDS, 'result': result}, indent=2))
    return int(any(w['status'] in ('short', 'timeout', 'file_timeout', 'file_budget_not_run',
                                   'partial_reject_timeout', 'partial_reject_file_timeout') for w in result['windows']))


if __name__ == '__main__':
    sys.exit(main())
