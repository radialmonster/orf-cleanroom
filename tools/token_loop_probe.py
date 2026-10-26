#!/usr/bin/env python3
"""Measure loop-growth negatives for lead #31.

Part of lead #31, scoped to its double-integration and Lorenzo negative. The
lead gives no public file list or method, so its private growth figures cannot
be reproduced. This tool tests the qualitative negative on public CC0 files
with a fixed measure declared before the run.

Parser: the candidate lead #11 token model (q zero bits, one stop bit, five
suffix bits; q >= 17 is an escape parsed like any other token, no extra skip).
The first rows x payload-width candidate tokens are used. A row is a nominal
block of exactly W tokens; this is not a claim about physical image rows.

Fixed suffix-to-residual mappings:
  u            32*q + s
  signed_digit 4*(s>>3) + (s&3) - 8*((s>>2)&1)
  signed_low3  (s&7)-8 if (s&4) else (s&7)

Fixed loops, zero initial state:
  P1  x[i] = 2*x[i-1] - x[i-2] + e[i]                  (per nominal row)
  P2  x[i] = 2*x[i-2] - x[i-4] + e[i]                  (per parity and row)
  L1  x[i] = x[i-1] + x[i-W] - x[i-W-1] + e[i]         (full sequence)
  L2  x[i] = x[i-2] + x[i-2W] - x[i-2W-2] + e[i]       (stride-2, full)
  R1  x[i] = x[i-1] + e[i]                             (per nominal row)
  R2  x[i] = x[i-2] + e[i]                             (per parity and row)
  LK05/LK09  x[i] = a*x[i-1] + e[i], a = 0.5 / 0.9     (per nominal row)

Growth is the peak-to-peak range (max-min) of the reconstructed sequence. The
initial zero state is excluded from this range. Even for nonnegative values,
the range need not be invariant under a within-row permutation (although the
final row sum is invariant).
The null shuffles the mapped values within each nominal row with a fixed seed and
repeats the same loops. Reports contain aggregate ranges only: no token or
pixel values, no images, no paths.

The double/Lorenzo cells report whether the real/null ratio is at least 1.5.
The running-sum cells report whether it is within the predeclared 0.5..1.5
"equal to null" band. Both readings are descriptive comparisons with the
same-token within-row null, not significance tests.

The tool reads files, prints JSON to stdout and writes nothing. Standard
library only, Python 3.8+.

Usage:
  python -I -B tools/token_loop_probe.py --self-test
  python -I -B tools/token_loop_probe.py --sample ID PUBLIC_NAME FILE [--sample ...]
      [--rows 300] [--perms 4]
"""
import argparse
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_signature  # noqa: E402
import orf_tokens  # noqa: E402

MAPPINGS = ("u", "signed_digit", "signed_low3")
DOUBLE_LORENZO = ("P1", "P2", "L1", "L2")
RUNNING_SUM = ("R1", "R2")
LEAKY = ("LK05", "LK09")
LOOPS = DOUBLE_LORENZO + RUNNING_SUM + LEAKY
MAX_ROWS = 2000
DEFAULT_ROWS = 300
DEFAULT_PERMS = 4
SEED_BASE = 20261021
ESC_Q = 17


class ProbeError(ValueError):
    """A safe diagnostic that does not contain a local path or sample bytes."""


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse can echo a private path supplied as an option value.
        self.print_usage(sys.stderr)
        self.exit(2, "invalid command line; use --help for accepted options\n")


def map_value(q, s, mapping):
    if mapping == "u":
        return 32 * q + s
    if mapping == "signed_digit":
        return 4 * (s >> 3) + (s & 3) - 8 * ((s >> 2) & 1)
    if mapping == "signed_low3":
        return (s & 7) - 8 if (s & 4) else (s & 7)
    raise ProbeError("unknown mapping")


def mapped_values(qs, ss, mapping):
    if len(qs) != len(ss):
        raise ProbeError("token arrays disagree")
    return [map_value(q, s, mapping) for q, s in zip(qs, ss)]


