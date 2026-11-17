"""Fixed global integer residual-origin sensitivity for #32 (candidate model).

The common origin is shared across windows and files within each fixed mapping,
stride and bit-depth family. Unknown cases never eliminate an origin. Passing
all adjudicable cases is not a physical framing, predictor or codec inference.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from free_anchor_second_order import mapped, segments, STARTS, WINDOW
from orf_signature import Tiff, size_class
from suffix_joint_probe import scan_prefix

ORIGINS = {'signed_digit': tuple(range(-8, 16)), 'signed_low3': tuple(range(-4, 4))}
CASE_SECONDS = 20
FILE_SECONDS = 570


def case(tokens, requested, bits, mapping, stride, origin, deadline=None, file_deadline=None):
    """One complete window/family/origin; undefined inputs never pass or fail."""
    if len(tokens) != requested or not tokens:
        return {'status': 'short', 'segments': None, 'passes': None}
    if any(q >= 17 for q, _ in tokens):
        return {'status': 'escape', 'segments': None, 'passes': None}
    if file_deadline is not None and time.monotonic() >= file_deadline:
        return {'status': 'file_budget_not_run', 'segments': None, 'passes': None}
    residuals = [mapped(s, mapping) - origin for _, s in tokens]
    counts = []
    lane_status = []
    for i in range(stride):
        try:
            counts.append(segments(residuals[i::stride], (1 << bits) - 1, deadline))
            lane_status.append('ok')
        except TimeoutError:
            status = 'file_timeout' if file_deadline is not None and time.monotonic() >= file_deadline else 'timeout'
            counts.extend([None] * (stride - i))
            lane_status.extend([status] + ['not_run'] * (stride - i - 1))
            passes = False if any(c is not None and c > 2 for c in counts) else None
            return {'status': status, 'segments': counts, 'lane_status': lane_status, 'passes': passes}
    return {'status': 'ok', 'segments': counts, 'lane_status': lane_status, 'passes': all(x <= 2 for x in counts)}


def summarize(origins, windows):
    """Possible/complete sets; windows map origin to case records.

    An observed failure excludes that origin, unknown status does not. When
    nothing is adjudicable, the full unfalsified set remains possible but the
    conclusion is undefined and the complete-pass set is empty.
    """
    adjudicated = sum(1 for window in windows for origin in origins
                      if window[origin]['passes'] is not None)
    if not adjudicated:
        return {'possible': list(origins), 'complete_pass': [], 'conclusion': 'undefined'}
    possible = []
    complete = []
    for origin in origins:
        records = [window[origin] for window in windows]
        if any(r['passes'] is False for r in records):
            continue
        possible.append(origin)
        eligible = [r for r in records if r['status'] != 'escape']
        if eligible and all(r['status'] == 'ok' and r['passes'] for r in eligible):
            complete.append(origin)
    return {'possible': possible, 'complete_pass': complete,
            'conclusion': 'rejected' if not possible else 'not_rejected'}


def summarize_stages(discovery, verification):
    """Summarize full-grid aggregates without reintroducing excluded origins."""
    output = []
    for bits in (16, 12):
        for mapping, origins in ORIGINS.items():
            for stride in (1, 2):
                def windows(reports):
                    result = []
                    for report in reports:
                        for window in report['sample']['windows']:
                            family = next(f for f in window['families'] if
                                          (f['bits'], f['mapping'], f['stride']) == (bits, mapping, stride))
                            records = {c['origin']: c for c in family['cases']}
                            if set(records) != set(origins):
                                raise ValueError('full origin grid required')
                            result.append(records)
                    return result
                initial = windows(discovery)
                later = windows(verification)
                first = summarize(origins, initial)
                if not first['possible']:
                    combined = {'possible': [], 'complete_pass': [], 'conclusion': 'rejected'}
                else:
                    combined = summarize(first['possible'], initial + later)
                    if not any(record[origin]['passes'] is not None
                               for record in later for origin in first['possible']):
                        combined['conclusion'] = 'undefined'
                output.append({'bits': bits, 'mapping': mapping, 'stride': stride,
                               'discovery': first, 'combined_restricted': combined})
    return output


def report(sample_id, name, path):
    file_deadline = time.monotonic() + FILE_SECONDS
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
        selected = tokens[start:start + WINDOW]
        families = []
        for bits in (16, 12):
            for mapping, origins in ORIGINS.items():
                for stride in (1, 2):
                    cases = []
                    for origin in origins:
                        deadline = min(time.monotonic() + CASE_SECONDS, file_deadline)
                        result = case(selected, WINDOW, bits, mapping, stride, origin, deadline, file_deadline)
                        cases.append({'origin': origin, **result})
                    families.append({'bits': bits, 'mapping': mapping, 'stride': stride, 'cases': cases})
        windows.append({'start_token': start, 'requested_tokens': WINDOW, 'returned_tokens': len(selected),
                        'escape_tokens': sum(q >= 17 for q, _ in selected), 'families': families})
    return {'pixls_id': sample_id, 'pixls_name': name, 'sha256': hashlib.sha256(data).hexdigest(),
            'variant': 'unassigned', 'payload_w': w, 'payload_h': h, 'payload_offset': off,
            'payload_bytes': length, 'returned_tokens': len(tokens), 'bits_consumed': end, 'windows': windows}


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
    for filename in ('free_anchor_origin.py', 'free_anchor_second_order.py', 'suffix_joint_probe.py', 'orf_signature.py'):
        with open(os.path.join(os.path.dirname(__file__), filename), 'rb') as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({'source_sha256': sources, 'python_version': sys.version.split()[0],
                      'case_seconds': CASE_SECONDS, 'file_seconds': FILE_SECONDS, 'sample': result}, indent=2))
    return int(any(c['status'] in ('short', 'timeout', 'file_timeout', 'file_budget_not_run') for w in result['windows']
                   for f in w['families'] for c in f['cases']))


if __name__ == '__main__':
    sys.exit(main())
