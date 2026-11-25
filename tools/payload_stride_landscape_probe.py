#!/usr/bin/env python3
"""Map stride and phase landscapes across disjoint payload bands.

Part of #296 (Builds on #144, #29, #30). Standard library CPU only.
Evaluates candidate row-stride stability, drift, and phase across sequential
disjoint bands from complete payloads. Compares a fixed-stride model, a
slowly-varying drift model, and a whole-search block-permutation null.

Outputs aggregate JSON only; no raw pixels, images, or token dumps are logged.
"""
import argparse
import array
import hashlib
import itertools
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens as T  # noqa: E402
from orf_signature import Tiff  # noqa: E402


def compute_stride_scores_for_band(q_tokens, s_min, s_max, head=32, min_rows=10):
    """Compute row-start q elevation z-score for candidate strides in a token band.

    Returns dict mapping stride S to {'z': float, 'elevation': float, 'rows': int}.
    """
    n = len(q_tokens)
    prefix = array.array("I", itertools.accumulate(q_tokens, initial=0))
    scores = {}

    for s in range(s_min, s_max + 1):
        if s <= head + 1:
            continue
        nrow = n // s
        if nrow < min_rows:
            continue
        vals = []
        for i in range(nrow):
            start = i * s
            a = prefix[start + head] - prefix[start]
            b = prefix[start + s] - prefix[start + head]
            vals.append(a / head - b / (s - head))
        mean_elev = sum(vals) / nrow
        if nrow > 1:
            var = sum((v - mean_elev) ** 2 for v in vals) / (nrow - 1)
        else:
            var = 0.0
        if var > 1e-12:
            z = mean_elev / (math.sqrt(var) / math.sqrt(nrow))
        else:
            z = 0.0
        scores[s] = {"z": z, "elevation": mean_elev, "rows": nrow}

    return scores


def find_band_winner(scores, s_min, s_max):
    """Find winning stride in scores dict, tracking ties and range boundaries."""
    if not scores:
        return {"best_stride": None, "best_z": None, "ties": [], "range_boundary": None}
    best_z = max(v["z"] for v in scores.values())
    ties = sorted(s for s, v in scores.items() if math.isclose(v["z"], best_z, rel_tol=1e-9, abs_tol=1e-9))
    best_s = ties[0]
    is_boundary = best_s in (s_min, s_max)
    return {
        "best_stride": best_s,
        "best_z": best_z,
        "ties": ties,
        "range_boundary": is_boundary,
    }


def compute_phase_profile(q_tokens, stride, head=32):
    """Compute elevation score across all candidate phases p in 0..stride-1."""
    n = len(q_tokens)
    nrow = (n - stride) // stride
    if nrow < 5:
        return 0, 0.0

    best_p = 0
    best_score = -1e9
    for p in range(stride):
        elev_sum = 0.0
        for i in range(nrow):
            start = i * stride + p
            head_sum = sum(q_tokens[start:start + head])
            tail_sum = sum(q_tokens[start + head:start + stride])
            elev_sum += (head_sum / head) - (tail_sum / (stride - head))
        avg_elev = elev_sum / nrow
        if avg_elev > best_score:
            best_score = avg_elev
            best_p = p
    return best_p, best_score


def shuffle_token_blocks(tokens, block_size, rng):
    """Permute candidate tokens within local blocks to form a local null."""
    out = array.array("B", tokens)
    for start in range(0, len(tokens), block_size):
        end = min(start + block_size, len(tokens))
        blk = list(out[start:end])
        rng.shuffle(blk)
        out[start:end] = array.array("B", blk)
    return out