def range_p1(values, w, rows):
    """Per-row second-order integration, reset at every nominal row."""
    lo = hi = None
    v = values
    for r in range(rows):
        base = r * w
        p2 = p1 = 0
        for j in range(w):
            x = 2 * p1 - p2 + v[base + j]
            if lo is None or x < lo:
                lo = x
            if hi is None or x > hi:
                hi = x
            p2, p1 = p1, x
    return hi - lo


def range_p2(values, w, rows):
    """Per-row, per-absolute-parity second-order integration."""
    lo = hi = None
    v = values
    for r in range(rows):
        base = r * w
        for parity in (0, 1):
            p4 = p2 = 0
            for j in range(parity, w, 2):
                x = 2 * p2 - p4 + v[base + j]
                if lo is None or x < lo:
                    lo = x
                if hi is None or x > hi:
                    hi = x
                p4, p2 = p2, x
    return hi - lo


def range_l1(values, w, rows):
    """Full-sequence 2D Lorenzo recurrence with stride 1."""
    n = w * rows
    x = [0] * n
    lo = hi = None
    for i in range(n):
        a = x[i - 1] if i >= 1 else 0
        b = x[i - w] if i >= w else 0
        c = x[i - w - 1] if i >= w + 1 else 0
        val = a + b - c + values[i]
        x[i] = val
        if lo is None or val < lo:
            lo = val
        if hi is None or val > hi:
            hi = val
    return hi - lo


def range_l2(values, w, rows):
    """Full-sequence 2D Lorenzo recurrence with stride 2."""
    n = w * rows
    x = [0] * n
    lo = hi = None
    for i in range(n):
        a = x[i - 2] if i >= 2 else 0
        b = x[i - 2 * w] if i >= 2 * w else 0
        c = x[i - 2 * w - 2] if i >= 2 * w + 2 else 0
        val = a + b - c + values[i]
        x[i] = val
        if lo is None or val < lo:
            lo = val
        if hi is None or val > hi:
            hi = val
    return hi - lo


def range_r1(values, w, rows):
    """Plain running sum per nominal row, reset at every row."""
    lo = hi = None
    v = values
    for r in range(rows):
        base = r * w
        x = 0
        for j in range(w):
            x += v[base + j]
            if lo is None or x < lo:
                lo = x
            if hi is None or x > hi:
                hi = x
    return hi - lo


def range_r2(values, w, rows):
    """Plain running sum per nominal row and absolute token parity."""
    lo = hi = None
    v = values
    for r in range(rows):
        base = r * w
        for parity in (0, 1):
            x = 0
            for j in range(parity, w, 2):
                x += v[base + j]
                if lo is None or x < lo:
                    lo = x
                if hi is None or x > hi:
                    hi = x
    return hi - lo


def range_leaky(values, w, rows, coeff):
    """Leaky running sum per nominal row, reset at every row."""
    lo = hi = None
    v = values
    for r in range(rows):
        base = r * w
        x = 0.0
        for j in range(w):
            x = coeff * x + v[base + j]
            if lo is None or x < lo:
                lo = x
            if hi is None or x > hi:
                hi = x
    return hi - lo


def range_lk05(values, w, rows):
    return range_leaky(values, w, rows, 0.5)


def range_lk09(values, w, rows):
    return range_leaky(values, w, rows, 0.9)


RANGE_FUNCS = {
    "P1": range_p1,
    "P2": range_p2,
    "L1": range_l1,
    "L2": range_l2,
    "R1": range_r1,
    "R2": range_r2,
    "LK05": range_lk05,
    "LK09": range_lk09,
}


def all_ranges(values, w, rows):
    return {name: RANGE_FUNCS[name](values, w, rows) for name in LOOPS}


def shuffled_rows(values, w, rows, rng):
    """Shuffle mapped values within each nominal row, preserving row marginals."""
    out = []
    for r in range(rows):
        row = list(values[r * w:(r + 1) * w])
        rng.shuffle(row)
        out.extend(row)
    return out


def mean(values):
    return sum(values) / float(len(values)) if values else None


