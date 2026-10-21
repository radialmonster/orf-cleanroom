#!/usr/bin/env python3
"""Reference decoder (library + CLI) for the uncompressed V0 ORF packings.

Supports: ROADMAP.md, specs/V0.md; findings/V0/ (packed-12 and packed-12.8), lead #71
(packed-16), findings/container/ (payload location and
the fixed-size rule). Standard library only (Python 3.8+). Released under CC0 1.0.

Handles the exact fixed-size payloads of VARIANTS.md V0:
  packed-12    verified (findings/V0/2026-10-19--radialmonster--packed-12-msb-two-values-per-three-bytes)
  packed-12.8  verified (findings/V0/2026-10-20--radialmonster--packed-12-8-groups-of-ten-values)
  packed-16    UNVERIFIED (lead #71)
Compressed payloads (V1, V2, ...) are detected and reported as "not yet specified".

Output is aggregate numbers only. This program has no file output at all: the
decoded values exist in memory one row at a time and are never written, so no
pixel data can end up in the repository or anywhere else.

The "output hash" is the SHA-256 of all decoded values as little-endian uint16,
row-major, rows 0..height-1 and columns 0..width-1, with the values exactly as
the layout yields them (no black level, no shift, no scaling). The pixel order
inside a two-pixel unit is not decided by the evidence (findings/V0 says so), so
the hash assumes the order written in specs/V0.md.

Usage: python decoder/orf_decode.py FILE [FILE ...] [--order ORDER]
"""
import argparse
import bisect
import hashlib
import operator
import os
import struct
import sys
from array import array

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tools"))
import orf_signature  # noqa: E402

F_PACKED12 = "2026-10-19--radialmonster--packed-12-msb-two-values-per-three-bytes"
F_PACKED128 = "2026-10-20--radialmonster--packed-12-8-groups-of-ten-values"
F_FIXED = "2026-10-19--radialmonster--fixed-size-payloads-exact-else-compressed"

# what the evidence is for each layout
STATUS = {
    "packed-12": "verified (%s, self-verified)" % F_PACKED12,
    "packed-12.8": "verified (%s, self-verified)" % F_PACKED128,
    "packed-16": "UNVERIFIED (lead #71)",
}
# the order choices per packing; the first one wins a tie
ORDERS = {
    "packed-12": ("plain", "word4-reversed"),
    "packed-12.8": ("lsb",),
    "packed-16": ("le", "be"),
}


LAYOUTS = ("natural", "two-field")      # row layout: stored row order (lead #77)


class NotSpecified(Exception):
    """The payload is not one of the specified layouts (or breaks a precondition)."""


def reverse_words4(raw):
    """Reverse the byte order inside every 4-byte word (packed-12: finding F_PACKED12)."""
    out = bytearray(len(raw))
    for k in range(4):
        out[k::4] = raw[3 - k::4]
    return bytes(out)


def row_bytes(packing, w):
    if packing == "packed-12":
        if w % 2:
            raise NotSpecified("packed-12 needs an even width")
        return w * 3 // 2
    if packing == "packed-12.8":
        if w % 10:
            raise NotSpecified("packed-12.8 needs a width that is a multiple of 10 (16-byte groups of 10 pixels)")
        return w // 10 * 16
    if packing == "packed-16":
        return w * 2
    raise NotSpecified("unknown packing %r" % packing)


