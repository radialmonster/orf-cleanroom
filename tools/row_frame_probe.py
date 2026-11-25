#!/usr/bin/env python3
"""Candidate row framing of compressed ORF strips, and the two readings of the six-field group.

Supports: #197 (framing), #339 (flat OM-3 codeword counts), #603 (capped-prefix escapes).
Standard library only (Python 3.8+). Prints numbers only: no paths, no image data.

Payload: the declared strip sequence of the unique image IFD with the largest
total strip byte count, read by strip_start_audit.independent_strips
(separated strips joined in table order without gap bytes; tied, overlapping or
mismatched strip tables are rejected and the input is reported as unknown).

Candidate grammar (measured on flat OM-3 payloads, not established): the
payload starts with a literal marker of leading zero bits and a 1. A word is q
zeros, a 1 stop bit, then 5 suffix bits (k=5); q >= 12 is an escape, 12 zeros
and 12 arbitrary raw bits. Word ends are bounded: a word that does not fit in
the payload is incomplete and ends any parse there (capped_prefix_counts.word_end).

Selected starts: every match of the bit pattern (?:100[01]{5}){6} (six 8-bit
fields 100xxxxx) from the marker end to marker + --rows * pitch bits, where
pitch = 6W+12 is an assumed interval. Matches are chained when the next one lies
pitch +/- tolerance bits after the previous one, tolerance = max(64,
pitch // 100); a match closer than the tolerance to the previous kept one is
dropped (a group of six fields also matches 8 bits later). Only the longest
chain is kept. Its starts are positions where the pattern was selected, not
physical row starts, and its intervals are not a measured row pitch.

From each selected start both readings are parsed for W words: plain k=5, and
six k=7 words followed by k=5 (the head rule). An interval is exact under a
reading when those W words end on the next selected start. One and the same
group reads as six k=7 fields at bit b and as six k=5 words at bit b+6, with
the same length and end, so this framing does not choose between them.

Whole-payload word counts after the marker (capped_prefix_counts.count):
guard24 is the historical loop that starts a word only while 24 bits remain;
complete counts every complete bounded word and reports the residual bits.

Nothing is decoded and no word value is mapped to a pixel.

Usage: python -I -B tools/row_frame_probe.py [--rows N] FILE [FILE ...]
"""
import argparse
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capped_prefix_counts import count, word_end  # noqa: E402
from strip_start_audit import independent_strips  # noqa: E402

OCTETS = [format(i, "08b") for i in range(256)]
HEAD = re.compile(r"(?=(?:100[01]{5}){6})")
K = 5                            # suffix bits of an ordinary word
HK, HN = 7, 6                    # head rule: suffix bits and word count
GROUP, NB = HN * 8, HN * 8 + 6   # the six 8-bit fields, plus the word that follows them