def measure_sample(sample_id, public_name, path, rows, perms):
    sig = orf_signature.signature(path)
    if sig.get("size_class") != "variable":
        raise ProbeError("sample is not a compressed variable-size payload")
    if sig.get("compression_tag") != 1:
        raise ProbeError("unexpected compression tag")
    if not sig.get("payload_w") or not sig.get("payload_h"):
        raise ProbeError("invalid payload dimensions")
    if sig["payload_bytes"] <= 0 or sig["payload_offset"] == "":
        raise ProbeError("invalid payload bounds")

    w, h, payload = orf_tokens.locate(path)
    if (w, h) != (sig["payload_w"], sig["payload_h"]):
        raise ProbeError("locators disagree on dimensions")
    if len(payload) != sig["payload_bytes"]:
        raise ProbeError("locators disagree on payload length")
    if sha256_file(path) != sig["sha256"]:
        raise ProbeError("sample changed while being read")

    token_count = rows * w
    if token_count > 100000000:
        raise ProbeError("requested token prefix is too large")
    qs, ss, _marks, consumed = orf_tokens.parse(payload, token_count, 0, 0)
    if len(qs) != len(ss):
        raise ProbeError("parser returned inconsistent token arrays")
    if consumed < 0 or consumed > len(payload) * 8:
        raise ProbeError("parser consumed outside the payload")
    if any(type(q) is not int or q < 0 for q in qs):
        raise ProbeError("parser returned an invalid unary count")
    if any(type(s) is not int or not 0 <= s < 32 for s in ss):
        raise ProbeError("parser returned an invalid suffix")

    used_rows = len(qs) // w
    if used_rows < 1:
        raise ProbeError("no complete nominal row in the requested prefix")
    shortfall = token_count - len(qs)
    result = {
        "raw_pixls_us_id": sample_id,
        "raw_pixls_us_name": public_name,
        "sha256": sig["sha256"],
        "payload_w": w,
        "payload_h": h,
        "payload_bytes": len(payload),
        "bpp": sig["bpp"],
        "rows_requested": rows,
        "rows_used": used_rows,
        "tokens_requested": token_count,
        "tokens_parsed": len(qs),
        "token_shortfall": shortfall,
        "prefix_complete": shortfall == 0,
        "consumed_bits": consumed,
        "escape_tokens": sum(1 for q in qs if q >= ESC_Q),
        "mappings": {},
    }
    for mi, mapping in enumerate(MAPPINGS):
        values = mapped_values(qs, ss, mapping)
        real = all_ranges(values, w, used_rows)
        null_ranges = {name: [] for name in LOOPS}
        for perm in range(perms):
            seed = SEED_BASE + 1000 * int(sample_id) + 10 * mi + perm
            shuffled = shuffled_rows(values, w, used_rows, random.Random(seed))
            nr = all_ranges(shuffled, w, used_rows)
            for name in LOOPS:
                null_ranges[name].append(nr[name])
        cells = {}
        for name in LOOPS:
            mn = mean(null_ranges[name])
            ratio = real[name] / float(mn) if mn else None
            cells[name] = {
                "real_range": real[name],
                "null_ranges": null_ranges[name],
                "mean_null_range": mn,
                "ratio": ratio,
                "at_least_1_5": ratio is not None and ratio >= 1.5,
                "in_0_5_1_5": ratio is not None and 0.5 <= ratio <= 1.5,
            }
        result["mappings"][mapping] = cells
    return result


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def provenance():
    return {
        "tool": "token_loop_probe.py",
        "tool_sha256": sha256_file(__file__),
        "orf_tokens_sha256": sha256_file(orf_tokens.__file__),
        "orf_signature_sha256": sha256_file(orf_signature.__file__),
        "python": sys.version.split()[0],
    }