def unpack_row(packing, order, raw, w):
    """Unpack one row of w values from its raw bytes; returns (array('H'), pad_nonzero)."""
    out = array("H", bytes(2 * w))
    pad = 0
    if packing == "packed-12":
        # finding F_PACKED12: two 12-bit values per 3 bytes, most-significant bit first:
        # first = b0 << 4 | b1 >> 4, second = (b1 & 15) << 8 | b2. Pixel order inside the
        # unit is not decided by the evidence (finding, last sentence of the claim).
        if order == "word4-reversed":
            # finding F_PACKED12: XZ-2, XZ-10, SH-2 have the bytes reversed inside every
            # 4-byte word before the same unit layout (needs row bytes % 4 == 0 here).
            if len(raw) % 4:
                raise NotSpecified("word4-reversed needs row bytes divisible by 4")
            raw = reverse_words4(raw)
        b0, b1, b2 = raw[0::3], raw[1::3], raw[2::3]
        out[0::2] = array("H", [x << 4 | y >> 4 for x, y in zip(b0, b1)])
        out[1::2] = array("H", [(y & 15) << 8 | z for y, z in zip(b1, b2)])
    elif packing == "packed-12.8":
        # F_PACKED128 (lead #70): rows are runs of 16-byte groups; bytes 0..14 are five
        # 3-byte units, each two 12-bit values least-significant bit first
        # (first = b0 | (b1 & 15) << 8, second = b1 >> 4 | b2 << 4); byte 15 is padding.
        for k in range(5):
            b0, b1, b2 = raw[3 * k::16], raw[3 * k + 1::16], raw[3 * k + 2::16]
            out[2 * k::10] = array("H", [x | (y & 15) << 8 for x, y in zip(b0, b1)])
            out[2 * k + 1::10] = array("H", [y >> 4 | z << 4 for y, z in zip(b1, b2)])
        pad = sum(1 for p in raw[15::16] if p)   # F_PACKED128: byte 15 is 0 on all 5 CC0 files
    elif packing == "packed-16":
        # lead #71 (unverified): one 16-bit word per pixel (12-bit value << 4 in the three
        # CC0 files); byte order per body (finding 2026-10-21--radialmonster--iiro-packed12-and-packed16-whole-frame-byte-order, Partial: the smoother order matches the TIFF mark on those 3 files; still autodetected by smoothness). Values are the stored words, not shifted back.
        out = array("H")
        out.frombytes(raw)
        if (order == "be") != (sys.byteorder == "big"):
            out.byteswap()
    else:
        raise NotSpecified("unknown packing %r" % packing)
    return out, pad


class Payload:
    """Where the raw payload of a file is, from the TIFF structure (findings/container)."""

    def __init__(self, path):
        with open(path, "rb") as f:
            data = f.read()
        self.size = len(data)
        t = orf_signature.Tiff(data)
        ifds = list(t.all_ifds())
        best = max(ifds, key=lambda d: sum(d.get(0x117) or [0]))   # largest strip byte count = raw IFD
        self.sig = orf_signature.signature(path)
        self.header = data[:4].decode("ascii", "replace")
        offs, cnts = best.get(0x111) or [], best.get(0x117) or []
        # The payload is the strips read one after another in tag order (TIFF 6.0). Strips need
        # not touch: in the 6 plain-order packed-12 CC0 files there is a gap between two strips
        # (unverified observation of this decoder, see specs/V0.md gap G1), so read per strip.
        self.strips = list(zip(offs, cnts))
        self.offset = offs[0] if offs else 0
        self.nbytes = sum(cnts)
        self.gaps = sum(1 for i in range(len(offs) - 1) if offs[i + 1] != offs[i] + cnts[i])
        self.in_file = all(o + c <= self.size for o, c in self.strips)
        self.starts = [sum(cnts[:i]) for i in range(len(cnts))]   # payload position of each strip

    def read(self, f, pos, n):
        """Read n payload bytes starting at payload position pos (may span strips)."""
        out = []
        i = bisect.bisect_right(self.starts, pos) - 1
        while n > 0 and 0 <= i < len(self.strips):
            off, cnt = self.strips[i]
            inner = pos - self.starts[i]
            take = min(n, cnt - inner)
            f.seek(off + inner)
            out.append(f.read(take))
            pos, n, i = pos + take, n - take, i + 1
        return b"".join(out)


def _score(rows):
    """Roughness: mean |x - x two columns left| over the mean value (lower is smoother)."""
    num = den = cnt = 0
    for r in rows:
        num += sum(map(abs, map(operator.sub, r[2:], r[:-2])))
        den += sum(r)
        cnt += len(r) - 2
    return (num / cnt) / ((den / (cnt + 2 * len(rows))) or 1.0)


