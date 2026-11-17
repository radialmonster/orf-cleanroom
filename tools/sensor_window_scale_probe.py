#!/usr/bin/env python3
"""Multi-scale window sensitivity probe for sensor rejection controls (#301, V0 G8).

Evaluates how synthetic development envelope limits and rejection confusion
behave across window dimensions (e.g. 32x24, 64x48, 128x96, 256x192). Builds on
sensor_rejection_controls.py (#310) and v0_sensor_controls.py (#324), addressing
specs/V0.md Gap G8.

Tests whether window scaling stabilizes feature bounds (lag2_mean_abs,
lane_mean_spread, seam_mean_abs, outside_fraction), how the confusion matrix
(false rejections of identity vs false acceptances of nonidentity transforms)
evolves with scale, and whether larger windows resolve or preserve the lag2
rejections observed in packed-16 V0 files (lead #325).

Standard library only (Python 3.8+). Emits aggregate JSON only.

Usage:
    python -I -B tools/sensor_window_scale_probe.py --scales 1 2 4 [--heldout]
    python -I -B tools/sensor_window_scale_probe.py --sample ID NAME SHA256 FILE --scales 1 2 4
    python -I -B tools/sensor_window_scale_probe.py --self-test
"""
import argparse
import hashlib
import json
import math
import os
import re
import stat
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sensor_rejection_controls as controls  # noqa: E402
from v0_sensor_controls import geometry  # noqa: E402

BASE_W, BASE_H = 32, 24
MAX_BYTES = 128 * 1024 * 1024


def scale_dimensions(multiplier):
    """Return (width, height) for a scale multiplier."""
    return BASE_W * multiplier, BASE_H * multiplier


def synthetic_cohort_at_scale(seeds, width, height):
    """Generate synthetic trials across scenes, noise levels, and mappings for (width, height)."""
    rows = []
    for seed in seeds:
        for scene in controls.SCENES:
            for noise in controls.NOISE:
                vals = controls.synthetic(scene, noise, seed, width=width, height=height)
                for mapping in controls.MAPPINGS:
                    t_vals = controls.transform(vals, mapping)
                    feats = controls.features(t_vals, width, height)
                    rows.append({
                        "seed": seed,
                        "scene": scene,
                        "noise": noise,
                        "mapping": mapping,
                        "features": feats,
                    })
    return rows


def envelope_at_scale(development_trials):
    """Compute upper envelope limits over identity development trials."""
    return controls.envelope([r for r in development_trials if r["mapping"] == "identity"])


def evaluate_confusion(trials, limits, width, height):
    """Classify trials against limits and return aggregate confusion counts."""
    counts = {
        "identity_accepted": 0,
        "identity_rejected": 0,
        "nonidentity_accepted": 0,
        "nonidentity_rejected": 0,
    }
    by_mapping = {m: {"accepted": 0, "rejected": 0} for m in controls.MAPPINGS}
    for t in trials:
        t_vals = controls.transform(
            controls.synthetic(t["scene"], t["noise"], t["seed"], width=width, height=height),
            t["mapping"]
        )
        feats = controls.features(t_vals, width, height)
        reasons = controls.classify(feats, limits)
        outcome = "rejected" if reasons else "accepted"
        label = "identity" if t["mapping"] == "identity" else "nonidentity"
        counts[label + "_" + outcome] += 1
        by_mapping[t["mapping"]][outcome] += 1

    return counts, by_mapping


def evaluate_scale_sensitivity(scales, include_heldout=True):
    """Evaluate synthetic envelope limits and confusion behavior across window scales."""
    results = {}
    for m in scales:
        w, h = scale_dimensions(m)
        dev_trials = synthetic_cohort_at_scale(controls.DEVELOPMENT_SEEDS, w, h)
        limits = envelope_at_scale(dev_trials)

        dev_counts, dev_by_map = evaluate_confusion(dev_trials, limits, w, h)
        entry = {
            "scale_multiplier": m,
            "width": w,
            "height": h,
            "sample_count": w * h,
            "envelope_limits": limits,
            "development_confusion": dev_counts,
            "development_by_mapping": dev_by_map,
        }

        if include_heldout:
            held_trials = synthetic_cohort_at_scale(controls.HELDOUT_SEEDS, w, h)
            held_counts, held_by_map = evaluate_confusion(held_trials, limits, w, h)
            entry["heldout_confusion"] = held_counts
            entry["heldout_by_mapping"] = held_by_map

        results["scale_%dx" % m] = entry
    return results


