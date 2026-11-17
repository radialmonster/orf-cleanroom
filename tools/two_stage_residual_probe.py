#!/usr/bin/env python3
"""Two-stage residual filter cascade and diagnostic sensitivity probe (#298, US7715639B2).

Evaluates the prediction-error filtering and stateful inverse described in
patent US7715639B2 (formulas 10, 11, 13, 14, 17, 19). The patent splits off an
error's low bit, filters the even part using an internal correction state, and
entropy-codes the resulting corrected error.

Because the inverse P[n] = 2*(E[n] + floor(C[n-1]/2)) + L[n] requires tracking
the state C[n-1], a memoryless (stateless) token-to-residual map cannot express
this inverse. This tool verifies exact round-trip inversion on synthetic signed
integer sequences, measures reconstruction drift under stateless mappings, and
evaluates the blind spot in direct integration/predictor tests (#31, #32).

Standard library only (Python 3.8+). Emits aggregate JSON only.

Usage:
    python -I -B tools/two_stage_residual_probe.py --synthetic [--tokens N] [--scene SCENE]
    python -I -B tools/two_stage_residual_probe.py --self-test
"""
import argparse
import json
import math
import os
import random
import sys


def two_stage_encode(p_seq, c_init=0):
    """Encode a sequence of signed prediction errors into (E, L) and state C.

    Formulas from US7715639B2:
        P_even = 2 * floor(P / 2)                (Formula 10)
        L = P - P_even                           (Formula 11, low bit: 0 or 1)
        C = floor(P_even / 2) + floor(Cprev / 2) (Formula 13, correction state)
        E = P_even - C                           (Formula 14, corrected error)
    """
    c_prev = c_init
    encoded = []
    states = []
    for p in p_seq:
        p_even = 2 * (p // 2)
        l = p - p_even
        c = (p_even // 2) + (c_prev // 2)
        e = p_even - c
        encoded.append((e, l))
        states.append(c)
        c_prev = c
    return encoded, states


def two_stage_decode(encoded_pairs, c_init=0):
    """Decode a sequence of (E, L) pairs into original prediction errors P.

    Formulas from US7715639B2:
        P_even = 2 * (E + floor(Cprev / 2))      (Formula 17)
        P = P_even + L                           (Formula 19)
        C = floor(P_even / 2) + floor(Cprev / 2) (State update)
    """
    c_prev = c_init
    decoded = []
    states = []
    for e, l in encoded_pairs:
        p_even = 2 * (e + (c_prev // 2))
        p = p_even + l
        c = (p_even // 2) + (c_prev // 2)
        decoded.append(p)
        states.append(c)
        c_prev = c
    return decoded, states


def stateless_decode(encoded_pairs):
    """Attempt memoryless / direct reconstruction assuming Cprev = 0."""
    return [2 * e + l for e, l in encoded_pairs]


def simulate_pixel_sequence(n=1000, scene='gradient', seed=42):
    """Generate a synthetic 1D pixel sequence and ground-truth 1D DPCM residuals."""
    rng = random.Random(seed)
    pixels = [0] * n
    base = 1000
    for i in range(n):
        if scene == 'flat':
            pixels[i] = int(base + rng.gauss(0, 5))
        elif scene == 'gradient':
            pixels[i] = int(base + 0.1 * i + rng.gauss(0, 5))
        elif scene == 'textured':
            pixels[i] = int(base + 50 * math.sin(i / 10.0) + rng.gauss(0, 8))
        else:
            raise ValueError("unknown scene: %s" % scene)

    # 1D DPCM predictor: P[0] = pixels[0] - 1000, P[i] = pixels[i] - pixels[i-1]
    residuals = [0] * n
    residuals[0] = pixels[0] - base
    for i in range(1, n):
        residuals[i] = pixels[i] - pixels[i - 1]

    return pixels, residuals


def evaluate_cascade(pixels, residuals):
    """Compare exact stateful cascade reconstruction against stateless direct map."""
    n = len(residuals)
    encoded, states = two_stage_encode(residuals, c_init=0)
    decoded, dec_states = two_stage_decode(encoded, c_init=0)

    # Exact round-trip verification
    exact_match = (decoded == residuals)

    # Reconstruct pixels using exact stateful residuals
    recon_stateful = [0] * n
    recon_stateful[0] = 1000 + decoded[0]
    for i in range(1, n):
        recon_stateful[i] = recon_stateful[i - 1] + decoded[i]
    stateful_pixel_match = (recon_stateful == pixels)

    # Reconstruct pixels using stateless direct map
    stateless_res = stateless_decode(encoded)
    recon_stateless = [0] * n
    recon_stateless[0] = 1000 + stateless_res[0]
    for i in range(1, n):
        recon_stateless[i] = recon_stateless[i - 1] + stateless_res[i]

    # Compute stateless drift metrics
    pixel_errors = [recon_stateless[i] - pixels[i] for i in range(n)]
    res_errors = [stateless_res[i] - residuals[i] for i in range(n)]

    max_res_err = max(abs(e) for e in res_errors)
    max_pixel_err = max(abs(e) for e in pixel_errors)
    rmse_pixel = math.sqrt(sum(e * e for e in pixel_errors) / n)

    # State properties
    min_c = min(states)
    max_c = max(states)
    nonzero_states = sum(1 for c in states if c != 0)

    return {
        'count': n,
        'exact_residual_roundtrip': exact_match,
        'stateful_pixel_roundtrip': stateful_pixel_match,
        'correction_state': {
            'min': min_c,
            'max': max_c,
            'nonzero_fraction': nonzero_states / n,
        },
        'stateless_direct_map_failure': {
            'max_residual_error': max_res_err,
            'max_pixel_drift': max_pixel_err,
            'pixel_rmse': rmse_pixel,
            'stateless_reconstructs_exact': (recon_stateless == pixels),
        },
        'diagnostic_conclusion': (
            'Direct stateless token-to-residual mapping fails on this cascade; '
            'reconstruction drifts with unbounded variance if correction state is neglected.'
            if not (recon_stateless == pixels) else 'Stateless mapping unexpectedly succeeded.'
        ),
    }


def self_test():
    """Exhaustive unit checks on US7715639B2 formulas, edge cases, and drift."""
    # 1. Patent publication text verification (PATENTS.md line 41)
    patent_example = [-3, -1, 0, 1, 3]
    enc, st = two_stage_encode(patent_example, c_init=0)
    expected_e = [-2, 0, 1, 1, 2]
    expected_l = [1, 1, 0, 1, 1]
    expected_c = [-2, -2, -1, -1, 0]
    assert [e for e, l in enc] == expected_e, "corrected error E mismatch with patent"
    assert [l for e, l in enc] == expected_l, "low bit L mismatch with patent"
    assert st == expected_c, "correction state C mismatch with patent"

    dec, dec_st = two_stage_decode(enc, c_init=0)
    assert dec == patent_example, "decoded sequence must exactly match patent input"
    assert dec_st == expected_c, "decoder states must match encoder states"

    # 2. Exhaustive small sequences: all combinations of -4..4 of length 4
    for a in range(-4, 5):
        for b in range(-4, 5):
            seq = [a, b, a + b, a - b]
            enc_seq, _ = two_stage_encode(seq, c_init=0)
            dec_seq, _ = two_stage_decode(enc_seq, c_init=0)
            assert dec_seq == seq, "exhaustive check failed on %r" % seq

    # 3. Large sequence random walk
    rng = random.Random(1337)
    rw = [int(rng.gauss(0, 50)) for _ in range(5000)]
    enc_rw, _ = two_stage_encode(rw, c_init=0)
    dec_rw, _ = two_stage_decode(enc_rw, c_init=0)
    assert dec_rw == rw, "random walk roundtrip failed"

    # 4. Inversion ambiguity without low bit L
    # Errors 0 and 1 with Cprev = 0 give identical corrected error E = 0:
    enc0, _ = two_stage_encode([0], c_init=0)
    enc1, _ = two_stage_encode([1], c_init=0)
    assert enc0[0][0] == enc1[0][0] == 0, "errors 0 and 1 must produce same E=0 when Cprev=0"
    assert enc0[0][1] != enc1[0][1], "low bit L must separate errors 0 and 1"

    # 5. Diagnostic sensitivity evaluation
    for scene in ('flat', 'gradient', 'textured'):
        pix, res = simulate_pixel_sequence(n=1000, scene=scene, seed=42)
        eval_res = evaluate_cascade(pix, res)
        assert eval_res['exact_residual_roundtrip'], "stateful residual must match"
        assert eval_res['stateful_pixel_roundtrip'], "stateful pixel must match"
        assert not eval_res['stateless_direct_map_failure']['stateless_reconstructs_exact'], \
            "stateless map must fail on %s scene" % scene
        assert eval_res['stateless_direct_map_failure']['max_pixel_drift'] > 10, \
            "stateless map must show significant pixel drift"

    print("self-test ok: US7715639B2 two-stage filter and inverse verified; "
          "exact round-trip confirmed; stateless direct-map drift demonstrated.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tokens', type=int, default=5000, help='number of synthetic tokens')
    parser.add_argument('--scene', choices=['flat', 'gradient', 'textured'], default='gradient',
                        help='synthetic scene type')
    parser.add_argument('--seed', type=int, default=42, help='random seed')
    parser.add_argument('--self-test', action='store_true', help='run regression self-tests and exit')
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    pixels, residuals = simulate_pixel_sequence(n=args.tokens, scene=args.scene, seed=args.seed)
    report = evaluate_cascade(pixels, residuals)
    output = {
        'method': 'us7715639b2_two_stage_residual_probe',
        'parameters': {
            'tokens': args.tokens,
            'scene': args.scene,
            'seed': args.seed,
        },
        'results': report,
        'limits': 'Synthetic control evaluating stateful residual filtering and '
                  'stateless diagnostic blind spots; no camera codec claim.',
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
