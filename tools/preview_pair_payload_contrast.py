#!/usr/bin/env python3
"""Candidate same-scene pair payload feature contrast probe (#295).

Compares frozen compressed bitstream features within candidate pairs (from
numeric preview screening or companion ORF/ORI pairs) to evaluate whether
numerically matched captures reduce scene/mode confounding.

Computes pairwise contrasts in bits per reported sample (bpp), candidate q0
proportion, escape rate, suffix bit balance, and candidate token lag
autocorrelation. Evaluates EXIF metadata agreement (exposure, aperture, ISO,
focal length) to separate shared-setting effects from scene identity.

Standard library only (Python 3.8+). Emits aggregate JSON only.

Usage:
    python -I -B tools/preview_pair_payload_contrast.py FILE_A FILE_B [--tokens N] [--names]
    python -I -B tools/preview_pair_payload_contrast.py --self-test
"""
import argparse
import hashlib
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc  # noqa: E402
import orf_tokens  # noqa: E402
from preview_pair_sensitivity import read_exif, rational_equal  # noqa: E402

DEFAULT_TOKENS = 500000


def calculate_autocorr(series, lag):
    """Compute Pearson autocorrelation at lag."""
    n = len(series)
    if n <= lag:
        return None
    mean = sum(series) / n
    centered = [x - mean for x in series]
    var = sum(x * x for x in centered) / n
    if var <= 0:
        return 0.0
    cov = sum(centered[i] * centered[i + lag] for i in range(n - lag)) / (n - lag)
    return cov / var


def extract_payload_features(data, max_tokens=DEFAULT_TOKENS):
    """Extract frozen bitstream features from raw ORF/ORI container."""
    w, h, payload = orf_tokens.locate_data(data)
    qs, ss, _, bits_used = orf_tokens.parse(payload, max_tokens, w)
    n = len(qs)
    if not n:
        raise ValueError("no tokens extracted from payload")

    reported_samples = w * h
    bpp = (len(payload) * 8.0) / reported_samples if reported_samples else 0.0

    q0_count = sum(1 for q in qs if q == 0)
    esc_count = sum(1 for q in qs if q >= orf_tokens.ESC_Q)

    b4_count = sum(1 for s in ss if (s >> 4) & 1)
    b2_count = sum(1 for s in ss if (s >> 2) & 1)

    # Token integer value representation (q capped at 17, combined with suffix)
    token_vals = [(min(q, 17) << 5) | (s & 31) for q, s in zip(qs, ss)]
    lag1 = calculate_autocorr(token_vals, 1)
    lag2 = calculate_autocorr(token_vals, 2)

    return {
        "width": w,
        "height": h,
        "reported_samples": reported_samples,
        "payload_bytes": len(payload),
        "bpp": bpp,
        "tokens_parsed": n,
        "bits_used": bits_used,
        "q0_fraction": q0_count / n,
        "escape_fraction": esc_count / n,
        "suffix_b4_fraction": b4_count / n,
        "suffix_b2_fraction": b2_count / n,
        "token_autocorr_lag1": lag1,
        "token_autocorr_lag2": lag2,
    }


def compute_preview_correlation(data_a, data_b):
    """Compute normalized correlation of first-component DC grids if previews exist."""
    try:
        prev_a = jpeg_dc.find_preview(data_a)
        prev_b = jpeg_dc.find_preview(data_b)
        if not prev_a or not prev_b:
            return None
        _, off_a, _, _, _ = prev_a
        _, off_b, _, _, _ = prev_b
        wb_a, hb_a, dc_a = jpeg_dc.decode(data_a, off_a)
        wb_b, hb_b, dc_b = jpeg_dc.decode(data_b, off_b)
        if wb_a != wb_b or hb_a != hb_b or not dc_a:
            return None
        n = len(dc_a)
        mean_a = sum(dc_a) / n
        mean_b = sum(dc_b) / n
        ca = [x - mean_a for x in dc_a]
        cb = [y - mean_b for y in dc_b]
        den = math.sqrt(sum(x * x for x in ca) * sum(y * y for y in cb))
        if den <= 0:
            return 0.0
        return sum(x * y for x, y in zip(ca, cb)) / den
    except Exception:
        return None


