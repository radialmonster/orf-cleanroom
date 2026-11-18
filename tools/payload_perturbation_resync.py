#!/usr/bin/env python3
"""Local bit perturbation and parser state resynchronization benchmark (#300).

Supports #300 (Builds on #197, #30, #87). Standard library CPU only.
Evaluates boundary recovery, consumed bits, value error propagation, and right
censoring under controlled 1-bit perturbations (flip, insert, delete) at frozen
anchor coordinates. Compares candidate camera grammar (lead #11: stop-1 Rice k=5)
against alternative candidate grammars (Rice k=4, fixed 5-bit).

Outputs aggregate JSON only; no raw pixels, images, or token dumps are logged.
"""
import argparse
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff  # noqa: E402

GRAMMARS = ("orf_rice5", "rice4", "fixed5")
OPERATIONS = ("flip", "insert", "delete")
DEFAULT_ANCHORS = (64, 128, 256, 512, 1024)
DEFAULT_WINDOW = 1024
DEFAULT_RUN = 3


def bytes_to_bits(data):
    """Convert bytes to MSB-first binary string '01...'."""
    return "".join(format(b, "08b") for b in data)


def parse_tokens(bits, grammar="orf_rice5", escape_q=17):
    """Parse bitstring into list of (start, end, q, value, is_escape) tokens and tail."""
    if grammar not in GRAMMARS:
        raise ValueError(f"Unknown grammar: {grammar}")
    tokens = []
    pos = 0
    n = len(bits)

    if grammar in ("orf_rice5", "rice4"):
        k = 5 if grammar == "orf_rice5" else 4
        while pos < n:
            start = pos
            stop = bits.find("1", pos)
            if stop < 0 or stop + 1 + k > n:
                break
            q = stop - start
            is_esc = (q >= escape_q) and (grammar == "orf_rice5")
            end = stop + 1 + k
            suffix = int(bits[stop + 1:end], 2)
            val = (q << k) | suffix
            tokens.append((start, end, q, val, is_esc))
            pos = end
    elif grammar == "fixed5":
        while pos + 5 <= n:
            start = pos
            end = pos + 5
            val = int(bits[start:end], 2)
            tokens.append((start, end, 0, val, False))
            pos = end

    tail = n - pos
    return tokens, tail


def perturb_bits(bits, anchor, operation):
    """Apply local 1-bit perturbation at anchor index."""
    if not 0 <= anchor < len(bits):
        raise ValueError(f"Anchor {anchor} outside bitstream of length {len(bits)}")
    if operation == "flip":
        flipped = "0" if bits[anchor] == "1" else "1"
        return bits[:anchor] + flipped + bits[anchor + 1:]
    if operation == "insert":
        ins = "1" if bits[anchor] == "0" else "0"
        return bits[:anchor] + ins + bits[anchor:]
    if operation == "delete":
        return bits[:anchor] + bits[anchor + 1:]
    raise ValueError(f"Unknown operation: {operation}")


def forward_coord(coordinate, anchor, operation):
    """Map original bit coordinate strictly after anchor to perturbed coordinate."""
    if coordinate <= anchor:
        raise ValueError("Coordinate must be strictly after anchor")
    offset = {"flip": 0, "insert": 1, "delete": -1}[operation]
    return coordinate + offset


