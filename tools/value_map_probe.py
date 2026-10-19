#!/usr/bin/env python3
"""Aggregate suffix bridge energies under the frozen lead #32 experiment.

Python 3.8+, standard library only. This is a candidate-token measurement,
not a decoder. Check each raw.pixls.us file's CC0 licence separately with
pixls_samples.py check before use. No token values, paths or images are output.

Example (repeat --sample for other files in the same phase):
  python tools/value_map_probe.py --phase discovery --measured-by HANDLE \
      --sample 1993 PUBLIC_SAMPLE_NAME /local/file.ORF > aggregates.json

Fixed settings: 128-token blocks at index zero, MSB-first original parser,
escape_extra=0, omit complete blocks containing q>=17, all three mappings,
lane counts 1 and 2 with absolute token parity. The last partial block is
discarded. Quantiles and pooling use exact rational arithmetic; "approx"
fields are conveniences only. A null ratio means zero null energy.
"""

import argparse
import hashlib
import json
import os
import re
import struct
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # sibling tools, also under python -I
import orf_signature
import orf_tokens


MAX_TOKENS = 262144
BLOCK_SIZE = 128
ESCAPE_Q = 17
PHASE_IDS = {"discovery": (1993, 6343, 5283), "validation": (1998, 6347, 7262)}
MAPPINGS = ("signed_digit", "signed_low3", "unsigned_suffix")
LIMITATIONS = [
    "This cannot reproduce historical figures lacking named files and an exact method.",
    "Payload location and token parsing are hypotheses, including after escapes.",
    "Omitting escape blocks can bias distributions and does not repair earlier misalignment.",
    "These are token blocks and token parity, not established physical rows or channels.",
    "Suffix-only mappings, fixed prefix and block size limit interpretation.",
    "Detrending removes mean drift; low ratios do not prove bounded undetrended reconstruction.",
    "Ratios and the rough 0.5 effect target are descriptive, not p-values or decoder claims.",
]


# Drafted by Qwen under the frozen pure-helper contract; independently reviewed
# before execution and incorporated unchanged. Tests use a distinct Fraction oracle.
def bridge_energy_terms(xs):
    if type(xs) not in (list, tuple):
        raise TypeError
    if len(xs) == 0:
        raise ValueError
    n = len(xs)
    for x in xs:
        if type(x) is not int:
            raise TypeError
    T = 0
    Q = 0
    for x in xs:
        T += x
        Q += x * x
    V = n * Q - T * T
    S_k = 0
    A = 0
    for k in range(1, n + 1):
        S_k += xs[k - 1]
        term = n * S_k - k * T
        A += term * term
    return (n, A, V)


class ProbeError(ValueError):
    """A safe diagnostic containing no local path or sample content."""


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default errors can echo a private path supplied as a value.
        self.print_usage(sys.stderr)
        self.exit(2, "invalid command line; use --help for accepted options\n")


def rational(value):
    """Serialize an exact rational alongside its approximate display value."""
    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator,
            "approx": float(value)}


def map_suffix(s, mapping):
    if mapping == "signed_digit":
        return 4 * (s >> 3) + (s & 3) - 8 * ((s >> 2) & 1)
    if mapping == "signed_low3":
        return (s & 7) - 8 if (s & 4) else (s & 7)
    if mapping == "unsigned_suffix":
        return s
    raise ValueError("unknown mapping")


def energies(n, a, v):
    return Fraction(a, n ** 3), Fraction((n + 1) * v, 6 * n ** 2)


def ratio(n, a, v):
    return Fraction(6 * a, n * (n + 1) * v) if v else None


def pooled(n, terms):
    """Each (A,V) is one lane; every lane in this cell has the same n."""
    count = len(terms)
    a = sum(t[0] for t in terms)
    v = sum(t[1] for t in terms)
    e, null = energies(n, a, v)
    return {"lane_count": count, "zero_variance_lanes": sum(t[1] == 0 for t in terms),
            "sum_A": a, "sum_V": v, "sum_E": rational(e), "sum_N": rational(null),
            "mean_E": rational(e / count) if count else None,
            "mean_N": rational(null / count) if count else None,
            "R_pool": rational(ratio(n, a, v))}