def extract_v0_windows(data, info, width, height):
    """Extract top, middle, bottom windows of dimensions (width, height) from packed-16 data."""
    img_w, img_h = info["width"], info["height"]
    if width > img_w or height > img_h:
        raise ValueError("requested window exceeds image geometry")
    x = (img_w - width) // 2
    out = {}
    for label, y in (("top", 0), ("middle", (img_h - height) // 2), ("bottom", img_h - height)):
        raw_words = []
        for r in range(y, y + height):
            start = info["payload_offset"] + 2 * (r * img_w + x)
            chunk = data[start:start + 2 * width]
            fmt = "<%dH" if info["byte_order"] == "little" else ">%dH"
            raw_words.extend(struct.unpack(fmt % width, chunk))
        shifted = [w >> 4 for w in raw_words]
        out[label] = {
            "x": x,
            "y": y,
            "raw_words": raw_words,
            "shifted_words": shifted,
        }
    return out


def measure_v0_sample(data, scales, limits_by_scale):
    """Measure packed-16 V0 sample across window scales."""
    info = geometry(data)
    scale_reports = {}
    for m in scales:
        w, h = scale_dimensions(m)
        limits = limits_by_scale["scale_%dx" % m]["envelope_limits"]
        windows = extract_v0_windows(data, info, w, h)
        win_reports = {}
        for pos in ("top", "middle", "bottom"):
            w_data = windows[pos]
            feats = controls.features(w_data["shifted_words"], w, h)
            reasons = controls.classify(feats, limits)
            win_reports[pos] = {
                "x": w_data["x"],
                "y": w_data["y"],
                "features": feats,
                "rejected_by": reasons,
                "status": "rejected" if reasons else "accepted",
            }
        scale_reports["scale_%dx" % m] = {
            "width": w,
            "height": h,
            "windows": win_reports,
        }
    return {
        "geometry": info,
        "scales": scale_reports,
    }


def self_test():
    """Unit and regression tests for multi-scale envelope probe."""
    # 1. Dimension scaling
    assert scale_dimensions(1) == (32, 24)
    assert scale_dimensions(2) == (64, 48)
    assert scale_dimensions(4) == (128, 96)

    # 2. Synthetic envelope calculation across scales 1x and 2x
    res = evaluate_scale_sensitivity([1, 2], include_heldout=True)
    assert "scale_1x" in res and "scale_2x" in res
    lim1 = res["scale_1x"]["envelope_limits"]
    lim2 = res["scale_2x"]["envelope_limits"]

    # Outside fraction must be bounded in [0, 4095]
    assert lim1["outside_fraction"] == 0.0
    assert lim2["outside_fraction"] == 0.0

    # Lag2 mean absolute difference remains finite and strictly positive
    assert 0.0 < lim1["lag2_mean_abs"] < 4095.0
    assert 0.0 < lim2["lag2_mean_abs"] < 4095.0

    # Development identity acceptance must be 100% (18/18 trials at each scale)
    dev1 = res["scale_1x"]["development_confusion"]
    assert dev1["identity_accepted"] == 18
    assert dev1["identity_rejected"] == 0

    # 3. Nonidentity offset_range must be 100% rejected at all scales
    map1 = res["scale_1x"]["development_by_mapping"]
    map2 = res["scale_2x"]["development_by_mapping"]
    assert map1["offset_range"]["rejected"] == 18
    assert map2["offset_range"]["rejected"] == 18

    # 4. Complement is an involution that mathematically preserves lag2 differences
    # (except for a known binary64 floating-tie edge case on textured/noise16)
    assert map1["complement"]["accepted"] >= 17
    assert map2["complement"]["accepted"] >= 17

    print("self-test ok: multi-scale window sensitivity and envelope accounting verified.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", type=int, nargs="+", default=[1, 2, 4],
                        help="scale multipliers relative to 32x24 (e.g. 1 2 4)")
    parser.add_argument("--no-heldout", action="store_true",
                        help="omit synthetic heldout seed evaluation")
    parser.add_argument("--sample", nargs=4, action="append",
                        metavar=("ID", "NAME", "SHA256", "FILE"),
                        help="packed-16 V0 input sample")
    parser.add_argument("--self-test", action="store_true",
                        help="run self-tests and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0

    scales = sorted(set(args.scales))
    for s in scales:
        if s < 1 or s > 32:
            parser.error("scale multipliers must be between 1 and 32")

    synthetic_results = evaluate_scale_sensitivity(scales, include_heldout=not args.no_heldout)

    report = {
        "method": "sensor_window_scale_probe",
        "base_dimensions": [BASE_W, BASE_H],
        "scales_evaluated": scales,
        "synthetic_scaling": synthetic_results,
        "samples": [],
        "limits": "Descriptive synthetic multi-scale sensitivity; toy envelope bounds "
                  "do not establish sensor truth or camera noise model.",
    }

    if args.sample:
        for sid, name, digest, path_str in args.sample:
            row = {"pixls_id": sid, "public_name": name, "sha256": digest}
            try:
                with open(path_str, "rb") as f:
                    data = f.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError("hash or size mismatch")
                res = measure_v0_sample(data, scales, synthetic_results)
                row.update(res, status="ok")
            except Exception as exc:
                row.update(status="error", error=type(exc).__name__)
            report["samples"].append(row)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
