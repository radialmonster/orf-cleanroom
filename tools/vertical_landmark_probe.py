#!/usr/bin/env python3
"""Bounded vertical-landmark pilot for #302/#197; read-only aggregate JSON.

Uses the original baseline JPEG DC reader as a coarse rendered-scene proxy.
No image is rendered, saved or printed. Checks two low-profile intervals in
128-bin column means over the central half of the preview, with three fixed
sub-bands. This does not establish raw clipping, focus or sensor truth.

One candidate payload rule only: k=5/stop=1, no extra escape bits, phase zero,
nominal width W, ordinary-suffix b2+b4 averaged over the central half of the
nominal rows. There is no stride, phase, polarity or mapping search. Real
versus reversed and circularly shifted preview correlations are descriptive,
not significance or a codec. Cross-file scores are also reported.

Standard library only. Private input hashes, paths, dates, serials and GPS are
not output. --names adds basenames for an owner-authorized safe report.
Inputs require prior ownership/permission or verified CC0 provenance.

Usage: python -I -B tools/vertical_landmark_probe.py [--names] FILE [FILE ...]
       python -I -B tools/vertical_landmark_probe.py --intake-only FILE [FILE ...]
       python -I -B tools/vertical_landmark_probe.py --self-test
"""
import argparse
from array import array
import hashlib
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc
import orf_tokens
from orf_signature import signature
from preview_pair_sensitivity import read_exif

BINS = 128
ROW_BANDS = ((.25, .40), (.40, .60), (.60, .75))
FIELD = bytes((((s >> 2) & 1) + ((s >> 4) & 1)) if s < 32 else 3
              for s in range(256))


