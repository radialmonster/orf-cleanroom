#!/usr/bin/env python3
"""Measure within/cross-unit roughness for V0 packed-12 / packed-12.8 (lead #75, G4).

The central 300 stored rows when height>400, otherwise every stored row,
are measured by default; --all-rows selects the entire stored frame. Both
use even i in range(2,width-3,2). Select strictly when
abs(r[i+2]-r[i-2])+abs(r[i+3]-r[i-1]) > threshold, separately for each
pair order. Swapping pairs preserves this gradient but changes cross-unit
neighbours. Exact sums/counts and undefined (null) means/ratios are reported.
This descriptive metric does not determine physical pixel order. Original
reference-decoder container/unpacking/order selection are reused unchanged.
Stdlib only, read-only inputs, aggregate JSON only; no images or pixel dumps.
Legacy THRESHOLD SAMPLE_DIR remains accepted; --sample avoids a directory scan.
"""
import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'decoder'))
import orf_decode as od


def nonnegative(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError('threshold must be nonnegative')
    return number


def accum_row(row, threshold, swapped=False):
    r = list(row)
    if len(r) % 2:
        raise ValueError('odd width')
    if swapped:
        r[0::2], r[1::2] = r[1::2], r[0::2]
    within = cross = count = 0
    for i in range(2, len(r)-3, 2):
        gradient = abs(r[i+2]-r[i-2]) + abs(r[i+3]-r[i-1])
        if gradient > threshold:
            within += abs(r[i]-r[i+1])
            cross += abs(r[i+1]-r[i+2])
            count += 1
    return within, cross, count


def summarize(within, cross, count):
    return {'within_sum': within, 'cross_sum': cross, 'selected_units': count,
            'within_mean': within/count if count else None,
            'cross_mean': cross/count if count else None,
            'cross_over_within': cross/within if within else None}


def analyse(path, threshold, all_rows=False):
    p = od.Payload(path)
    sc = p.sig['size_class']
    w, h = p.sig['payload_w'], p.sig['payload_h']
    result = {'input_sha256': p.sig['sha256'], 'size_class': sc,
              'width': w, 'height': h}
    if sc not in ('packed-12', 'packed-12.8'):
        result['skipped'] = 'unsupported packing'
        return result
    if w <= 0 or h <= 0 or not p.in_file:
        raise ValueError('invalid payload')
    rb = od.row_bytes(sc, w)
    start, stop = (h//2-150, h//2+150) if h > 400 and not all_rows else (0, h)
    sums = [[0, 0, 0], [0, 0, 0]]
    with open(path, 'rb') as stream:
        order, unused_margin = od.detect_order(stream, p, sc, w, h, rb)
        for y in range(start, stop):
            raw = p.read(stream, y*rb, rb)
            if len(raw) != rb:
                raise ValueError('short row')
            row = od.unpack_row(sc, order, raw, w)[0]
            if len(row) != w:
                raise ValueError('short decoded row')
            for swap in (0, 1):
                values = accum_row(row, threshold, bool(swap))
                for k in range(3):
                    sums[swap][k] += values[k]
    result.update(order=order, stored_row_start=start, stored_row_stop=stop,
                  rows_measured=stop-start, eligible_units=(stop-start)*len(range(2,w-3,2)),
                  emitted=summarize(*sums[0]), swapped=summarize(*sums[1]))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('threshold', type=nonnegative)
    parser.add_argument('sample_dir', nargs='?')
    parser.add_argument('--all-rows', action='store_true', help='measure every stored row')
    parser.add_argument('--sample', nargs=3, action='append', default=[],
                        metavar=('ID', 'PUBLIC_NAME', 'FILE'))
    args = parser.parse_args(argv)
    if bool(args.sample_dir) == bool(args.sample):
        parser.error('choose SAMPLE_DIR or one or more --sample entries')
    samples = list(args.sample)
    if args.sample_dir:
        try:
            samples = [('', name, os.path.join(args.sample_dir, name))
                       for name in sorted(os.listdir(args.sample_dir))
                       if os.path.isfile(os.path.join(args.sample_dir, name))]
        except OSError as exc:
            print(json.dumps({'error': type(exc).__name__, 'samples': [], 'complete': False}))
            return 1
    reports = []
    failed = False
    for sample_id, public_name, path in samples:
        report = {'sample_id': sample_id, 'public_name': public_name}
        try:
            report.update(analyse(path, args.threshold, args.all_rows))
        except (od.NotSpecified, ValueError, IndexError, KeyError, struct.error, OSError) as exc:
            report['error'] = type(exc).__name__
            failed = True
        reports.append(report)
    print(json.dumps({'threshold': args.threshold, 'samples': reports,
                      'complete': not failed}, sort_keys=True, allow_nan=False))
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