def pitch_and_tolerance(width):
    """Assumed interval between selected starts and the chaining tolerance, in bits."""
    pitch = width * (K + 1) + 12      # W words of 6 bits, plus 12 extra group bits
    return pitch, max(64, pitch // 100)


def chain(starts, pitch, band):
    """Longest chain of matches lying pitch +/- band apart; a match closer than band
    to the last kept one is dropped. Chains of one match are not kept."""
    chains, cur = [], []
    for m in starts:
        if cur and m - cur[-1] < band:
            continue
        if cur and pitch - band <= m - cur[-1] <= pitch + band:
            cur.append(m)
        else:
            if len(cur) > 1:
                chains.append(cur)
            cur = [m]
    if len(cur) > 1:
        chains.append(cur)
    return max(chains, key=len) if chains else []


def words(bits, pos, width, head):
    """End bit of `width` words from pos (the first six k=7 under the head rule),
    or None when a word is incomplete."""
    for i in range(width):
        pos = word_end(bits, pos, HK if head and i < HN else K)
        if pos is None:
            return None
    return pos


def analyse_payload(payload, width, height, nrows):
    """Ordered (label, value) pairs for one payload."""
    out = [("W", width), ("H", height)]
    bits = "".join(OCTETS[b] for b in payload)
    marker = bits.find("1") + 1                 # leading zeros, then the 1
    if not marker:
        return out + [("status", "no_marker"), ("payload_bits", len(bits))]
    pitch, band = pitch_and_tolerance(width)

    # 1. selected starts from the bit pattern alone, no word parse
    scan = min(len(bits), marker + nrows * pitch)
    head_at = chain((m.start() for m in HEAD.finditer(bits, marker, scan)), pitch, band)
    # 2. plain k=5 parse from the marker in blocks of W words: word column and bit
    #    offset of each selected start inside its block
    wanted, at, seen = set(head_at), {}, {}
    pos = marker
    while wanted and pos is not None and pos < head_at[-1]:
        block = pos
        for c in range(width):
            if pos in wanted:
                at[pos] = (c, pos - block)
                seen[pos] = bits[pos:pos + NB]
            pos = word_end(bits, pos, K)
            if pos is None:
                break
    # 3. both readings, W words from each selected start
    exact, differ = [0, 0], 0
    for a, b in zip(head_at, head_at[1:]):
        e5, eh = words(bits, a, width, False), words(bits, a, width, True)
        exact[0] += e5 == b
        exact[1] += eh == b
        differ += e5 != eh
    # 4. whole-payload word counts: historical 24-bit guard and complete words
    counted = count(bits, marker)
    guard, complete = counted["guard24"], counted["complete"]
    # 5. the six-field group: modal fields, both readings, where it sits
    fields, cols, offs, shared, k7, k5 = "-", "-", "-", 0, "-", "-"
    if seen:
        cols = ",".join(map(str, sorted({at[p][0] for p in seen})))
        offs = ",".join(map(str, sorted({at[p][1] for p in seen})))
        fields = max(sorted(set(g[:GROUP] for g in seen.values())),
                     key=lambda f: sum(g[:GROUP] == f for g in seen.values()))
        with_modal = [p for p in seen if seen[p][:GROUP] == fields]
        shared = len(with_modal)
        k7 = ",".join(str(int(fields[8 * i + 1:8 * i + 8], 2)) for i in range(HN))
        after = seen[with_modal[0]][6:]          # the plain k=5 reading starts 6 bits in
        k5 = ",".join(str(int(t[3:], 2)) if t[:3] == "001" else "-"
                      for t in (after[8 * i:8 * i + 8] for i in range(HN)))
    return out + [
        ("status", "ok"), ("marker", marker), ("pitch", pitch), ("tolerance", band),
        ("search_bits", scan - marker),
        ("guard24_k5_minus_wh", "%+d" % (guard["tokens"] - width * height)),
        ("complete_k5_minus_wh", "%+d" % (complete["tokens"] - width * height)),
        ("residual_bits", complete["residual_bits"]),
        ("selected_starts", len(head_at)), ("selected_intervals", max(0, len(head_at) - 1)),
        ("intervals_exact_k5", exact[0]), ("intervals_exact_head", exact[1]),
        ("ends_differ", differ), ("group_bit", offs), ("group_col", cols),
        ("fields_k7", k7), ("fields_k5", k5), ("group_starts", shared)]


def analyse(data, nrows):
    geometry, payload = independent_strips(data)
    return ([("sha256", hashlib.sha256(data).hexdigest())]
            + analyse_payload(payload, geometry["width"], geometry["height"], nrows))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--rows", type=int, default=400,
                    help="search length in assumed pitches from the marker (default 400)")
    args = ap.parse_args()
    failed = False
    for n, path in enumerate(args.files, 1):
        try:
            with open(path, "rb") as f:
                pairs = analyse(f.read(), args.rows)
        except (OSError, ValueError, IndexError) as exc:
            reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            pairs = [("input", n), ("status", "unknown"), ("reason", reason)]
            failed = True
        print(" ".join("%s=%s" % kv for kv in pairs), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