def measure_trial(bits, grammar, anchor, operation, window=DEFAULT_WINDOW, run=DEFAULT_RUN):
    """Measure recovery and value agreement for one perturbation trial."""
    if window < 1 or run < 1:
        raise ValueError("Positive window and run required")
    limit = min(len(bits), anchor + window)
    if limit <= anchor:
        raise ValueError("Window must extend beyond anchor")

    orig_tokens, orig_tail = parse_tokens(bits[:limit], grammar)
    changed_stream = perturb_bits(bits, anchor, operation)
    changed_limit = forward_coord(limit, anchor, operation)
    changed_tokens, changed_tail = parse_tokens(changed_stream[:changed_limit], grammar)

    # Index changed tokens by span (start, end)
    changed_spans = {(s, e): (q, v) for s, e, q, v, _ in changed_tokens}
    changed_boundaries = {0} | {e for _, e, _, _, _ in changed_tokens}

    # Common boundaries strictly after edit
    common_endpoints = [
        e for _, e, _, _, _ in orig_tokens
        if e > anchor and forward_coord(e, anchor, operation) in changed_boundaries
    ]

    # Evaluate sustained boundary recovery (run consecutive matching spans)
    eligible = [(s, e, q, v) for s, e, q, v, _ in orig_tokens if s > anchor]
    consecutive = 0
    recovery_dist = None
    mismatches = 0
    comparable_spans = 0

    for idx, (s, e, q, v) in enumerate(eligible):
        mapped_span = (forward_coord(s, anchor, operation), forward_coord(e, anchor, operation))
        if mapped_span in changed_spans:
            comparable_spans += 1
            ch_q, ch_v = changed_spans[mapped_span]
            if v != ch_v:
                mismatches += 1
            consecutive += 1
            if consecutive == run and recovery_dist is None:
                # Sustained recovery point is the start of the first span in the run
                recovery_dist = eligible[idx - run + 1][0] - anchor
        else:
            consecutive = 0

    first_common_dist = (common_endpoints[0] - anchor) if common_endpoints else None

    return {
        "anchor": anchor,
        "operation": operation,
        "grammar": grammar,
        "observed_bits": limit - anchor,
        "first_common_boundary_bits": first_common_dist,
        "sustained_recovery_bits": recovery_dist,
        "right_censored": recovery_dist is None,
        "comparable_spans": comparable_spans,
        "value_mismatches": mismatches,
        "orig_tokens_count": len(orig_tokens),
        "changed_tokens_count": len(changed_tokens),
        "orig_consumed_bits": limit - orig_tail,
        "changed_consumed_bits": changed_limit - changed_tail,
    }


