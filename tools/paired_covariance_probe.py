#!/usr/bin/env python3
"""Paired-image difference covariance probe (Campaign B, #302, EMVA 1288 §6.6).

Subtracting a same-setting, same-scene pair of exposures cancels deterministic
scene content and fixed-pattern noise (FPN). Under independent temporal noise,
the difference of linear-predicted residuals has a fixed theoretical covariance
signature that depends only on the predictor stencil, while noise scale cancels.
For example, a linear predictor x[i] - x[i-d] yields a normalized autocovariance
rho(d) = -0.5 at lag d and 0 elsewhere.

Standard library only (Python 3.8+). Emits aggregate JSON only; no images,
previews, or pixel dumps are printed or stored.

Usage:
    python -I -B tools/paired_covariance_probe.py FILE_A FILE_B [--tokens N] [--max-lag L] [--stride W]
    python -I -B tools/paired_covariance_probe.py --synthetic [--tokens N] [--predictor PREDICTOR]
    python -I -B tools/paired_covariance_probe.py --self-test
"""
import argparse
import hashlib
import json
import math
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff  # noqa: E402
import orf_tokens  # noqa: E402
from preview_pair_sensitivity import read_exif, rational_equal  # noqa: E402

DEFAULT_TOKENS = 500000
DEFAULT_MAX_LAG = 16


def theoretical_predictor_signature(name, max_lag=DEFAULT_MAX_LAG, stride=None):
    """Compute exact theoretical autocorrelation rho(lag) for a linear predictor.

    Given residual difference D = sum_k c_k Delta[n - k],
    rho(l) = sum_k c_k c_{k+l} / sum_k c_k^2.
    """
    coeffs = {}  # lag -> coefficient
    coeffs[0] = 1.0

    if name == 'none' or name == 'white_noise':
        pass
    elif name.startswith('lag') and name[3:].isdigit():
        d = int(name[3:])
        coeffs[d] = -1.0
    elif name == 'lag1_lag2_bayer':
        # Candidate 2-tap predictor: 0.5 * x[n-1] + 0.5 * x[n-2]
        coeffs[1] = -0.5
        coeffs[2] = -0.5
    elif name == 'lag2_2nd_order':
        # 2 * x[n-2] - x[n-4]
        coeffs[2] = -2.0
        coeffs[4] = 1.0
    elif stride and stride > 0:
        d = 2  # Bayer horizontal stride
        w = stride
        if name == '2d_average':
            # 0.5 * x[n-d] + 0.5 * x[n-w]
            coeffs[d] = -0.5
            coeffs[w] = -0.5
        elif name == '2d_planar':
            # x[n-d] + x[n-w] - x[n-w-d]
            coeffs[d] = -1.0
            coeffs[w] = -1.0
            coeffs[w + d] = 1.0
        else:
            raise ValueError("unknown predictor: %s" % name)
    else:
        raise ValueError("unknown predictor: %s" % name)

    denom = sum(c * c for c in coeffs.values())
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
    """Compute empirical mean, variance, autocovariance, and normalized autocorrelation."""
    n = len(series)
    if n < 2:
        return {'n': n, 'mean': None, 'variance': None, 'lags': {}}

    mean = sum(series) / n
    centered = [x - mean for x in series]
    var = sum(x * x for x in centered) / n
    if var <= 0:
        return {'n': n, 'mean': mean, 'variance': var, 'lags': {}}

    target_lags = set(range(1, min(max_lag + 1, n)))
    if special_lags:
        for l in special_lags:
            if 0 < l < n:
                target_lags.add(l)

    results = {}
    for l in sorted(target_lags):
        cov = sum(centered[i] * centered[i + l] for i in range(n - l)) / (n - l)
        results[l] = {
            'lag': l,
            'cov': cov,
            'rho': cov / var,
        }

    return {
        'n': n,
        'mean': mean,
        'variance': var,
        'std_dev': math.sqrt(var),
        'lags': results,
    }


def compare_signatures(observed_lags, theoretical_lags):
    """Calculate mean squared error and max absolute difference against theoretical rho."""
    common = [l for l in theoretical_lags if l in observed_lags]
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
            residuals.append(0)
    return {
        'width': w,
        'height': h,
        'payload_bytes': len(payload),
        'tokens_parsed': n,
        'bits_used': bits_used,
        'residuals': residuals,
    }


def check_metadata_match(exif_a, exif_b, geom_a, geom_b):
    """Verify that pair exposures share identical camera settings."""
    mismatches = []
    if exif_a.get('model') != exif_b.get('model'):
        mismatches.append('model')
    if geom_a != geom_b:
        mismatches.append('geometry')
    if exif_a.get('iso') != exif_b.get('iso'):
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
    }


def generate_synthetic_pair(n_samples=50000, seed=42, predictor='lag2',
                            noise_sigma=10.0, fpn_sigma=20.0, scene_gradient=0.5):
    """Generate a synthetic flat pair with known scene, FPN, noise, and predictor."""
    rng = random.Random(seed)
    scene_fpn = [
        int(1000.0 + scene_gradient * i + rng.gauss(0, fpn_sigma))
        for i in range(n_samples)
    ]
    temporal_a = [rng.gauss(0, noise_sigma) for _ in range(n_samples)]
    temporal_b = [rng.gauss(0, noise_sigma) for _ in range(n_samples)]

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
    """Run EMVA 1288 difference autocovariance and fit theoretical predictor models."""
    n = min(len(stream_a), len(stream_b))
    diff = [stream_a[i] - stream_b[i] for i in range(n)]

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

    return {
        'sample_count': n,
        'difference_mean': stats['mean'],
        'difference_variance': stats['variance'],
        'difference_std_dev': stats['std_dev'],
        'autocorrelation_lags': stats['lags'],
        'model_fits': model_fits,
        'best_matching_predictor': best_model,
        'best_matching_rmse': best_rmse if best_model else None,
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

    print("self-test ok: EMVA 1288 paired difference covariance and theoretical predictor matching verified.")


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

    if args.self_test:
        self_test()
        return 0

    if args.synthetic:
        a, b = generate_synthetic_pair(n_samples=args.tokens, seed=20261117, predictor='lag2')
        result = analyze_pair_difference(a, b, max_lag=args.max_lag, stride=args.stride)
        output = {
            'method': 'synthetic_paired_difference_covariance',
            'analysis': result,
            'limits': 'EMVA 1288 paired difference test; synthetic control.',
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

    report = {
        'method': 'emva1288_paired_difference_covariance',
        'metadata_match': meta_check,
        'tokens_requested': args.tokens,
        'pair': {
            'file_a': os.path.basename(path_a) if args.names else None,
            'file_b': os.path.basename(path_b) if args.names else None,
            'model_a': exif_a.get('model'),
            'model_b': exif_b.get('model'),
            'geometry': geom_a if meta_check['eligible'] else {'a': geom_a, 'b': geom_b},
        },
        'analysis': analysis,
        'limits': 'EMVA 1288 paired difference method; nominal token residuals do not establish '
                  'sensor ground truth or complete decode.',
    }
    print(json.dumps(report, indent=2))
    return 0 if meta_check['eligible'] else 1


if __name__ == '__main__':
    sys.exit(main())
