#!/usr/bin/env python3
"""Measure local H/L lag tables in four declared token windows (lead #11).

Original measurement convention, not a decoder or historical reproduction.
Parse from payload bit zero: q zeros, one stop bit, five suffix bits; q>=17
has no extra skip. Four 262144-token windows count escapes in their absolute
indices. Their start-to-start stride defaults to 262144 (consecutive windows);
--window-stride can declare separated windows, and must be at least 262144.
For lags 1..3 omit pairs with either endpoint q>=17,
without compacting indices; intervening escapes remain. Pairs never cross
windows. H=suffix>>3, L=suffix&7. Report all four ordered H/L pair tables,
unsmoothed empirical plug-in MI (bits) and exact omission counts.

Strict alternating ordering: at lags1/3 every cross-field MI exceeds every
same-field MI, and at lag2 every same-field MI exceeds every cross-field MI.
Undefined MI gives null ordering. This descriptive criterion is not a null
comparison, significance test, stationarity test, physical row/CFA inference,
or proof of initial/escape framing. Local token windows are not sensor rows.
Stdlib Python 3.8+; reads inputs and prints aggregate JSON only. Reuse retained
CC0 verification only after matching the input SHA256; no preview access.
Incomplete requested windows and input failures produce a nonzero exit;
available aggregate reports are retained.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class
from suffix_joint_probe import mutual_information, scan_prefix

WINDOW = 262144
COUNT = 4


def measure(tokens, stride=None):
    stride = WINDOW if stride is None else stride
    if stride < WINDOW:
        raise ValueError("window stride must be at least the window size")
    results = []
    for window in range(COUNT):
        start = window * stride
        selected = tokens[start:start + WINDOW]
        lag_results = []
        for lag in (1, 2, 3):
            joint = [[0] * 32 for _ in range(32)]
            candidates = max(0, len(selected) - lag)
            retained = 0
            for i in range(lag, len(selected)):
                q1, s1 = selected[i - lag]
                q2, s2 = selected[i]
                if q1 < 17 and q2 < 17:
                    joint[s1][s2] += 1
                    retained += 1
            pairs = []
            for source, nx in (("H", 4), ("L", 8)):
                for target, ny in (("H", 4), ("L", 8)):
                    table = [[0] * ny for _ in range(nx)]
                    for a in range(32):
                        for b in range(32):
                            x = a >> 3 if source == "H" else a & 7
                            y = b >> 3 if target == "H" else b & 7
                            table[x][y] += joint[a][b]
                    pairs.append({"source": source, "target": target,
                                  "joint_source_rows_target_columns": table,
                                  "plugin_mi_bits": mutual_information(table)})
            same = [p["plugin_mi_bits"] for p in pairs if p["source"] == p["target"]]
            cross = [p["plugin_mi_bits"] for p in pairs if p["source"] != p["target"]]
            ordering = None
            if retained:
                higher, lower = (same, cross) if lag == 2 else (cross, same)
                ordering = min(higher) > max(lower)
            lag_results.append({"lag_tokens": lag, "candidate_pairs": candidates,
                                "retained_pairs": retained, "omitted_endpoint_pairs": candidates - retained,
                                "strict_alternating_order": ordering, "pairings": pairs})
        flags = [r["strict_alternating_order"] for r in lag_results]
        results.append({"start_token": start, "requested_tokens": WINDOW,
                        "returned_tokens": len(selected), "shortfall_tokens": WINDOW - len(selected),
                        "escape_tokens": sum(q >= 17 for q, _ in selected),
                        "all_lags_strict_alternating_order": all(flags) if None not in flags else None,
                        "lags": lag_results})
    return results


def report(sample_id, name, path, stride=None):
    stride = WINDOW if stride is None else stride
    if stride < WINDOW:
        raise ValueError("window stride must be at least the window size")
    with open(path, "rb") as handle:
        data = handle.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError("one contiguous strip required")
    off, count = offsets[0], lengths[0]
    w, h = best[0x100][0], best[0x101][0]
    if off < 0 or count <= 0 or off + count > len(data):
        raise ValueError("payload out of bounds")
    if w <= 0 or h <= 0 or size_class(count, w, h) != "variable" or best.get(0x103) != [1]:
        raise ValueError("positive variable-size payload with compression tag 1 required")
    requested = (COUNT - 1) * stride + WINDOW
    tokens, end = scan_prefix(data[off:off + count], requested)
    return {"pixls_id": sample_id, "pixls_name": name, "sha256": hashlib.sha256(data).hexdigest(),
            "variant": "unassigned", "payload_w": w, "payload_h": h,
            "payload_offset": off, "payload_bytes": count, "compression_tag": 1,
            "size_class": "variable", "requested_scan_tokens": requested,
            "returned_tokens": len(tokens), "bits_consumed": end,
            "window_stride_tokens": stride, "windows": measure(tokens, stride)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", required=True, metavar=("ID", "PUBLIC_NAME", "FILE"))
    parser.add_argument("--window-stride", type=int, default=WINDOW,
                        help="start-to-start token stride, at least %(default)s; default consecutive")
    args = parser.parse_args()
    if args.window_stride < WINDOW:
        parser.error("window stride must be at least %d" % WINDOW)
    ids = [s[0] for s in args.sample]
    if any(not i.isascii() or not i.isdecimal() or int(i) <= 0 for i in ids) or len({int(i) for i in ids}) != len(ids):
        parser.error("sample IDs must be distinct positive ASCII decimals")
    reports, failures = [], []
    for sample_id, name, path in args.sample:
        try:
            reports.append(report(sample_id, name, path, args.window_stride))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sample_id, "error": type(exc).__name__})
    sources = {}
    for filename in ("suffix_window_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": sources, "python_version": sys.version.split()[0],
                      "window_tokens": WINDOW, "window_count": COUNT,
                      "window_stride_tokens": args.window_stride, "escape_extra_bits": 0,
                      "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    return 1 if failures or any(w['shortfall_tokens'] for r in reports for w in r['windows']) else 0


if __name__ == "__main__":
    sys.exit(main())
