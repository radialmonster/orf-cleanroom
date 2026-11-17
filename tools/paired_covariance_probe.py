#!/usr/bin/env python3
"""Exploratory paired candidate-index covariance probe (Campaign B, #302).

The synthetic linear-filter reference assumes independent exposures, spatially
white equal-variance noise, the same fixed linear stencil, and aligned physical
sites. Under these assumptions x[i]-x[i-d] has rho(d)=-0.5.
Spatially correlated noise can change the footprint even for a correct stencil.

Raw mode subtracts unverified zigzag mappings of literal k=5 candidate tokens at
equal candidate indices. Token/pixel alignment, value mapping, rows and escape
semantics are unknown. Metadata equality establishes neither same scene nor
independent captures, fixed-pattern cancellation or these noise assumptions.
RMSE ranks the supplied reference signatures descriptively; it does not identify
a camera predictor. EMVA 1288 Linear 4.0 sections 2.5/6.6 motivate paired image
variance measurements, not this candidate-token test or EMVA conformity.

Standard library only (Python 3.8+). Emits aggregate JSON only; no images,
previews, or pixel dumps are printed or stored.

Usage:
    python -I -B tools/paired_covariance_probe.py FILE_A FILE_B [--tokens N] [--max-lag L] [--stride W]
    python -I -B tools/paired_covariance_probe.py --synthetic [--tokens N]
    python -I -B tools/paired_covariance_probe.py --self-test
"""
import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens  # noqa: E402
from preview_pair_sensitivity import read_exif, rational_equal  # noqa: E402

DEFAULT_TOKENS = 500000
DEFAULT_MAX_LAG = 16


def theoretical_predictor_signature(name, max_lag=DEFAULT_MAX_LAG, stride=None):
    """Compute exact theoretical autocorrelation rho(lag) for a linear predictor.

    For spatially white equal-variance Delta and fixed linear coefficients,
    given residual difference D = sum_k c_k Delta[n - k],
    rho(l) = sum_k c_k c_{k+l} / sum_k c_k^2.
    """
    coeffs = {}  # lag -> coefficient

    def add(offset, coefficient):
        coeffs[offset] = coeffs.get(offset, 0.0) + coefficient

    add(0, 1.0)

    if name == 'none' or name == 'white_noise':
        pass
    elif name.startswith('lag') and name[3:].isdigit():
        d = int(name[3:])
        add(d, -1.0)
    elif name == 'lag1_lag2_bayer':
        # Candidate 2-tap predictor: 0.5 * x[n-1] + 0.5 * x[n-2]
        add(1, -0.5)
        add(2, -0.5)
    elif name == 'lag2_2nd_order':
        # 2 * x[n-2] - x[n-4]
        add(2, -2.0)
        add(4, 1.0)
    elif stride and stride > 0:
        d = 2  # Bayer horizontal stride
        w = stride
        if name == '2d_average':
            # 0.5 * x[n-d] + 0.5 * x[n-w]
            add(d, -0.5)
            add(w, -0.5)
        elif name == '2d_planar':
            # x[n-d] + x[n-w] - x[n-w-d]
            add(d, -1.0)
            add(w, -1.0)
            add(w + d, 1.0)
        else:
            raise ValueError("unknown predictor: %s" % name)
    else:
        raise ValueError("unknown predictor: %s" % name)

    denom = sum(c * c for c in coeffs.values())
    if denom == 0:
        raise ValueError('zero-energy stencil has no normalized signature')
    lags = {}
    for l in range(1, max_lag + 1):
        num = sum(coeffs[k] * coeffs.get(k + l, 0.0) for k in coeffs)
        lags[l] = num / denom

    if stride and stride > 0:
        for offset in (-2, -1, 0, 1, 2):
            l = stride + offset
            if l not in lags and l > 0:
                num = sum(coeffs[k] * coeffs.get(k + l, 0.0) for k in coeffs)
                lags[l] = num / denom
            l2 = 2 * stride + offset
            if l2 not in lags and l2 > 0:
                num = sum(coeffs[k] * coeffs.get(k + l2, 0.0) for k in coeffs)
                lags[l2] = num / denom

    return lags


