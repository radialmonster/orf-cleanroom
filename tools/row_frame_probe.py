#!/usr/bin/env python3
"""Row framing of compressed ORF strips, and the two readings of the six-token group.

Supports: #197 (framing), #339 (flat OM-3 codeword counts), #603 (capped-prefix escapes).
Standard library only (Python 3.8+). Prints numbers only: no paths, no image data.

Grammar (measured on flat OM-3 payloads): the strip starts with a marker of leading
zero bits followed by a 1 (40 bits when it starts with 39 zeros). A token is q
zeros, a 1 stop bit, then 5 suffix bits (k=5); q >= 12 is an escape, 12 zeros
and 12 raw bits. The container is read with orf_signature.Tiff; the payload is
the image IFD with the largest total strip byte count.

Row starts are located without any token parse: the bit pattern
(?:100[01]{5}){6}, six 8-bit fields 100xxxxx, is searched in the first --rows
rows' worth of bits and its matches are chained where they lie one row pitch
(6W+12 bits) apart. From each located start both readings are parsed for W
tokens: plain k=5, and six k=7 tokens followed by k=5 (the head rule). A row is
exact when those W tokens end on the next located start.

Not established here: one and the same 8-bit group reads as six k=7 fields at
bit b of the row and as six k=5 tokens at bit b+6 - same bit length, same token
count, same row end - so row framing alone does not choose between them. Both
readings are printed. Nothing is decoded and no token value is mapped to a pixel.

Usage: python -I -B tools/row_frame_probe.py [--rows N] FILE [FILE ...]
"""
import argparse
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff  # noqa: E402

OCTETS = [format(i, "08b") for i in range(256)]
HEAD = re.compile(r"(?=(?:100[01]{5}){6})")
K, CAP, RAW = 5, 12, 12          # suffix bits, escape prefix, escape payload
HK, HN = 7, 6                    # head rule: suffix bits and token count
LONG = CAP + RAW                 # longest token spelling, in bits
GROUP, NB = HN * 8, HN * 8 + 6   # the six 8-bit fields, plus the token that follows them


def payload(data):
    """(strip bytes, width, height) of the image IFD with the largest strip byte count."""
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    start, counts = best[0x111][0], best[0x117]
    return data[start:start + sum(counts)], best[0x100][0], best[0x101][0]


def chain(starts, pitch, band):
    """Keep the matches one row pitch apart; drop the second match a head produces
    (its next 8-bit field starts one) and any chain too short to be rows."""
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


def analyse(path, nrows):
    with open(path, "rb") as f:
        data = f.read()
    digest = hashlib.sha256(data).hexdigest()
    strip, width, height = payload(data)
    bits = "".join(OCTETS[b] for b in strip)
    first = next(i for i, b in enumerate(strip) if b)
    marker = first * 8 + 8 - strip[first].bit_length() + 1   # leading zeros, then the stop 1
    pitch = width * (K + 1) + 12      # W tokens of 6 bits, plus the 12 extra head bits
    band = max(64, pitch // 100)

    def end(pos, k):
        """End bit of the token at pos."""
        i = bits.find("1", pos, pos + CAP)
        return pos + LONG if i < 0 else i + 1 + k

    def row(pos, head):
        """End bit of `width` tokens from pos, with or without the six k=7 head tokens."""
        for i in range(width):
            pos = end(pos, HK if head and i < HN else K)
        return pos

    # 1. row starts from the bit pattern alone, no token parse
    scan = min(len(bits), marker + nrows * pitch)
    head_at = chain((m.start() for m in HEAD.finditer(bits, marker, scan)), pitch, band)
    # 2. plain k=5 chain from the marker: token column and bit offset of each head in its row
    wanted, at, seen = set(head_at), {}, {}
    pos = marker
    while wanted and pos < head_at[-1]:
        row_start = pos
        for c in range(width):
            if pos in wanted:
                at[pos] = (c, pos - row_start)
                seen[pos] = bits[pos:pos + NB]
            pos = end(pos, K)
    # 3. both readings, W tokens from each located start; 4. whole-payload k=5 count
    exact, differ = [0, 0], 0
    for a, b in zip(head_at, head_at[1:]):
        e5, eh = row(a, False), row(a, True)
        exact[0] += e5 == b
        exact[1] += eh == b
        differ += e5 != eh
    pos, counted = marker, 0
    while pos + LONG <= len(bits):
        i = bits.find("1", pos, pos + CAP)
        pos = pos + LONG if i < 0 else i + 1 + K
        counted += 1
    # 5. the six-token group: modal fields, both readings, where it sits
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
    print("sha256=%s W=%d H=%d marker=%d tokens_k5_minus_wh=%+d rows=%d ends_k5=%d ends_head=%d "
          "ends_differ=%d group_bit=%s group_col=%s fields_k7=%s fields_k5=%s group_rows=%d" % (
              digest, width, height, marker, counted - width * height, max(0, len(head_at) - 1),
              exact[0], exact[1], differ, offs, cols, k7, k5, shared), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--rows", type=int, default=400,
                    help="rows whose starts are located (default 400)")
    args = ap.parse_args()
    for path in args.files:
        analyse(path, args.rows)


if __name__ == "__main__":
    main()
