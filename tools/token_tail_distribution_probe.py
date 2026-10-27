#!/usr/bin/env python3
"""Fixed candidate-tail q/suffix distributions for #144; aggregate JSON only.

Builds on #11/#218/#234. Candidate rows are absolute r*S token intervals,
not physical image rows. For T=S-W compare tail [W,S) with first-width
[0,W), preceding [W-T,W), and middle [S//2,S//2+T). Comparisons are fixed
position descriptions, not exchangeable nulls or significance tests. No
stride/phase fitting, decoding, preview access or field semantics. Retain
q>=17 with zero extra escape skip; actual escape syntax remains unknown.
Reuse retained CC0 verification after matching the local SHA-256. Stdlib,
Python 3.8+; reads files and prints numbers, without writing sample data.
Sample IDs must be unique positive ASCII decimals; names must be printable
and contain no path separators.
"""
import argparse
import collections
import hashlib
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class


def scan_tokens(payload, limit):
    """Yield exact q, five-bit suffix, ending bit; accept complete tokens only."""
    pos, nbits, count = 0, len(payload) * 8, 0
    while count < limit and pos + 6 <= nbits:
        start = pos
        while pos < nbits and not (payload[pos >> 3] >> (7 - (pos & 7))) & 1:
            pos += 1
        if pos + 6 > nbits:
            break
        q = pos - start
        suffix = 0
        for j in range(1, 6):
            suffix = (suffix << 1) | ((payload[(pos + j) >> 3] >>
                                      (7 - ((pos + j) & 7))) & 1)
        pos += 6
        count += 1
        yield q, suffix, pos