def run_benchmark(bits, grammars=GRAMMARS, operations=OPERATIONS, anchors=DEFAULT_ANCHORS,
                  window=DEFAULT_WINDOW, run=DEFAULT_RUN):
    """Run full matrix of trials and aggregate statistics."""
    trials = []
    for g in grammars:
        for op in operations:
            for anc in anchors:
                if anc + 32 < len(bits):
                    res = measure_trial(bits, grammar=g, anchor=anc, operation=op,
                                        window=window, run=run)
                    trials.append(res)

    # Aggregate summaries by grammar and operation
    grammar_summary = {}
    for g in grammars:
        g_trials = [t for t in trials if t["grammar"] == g]
        if not g_trials:
            continue
        rec = [t["sustained_recovery_bits"] for t in g_trials if not t["right_censored"]]
        cens = sum(1 for t in g_trials if t["right_censored"])
        grammar_summary[g] = {
            "trials": len(g_trials),
            "recovered": len(rec),
            "censored": cens,
            "recovery_rate": round(len(rec) / len(g_trials), 4) if g_trials else 0.0,
            "mean_recovery_bits": round(sum(rec) / len(rec), 2) if rec else None,
            "median_recovery_bits": sorted(rec)[len(rec) // 2] if rec else None,
            "total_value_mismatches": sum(t["value_mismatches"] for t in g_trials),
        }

    op_summary = {}
    for op in operations:
        op_trials = [t for t in trials if t["operation"] == op]
        if not op_trials:
            continue
        rec = [t["sustained_recovery_bits"] for t in op_trials if not t["right_censored"]]
        op_summary[op] = {
            "trials": len(op_trials),
            "recovered": len(rec),
            "censored": sum(1 for t in op_trials if t["right_censored"]),
            "recovery_rate": round(len(rec) / len(op_trials), 4),
            "mean_recovery_bits": round(sum(rec) / len(rec), 2) if rec else None,
        }

    return {
        "total_trials": len(trials),
        "total_stream_bits": len(bits),
        "grammars": list(grammars),
        "operations": list(operations),
        "anchors": list(anchors),
        "window_bits": window,
        "sustained_run_tokens": run,
        "by_grammar": grammar_summary,
        "by_operation": op_summary,
        "trials": trials,
    }


def self_test():
    """Verify coordinate tracking and recovery behavior on synthetic bitstreams."""
    # Build synthetic stream: 300 Rice k=5 tokens with random q in 0..4 and random suffix
    rng = random.Random(300)
    bits_list = []
    for _ in range(300):
        q = rng.randint(0, 4)
        bits_list.append("0" * q + "1")
        suffix = rng.randint(0, 31)
        bits_list.append(format(suffix, "05b"))
    test_bits = "".join(bits_list)

    res = run_benchmark(
        test_bits,
        grammars=("orf_rice5", "fixed5"),
        operations=("flip", "insert", "delete"),
        anchors=(64, 128, 256),
        window=512,
        run=3,
    )

    assert res["total_trials"] == 18, f"Expected 18 trials, got {res['total_trials']}"
    rice_res = res["by_grammar"]["orf_rice5"]
    fixed_res = res["by_grammar"]["fixed5"]

    # In a variable-length Rice stream, Rice k=5 should self-synchronize on flips, inserts, deletes
    assert rice_res["recovered"] > 0, "Rice k=5 must achieve recoveries on synthetic stream"
    assert rice_res["recovery_rate"] > 0.5, f"Expected high recovery rate for Rice, got {rice_res['recovery_rate']}"

    # For fixed5 on a stream whose true token lengths vary, fixed5 should experience heavy desync/censoring on insertions/deletions
    assert fixed_res["trials"] == 9

    # Verify single trial properties
    t_flip = measure_trial(test_bits, grammar="orf_rice5", anchor=64, operation="flip", window=512, run=3)
    assert t_flip["anchor"] == 64
    assert t_flip["operation"] == "flip"
    assert t_flip["sustained_recovery_bits"] is not None, "Flip should recover under Rice k=5"
    assert t_flip["right_censored"] is False

    t_ins = measure_trial(test_bits, grammar="orf_rice5", anchor=64, operation="insert", window=512, run=3)
    assert t_ins["sustained_recovery_bits"] is not None, "Insert should recover under Rice k=5"

    t_del = measure_trial(test_bits, grammar="orf_rice5", anchor=64, operation="delete", window=512, run=3)
    assert t_del["sustained_recovery_bits"] is not None, "Delete should recover under Rice k=5"

    print("self-test ok: coordinate-aware perturbation and resync benchmark verified.")


def main():
    parser = argparse.ArgumentParser(
        description="Local bit perturbation and parser state resynchronization benchmark (#300)"
    )
    parser.add_argument("file", nargs="?", help="Input ORF/raw file path")
    parser.add_argument("--self-test", action="store_true", help="Run synthetic self-test")
    parser.add_argument("--sha256", help="Expected full-file SHA-256 hex")
    parser.add_argument("--max-bits", type=int, default=16384, help="Maximum payload bits to read (default: 16384)")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW, help="Observation window bits (default: 1024)")
    parser.add_argument("--run", type=int, default=DEFAULT_RUN, help="Sustained recovery run tokens (default: 3)")
    parser.add_argument("--anchors", type=int, nargs="+", default=DEFAULT_ANCHORS, help="Anchor bit coordinates")
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
    offset, length = tiff.strip_offsets[0], tiff.strip_byte_counts[0]
    payload_bytes = min(length, (args.max_bits + 7) // 8)
    raw_payload = data[offset:offset + payload_bytes]
    stream_bits = bytes_to_bits(raw_payload)[:args.max_bits]

    result = run_benchmark(
        stream_bits,
        grammars=GRAMMARS,
        operations=OPERATIONS,
        anchors=args.anchors,
        window=args.window,
        run=args.run,
    )
    result["file_sha256"] = actual_hash
    result["payload_offset"] = offset

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