def resample(values, bins=BINS):
    if len(values) < bins:
        raise ValueError('profile shorter than fixed grid')
    return [math.fsum(values[k * len(values) // bins:(k + 1) * len(values) // bins]) /
            ((k + 1) * len(values) // bins - k * len(values) // bins)
            for k in range(bins)]


def correlation(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    aa, bb = [v - ma for v in a], [v - mb for v in b]
    den = math.sqrt(math.fsum(v * v for v in aa) * math.fsum(v * v for v in bb))
    return math.fsum(x * y for x, y in zip(aa, bb)) / den if den else None


def intervals(profile):
    """Fixed ROI/threshold; no per-file search or forced choice of two bands."""
    lo, hi = BINS // 20, BINS - BINS // 20
    ordered = sorted(profile[lo:hi])
    p10 = ordered[len(ordered) // 10]
    p90 = ordered[9 * len(ordered) // 10]
    threshold = (p10 + p90) / 2
    runs, start = [], None
    for k in range(lo, hi + 1):
        dark = k < hi and profile[k] < threshold
        if dark and start is None:
            start = k
        if not dark and start is not None:
            if k - start >= 2:
                runs.append(dict(start_bin=start, stop_bin=k,
                                 center=(start + k) / (2 * BINS),
                                 width_bins=k - start,
                                 touches_roi=start == lo or k == hi))
            start = None
    good = (p90 > p10 and len(runs) == 2 and
            not any(r['touches_roi'] for r in runs))
    ratio = None
    if len(runs) == 2:
        widths = [r['width_bins'] for r in runs]
        ratio = max(widths) / min(widths)
        good = good and 1.5 <= ratio <= 4
    return dict(two_band_gate=bool(good), runs=runs, width_ratio=ratio,
                p90_minus_p10=p90 - p10)


def preview_columns(dc, wb, hb, lower, upper):
    lo, hi = int(hb * lower), int(hb * upper)
    return resample([statistics.mean(dc[y * wb + x] for y in range(lo, hi))
                     for x in range(wb)])


def preview_report(data):
    selected = jpeg_dc.find_preview(data)
    if selected is None:
        raise ValueError('no supported embedded preview')
    _, offset, _, width, height = selected
    wb, hb, dc = jpeg_dc.decode(data, offset)
    profile = preview_columns(dc, wb, hb, .25, .75)
    pooled = intervals(profile)
    bands = [intervals(preview_columns(dc, wb, hb, lo, hi)) for lo, hi in ROW_BANDS]
    stable = pooled['two_band_gate'] and all(b['two_band_gate'] for b in bands)
    disagreement = None
    if stable:
        disagreement = max(abs(a['center'] - b['center']) * BINS
                           for band in bands for a, b in zip(pooled['runs'], band['runs']))
        stable = disagreement <= 2
    return profile, dict(width=width, height=height, dc_width=wb, dc_height=hb,
                         pooled=pooled, fixed_subbands=bands,
                         maximum_center_disagreement_bins=disagreement,
                         stable_two_band_gate=bool(stable))


def candidate_columns(suffixes, width, height):
    first, stop = height // 4, 3 * height // 4
    if len(suffixes) < stop * width:
        raise ValueError('incomplete fixed nominal-row extent')
    values = bytes(suffixes[first * width:stop * width]).translate(FIELD)
    columns, missing = [], 0
    for x in range(width):
        col = values[x::width]
        absent = col.count(3)
        missing += absent
        if len(col) == absent:
            raise ValueError('column has no ordinary suffix')
        columns.append((sum(col) - 3 * absent) / (len(col) - absent))
    return resample(columns), dict(first_nominal_row=first, stop_nominal_row=stop,
                                   ordinary_tokens=len(values) - missing,
                                   excluded_escape_tokens=missing)


def score_summary(candidate, preview):
    observed = correlation(candidate, preview)
    shifts = [correlation(candidate, preview[k:] + preview[:k]) for k in range(1, BINS)]
    return dict(identity_r=observed, reversed_preview_r=correlation(candidate, preview[::-1]),
                circular_rank=(1 + sum(v >= observed - 1e-12 for v in shifts)
                               if observed is not None else None),
                circular_comparisons=BINS,
                maximum_shift_r=max(v for v in shifts if v is not None)
                if observed is not None else None)


def measure(index, path, intake_only, names):
    data = open(path, 'rb').read()
    sig, meta = signature(path), read_exif(data)
    if hashlib.sha256(data).hexdigest() != sig['sha256']:
        raise ValueError('input changed during measurement')
    result = dict(input=index, **{k: sig[k] for k in
                                 ('model', 'payload_w', 'payload_h', 'payload_bytes',
                                  'bpp', 'size_class', 'compression_tag')})
    result['settings'] = {k: meta[k] for k in ('exposure', 'fnumber', 'iso', 'focal')}
    if names:
        result['name'] = os.path.basename(path)
    preview, result['preview'] = preview_report(data)
    candidate = None
    if not intake_only:
        width, height, payload = orf_tokens.locate_data(data)
        qs, suffixes = array('B'), array('B')
        limit = (3 * height // 4) * width
        _, consumed = orf_tokens.scan(payload, limit, 0, 0, None, qs, suffixes, 40, None, 32)
        candidate, extent = candidate_columns(suffixes, width, height)
        result['candidate'] = dict(parsed_tokens=len(suffixes), consumed_bits=consumed,
                                   **extent, **intervals(candidate),
                                   **score_summary(candidate, preview))
    return result, preview, candidate


def pack_suffixes(suffixes):
    """Original synthetic q=0 tokens, explicitly encoded MSB-first in memory."""
    out, accumulator, count = bytearray(), 0, 0
    for suffix in suffixes:
        accumulator = (accumulator << 6) | (32 + suffix)
        count += 6
        while count >= 8:
            count -= 8
            out.append((accumulator >> count) & 255)
        accumulator &= (1 << count) - 1
    if count:
        out.append(accumulator << (8 - count))
    return bytes(out)


def self_test():
    width, height = 256, 96
    for shift in (-24, 0, 24):
        dark = [(64 + shift, 76 + shift), (112 + shift, 142 + shift)]
        target = [(-100 if any(a <= x < b for a, b in dark) else 100)
                  for x in range(width)]
        suffixes = [20 if y % 8 < (1 if target[x] < 0 else 6) else 0
                    for y in range(height) for x in range(width)]
        qs, parsed = array('B'), array('B')
        orf_tokens.scan(pack_suffixes(suffixes), width * height, 0, 0, None,
                        qs, parsed, 40, None, 32)
        assert list(parsed) == suffixes and not any(qs)
        profile, extent = candidate_columns(parsed, width, height)
        preview = resample(target)
        assert intervals(profile)['two_band_gate']
        assert intervals(preview)['two_band_gate']
        score = score_summary(profile, preview)
        assert score['identity_r'] > .999 and score['circular_rank'] == 1
        assert score['reversed_preview_r'] < .9
        wrong = preview[32:] + preview[:32]
        assert correlation(profile, wrong) < .9
    assert not intervals([1] * BINS)['two_band_gate']
    one = [0 if 40 <= k < 60 else 1 for k in range(BINS)]
    assert not intervals(one)['two_band_gate']
    print('self-test ok: three known shifted band pairs survive encoding/parsing; '
          'reversal, wrong labels, flat and one-band controls do not pass the matched criteria')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*')
    parser.add_argument('--names', action='store_true')
    parser.add_argument('--intake-only', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.files:
        parser.error('supply inputs or --self-test')
    records, previews, candidates, failures = [], [], [], []
    for index, path in enumerate(args.files, 1):
        try:
            result, preview, candidate = measure(index, path, args.intake_only, args.names)
            records.append(result)
            previews.append(preview)
            candidates.append(candidate)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            failures.append(dict(input=index, error=type(exc).__name__))
    cross_file = []
    if not args.intake_only:
        for i, candidate in enumerate(candidates):
            scores = [correlation(candidate, preview) for preview in previews]
            observed = scores[i]
            cross_file.append(dict(input=records[i]['input'], correlations=scores,
                                   matched_rank=1 + sum(v >= observed - 1e-12 for j, v in enumerate(scores)
                                                        if i != j and v is not None)
                                   if observed is not None else None))
    print(json.dumps(dict(method='fixed-width-phase-zero-b2-plus-b4-vertical-pilot',
                          bins=BINS, python=sys.version.split()[0],
                          records=records, cross_file=cross_file, failures=failures,
                          limits='exploratory; preview is a rendering proxy; nominal token rows '
                          'are assumed; no physical framing, raw clipping, predictor or codec'),
                     indent=2, allow_nan=False))
    return int(bool(failures))


if __name__ == '__main__':
    sys.exit(main())