def detect_order(f, p, packing, w, h, rb):
    """Pick the order with the lowest roughness on a window (3 bands x 16 rows x up to 1200
    columns, bands spread through the frame): the method of finding F_PACKED12 and lead #71
    (smoothness at same-colour distance 2). Ties go to the first order in ORDERS.
    Returns (order, margin), margin = second-best score / best score."""
    choices = ORDERS[packing]
    if len(choices) == 1:
        return choices[0], 1.0
    nb, nr = 3, min(16, h)
    cols = min(w, 1200) // 30 * 30 or w
    starts = [min((h * (2 * k + 1) // (2 * nb)) // 2 * 2, h - nr) for k in range(nb)]
    scores = {}
    for o in choices:
        rows = []
        for s in starts:
            for i in range(nr):
                rows.append(unpack_row(packing, o, p.read(f, (s + i) * rb, rb), w)[0][:cols])
        scores[o] = _score(rows)
    best = min(choices, key=lambda o: scores[o])    # min() keeps the first of equal scores
    rest = [scores[o] for o in choices if o != best]
    return best, (min(rest) / scores[best] if scores[best] else float("inf"))


def stored_row(y, h, layout):
    """Stored row holding image row y. natural: y. two-field (lead #77): stored rows 0..n1-1 are the
    even image rows, n1..h-1 the odd ones, n1 = ceil(h/2)."""
    if layout == "natural":
        return y
    return y // 2 if y % 2 == 0 else (h + 1) // 2 + y // 2


def detect_layout(f, p, packing, order, w, h, rb):
    """Row layout from the stored rows themselves (lead #77): the mean absolute difference of
    stored rows 1 apart against 2 apart, on 3 bands x 8 rows x up to 400 centre columns. Rows of
    one CFA colour are 2 apart in the image, so natural order has the 2-apart rows closer;
    two-field order has the 1-apart stored rows closer. Returns (layout, margin), margin =
    larger / smaller of the two sums. Ties go to natural."""
    if h < 64:
        return "natural", 1.0
    c0 = max(0, (w - 400) // 2)
    c1 = min(w, c0 + 400)
    d1 = d2 = 0
    for k in range(3):
        s0 = (h * (2 * k + 1) // 6) // 2 * 2 - 4
        rows = [unpack_row(packing, order, p.read(f, (s0 + i) * rb, rb), w)[0][c0:c1] for i in range(10)]
        for i in range(8):
            d1 += sum(map(abs, map(operator.sub, rows[i], rows[i + 1])))
            d2 += sum(map(abs, map(operator.sub, rows[i], rows[i + 2])))
    if d1 < d2:
        return "two-field", d2 / (d1 or 1)
    return "natural", d1 / (d2 or 1)


def decode_file(path, order=None, layout=None):
    """Decode one file (streaming). Returns a dict of aggregates; no pixel data is kept.

    Always present: file, sha256, model, header, status, variant, packing, width, height,
    payload_offset, payload_bytes, strips, strip_gaps, notes. When a layout applies also: order, order_margin,
    row_layout, layout_margin,
    consumed_bytes, consumed_bits, exact_end, min, max, out_of_range, smooth, output_sha256,
    pad_nonzero (packed-12.8)."""
    p = Payload(path)
    sig = p.sig
    w, h, sc = sig["payload_w"], sig["payload_h"], sig["size_class"]
    r = {"file": sig["file"], "sha256": sig["sha256"], "model": sig["model"], "header": p.header,
         "width": w, "height": h, "payload_offset": p.offset, "payload_bytes": p.nbytes,
         "strips": len(p.strips), "strip_gaps": p.gaps,
         "packing": "", "order": "", "notes": []}
    if sc == "variable":
        # finding F_FIXED: a payload that is not an exact 12 / 12.8 / 16 bit packing is compressed
        r.update(variant="compressed", status="not yet specified")
        r["notes"].append("compressed payload (%s bits per pixel); no decoder is specified yet, see ROADMAP.md" % sig["bpp"])
        return r
    packing = sc
    r.update(variant="V0", packing=packing, status=STATUS[packing])
    rb = row_bytes(packing, w)
    if not p.in_file:
        raise NotSpecified("a strip lies outside the file")
    if order is not None and order not in ORDERS[packing]:
        raise NotSpecified("order %r is not defined for %s (choose from %s)" % (order, packing, ", ".join(ORDERS[packing])))
    if layout is not None and layout not in LAYOUTS:
        raise NotSpecified("row layout %r is not defined (choose from %s)" % (layout, ", ".join(LAYOUTS)))
    digest = hashlib.sha256()
    lo, hi, bad, smooth_n, pad = 1 << 30, -1, 0, 0, 0
    # out of range: a value above 4095 for packed-12 and packed-12.8 (12-bit data); for packed-16
    # (lead #71: 12-bit value << 4) a word with any of its low 4 bits set
    with open(path, "rb") as f:
        margin = None
        if order is None:
            order, margin = detect_order(f, p, packing, w, h, rb)
        layout_margin = None
        if layout is None:
            layout, layout_margin = detect_layout(f, p, packing, order, w, h, rb)
        for y in range(h):
            row, pd = unpack_row(packing, order, p.read(f, stored_row(y, h, layout) * rb, rb), w)
            pad += pd
            lo, hi = min(lo, min(row)), max(hi, max(row))
            if packing == "packed-16":
                bad += sum(1 for v in row if v & 15)
            else:
                bad += sum(map((4095).__lt__, row))
            smooth_n += sum(map(abs, map(operator.sub, row[2:], row[:-2])))   # same-colour neighbour two columns left
            if sys.byteorder == "big":
                row.byteswap()
            digest.update(row.tobytes())           # little-endian uint16, row-major
    consumed = rb * h
    r.update(order=order, order_margin=margin, row_layout=layout, layout_margin=layout_margin, consumed_bytes=consumed, consumed_bits=consumed * 8,
             exact_end=(consumed == p.nbytes), min=lo, max=hi, out_of_range=bad,
             smooth=smooth_n / (h * (w - 2)), output_sha256=digest.hexdigest(),
             pad_nonzero=pad if packing == "packed-12.8" else "")
    if packing == "packed-12.8" and pad:
        r["notes"].append("%d group padding bytes are not zero (finding for lead #70 found zero)" % pad)
    if packing != "packed-12":
        r["notes"].append("layout is UNVERIFIED (%s); pixel order inside a unit is undecided" % STATUS[packing].split("(")[1].rstrip(")"))
    else:
        r["notes"].append("pixel order inside a two-pixel unit is undecided by the evidence")
    if layout == "two-field":
        r["notes"].append("rows are stored as two fields (even image rows, then odd rows; lead #77); layout is UNVERIFIED")
    if packing == "packed-16":
        r["notes"].append("values are the stored 16-bit words (not shifted); out_of_range counts words with a low-4-bit set")
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog="Aggregates on stdout only; nothing is ever written to disk.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--order", help="force the order instead of detecting it: packed-12 plain|word4-reversed, "
                                    "packed-16 le|be (packed-12.8 has one)")
    ap.add_argument("--layout", choices=LAYOUTS, help="force the row layout instead of detecting it")
    a = ap.parse_args(argv)
    code = 0
    for path in a.files:
        try:
            r = decode_file(path, a.order, a.layout)
        except (NotSpecified, ValueError, struct.error, OSError) as exc:
            print("== %s\nerror: %s" % (os.path.basename(path), exc))
            code = 1
            continue
        print("== %s" % r["file"])
        for k in ("sha256", "model", "header", "variant", "packing", "status", "order", "order_margin", "row_layout", "layout_margin",
                  "width", "height", "payload_offset", "payload_bytes", "strips", "strip_gaps", "consumed_bytes", "exact_end",
                  "min", "max", "out_of_range", "smooth", "pad_nonzero", "output_sha256"):
            v = r.get(k, "")
            if v == "" or v is None:
                continue
            print("%-14s %s" % (k, ("%.4f" % v) if isinstance(v, float) else v))
        for n in r["notes"]:
            print("note           %s" % n)
    return code


if __name__ == "__main__":
    sys.exit(main())
