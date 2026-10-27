#!/usr/bin/env python3
"""Measure nominal width-lag bit correlations for #29 item 8; builds on #11.

Python 3.8+, stdlib. Read-only inputs; aggregate JSON only; no preview access.
Fixed candidate parse: first 262144 complete q-zero/one/5-suffix tokens from
payload bit zero; q>=17 consumes q+6 with no extra skip. W is payload width,
NOT an established token row stride. At lags W,2W,2W-2,2W+2 report past b2
versus current b2; at 2W-1 report past b4 versus current b2. Include all
eligible indices t>=lag, even in a final partial nominal row. Omit a pair if
either endpoint has q>=17; keep original indices and report omissions.
An escape between endpoints is not excluded. This selective endpoint rule
cannot repair unknown post-escape framing. No concatenation or renumbering.

Report exact binary tables, candidate/omitted/retained pair counts, pooled and
by target ((t//W)%2,(t%W)%2). These strata describe only a nominal token grid,
not sensor/CFA parity. Pearson is null if either marginal has zero variance
(including empty tables); counts remain available. No uncertainty, shuffle,
significance test, donor/predictor interpretation or decoder is supplied.
Historical private files, precise estimator and row alignment are unknown;
this descriptive public metric does not reproduce their exact values.
Licence-check samples separately before use. Requires one contiguous,
in-bounds, positive variable-size payload; variant remains unassigned.
Incomplete requested prefixes and input failures produce a nonzero exit;
available aggregate reports are retained.
Sample IDs must be distinct positive ASCII decimals and names printable basenames.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class
from suffix_joint_probe import LIMIT, scan_prefix, correlation


def specifications(width):
    if type(width) is not int or width < 2:
        raise ValueError("width must be an integer >=2")
    return (("W", width, 2), ("2W", 2 * width, 2),
            ("2W-2", 2 * width - 2, 2), ("2W+2", 2 * width + 2, 2),
            ("2W-1", 2 * width - 1, 4))


def measure(tokens, width):
    specs = specifications(width)
    for q, suffix in tokens:
        if type(q) is not int or q < 0 or type(suffix) is not int or not 0 <= suffix < 32:
            raise ValueError("invalid candidate token")
    result = []
    for label, lag, past_bit in specs:
        tables = [[[0, 0], [0, 0]] for _ in range(4)]
        candidates, omitted = [0] * 4, [0] * 4
        for t in range(lag, len(tokens)):
            stratum = 2 * ((t // width) % 2) + (t % width) % 2
            candidates[stratum] += 1
            qa, sa = tokens[t - lag]
            qb, sb = tokens[t]
            if qa >= 17 or qb >= 17:
                omitted[stratum] += 1
                continue
            tables[stratum][(sa >> past_bit) & 1][(sb >> 2) & 1] += 1
        cells = []
        pooled = [[sum(table[a][b] for table in tables) for b in range(2)] for a in range(2)]
        for index, table in enumerate(tables + [pooled]):
            candidate = candidates[index] if index < 4 else sum(candidates)
            excluded = omitted[index] if index < 4 else sum(omitted)
            retained = sum(map(sum, table))
            cells.append({"target_nominal_parity": [index // 2, index % 2] if index < 4 else None,
                          "candidate_pairs": candidate, "escape_endpoint_omitted_pairs": excluded,
                          "retained_pairs": retained, "past_by_current_counts": table,
                          "pearson": correlation(table)})
        result.append({"lag_label": label, "lag_tokens": lag,
                       "past_bit": past_bit, "current_bit": 2, "strata_then_pooled": cells})
    return result


def report(sample_id, name, path):
    with open(path, "rb") as handle:
        data = handle.read()
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or []))
    offsets, lengths = best[0x111], best[0x117]
    if len(offsets) != 1 or len(lengths) != 1:
        raise ValueError("requires one contiguous strip")
    off, count = offsets[0], lengths[0]
    if off < 0 or count <= 0 or off + count > len(data):
        raise ValueError("payload out of bounds")
    width, height = best[0x100][0], best[0x101][0]
    if width < 2 or height <= 0 or size_class(count, width, height) != "variable":
        raise ValueError("requires positive variable-size payload and width>=2")
    tokens, end = scan_prefix(data[off:off + count], LIMIT)
    return {"pixls_id": sample_id, "pixls_name": name,
            "sha256": hashlib.sha256(data).hexdigest(), "variant": "unassigned",
            "payload_w": width, "payload_h": height, "payload_offset": off,
            "payload_bytes": count, "size_class": "variable",
            "requested_tokens": LIMIT, "returned_tokens": len(tokens),
            "shortfall_tokens": LIMIT - len(tokens), "bits_consumed": end,
            "parsed_escapes": sum(q >= 17 for q, _ in tokens),
            "measurements": measure(tokens, width)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "FILE"))
    args = parser.parse_args(argv)
    ids = [sid for sid, _, _ in args.sample]
    try:
        invalid_ids = any(not sid.isascii() or not sid.isdecimal() or int(sid) <= 0 for sid in ids) or len(set(map(int, ids))) != len(ids)
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        parser.error("sample IDs must be distinct positive ASCII decimals")
    if any(not name or not name.isprintable() or any(c in name for c in '/\\') for _, name, _ in args.sample):
        parser.error("sample public name must be a printable basename")
    reports, failures = [], []
    for sid, name, path in args.sample:
        try:
            reports.append(report(sid, name, path))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failures.append({"pixls_id": sid, "error_type": type(exc).__name__})
    hashes = {}
    for source in ("token_width_lag_probe.py", "suffix_joint_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), source), "rb") as handle:
            hashes[source] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({"source_sha256": hashes, "python_version": sys.version.split()[0],
                      "escape_extra_bits": 0, "pair_selection": "both endpoint q<17; original indices",
                      "samples": reports, "failures": failures}, indent=2, allow_nan=False))
    return 1 if failures or any(r["shortfall_tokens"] for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