def autocovariance(series, max_lag=DEFAULT_MAX_LAG, special_lags=None):
    """Global valid-site centering; None masks preserve index distances.

    Covariance at each lag uses only valid endpoint pairs, normalized by that
    pair count. Variance uses all valid sites. Mask selection is descriptive;
    it does not establish missing-at-random sampling or a noise model.
    """
    n = len(series)
    values = [x for x in series if x is not None]
    valid = len(values)
    mean = sum(values)/valid if valid >= 2 else None
    centered = [x-mean if x is not None and mean is not None else None for x in series]
    var = sum(x*x for x in centered if x is not None)/valid if valid >= 2 else None

    target_lags = set(range(1, min(max_lag + 1, n)))
    if special_lags:
        for l in special_lags:
            if 0 < l < n:
                target_lags.add(l)

    results = {}
    for l in sorted(target_lags):
        count, total = 0, 0.0
        for i in range(n-l):
            if series[i] is not None and series[i+l] is not None:
                count += 1
                if mean is not None:
                    total += centered[i]*centered[i+l]
        cov = total/count if count and mean is not None else None
        results[l] = {
            'lag': l,
            'valid_pairs': count,
            'cov': cov,
            'rho': cov/var if var is not None and var > 0 and cov is not None else None,
        }

    return {
        'n': n,
        'valid_samples': valid,
        'masked_samples': n-valid,
        'status': ('insufficient_valid_samples' if valid < 2 else
                   'zero_variance' if var == 0 else 'ok'),
        'mean': mean,
        'variance': var,
        'std_dev': math.sqrt(var) if var is not None else None,
        'lags': results,
    }


def compare_signatures(observed_lags, theoretical_lags):
    """Calculate mean squared error and max absolute difference against theoretical rho."""
    common = [l for l in theoretical_lags if l in observed_lags
              and observed_lags[l]['rho'] is not None]
    if not common:
        return None
    sq_errs = []
    max_abs = 0.0
    for l in common:
        obs = observed_lags[l]['rho']
        th = theoretical_lags[l]
        err = obs - th
        sq_errs.append(err * err)
        if abs(err) > max_abs:
            max_abs = abs(err)

    rmse = math.sqrt(sum(sq_errs) / len(common))
    return {
        'compared_lags': len(common),
        'rmse': rmse,
        'max_abs_error': max_abs,
    }


def signed_zig_zag(u):
    """Standard signed mapping: even -> positive, odd -> negative."""
    return -(u + 1) // 2 if (u & 1) else u // 2


def extract_candidate_stream(data, max_tokens=DEFAULT_TOKENS):
    """Extract candidate bounded tokens and signed residual proxies from raw container."""
    w, h, payload = orf_tokens.locate_data(data)
    qs, ss, _, bits_used = orf_tokens.parse(payload, max_tokens, w)
    n = len(qs)
    residuals = []
    for q, s in zip(qs, ss):
        if q < orf_tokens.ESC_Q:
            u = (q << 5) | s
            residuals.append(signed_zig_zag(u))
        else:
            residuals.append(None)
    return {
        'width': w,
        'height': h,
        'payload_bytes': len(payload),
        'tokens_parsed': n,
        'tokens_requested': max_tokens,
        'token_shortfall': max_tokens-n,
        'escape_tokens': sum(q >= orf_tokens.ESC_Q for q in qs),
        'bits_used': bits_used,
        'residuals': residuals,
    }


def check_metadata_match(exif_a, exif_b, geom_a, geom_b):
    """Required metadata compatibility only, never capture/scene eligibility."""
    mismatches = []
    if not exif_a.get('model') or not exif_b.get('model') or exif_a['model'] != exif_b['model']:
        mismatches.append('model')
    valid_geometry = lambda g: (isinstance(g, (tuple, list)) and len(g) == 2
                                and all(type(v) is int and v > 0 for v in g))
    if not valid_geometry(geom_a) or not valid_geometry(geom_b) or geom_a != geom_b:
        mismatches.append('geometry')
    if not exif_a.get('iso') or not exif_b.get('iso') or exif_a['iso'] != exif_b['iso']:
        mismatches.append('iso')
    if not rational_equal(exif_a.get('exposure'), exif_b.get('exposure')):
        mismatches.append('exposure')
    if not rational_equal(exif_a.get('fnumber'), exif_b.get('fnumber')):
        mismatches.append('fnumber')
    if not rational_equal(exif_a.get('focal'), exif_b.get('focal')):
        mismatches.append('focal')

    return {
        'eligible': len(mismatches) == 0,
        'mismatches': mismatches,
        'scope': 'required metadata only; same scene, capture independence and site alignment unknown',
    }


