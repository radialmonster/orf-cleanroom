#!/usr/bin/env python3
"""Lead #338: suffix equality on a dy*W + dx lag lattice, against a fixed shuffled baseline.

Original clean-room analysis; stdlib Python 3.8+. Candidate k=5 tokens (lead #11: q zero bits, a 1
stop bit, a 5-bit suffix), parsed from payload bit 0 with orf_tokens.scan; a final token whose bits
do not all fit in the payload is dropped. The payload comes from orf_tokens.locate_data.
Tokens with q >= 17 never match. W is the payload width from the TIFF tags; token index i is
treated as row i // W, column i % W. That is a coordinate choice, not an established pixel map.

Per file (aggregate JSON; no paths, pixels or images):
  whole payload   tokens, consumed bits, residual bits, tokens minus W*H
  grid            for dy in 0..3 and dx in -4..4 (lag = dy*W + dx > 0), over the first --tokens
                  tokens with i >= 4*W: pairs P (both tokens ordinary), matches M and M/P,
                  for the real stream and for one fixed shuffle (seed --seed) that permutes
                  ordinary suffixes within consecutive W-token blocks, escape positions fixed
  large_q         whole payload: count of tokens with q >= --large-q, and the first 64 as
                  [index, q]
  site_tables     for each --window ROW0:ROW1, tokens grouped by (row % 2, col % 2) after
                  shifting indices by --offset; per cell the total and the three most common
                  (q, suffix) pairs with counts
The CFA phase is not known: the site tables only show whether a 2x2 pattern exists.
Container geometry, payload and input hash use the same file snapshot.

    python -I -B tools/bayer_grid_probe.py FILE [FILE ...]
    python -I -B tools/test_bayer_grid_probe.py
"""
import argparse
from array import array
from collections import Counter
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens  # noqa: E402

ESCAPE = 255
DX = tuple(range(-4, 5))
DY = (0, 1, 2, 3)


def parse(payload):
    """Whole-payload bounded k=5 parse -> (q array, suffix array with ESCAPE for q >= 17, bits used)."""
    qs, ss = array("H"), array("B")
    _, used = orf_tokens.scan(payload, 1 << 62, 0, 0, None, qs, ss, 65535)
    if used > len(payload) * 8:  # the shared scanner can read a last suffix past the payload end
        used -= qs.pop() + 6
        ss.pop()
    for i, q in enumerate(qs):
        if q >= orf_tokens.ESC_Q:
            ss[i] = ESCAPE
    return qs, ss, used


def match_counts(ss, start, lag):
    pairs = matches = 0
    for a, b in zip(ss[start:], ss[start - lag:]):
        if a != ESCAPE and b != ESCAPE:
            pairs += 1
            if a == b:
                matches += 1
    return pairs, matches


def shuffled(ss, width, seed):
    """Permute ordinary suffixes within consecutive width-token blocks; escapes stay in place."""
    rng = random.Random(seed)
    out = array("B", ss)
    for start in range(0, len(out), width):
        slots = [i for i in range(start, min(start + width, len(out))) if out[i] != ESCAPE]
        values = [out[i] for i in slots]
        rng.shuffle(values)
        for i, v in zip(slots, values):
            out[i] = v
    return out


def grid(ss, width, limit):
    ss = ss[:limit]
    start = 4 * width
    rows = []
    for dy in DY:
        for dx in DX:
            lag = dy * width + dx
            if lag <= 0:
                continue
            if start - lag < 0 or start >= len(ss):
                rows.append({"dy": dy, "dx": dx, "lag": lag, "P": 0, "M": 0, "rate": None})
                continue
            p, m = match_counts(ss, start, lag)
            rows.append({"dy": dy, "dx": dx, "lag": lag, "P": p, "M": m,
                         "rate": round(m / p, 6) if p else None})
    return rows


def site_tables(qs, ss, width, windows, offset):
    out = []
    for r0, r1 in windows:
        cells = {}
        for key in ((0, 0), (0, 1), (1, 0), (1, 1)):
            cells[key] = Counter()
        complete = True
        for row in range(r0, r1):
            base = row * width + offset
            if base < 0 or base + width > len(qs):
                complete = False
                break
            for col in range(width):
                i = base + col
                cells[(row & 1, col & 1)][(qs[i], ss[i])] += 1
        table = {}
        for (rp, cp), counter in sorted(cells.items()):
            table["%d%d" % (rp, cp)] = {
                "total": sum(counter.values()),
                "top": [[q, (None if s == ESCAPE else s), n] for (q, s), n in counter.most_common(3)]}
        out.append({"rows": [r0, r1], "complete": complete, "cells": table})
    return out


def analyze(payload, width, height, limit, seed, windows, offset, large_q):
    qs, ss, used = parse(payload)
    big = [[i, q] for i, q in enumerate(qs) if q >= large_q]
    return {
        "whole_payload": {"payload_bits": len(payload) * 8, "tokens": len(qs), "consumed_bits": used,
                          "residual_bits": len(payload) * 8 - used,
                          "tokens_minus_sites": len(qs) - width * height,
                          "escapes_q_ge_17": sum(1 for s in ss if s == ESCAPE)},
        "grid_tokens": min(limit, len(qs)),
        "grid_real": grid(ss, width, limit),
        "grid_shuffled": grid(shuffled(ss[:limit], width, seed), width, limit),
        "large_q": {"threshold": large_q, "count": len(big), "first": big[:64]},
        "site_tables": site_tables(qs, ss, width, windows, offset)}


def window(text):
    try:
        a, b = text.split(":")
        a, b = int(a), int(b)
    except ValueError:
        raise argparse.ArgumentTypeError("use ROW0:ROW1")
    if a < 0 or b <= a:
        raise argparse.ArgumentTypeError("need 0 <= ROW0 < ROW1")
    return a, b


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--tokens", type=int, default=4000000, help="grid prefix in tokens (default 4000000)")
    ap.add_argument("--seed", type=int, default=20261023, help="shuffle seed (default 20261023)")
    ap.add_argument("--window", type=window, action="append",
                    help="site-table rows ROW0:ROW1 (repeatable; default 2:202 and 565:765)")
    ap.add_argument("--offset", type=int, default=0, help="token index shift for site tables (default 0)")
    ap.add_argument("--large-q", type=int, default=6, help="large-q threshold (default 6)")
    a = ap.parse_args()
    if a.tokens <= 0:
        ap.error("--tokens must be positive")
    windows = a.window or [(2, 202), (565, 765)]
    results, failures = [], []
    for n, path in enumerate(a.files):
        try:
            with open(path, "rb") as f:
                data = f.read()
            w, h, payload = orf_tokens.locate_data(data)
            input_digest = hashlib.sha256(data).hexdigest()
            del data
            if w <= 0 or h <= 0 or not payload:
                raise ValueError("no payload")
            r = analyze(payload, w, h, a.tokens, a.seed, windows, a.offset, a.large_q)
            r.update({"sha256": input_digest, "W": w, "H": h,
                      "payload_bytes": len(payload)})
            results.append(r)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            failures.append({"argument": n, "error": type(exc).__name__})
    with open(os.path.abspath(__file__), "rb") as f:
        source = hashlib.sha256(f.read()).hexdigest()
    print(json.dumps({"tool_sha256": source, "python": sys.version.split()[0], "tokens": a.tokens,
                      "seed": a.seed, "windows": windows, "offset": a.offset, "results": results,
                      "failures": failures}, indent=1))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
