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

--blank FILE additionally reports a descriptive difference against an explicit
blank. Compare only identical model/geometry/exposure/aperture/ISO/focal tags;
missing tags or differences exclude the comparison. Preview differences undo
the luma DC quantizer, while candidate differences subtract the same fixed
b2+b4 proxy. This does not imply linear sensor/rendering response or phase
correspondence. No blank-adjusted phase, sign or map is fitted.

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
from preview_pair_sensitivity import read_exif, rational_equal

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


def dc_quantizer(data):
    """JPEG baseline header: first component's DQT[0], not an image decode."""
    selected = jpeg_dc.find_preview(data)
    if selected is None:
        raise ValueError('no supported embedded preview')
    pos = selected[1] + 2
    tables, luma_table = {}, None
    while pos < len(data):
        if data[pos] != 255:
            raise ValueError('invalid JPEG header marker')
        while data[pos] == 255:
            pos += 1
        marker = data[pos]
        pos += 1
        if marker == 0xDA:
            break
        length = int.from_bytes(data[pos:pos + 2], 'big')
        segment = data[pos + 2:pos + length]
        if length < 2 or len(segment) != length - 2:
            raise ValueError('invalid JPEG header segment')
        if marker == 0xDB:
            k = 0
            while k < len(segment):
                precision, table = segment[k] >> 4, segment[k] & 15
                step = 1 if precision == 0 else 2
                if precision not in (0, 1) or k + 1 + 64 * step > len(segment):
                    raise ValueError('invalid quantization table')
                tables[table] = int.from_bytes(segment[k + 1:k + 1 + step], 'big')
                k += 1 + 64 * step
        elif marker == 0xC0:
            luma_table = segment[8]
        pos += length
    value = tables.get(luma_table)
    if value is None or value <= 0:
        raise ValueError('missing luma DC quantizer')
    return value


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
    result['preview']['dc_quantizer'] = dc_quantizer(data)
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


def matched_settings(target, blank):
    if any(target[k] != blank[k] for k in ('model', 'payload_w', 'payload_h')):
        return False
    a, b = target['settings'], blank['settings']
    if a['iso'] is None or b['iso'] is None or a['iso'] != b['iso']:
        return False
    return all(rational_equal(a[k], b[k]) is True for k in ('exposure', 'fnumber', 'focal'))


def difference_report(target, preview, candidate, blank, bp, bc):
    if not matched_settings(target, blank):
        return dict(eligible=False, reason='model_geometry_or_settings_mismatch')
    q, bq = target['preview']['dc_quantizer'], blank['preview']['dc_quantizer']
    pd = [q * a - bq * b for a, b in zip(preview, bp)]
    result = dict(eligible=True, preview=intervals(pd),
                  preview_dc_quantizers=[q, bq],
                  limits='difference of rendering/proxy profiles, not sensor values')
    if candidate is not None and bc is not None:
        cd = [a - b for a, b in zip(candidate, bc)]
        result.update(candidate=intervals(cd), **score_summary(cd, pd))
        if result['preview']['two_band_gate'] and result['candidate']['two_band_gate']:
            result['maximum_center_error_bins'] = max(
                abs(a['center'] - b['center']) * BINS for a, b in
                zip(result['preview']['runs'], result['candidate']['runs']))
        else:
            result['maximum_center_error_bins'] = None
    return result


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
    # Explicit JPEG header fixtures select the first component's table ID and
    # handle both permitted quantizer precisions, without decoding any image.
    def segment(marker, body):
        return bytes((255, marker)) + (len(body) + 2).to_bytes(2, 'big') + body
    for precision, quantizer in ((0, 7), (1, 257)):
        step = precision + 1
        dqt = bytes((0,)) + bytes((3,)) * 64
        dqt += bytes(((precision << 4) | 1,)) + quantizer.to_bytes(step, 'big') * 64
        sof = bytes((8, 3, 232, 3, 232, 1, 1, 17, 1))
        sos = bytes((1, 1, 0, 0, 63, 0))
        fixture = (bytes((255, 216)) + segment(0xDB, dqt) +
                   segment(0xC0, sof) + segment(0xDA, sos) + bytes((255, 217)))
        assert dc_quantizer(fixture) == quantizer
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
    # Blank subtraction preserves a known pair with independent constant offsets
    # and quantizer scales. A blank versus itself remains undefined/negative.
    known = [0 if 30 <= k < 36 or 54 <= k < 69 else 1 for k in range(BINS)]
    meta = dict(model='synthetic', payload_w=256, payload_h=96,
                settings=dict(iso=200, exposure=[1, 50], fnumber=[56, 10], focal=[25, 1]),
                preview=dict(dc_quantizer=2))
    blank = dict(meta, preview=dict(dc_quantizer=4))
    target_dc = [v * 100 + 30 for v in known]
    blank_dc = [65] * BINS
    blank_candidate = [.7] * BINS
    target_candidate = [v + .2 for v in known]
    delta = difference_report(meta, target_dc, target_candidate,
                              blank, blank_dc, blank_candidate)
    assert delta['eligible'] and delta['identity_r'] > .999
    assert delta['preview']['two_band_gate'] and delta['candidate']['two_band_gate']
    assert delta['maximum_center_error_bins'] == 0 and delta['circular_rank'] == 1
    empty = difference_report(blank, blank_dc, blank_candidate,
                              blank, blank_dc, blank_candidate)
    assert empty['identity_r'] is None and not empty['preview']['two_band_gate']
    mismatch = dict(meta, settings=dict(meta['settings'], iso=400))
    assert not difference_report(mismatch, target_dc, target_candidate,
                                  blank, blank_dc, blank_candidate)['eligible']
    print('self-test ok: three known shifted band pairs survive encoding/parsing; '
          'reversal, wrong labels, flat and one-band controls fail; matched blank '
          'differences survive quantizer scaling, zero/mismatched blanks do not pass')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*')
    parser.add_argument('--names', action='store_true')
    parser.add_argument('--intake-only', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--blank', help='explicit owner-identified blank reference')
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
    blank_report = None
    if args.blank:
        try:
            blank_report, bp, bc = measure(0, args.blank, args.intake_only, args.names)
            for result, preview, candidate in zip(records, previews, candidates):
                result['blank_difference'] = difference_report(
                    result, preview, candidate, blank_report, bp, bc)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            failures.append(dict(input=0, role='blank', error=type(exc).__name__))
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
                          blank_reference=blank_report,
                          limits='exploratory; preview is a rendering proxy; nominal token rows '
                          'are assumed; no physical framing, raw clipping, predictor or codec'),
                     indent=2, allow_nan=False))
    return int(bool(failures))


if __name__ == '__main__':
    sys.exit(main())