def evaluate_pair_contrast(feat_a, feat_b, exif_a, exif_b, preview_r=None):
    """Compute scalar differences across frozen bitstream features and check metadata."""
    mismatches = []
    if exif_a.get("model") != exif_b.get("model"):
        mismatches.append("model")
    if (feat_a["width"], feat_a["height"]) != (feat_b["width"], feat_b["height"]):
        mismatches.append("geometry")
    if exif_a.get("iso") != exif_b.get("iso"):
        mismatches.append("iso")
    if not rational_equal(exif_a.get("exposure"), exif_b.get("exposure")):
        mismatches.append("exposure")
    if not rational_equal(exif_a.get("fnumber"), exif_b.get("fnumber")):
        mismatches.append("fnumber")
    if not rational_equal(exif_a.get("focal"), exif_b.get("focal")):
        mismatches.append("focal")

    d_bpp = abs(feat_a["bpp"] - feat_b["bpp"])
    d_q0 = abs(feat_a["q0_fraction"] - feat_b["q0_fraction"])
    d_esc = abs(feat_a["escape_fraction"] - feat_b["escape_fraction"])
    d_b4 = abs(feat_a["suffix_b4_fraction"] - feat_b["suffix_b4_fraction"])
    d_b2 = abs(feat_a["suffix_b2_fraction"] - feat_b["suffix_b2_fraction"])

    lag1_diff = abs(feat_a["token_autocorr_lag1"] - feat_b["token_autocorr_lag1"]) \
        if feat_a["token_autocorr_lag1"] is not None and feat_b["token_autocorr_lag1"] is not None else None
    lag2_diff = abs(feat_a["token_autocorr_lag2"] - feat_b["token_autocorr_lag2"]) \
        if feat_a["token_autocorr_lag2"] is not None and feat_b["token_autocorr_lag2"] is not None else None

    # Composite feature distance (normalized L2 over dimensionless fractions)
    diffs = [d_q0, d_esc, d_b4, d_b2]
    if lag1_diff is not None:
        diffs.append(lag1_diff)
    if lag2_diff is not None:
        diffs.append(lag2_diff)
    composite_dist = math.sqrt(sum(d * d for d in diffs))

    return {
        "metadata_agreement": {
            "all_matched": len(mismatches) == 0,
            "mismatches": mismatches,
            "shared_exposure_settings": not any(m in mismatches for m in ("iso", "exposure", "fnumber", "focal")),
        },
        "preview_correlation": preview_r,
        "feature_differences": {
            "delta_bpp": d_bpp,
            "delta_q0_fraction": d_q0,
            "delta_escape_fraction": d_esc,
            "delta_suffix_b4_fraction": d_b4,
            "delta_suffix_b2_fraction": d_b2,
            "delta_token_autocorr_lag1": lag1_diff,
            "delta_token_autocorr_lag2": lag2_diff,
            "composite_fractional_distance": composite_dist,
        },
    }


def self_test():
    """Synthetic unit tests for pair feature extraction and contrast calculation."""
    # 1. Autocorrelation check on constant and alternating sequences
    assert calculate_autocorr([5] * 10, 1) == 0.0
    alt = [1, -1] * 50
    assert abs(calculate_autocorr(alt, 1) - (-1.0)) < 1e-10
    assert abs(calculate_autocorr(alt, 2) - 1.0) < 1e-10

    # 2. Contrast evaluation between two synthetic feature sets
    fa = {
        "width": 5220, "height": 3912, "reported_samples": 5220 * 3912,
        "payload_bytes": 15000000, "bpp": 5.87, "tokens_parsed": 100000,
        "bits_used": 800000, "q0_fraction": 0.40, "escape_fraction": 0.01,
        "suffix_b4_fraction": 0.50, "suffix_b2_fraction": 0.48,
        "token_autocorr_lag1": 0.35, "token_autocorr_lag2": 0.20,
    }
    # fb is very close (same scene with minor noise)
    fb = dict(fa, payload_bytes=15050000, bpp=5.89, q0_fraction=0.405, escape_fraction=0.011,
              suffix_b4_fraction=0.502, token_autocorr_lag1=0.348)

    exif = {"model": "OM-1", "iso": 200, "exposure": (1, 100), "fnumber": (28, 10), "focal": (25, 1)}
    contrast = evaluate_pair_contrast(fa, fb, exif, exif, preview_r=0.999)
    assert contrast["metadata_agreement"]["all_matched"]
    assert contrast["feature_differences"]["delta_bpp"] < 0.05
    assert contrast["feature_differences"]["composite_fractional_distance"] < 0.02

    # fc is unrelated (completely different scene statistics)
    fc = dict(fa, payload_bytes=22000000, bpp=8.62, q0_fraction=0.15, escape_fraction=0.08,
              suffix_b4_fraction=0.62, token_autocorr_lag1=0.05)
    unrelated_contrast = evaluate_pair_contrast(fa, fc, exif, exif, preview_r=0.45)
    assert unrelated_contrast["feature_differences"]["delta_bpp"] > 2.0
    assert unrelated_contrast["feature_differences"]["composite_fractional_distance"] > 0.20

    print("self-test ok: pair payload contrast and metadata checks verified.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="pair of ORF/ORI files to compare")
    parser.add_argument("--tokens", type=int, default=DEFAULT_TOKENS, help="tokens to parse per file")
    parser.add_argument("--names", action="store_true", help="output file basenames")
    parser.add_argument("--self-test", action="store_true", help="run self-test and exit")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if len(args.files) != 2:
        parser.error("provide exactly two files to compare as a pair, or use --self-test")

    path_a, path_b = args.files
    with open(path_a, "rb") as f:
        data_a = f.read()
    with open(path_b, "rb") as f:
        data_b = f.read()

    exif_a = read_exif(data_a)
    exif_b = read_exif(data_b)

    feat_a = extract_payload_features(data_a, max_tokens=args.tokens)
    feat_b = extract_payload_features(data_b, max_tokens=args.tokens)

    prev_r = compute_preview_correlation(data_a, data_b)
    contrast = evaluate_pair_contrast(feat_a, feat_b, exif_a, exif_b, preview_r=prev_r)

    report = {
        "method": "preview_pair_payload_contrast",
        "pair": {
            "file_a": os.path.basename(path_a) if args.names else None,
            "file_b": os.path.basename(path_b) if args.names else None,
            "model_a": exif_a.get("model"),
            "model_b": exif_b.get("model"),
        },
        "features_a": feat_a,
        "features_b": feat_b,
        "contrast": contrast,
        "limits": "Descriptive pair comparison; preview correlation and shared metadata "
                  "do not establish identical sensor readout or scene identity.",
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