def generate_synthetic_pair(n_samples=50000, seed=42, predictor='lag2',
                            noise_sigma=10.0, fpn_sigma=20.0, scene_gradient=0.5,
                            noise_correlation=0.0):
    """Supplied shared scene/FPN and independent exposure noise.

    noise_correlation=0 gives spatial white Gaussian noise; a nonzero value
    gives AR(1) noise as an explicit countercontrol to the white-noise premise.
    The recurrence starts at zero; no stationarity or camera behavior inferred.
    """
    rng = random.Random(seed)
    scene_fpn = [
        int(1000.0 + scene_gradient * i + rng.gauss(0, fpn_sigma))
        for i in range(n_samples)
    ]
    def noise():
        out, previous = [], 0.0
        for _ in range(n_samples):
            previous = noise_correlation*previous + rng.gauss(0, noise_sigma)
            out.append(previous)
        return out

    temporal_a, temporal_b = noise(), noise()

    raw_a = [scene_fpn[i] + temporal_a[i] for i in range(n_samples)]
    raw_b = [scene_fpn[i] + temporal_b[i] for i in range(n_samples)]

    def apply_pred(raw):
        res = [0.0] * n_samples
        if predictor == 'none' or predictor == 'white_noise':
            return list(raw)
        elif predictor.startswith('lag') and predictor[3:].isdigit():
            d = int(predictor[3:])
            for i in range(n_samples):
                pred = raw[i - d] if i >= d else 1000.0
                res[i] = raw[i] - pred
        else:
            raise ValueError("unsupported synthetic predictor: %s" % predictor)
        return res

    res_a = apply_pred(raw_a)
    res_b = apply_pred(raw_b)
    return res_a, res_b


def analyze_pair_difference(stream_a, stream_b, max_lag=DEFAULT_MAX_LAG, stride=None):
    """Descriptive differences at supplied equal indices, not verified sensor sites."""
    n = min(len(stream_a), len(stream_b))
    diff = [stream_a[i]-stream_b[i]
            if stream_a[i] is not None and stream_b[i] is not None else None for i in range(n)]

    special_lags = []
    if stride and stride > 0:
        for offset in (-2, -1, 0, 1, 2):
            if stride + offset > 0:
                special_lags.append(stride + offset)
            if 2 * stride + offset > 0:
                special_lags.append(2 * stride + offset)

    stats = autocovariance(diff, max_lag=max_lag, special_lags=special_lags)

    candidates = ['none', 'lag1', 'lag2', 'lag3', 'lag4', 'lag1_lag2_bayer']
    if stride and stride > 0:
        candidates.extend(['2d_average', '2d_planar'])

    model_fits = {}
    best_model = None
    best_rmse = float('inf')

    for name in candidates:
        th = theoretical_predictor_signature(name, max_lag=max_lag, stride=stride)
        fit = compare_signatures(stats['lags'], th)
        if fit is not None:
            model_fits[name] = fit
            if fit['rmse'] < best_rmse:
                best_rmse = fit['rmse']
                best_model = name

    equal_lengths = len(stream_a) == len(stream_b)
    return {
        'sample_count': n,
        'max_lag': max_lag,
        'nominal_stride': stride,
        'stream_counts': {'a':len(stream_a), 'b':len(stream_b)},
        'unpaired_tail_counts': {'a':len(stream_a)-n, 'b':len(stream_b)-n},
        'complete_pair_lengths': equal_lengths,
        'valid_difference_samples': stats['valid_samples'],
        'masked_difference_samples': stats['masked_samples'],
        'status': stats['status'] if equal_lengths else 'unequal_stream_lengths',
        'difference_mean': stats['mean'],
        'difference_variance': stats['variance'],
        'difference_std_dev': stats['std_dev'],
        'autocorrelation_lags': stats['lags'],
        'model_fits': model_fits,
        'best_matching_predictor': best_model if equal_lengths else None,
        'best_matching_rmse': best_rmse if best_model and equal_lengths else None,
        'comparison_scope': 'descriptive reference ranking only; no predictor identification',
    }