def regions(width, stride):
    """Position comparisons fit inside first-width; they may overlap each other."""
    tail = stride - width
    if width < 1 or tail < 1 or tail > width or stride // 2 + tail > width:
        raise ValueError("require positive tail and comparison windows inside first-width")
    return {"first_width": (0, width), "tail": (width, stride),
            "preceding": (width - tail, width),
            "middle": (stride // 2, stride // 2 + tail)}


def empty_histograms(bounds):
    return {key: (collections.Counter(), [0] * 32) for key in bounds}


def entropy(counts):
    total = sum(counts)
    return (-sum(n / total * math.log2(n / total) for n in counts if n)
            if total else None)


def total_variation(a, b):
    na, nb = sum(a.values()), sum(b.values())
    return (sum(abs(a.get(k, 0) / na - b.get(k, 0) / nb)
                for k in set(a) | set(b)) / 2 if na and nb else None)


def summarize(histograms, bounds):
    result = {}
    for key, (qhist, shist) in histograms.items():
        result[key] = dict(start_position=bounds[key][0], stop_position=bounds[key][1],
                           tokens=sum(qhist.values()),
                           q_counts={str(q): n for q, n in sorted(qhist.items())},
                           suffix_counts_0_to_31=shist,
                           sum_q=sum(q * n for q, n in qhist.items()),
                           escape_tokens=sum(n for q, n in qhist.items() if q >= 17),
                           q_entropy_bits=entropy(qhist.values()),
                           suffix_entropy_bits=entropy(shist))
    tailq, tails = histograms["tail"]
    comparisons = {}
    for key in ("first_width", "preceding", "middle"):
        qhist, shist = histograms[key]
        comparisons[key] = dict(q_total_variation=total_variation(tailq, qhist),
                               suffix_total_variation=total_variation(
                                   dict(enumerate(tails)), dict(enumerate(shist))))
    return result, comparisons


def distributions(payload, width, stride, starts, rows):
    bounds = regions(width, stride)
    if rows < 1 or not starts or min(starts) < 0:
        raise ValueError("require rows>=1 and nonnegative band starts")
    limit = (max(starts) + rows) * stride
    totals = {start: empty_histograms(bounds) for start in starts}
    complete_rows = dict.fromkeys(starts, 0)
    parsed = end = 0
    current = None
    active = []
    for index, (q, suffix, end) in enumerate(scan_tokens(payload, limit)):
        parsed = index + 1
        row, position = divmod(index, stride)
        if position == 0:
            active = [start for start in starts if start <= row < start + rows]
            current = empty_histograms(bounds) if active else None
        if not active:
            continue
        for key, (lo, hi) in bounds.items():
            if lo <= position < hi:
                current[key][0][q] += 1
                current[key][1][suffix] += 1
        # Incomplete final candidate rows contribute no region statistics.
        if position == stride - 1:
            for start in active:
                complete_rows[start] += 1
                for key in bounds:
                    targetq, targets = totals[start][key]
                    sourceq, sources = current[key]
                    targetq.update(sourceq)
                    for suffix_index, n in enumerate(sources):
                        targets[suffix_index] += n
    bands = []
    for start in starts:
        summary, comparisons = summarize(totals[start], bounds)
        bands.append(dict(start_candidate_row=start, start_token=start * stride,
                          requested_rows=rows, complete_rows=complete_rows[start],
                          complete=complete_rows[start] == rows,
                          regions=summary, tail_comparisons=comparisons))
    return dict(requested_tokens=limit, parsed_tokens=parsed, consumed_bits=end,
                token_shortfall=limit - parsed, bands=bands)


def measure(path, digest, stride, starts, rows):
    with open(path, "rb") as source:
        data = source.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest.lower():
        raise ValueError("SHA-256 differs from retained verified record")
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    width, height = best[0x100][0], best[0x101][0]
    offsets, sizes = best[0x111], best[0x117]
    if len(offsets) != 1 or len(sizes) != 1:
        raise ValueError("single strip required")
    off, size = offsets[0], sizes[0]
    if width <= 0 or height <= 0 or off < 0 or size <= 0 or off + size > len(data):
        raise ValueError("invalid dimensions or strip bounds")
    if size_class(size, width, height) != "variable":
        raise ValueError("variable-size payload required")
    result = distributions(data[off:off + size], width, stride, starts, rows)
    result.update(sha256=actual, payload_width=width, payload_height=height,
                  payload_bytes=size, compression_tag=best.get(0x103),
                  size_class="variable", variant="unassigned", stride=stride)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="append", nargs=4, required=True,
                        metavar=("ID", "NAME", "SHA256", "FILE"))
    parser.add_argument("--stride", type=int, required=True)
    parser.add_argument("--start-row", type=int, action="append")
    parser.add_argument("--rows", type=int, default=300)
    args = parser.parse_args(argv)
    starts = sorted(set(args.start_row if args.start_row is not None else [0, 1000, 2000]))
    ids = [s[0] for s in args.sample]
    if args.rows < 1 or args.stride < 2 or min(starts) < 0:
        parser.error("require positive rows/stride and nonnegative starts")
    try:
        if any(not sid.isascii() or not sid.isdecimal() or int(sid) <= 0 for sid in ids):
            raise ValueError
        if len(set(int(sid) for sid in ids)) != len(ids):
            raise ValueError
    except ValueError:
        parser.error("sample IDs must be distinct positive ASCII decimals")
    if any(not name or not name.isprintable() or any(c in name for c in "/\\")
           for _, name, _, _ in args.sample):
        parser.error("sample public name must be printable without path separators")
    samples, failed = [], False
    for sid, name, digest, path in args.sample:
        entry = dict(pixls_id=sid, pixls_name=name)
        try:
            if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
                raise ValueError("invalid SHA-256")
            entry.update(measure(path, digest, args.stride, starts, args.rows))
            entry["ok"] = entry["token_shortfall"] == 0
        except (OSError, ValueError, KeyError, TypeError, IndexError, struct.error) as exc:
            entry.update(ok=False, error=type(exc).__name__)
        samples.append(entry)
        failed = failed or not entry["ok"]
    hashes = {}
    for filename in ("token_tail_distribution_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), filename), "rb") as source:
            hashes[filename] = hashlib.sha256(source.read()).hexdigest()
    print(json.dumps(dict(schema_version=1, method="fixed-candidate-tail-distributions",
                          python_version=sys.version.split()[0],
                          escape_extra_bits=0, source_sha256=hashes,
                          samples=samples), indent=2, allow_nan=False))
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