def ratio_summary(values):
    """Nearest rank quantiles and thresholds are evaluated before formatting."""
    values = sorted(values)
    count = len(values)
    below = sum(x <= Fraction(1, 2) for x in values)
    distribution = None
    if count:
        def rank(num, den):
            return rational(values[(num * count + den - 1) // den - 1])
        distribution = {"min": rational(values[0]), "Q25": rank(1, 4),
                        "median": rank(1, 2), "Q75": rank(3, 4),
                        "max": rational(values[-1])}
    return {"defined_blocks": count, "distribution": distribution,
            "at_most_half_count": below, "fraction_denominator": count,
            "at_most_half_fraction": rational(Fraction(below, count)) if count else None}


def token_aggregates(qs, ss):
    """Block selection keeps original indices; never join across an omission."""
    if len(qs) != len(ss) or len(qs) > MAX_TOKENS:
        raise ProbeError("invalid token array lengths")
    if any(type(q) is not int or q < 0 for q in qs):
        raise ProbeError("invalid unary counts")
    if any(type(s) is not int or not 0 <= s < 32 for s in ss):
        raise ProbeError("invalid suffix range")
    complete = len(qs) // BLOCK_SIZE
    end = complete * BLOCK_SIZE
    retained = [i for i in range(complete)
                if not any(q >= ESCAPE_Q for q in qs[i * BLOCK_SIZE:(i + 1) * BLOCK_SIZE])]
    omitted = complete - len(retained)
    accounting = {"parsed_tokens": len(qs), "complete_blocks": complete,
                  "retained_blocks": len(retained), "escape_omitted_blocks": omitted,
                  "parsed_escapes": sum(q >= ESCAPE_Q for q in qs),
                  "escapes_in_incomplete_tail": sum(q >= ESCAPE_Q for q in qs[end:]),
                  "incomplete_tail_tokens": len(qs) - end,
                  "escape_omitted_tokens": omitted * BLOCK_SIZE,
                  "total_omitted_tokens": omitted * BLOCK_SIZE + len(qs) - end}
    cells = []
    for mapping in MAPPINGS:
        for lane_count in (1, 2):
            n = BLOCK_SIZE // lane_count
            blocks, all_terms, values = [], [], []
            parity_terms = [[], []]
            for block_index in retained:
                start = block_index * BLOCK_SIZE
                stop = start + BLOCK_SIZE
                lanes = []
                block_terms = []
                for lane in range(lane_count):
                    # Select by absolute index, independently of earlier omissions.
                    indices = (j for j in range(start, stop)
                               if lane_count == 1 or j % 2 == lane)
                    xs = [map_suffix(ss[j], mapping) for j in indices]
                    actual_n, a, v = bridge_energy_terms(xs)
                    if actual_n != n:
                        raise ProbeError("unexpected lane length")
                    lanes.append({"absolute_parity": lane if lane_count == 2 else None,
                                  "A": a, "V": v})
                    block_terms.append((a, v))
                    if lane_count == 2:
                        parity_terms[lane].append((a, v))
                a = sum(t[0] for t in block_terms)
                v = sum(t[1] for t in block_terms)
                e, null = energies(n, a, v)
                r = ratio(n, a, v)
                if r is not None:
                    values.append(r)
                blocks.append({"block_index": block_index, "sum_A": a, "sum_V": v,
                               "sum_E": rational(e), "sum_N": rational(null),
                               "R": rational(r), "lanes": lanes})
                all_terms.extend(block_terms)
            cells.append({"mapping": mapping, "lane_count": lane_count,
                          "increments_per_lane": n, "blocks": blocks,
                          "zero_variance_blocks": sum(b["sum_V"] == 0 for b in blocks),
                          "pool": pooled(n, all_terms), "block_ratios": ratio_summary(values),
                          "parity_pools": [dict(absolute_parity=p, **pooled(n, parity_terms[p]))
                                           for p in (0, 1)] if lane_count == 2 else []})
    return {"omissions": accounting, "cells": cells}


def guarded_parse(payload, max_tokens):
    """Use the original parser, rejecting any lookahead into its padding."""
    if type(max_tokens) is not int or not 1 <= max_tokens <= MAX_TOKENS:
        raise ProbeError("max_tokens must be between 1 and 262144")
    qs, ss, marks, consumed = orf_tokens.parse(payload, max_tokens, 0, 0)
    if consumed < 0 or consumed > len(payload) * 8:
        raise ProbeError("candidate parser consumed beyond payload; no results emitted")
    if len(qs) != len(ss) or len(qs) > max_tokens:
        raise ProbeError("candidate parser returned invalid token counts")
    return qs, ss, consumed


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def measure(sample_id, public_name, path, max_tokens):
    sig = orf_signature.signature(path)
    offset, size = sig["payload_offset"], sig["payload_bytes"]
    if (type(offset) is not int or offset < 0 or type(size) is not int or size <= 0
            or offset + size > os.path.getsize(path)):
        raise ProbeError("payload locator returned invalid or truncated bounds")
    w, h, payload = orf_tokens.locate(path)
    if len(payload) != size or (w, h) != (sig["payload_w"], sig["payload_h"]):
        raise ProbeError("payload locator disagrees with signature")
    if file_hash(path) != sig["sha256"]:
        raise ProbeError("sample changed while being read")
    # Replace the local basename with the explicitly supplied public sample name.
    sig["file"] = public_name
    qs, ss, consumed = guarded_parse(payload, max_tokens)
    result = token_aggregates(qs, ss)
    return {"raw_pixls_us_id": sample_id, "raw_pixls_us_name": public_name,
            "sha256": sig["sha256"], "measured_signature": sig,
            "requested_tokens": max_tokens, "returned_tokens": len(qs),
            "payload_bytes": len(payload), "consumed_bits": consumed,
            "token_limit_reached": len(qs) == max_tokens, **result}


def provenance():
    return {"tool_version": "lead32-bridge-energy-v1", "python_version": sys.version.split()[0],
            "parser_version": "original candidate lead #11; identified by SHA-256",
            "source_sha256": {"value_map_probe.py": file_hash(__file__),
                              "orf_tokens.py": file_hash(orf_tokens.__file__),
                              "orf_signature.py": file_hash(orf_signature.__file__)}}


def main(argv=None):
    ap = PrivateArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true", help="run only deterministic synthetic machinery checks")
    ap.add_argument("--phase", choices=tuple(PHASE_IDS))
    ap.add_argument("--measured-by", help="the human measurer's GitHub handle (no @ needed)")
    ap.add_argument("--sample", action="append", nargs=3, metavar=("ID", "PUBLIC_NAME", "FILE"),
                    help="repeat for selected CC0 files; IDs must belong to the declared phase")
    ap.add_argument("--max-tokens", type=int, default=MAX_TOKENS,
                    help="bounded prefix size, 1..262144 (default: 262144)")
    args = ap.parse_args(argv)
    if args.self_test:
        if args.sample or args.phase or args.measured_by or args.max_tokens != MAX_TOKENS:
            ap.error("--self-test cannot be combined with measurement options")
        import unittest
        import test_value_map_probe
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_value_map_probe)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if not args.phase or not args.measured_by or not args.sample:
        ap.error("measurement requires --phase, --measured-by and at least one --sample")
    if not 1 <= args.max_tokens <= MAX_TOKENS:
        ap.error("--max-tokens must be between 1 and 262144")
    handle = args.measured_by.lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", handle):
        ap.error("invalid GitHub handle")
    selected = []
    for raw_id, public_name, path in args.sample:
        if not raw_id.isascii() or not raw_id.isdigit() or int(raw_id) not in PHASE_IDS[args.phase]:
            ap.error("sample ID is outside the declared phase")
        if not public_name or not public_name.isprintable() or any(c in public_name for c in "/\\"):
            ap.error("sample public name must be a name, without local path or control separators")
        sample_id = int(raw_id)
        if any(s[0] == sample_id for s in selected):
            ap.error("duplicate sample ID")
        selected.append((sample_id, public_name, path))
    selected.sort(key=lambda s: PHASE_IDS[args.phase].index(s[0]))
    try:
        samples = [measure(sid, name, path, args.max_tokens) for sid, name, path in selected]
        result = {"schema": "orf-lead32-bridge-energy-v1", "design_date": "2026-10-19",
                  "builds_on": [32, 11], "phase": args.phase, "measured_by": handle,
                  "phase_declared_ids": list(PHASE_IDS[args.phase]),
                  "settings": {"max_tokens": args.max_tokens, "block_tokens": BLOCK_SIZE,
                               "block_start_index": 0, "escape_q_min": ESCAPE_Q,
                               "escape_extra": 0, "bit_order": "MSB-first",
                               "mappings": list(MAPPINGS), "lane_counts": [1, 2],
                               "lane_selection": "absolute token index modulo lane count",
                               "quantiles": "nearest rank ceil(p*m), one-based",
                               "pooling": "sum(E)/sum(N)", "threshold": rational(Fraction(1, 2))},
                  "provenance": provenance(), "limitations": LIMITATIONS, "samples": samples}
        # Collect everything first: any failed sample means no partial JSON output.
        print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    except ProbeError as exc:
        print("measurement failed: " + str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, IndexError, struct.error, OverflowError):
        # Exception messages from file APIs can contain private local paths.
        print("measurement failed: input, locator, signature or parser error; no results emitted", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