def self_test():
    """Run mathematical and synthetic regression verification tests."""
    th_white = theoretical_predictor_signature('white_noise', max_lag=4)
    assert all(th_white[l] == 0.0 for l in range(1, 5)), "white noise rho must be 0"

    th_lag1 = theoretical_predictor_signature('lag1', max_lag=4)
    assert abs(th_lag1[1] - (-0.5)) < 1e-12, "lag1 predictor rho(1) must be -0.5"
    assert all(abs(th_lag1[l]) < 1e-12 for l in (2, 3, 4)), "lag1 predictor rho(l>1) must be 0"

    th_lag2 = theoretical_predictor_signature('lag2', max_lag=4)
    assert abs(th_lag2[2] - (-0.5)) < 1e-12, "lag2 predictor rho(2) must be -0.5"
    assert all(abs(th_lag2[l]) < 1e-12 for l in (1, 3, 4)), "lag2 predictor rho(l!=2) must be 0"

    th_planar = theoretical_predictor_signature('2d_planar', max_lag=4, stride=100)
    assert abs(th_planar[2] - (-0.5)) < 1e-12, "planar horizontal rho must be -0.5"
    assert abs(th_planar[100] - (-0.5)) < 1e-12, "planar vertical rho must be -0.5"
    assert abs(th_planar[102] - 0.25) < 1e-12, "planar diagonal rho must be +0.25"

    res_a, res_b = generate_synthetic_pair(n_samples=100000, seed=1234, predictor='lag2',
                                           noise_sigma=15.0, fpn_sigma=50.0, scene_gradient=1.2)
    report = analyze_pair_difference(res_a, res_b, max_lag=8)
    assert report['sample_count'] == 100000
    assert abs(report['difference_mean']) < 0.2, "mean difference must be near zero"
    rho2 = report['autocorrelation_lags'][2]['rho']
    assert abs(rho2 - (-0.5)) < 0.02, "lag-2 empirical rho must be near -0.5 (got %f)" % rho2
    for l in (1, 3, 4, 5):
        rho_l = report['autocorrelation_lags'][l]['rho']
        assert abs(rho_l) < 0.02, "non-stencil empirical rho must be near 0 (lag %d got %f)" % (l, rho_l)
    assert report['best_matching_predictor'] == 'lag2', "best predictor must be lag2"
    assert report['best_matching_rmse'] < 0.02, "best rmse must be small"

    raw_a, raw_b = generate_synthetic_pair(n_samples=50000, seed=5678, predictor='none',
                                           noise_sigma=10.0, fpn_sigma=30.0)
    report_raw = analyze_pair_difference(raw_a, raw_b, max_lag=8)
    assert report_raw['best_matching_predictor'] in ('none', 'white_noise')
    for l in range(1, 9):
        assert abs(report_raw['autocorrelation_lags'][l]['rho']) < 0.02

    exif_base = {'model': 'OM-1', 'iso': 200, 'exposure': (1, 100), 'fnumber': (28, 10), 'focal': (25, 1)}
    assert check_metadata_match(exif_base, exif_base, (5220, 3912), (5220, 3912))['eligible']
    exif_iso_diff = dict(exif_base, iso=400)
    mismatch = check_metadata_match(exif_base, exif_iso_diff, (5220, 3912), (5220, 3912))
    assert not mismatch['eligible'] and 'iso' in mismatch['mismatches']

    colored_a, colored_b = generate_synthetic_pair(
        n_samples=100000, seed=764, predictor='lag1', noise_correlation=0.6)
    colored = analyze_pair_difference(colored_a, colored_b, max_lag=4)
    # For AR(1) source correlation r, the lag1 difference has rho1=-(1-r)/2.
    assert abs(colored['autocorrelation_lags'][1]['rho'] + 0.2) < 0.02
    assert abs(colored['autocorrelation_lags'][1]['rho'] + 0.5) > 0.2

    print("self-test ok: synthetic white and spatially colored noise controls; no camera inference.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*', help='two same-setting ORF input files')
    parser.add_argument('--tokens', type=int, default=DEFAULT_TOKENS, help='tokens to analyze per file')
    parser.add_argument('--max-lag', type=int, default=DEFAULT_MAX_LAG, help='maximum autocorrelation lag')
    parser.add_argument('--stride', type=int, default=None, help='candidate 2D row stride (tokens)')
    parser.add_argument('--names', action='store_true', help='include input basenames in report')
    parser.add_argument('--synthetic', action='store_true', help='run analysis on synthetic pair')
    parser.add_argument('--self-test', action='store_true', help='run self-tests and exit')
    args = parser.parse_args()
    if args.tokens < 1 or args.max_lag < 1 or (args.stride is not None and args.stride < 1):
        parser.error('tokens, max-lag and any stride must be positive')

    if args.self_test:
        self_test()
        return 0

    if args.synthetic:
        a, b = generate_synthetic_pair(n_samples=args.tokens, seed=20261117, predictor='lag2')
        result = analyze_pair_difference(a, b, max_lag=args.max_lag, stride=args.stride)
        output = {
            'method': 'synthetic_paired_difference_covariance',
            'analysis': result,
            'limits': 'Supplied aligned linear-filter synthetic control with spatially white noise; no camera inference.',
        }
        print(json.dumps(output, indent=2))
        return 0

    if len(args.files) != 2:
        parser.error("provide exactly two files to analyze as a pair, or use --self-test / --synthetic")

    path_a, path_b = args.files
    with open(path_a, 'rb') as f:
        data_a = f.read()
    with open(path_b, 'rb') as f:
        data_b = f.read()

    exif_a = read_exif(data_a)
    exif_b = read_exif(data_b)
    stream_a = extract_candidate_stream(data_a, max_tokens=args.tokens)
    stream_b = extract_candidate_stream(data_b, max_tokens=args.tokens)

    geom_a = (stream_a['width'], stream_a['height'])
    geom_b = (stream_b['width'], stream_b['height'])
    meta_check = check_metadata_match(exif_a, exif_b, geom_a, geom_b)

    stride = args.stride or stream_a['width']
    analysis = analyze_pair_difference(stream_a['residuals'], stream_b['residuals'],
                                       max_lag=args.max_lag, stride=stride)
    if stream_a['token_shortfall'] or stream_b['token_shortfall']:
        analysis.update(status='token_shortfall', best_matching_predictor=None,
                        best_matching_rmse=None)
    if not meta_check['eligible']:
        analysis.update(status='metadata_incompatible', best_matching_predictor=None,
                        best_matching_rmse=None)

    report = {
        'method': 'exploratory_candidate_index_difference_covariance',
        'metadata_match': meta_check,
        'tokens_requested': args.tokens,
        'streams': {key:{k:v for k,v in stream.items() if k != 'residuals'}
                    for key,stream in (('a',stream_a),('b',stream_b))},
        'complete': (meta_check['eligible'] and not stream_a['token_shortfall']
                     and not stream_b['token_shortfall'] and analysis['complete_pair_lengths']),
        'pair': {
            'file_a': os.path.basename(path_a) if args.names else None,
            'file_b': os.path.basename(path_b) if args.names else None,
            'model_a': exif_a.get('model'),
            'model_b': exif_b.get('model'),
            'geometry': geom_a if meta_check['eligible'] else {'a': geom_a, 'b': geom_b},
        },
        'analysis': analysis,
        'candidate_grammar': 'MSB stop1 k5; no extra escape skip; q>=17 masked at original candidate index',
        'limits': 'Exploratory equal-candidate-index proxies with an assumed zigzag mapping and nominal W stride. '
                  'Metadata agreement does not establish same scene, independent captures, physical site alignment, '
                  'spatial white noise, fixed-pattern cancellation or a camera predictor. '
                  'Escape masks may depend on signal, valid support differs by lag, and masking does not repair framing. '
                  'No EMVA conformity claimed.',
    }
    print(json.dumps(report, indent=2))
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    sys.exit(main())
