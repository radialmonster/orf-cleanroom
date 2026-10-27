#!/usr/bin/env python3
"""Fixed-origin versus phase-adjusted candidate periods for #144.

Fits contiguous shifted boundaries, unlike token_phase_holdout_probe's cyclic
heads within fixed blocks. Test starts preserve the fitted phase and period.
Also scores all three fitted models over one common token interval, including
partial edge blocks; head counts can differ. This is descriptive, not a null.
Capped-q candidate tokens are not established physical rows or a codec.
No significance or universal stride inference follows; aggregate JSON only.
"""
import argparse
from array import array
import hashlib
import json
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_band_profile as B

ANCHOR = 2000 * 5240
CENTER, RADIUS, ROWS, HEAD = 5240, 64, 100, 32
THRESHOLD = 0.02


def test_start(anchor, barrier, stride, phase):
    return anchor + phase + ((barrier - anchor - phase + stride - 1) // stride) * stride


def diagnostic(qs, anchor, center, radius, rows, head):
    lo, hi = center - radius, center + radius
    if anchor < 0 or rows < 1 or head < 1 or lo <= head:
        raise ValueError('invalid fixed design')
    barrier = anchor + (rows + 2) * hi
    # Largest possible test end, including phase-dependent rounding.
    required = barrier + (rows + 1) * hi
    if len(qs) < required:
        return {'complete': False, 'required_tokens': required, 'parsed_tokens': len(qs),
                'test_barrier': barrier}
    # Only the declared interval is indexed; integer prefix sums are exact.
    prefix = array('Q', [0])
    total = 0
    for q in memoryview(qs)[anchor:required]:
        total += q
        prefix.append(total)
    def score(stride, phase, start):
        head_sum = row_sum = 0
        for r in range(rows):
            i = start - anchor + r * stride
            head_sum += prefix[i + head] - prefix[i]
            row_sum += prefix[i + stride] - prefix[i]
        numerator = stride * head_sum - head * row_sum
        return numerator, rows * head * (stride - head)
    curves, fixed_curve = [], []
    global_choice = fixed_choice = None
    for stride in range(lo, hi + 1):
        best_num = None
        best_phase = 0
        ties = 0
        phase_means = []
        for phase in range(stride):
            num, den = score(stride, phase, anchor + phase)
            phase_means.append(num / den)
            if stride == center:
                fixed_curve.append(num / den)
            if best_num is None or num > best_num:
                best_num, best_phase, ties = num, phase, 1
            elif num == best_num:
                ties += 1
        candidate = (best_num, rows * head * (stride - head), stride, best_phase)
        curves.append({'stride': stride, 'phase': best_phase, 'ties': ties,
                       'train_numerator': best_num, 'train_denominator': candidate[1],
                       'train_mean': best_num / candidate[1], 'phase_means': phase_means})
        if stride == center:
            fixed_choice = candidate
        if global_choice is None or candidate[0] * global_choice[1] > global_choice[0] * candidate[1]:
            global_choice = candidate
    def evaluate(choice):
        num, den, stride, phase = choice
        train_start = anchor + phase
        start = test_start(anchor, barrier, stride, phase)
        test_num, test_den = score(stride, phase, start)
        return {'stride': stride, 'phase': phase, 'train_start': train_start,
                'train_end_exclusive': train_start + rows * stride,
                'test_start': start, 'test_end_exclusive': start + rows * stride,
                'train_mean': num / den, 'test_numerator': test_num,
                'test_denominator': test_den, 'test_mean': test_num / test_den}
    joint, fixed = evaluate(global_choice), evaluate(fixed_choice)
    baseline_num, baseline_den = score(center, 0, anchor)
    baseline = evaluate((baseline_num, baseline_den, center, 0))
    common_end = barrier + rows * lo
    def common_score(model):
        stride, phase = model['stride'], model['phase']
        start = anchor + phase + ((barrier - anchor - phase) // stride) * stride
        head_sum = head_count = 0
        while start < common_end:
            left, right = max(start, barrier), min(start + head, common_end)
            if right > left:
                head_sum += prefix[right - anchor] - prefix[left - anchor]
                head_count += right - left
            start += stride
        total_sum = prefix[common_end - anchor] - prefix[barrier - anchor]
        rest_count = common_end - barrier - head_count
        rest_sum = total_sum - head_sum
        return {'start': barrier, 'end_exclusive': common_end,
                'head_count': head_count, 'head_sum': head_sum,
                'rest_count': rest_count, 'rest_sum': rest_sum,
                'mean_head_minus_rest': (head_sum / head_count - rest_sum / rest_count
                                         if head_count and rest_count else None)}
    common_joint, common_fixed, common_origin = map(common_score, (joint, fixed, baseline))
    common_delta = (common_joint['mean_head_minus_rest'] - common_fixed['mean_head_minus_rest']
                    if common_joint['mean_head_minus_rest'] is not None
                    and common_fixed['mean_head_minus_rest'] is not None else None)
    delta = joint['test_mean'] - fixed['test_mean']
    return {'complete': True, 'required_tokens': required, 'test_barrier': barrier,
            'fixed_phase_training_means': fixed_curve, 'best_phase_by_stride': curves,
            'joint_selected': joint, 'fixed_stride_selected': fixed, 'fixed_origin': baseline,
            'common_interval_joint': common_joint, 'common_interval_fixed': common_fixed,
            'common_interval_origin': common_origin,
            'common_interval_joint_minus_fixed': common_delta,
            'heldout_joint_minus_fixed': delta, 'practical_threshold': THRESHOLD,
            'at_least_threshold': delta >= THRESHOLD}


def measure(path, digest):
    with open(path, 'rb') as f:
        data = f.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest.lower():
        raise ValueError('hash mismatch')
    best = max(B.Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    width, height = best[0x100][0], best[0x101][0]
    offsets, sizes = best[0x111], best[0x117]
    if (width <= 0 or height <= 0 or len(offsets) != 1 or len(sizes) != 1
            or offsets[0] < 0 or sizes[0] <= 0 or offsets[0] + sizes[0] > len(data)
            or B.size_class(sizes[0], width, height) != 'variable'):
        raise ValueError('unsupported container')
    required = ANCHOR + (ROWS + 2) * (CENTER + RADIUS) + (ROWS + 1) * (CENTER + RADIUS)
    qs, consumed = B.scan_q(data[offsets[0]:offsets[0] + sizes[0]], required)
    result = diagnostic(qs, ANCHOR, CENTER, RADIUS, ROWS, HEAD)
    result.update(sha256=actual, payload_width=width, payload_height=height,
                  payload_bytes=sizes[0], consumed_bits=consumed, parsed_tokens=len(qs))
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sample', nargs=4, required=True, metavar=('ID', 'PUBLIC_NAME', 'SHA256', 'FILE'))
    args = ap.parse_args(argv)
    sid, name, digest, path = args.sample
    if (not sid.isascii() or not sid.isdecimal() or not sid.strip('0') or not name or not name.isprintable()
            or any(c in name for c in '/\\') or len(digest) != 64
            or any(c not in '0123456789abcdef' for c in digest)):
        ap.error('invalid declared public identity or hash')
    start = time.perf_counter()
    try:
        result = measure(path, digest)
    except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
        print(json.dumps({'pixls_id': sid, 'complete': False, 'error': type(exc).__name__}))
        return 1
    result.update(pixls_id=sid, pixls_name=name, anchor=ANCHOR, center=CENTER,
                  radius=RADIUS, rows_per_split=ROWS, head=HEAD,
                  elapsed_seconds=time.perf_counter() - start)
    print(json.dumps(result, indent=2, allow_nan=False))
    return int(not result['complete'])


if __name__ == '__main__':
    sys.exit(main())