def main(argv=None):
    ap = PrivateArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--self-test", action="store_true", help="run synthetic tests only")
    ap.add_argument("--sample", action="append", nargs=3,
                    metavar=("ID", "PUBLIC_NAME", "FILE"),
                    help="repeat for each public CC0 file")
    ap.add_argument("--rows", type=int, default=DEFAULT_ROWS,
                    help="nominal W-token rows to parse (default: 300)")
    ap.add_argument("--perms", type=int, default=DEFAULT_PERMS,
                    help="within-row shuffles per cell (default: 4)")
    args = ap.parse_args(argv)

    if args.self_test:
        if args.sample or args.rows != DEFAULT_ROWS or args.perms != DEFAULT_PERMS:
            ap.error("--self-test cannot be combined with measurement options")
        import unittest
        import test_token_loop_probe
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_token_loop_probe)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1

    if not args.sample:
        ap.error("measurement requires at least one --sample")
    if not 1 <= args.rows <= MAX_ROWS:
        ap.error("--rows must be between 1 and %d" % MAX_ROWS)
    if not 1 <= args.perms <= 10:
        # seeds are SEED_BASE + 1000*id + 10*mapping + perm: perm >= 10 would reuse the
        # next mapping's seeds
        ap.error("--perms must be between 1 and 10")

    selected = []
    for raw_id, public_name, path in args.sample:
        if not raw_id.isascii() or not raw_id.isdigit() or int(raw_id) <= 0:
            ap.error("sample ID must be a positive decimal")
        if not public_name or not public_name.isprintable() or any(c in public_name for c in "/\\"):
            ap.error("public sample name must not contain a local path")
        if any(s[0] == int(raw_id) for s in selected):
            ap.error("duplicate sample ID")
        selected.append((int(raw_id), public_name, path))

    try:
        samples = [measure_sample(sid, name, path, args.rows, args.perms)
                   for sid, name, path in selected]
    except ProbeError as exc:
        print("measurement failed: " + str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError):
        print("measurement failed: input, locator, signature or parser error; no results emitted",
              file=sys.stderr)
        return 1

    result = {
        "schema": "orf-lead31-loop-probe-v1",
        "builds_on": [31, 11],
        "settings": {
            "rows": args.rows,
            "perms": args.perms,
            "seed_base": SEED_BASE,
            "escape_q_min": ESC_Q,
            "escape_extra": 0,
            "bit_order": "MSB-first",
            "mappings": list(MAPPINGS),
            "loops": list(LOOPS),
            "double_lorenzo_loops": list(DOUBLE_LORENZO),
            "running_sum_loops": list(RUNNING_SUM),
            "leaky_loops": list(LEAKY),
            "growth": "peak-to-peak range",
            "row_reset": {"P1": True, "P2": True, "L1": False, "L2": False,
                          "R1": True, "R2": True, "LK05": True, "LK09": True},
            "double_lorenzo_ratio_threshold": 1.5,
            "running_sum_band": [0.5, 1.5],
        },
        "provenance": provenance(),
        "samples": samples,
    }
    all_cells = [(s, m, name, cell) for s in samples
                 for m, cells in s["mappings"].items()
                 for name, cell in cells.items()]
    dl_cells = [(s, m, name, c) for s, m, name, c in all_cells if name in DOUBLE_LORENZO]
    rs_cells = [(s, m, name, c) for s, m, name, c in all_cells if name in RUNNING_SUM]
    lk_cells = [(s, m, name, c) for s, m, name, c in all_cells if name in LEAKY]
    result["summary"] = {
        "cells": len(all_cells),
        "double_lorenzo_cells": len(dl_cells),
        "double_lorenzo_at_least_1_5": sum(1 for _s, _m, _n, c in dl_cells if c["at_least_1_5"]),
        "double_lorenzo_all_at_least_1_5": all(c["at_least_1_5"] for _s, _m, _n, c in dl_cells),
        "running_sum_cells": len(rs_cells),
        "running_sum_in_0_5_1_5": sum(1 for _s, _m, _n, c in rs_cells if c["in_0_5_1_5"]),
        "running_sum_all_in_0_5_1_5": all(c["in_0_5_1_5"] for _s, _m, _n, c in rs_cells),
        "leaky_cells": len(lk_cells),
        "incomplete_prefixes": sum(1 for s in samples if not s["prefix_complete"]),
    }
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0 if result["summary"]["incomplete_prefixes"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
