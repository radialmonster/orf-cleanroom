"""Exact free-anchor second-order range feasibility for candidate windows (#31).

For each independently reset segment, the first two values are unrestricted
integers in [0, 2**B-1]; subsequent values obey x[i]=2*x[i-1]-x[i-2]+e[i].
Greedy maximal feasible prefixes minimize segment count because feasibility is
hereditary. For d=2 the parity lanes are treated independently: their reset
positions need not coincide, so the result is a permissive necessary condition.
A window with q>=17 or a short window is undefined for every family. This is
not evidence of physical rows, framing, predictor, value interpretation or a
decode. Reads input only and prints aggregate JSON; no reconstructed values.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class
from suffix_joint_probe import scan_prefix

WINDOW = 4096
STARTS = (262144, 524288, 1048576, 1572864)


def segments(residuals, maximum, deadline=None):
    """Return minimum segment count by incremental exact slope intersection."""
    if maximum < 0:
        raise ValueError('negative range')
    start = 0
    count = 0
    while start < len(residuals):
        sums = [0]
        low, high = -maximum, maximum
        j = start + 1
        while j < len(residuals):
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError('case deadline reached')
            k = j - start
            value = 0 if k == 1 else 2 * sums[-1] - sums[-2] + residuals[j]
            next_low, next_high = low, high
            for i, previous in enumerate(sums):
                distance = k - i
                difference = value - previous
                next_low = max(next_low, -((maximum + difference) // distance))
                next_high = min(next_high, (maximum - difference) // distance)
                if next_low > next_high:
                    break
            if next_low > next_high:
                break
            sums.append(value)
            low, high = next_low, next_high
            j += 1
        count += 1
        start = j
    return count


def mapped(suffix, name):
    if name == 'signed_digit':
        return 4 * (suffix >> 3) + (suffix & 3) - 8 * ((suffix >> 2) & 1)
    if name == 'signed_low3':
        return (suffix & 7) - 8 if suffix & 4 else suffix & 7
    raise ValueError('unknown mapping')


def measure(tokens, requested=WINDOW, file_deadline=None):
    n = len(tokens)
    escapes = sum(q >= 17 for q, _ in tokens)
    families = []
    for bits in (16, 12):
        for name in ('signed_digit', 'signed_low3'):
            for stride in (1, 2):
                lane_lengths = [len(tokens[i::stride]) for i in range(stride)]
                counts = None
                status = 'undefined' if not n or n != requested or escapes else 'ok'
                if n and n == requested and not escapes:
                    values = [mapped(s, name) for _, s in tokens]
                    deadline = time.monotonic() + 120
                    if file_deadline is not None:
                        deadline = min(deadline, file_deadline)
                    try:
                        counts = [segments(values[i::stride], (1 << bits) - 1, deadline) for i in range(stride)]
                    except TimeoutError:
                        status = 'timeout'
                families.append({'bits': bits, 'mapping': name, 'stride': stride,
                                 'lane_lengths': lane_lengths,
                                 'vacuous_lanes': [length < 3 for length in lane_lengths],
                                 'status': status, 'segments': counts,
                                 'at_most_two_each': all(c <= 2 for c in counts) if counts is not None else None})
    return {'requested_tokens': requested, 'returned_tokens': n, 'escape_tokens': escapes,
            'families': families}


def report(sample_id, name, path):
    file_deadline = time.monotonic() + 600
    with open(path, 'rb') as handle:
        data = handle.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError('one contiguous strip required')
    off, length = offsets[0], lengths[0]
    w, h = best[0x100][0], best[0x101][0]
    if off < 0 or length <= 0 or off + length > len(data):
        raise ValueError('payload out of bounds')
    if w <= WINDOW or h <= 0 or size_class(length, w, h) != 'variable' or best.get(0x103) != [1]:
        raise ValueError('width greater than window and variable-size payload required')
    tokens, end = scan_prefix(data[off:off + length], STARTS[-1] + WINDOW)
    windows = []
    for start in STARTS:
        window = measure(tokens[start:start + WINDOW], file_deadline=file_deadline)
        window['start_token'] = start
        windows.append(window)
    return {'pixls_id': sample_id, 'pixls_name': name, 'sha256': hashlib.sha256(data).hexdigest(),
            'variant': 'unassigned', 'payload_w': w, 'payload_h': h, 'payload_offset': off,
            'payload_bytes': length, 'returned_tokens': len(tokens), 'bits_consumed': end,
            'windows': windows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', nargs=3, required=True, metavar=('ID', 'PUBLIC_NAME', 'FILE'))
    args = parser.parse_args()
    sample_id, name, path = args.sample
    if not sample_id.isascii() or not sample_id.isdecimal() or int(sample_id) <= 0:
        parser.error('sample ID must be a positive ASCII decimal')
    if not name or not name.isprintable() or any(c in name for c in '/\\'):
        parser.error('public name must be a printable basename')
    try:
        result = report(sample_id, name, path)
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
        parser.exit(1, 'sample %s: %s\n' % (sample_id, type(exc).__name__))
    sources = {}
    for filename in ('free_anchor_second_order.py', 'suffix_joint_probe.py', 'orf_signature.py'):
        with open(os.path.join(os.path.dirname(__file__), filename), 'rb') as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({'source_sha256': sources, 'python_version': sys.version.split()[0],
                      'sample': result}, indent=2, allow_nan=False))
    return int(any(w['returned_tokens'] != w['requested_tokens'] or
                   any(f['status'] == 'timeout' for f in w['families']) for w in result['windows']))


if __name__ == '__main__':
    sys.exit(main())