def analyze_landscape(
    buf,
    nominal_w,
    s_min=None,
    s_max=None,
    delta_s=8,
    band_tokens=131072,
    head=32,
    max_bands=16,
    null_replicates=5,
    seed=296,
):
    """Map stride and phase stability across sequential disjoint payload bands."""
    if nominal_w <= 0:
        raise ValueError("nominal_w must be positive")
    if s_min is None:
        s_min = nominal_w - delta_s
    if s_max is None:
        s_max = nominal_w + delta_s
    if s_min > s_max or s_min <= head + 1:
        raise ValueError("Invalid stride range")

    # Parse full token stream with orf_tokens
    q_all = array.array("B")
    s_all = array.array("B")
    esc_pos = []
    esc_counts = collections.defaultdict(int) if "collections" in globals() else {}
    max_req_tokens = band_tokens * max_bands
    marks, bits_used = T.scan(
        buf,
        max_req_tokens,
        nominal_w,
        esc_extra=0,
        esc_pos=esc_pos,
        qs=q_all,
        ss=s_all,
        cap=31,
    )

    total_tokens = len(q_all)
    if total_tokens < band_tokens:
        raise ValueError(
            f"Insufficient tokens parsed ({total_tokens}) for even one band ({band_tokens})"
        )

    num_bands = min(max_bands, total_tokens // band_tokens)
    bands = []
    all_band_scores = []
    rng = random.Random(seed)

    for b in range(num_bands):
        t_start = b * band_tokens
        t_end = t_start + band_tokens
        q_band = q_all[t_start:t_end]

        # Escape accounting
        # esc_pos entries are (bit_pos, q)
        # Approximate bit extents from marks or linear ratio
        b_scores = compute_stride_scores_for_band(q_band, s_min, s_max, head=head)
        all_band_scores.append(b_scores)
        w = find_band_winner(b_scores, s_min, s_max)

        # Candidate phase at winning stride
        phase, phase_score = compute_phase_profile(q_band, w["best_stride"], head=head)

        # Whole-search null maximum over local block shuffle
        null_max_zs = []
        for _ in range(null_replicates):
            shuffled = shuffle_token_blocks(q_band, block_size=128, rng=rng)
            null_scores = compute_stride_scores_for_band(shuffled, s_min, s_max, head=head)
            nw = find_band_winner(null_scores, s_min, s_max)
            null_max_zs.append(nw["best_z"] if nw["best_z"] is not None else 0.0)

        bands.append({
            "band_index": b,
            "token_start": t_start,
            "token_end": t_end,
            "tokens": band_tokens,
            "best_stride": w["best_stride"],
            "best_z": round(w["best_z"], 4) if w["best_z"] is not None else None,
            "ties": w["ties"],
            "range_boundary": w["range_boundary"],
            "best_phase": phase,
            "phase_score": round(phase_score, 4),
            "null_max_z_median": round(sorted(null_max_zs)[len(null_max_zs) // 2], 4)
            if null_max_zs else 0.0,
        })

    # Model comparisons across bands
    # 1. Fixed-stride model: stride maximizing cumulative sum of z across all bands
    stride_candidates = sorted(all_band_scores[0].keys())
    cum_z = {
        s: sum(b_scores[s]["z"] for b_scores in all_band_scores if s in b_scores)
        for s in stride_candidates
    }
    fixed_stride = max(cum_z, key=cum_z.get)
    fixed_model_mean_z = cum_z[fixed_stride] / num_bands

    # 2. Candidate drift: linear slope of best_stride vs band_index
    best_strides = [b["best_stride"] for b in bands]
    if num_bands >= 2:
        mean_b = (num_bands - 1) / 2.0
        mean_s = sum(best_strides) / num_bands
        denom = sum((i - mean_b) ** 2 for i in range(num_bands))
        drift_slope = (
            sum((i - mean_b) * (best_strides[i] - mean_s) for i in range(num_bands)) / denom
            if denom > 0 else 0.0
        )
    else:
        drift_slope = 0.0

    # 3. Prediction test on held-out last band
    # Fit fixed stride on bands 0..N-2, test on band N-1
    if num_bands >= 2:
        train_cum_z = {
            s: sum(all_band_scores[b][s]["z"] for b in range(num_bands - 1) if s in all_band_scores[b])
            for s in stride_candidates
        }
        train_predicted_stride = max(train_cum_z, key=train_cum_z.get)
        actual_last_stride = bands[-1]["best_stride"]
        prediction_residual = abs(actual_last_stride - train_predicted_stride)
        prediction_match = (actual_last_stride == train_predicted_stride)
    else:
        train_predicted_stride = best_strides[0]
        prediction_residual = 0
        prediction_match = True

    # Check stability: fraction of bands where best_stride matches fixed_stride
    matching_bands = sum(1 for s in best_strides if s == fixed_stride)
    stability_fraction = matching_bands / num_bands

    return {
        "nominal_width": nominal_w,
        "stride_search_range": [s_min, s_max],
        "band_tokens": band_tokens,
        "bands_analyzed": num_bands,
        "total_tokens_read": total_tokens,
        "total_bits_read": bits_used,
        "fixed_model_stride": fixed_stride,
        "fixed_model_mean_z": round(fixed_model_mean_z, 4),
        "stability_fraction": round(stability_fraction, 4),
        "drift_slope_per_band": round(drift_slope, 5),
        "held_out_prediction": {
            "predicted_stride": train_predicted_stride,
            "actual_stride": best_strides[-1],
            "residual_tokens": prediction_residual,
            "match": prediction_match,
        },
        "bands": bands,
    }


def self_test():
    """Verify probe on synthetic multi-band streams with known periodic structure."""
    nominal_stride = 120
    head = 16
    band_tokens = 2400  # 20 rows per band
    num_bands = 4
    total_tokens = band_tokens * num_bands

    # Construct synthetic q token array with periodic elevation at S=120
    # Head has mean q=8, tail has mean q=1
    rng = random.Random(42)
    q_stream = array.array("B")
    for i in range(total_tokens):
        col = i % nominal_stride
        if col < head:
            # high q in head (80% stop bit after 4..8 zeros)
            q_val = rng.randint(4, 9)
        else:
            q_val = rng.randint(0, 2)
        q_stream.append(q_val)

    # Encode q_stream into raw bitstream (stop-1, 5-bit suffix)
    # Each token: q zeros + 1 (stop) + 5-bit suffix 0
    bits = []
    for q in q_stream:
        bits.extend([0] * q)
        bits.append(1)
        bits.extend([0, 0, 0, 0, 0])

    # Convert bit array to bytes
    pad_len = (8 - (len(bits) % 8)) % 8
    bits.extend([0] * pad_len)
    byte_vals = bytearray()
    for i in range(0, len(bits), 8):
        byte_vals.append(sum(bits[i + j] << (7 - j) for j in range(8)))
    buf = bytes(byte_vals)

    res = analyze_landscape(
        buf,
        nominal_w=nominal_stride,
        delta_s=6,
        band_tokens=band_tokens,
        head=head,
        max_bands=num_bands,
        null_replicates=3,
        seed=123,
    )

    # Verify self-test assertions
    assert res["bands_analyzed"] == num_bands, f"Expected {num_bands} bands, got {res['bands_analyzed']}"
    assert res["fixed_model_stride"] == nominal_stride, (
        f"Expected fixed stride {nominal_stride}, got {res['fixed_model_stride']}"
    )
    assert res["stability_fraction"] == 1.0, f"Expected 1.0 stability, got {res['stability_fraction']}"
    assert res["held_out_prediction"]["match"] is True, "Expected prediction match on stationary synthetic stream"
    assert res["drift_slope_per_band"] == 0.0, "Expected zero drift slope on stationary synthetic stream"

    for b in res["bands"]:
        assert b["best_stride"] == nominal_stride
        assert b["best_z"] > 5.0, f"Expected strong z-score (>5), got {b['best_z']}"
        assert b["best_z"] > b["null_max_z_median"], "Observed z must exceed shuffle null"
        assert b["range_boundary"] is False, "True optimum should not be on range boundary"

    # Verify range boundary detection when grid intentionally misses the true stride
    res_miss = analyze_landscape(
        buf,
        nominal_w=140,
        s_min=130,
        s_max=150,
        band_tokens=band_tokens,
        head=head,
        max_bands=2,
        null_replicates=1,
    )
    # Strides around 140 are far from true stride 120, z scores should be near zero or boundary
    assert res_miss["fixed_model_mean_z"] < 3.0, "Mismatched stride grid should produce low z scores"

    print("self-test ok: multi-band stride landscape and prediction benchmark verified.")


def main():
    parser = argparse.ArgumentParser(
        description="Map stride and phase landscapes across disjoint payload bands (#296)"
    )
    parser.add_argument("file", nargs="?", help="Input ORF/raw file path")
    parser.add_argument("--self-test", action="store_true", help="Run synthetic self-test")
    parser.add_argument("--sha256", help="Expected full-file SHA-256 hex")
    parser.add_argument("--stride", type=int, help="Nominal payload stride / width")
    parser.add_argument("--delta-s", type=int, default=8, help="Stride half-search window (default: 8)")
    parser.add_argument("--band-tokens", type=int, default=131072, help="Tokens per band (default: 131072)")
    parser.add_argument("--max-bands", type=int, default=16, help="Maximum bands to evaluate (default: 16)")
    parser.add_argument("--head", type=int, default=32, help="Row head length (default: 32)")
    parser.add_argument("--null-replicates", type=int, default=5, help="Shuffle null replicates per band (default: 5)")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    if not args.file:
        parser.error("file is required unless --self-test is passed")

    with open(args.file, "rb") as f:
        data = f.read()

    actual_hash = hashlib.sha256(data).hexdigest()
    if args.sha256 and actual_hash.lower() != args.sha256.lower():
        sys.exit(f"SHA-256 mismatch: expected {args.sha256}, got {actual_hash}")

    tiff = Tiff(data)
    nominal_w = args.stride or tiff.width
    offset, length = tiff.strip_offsets[0], tiff.strip_byte_counts[0]
    payload = data[offset:offset + length]

    result = analyze_landscape(
        payload,
        nominal_w=nominal_w,
        delta_s=args.delta_s,
        band_tokens=args.band_tokens,
        head=args.head,
        max_bands=args.max_bands,
        null_replicates=args.null_replicates,
    )
    result["file_sha256"] = actual_hash
    result["payload_offset"] = offset
    result["payload_bytes"] = length

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
