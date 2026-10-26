#!/usr/bin/env python3
"""Baseline JPEG DC-only decoder for an ORF's embedded preview.

Supports: the P0 token-to-luma probe (tools/token_luma_probe.py), the geometry
claim of lead #11. Standard library only; reads a file and prints aggregate
numbers. It writes no images and no pixel data.

Only the DC coefficient of each 8x8 block is decoded, for the first (luma)
component. That is enough to get a 1/8-resolution luma image (400x300 for the
3200x2400 preview used by the E-M1 Mark II files). AC coefficients are skipped.
Baseline sequential JPEG (SOF0) only, which is what these previews use.

Usage:
    python -I tools/jpeg_dc.py FILE.ORF [FILE.ORF ...]
    python -I tools/jpeg_dc.py FILE.jpg

For an ORF the largest baseline JPEG with width and height >= 1000 is used.
"""
import os
import sys


class BitReader:
    def __init__(self, data, pos):
        self.data = data
        self.pos = pos
        self.cur = 0
        self.nbits = 0

    def align(self):
        self.nbits = 0

    def bit(self):
        if self.nbits == 0:
            b = self.data[self.pos]
            self.pos += 1
            if b == 0xFF:
                n = self.data[self.pos]
                if n == 0x00:
                    self.pos += 1
                else:
                    raise ValueError("marker inside entropy data at %d" % (self.pos - 1))
            self.cur = b
            self.nbits = 8
        self.nbits -= 1
        return (self.cur >> self.nbits) & 1

    def bits(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bit()
        return v

    def restart(self):
        self.align()
        if self.pos + 1 >= len(self.data) or self.data[self.pos] != 0xFF:
            raise ValueError("expected restart marker at %d" % self.pos)
        m = self.data[self.pos + 1]
        if not (0xD0 <= m <= 0xD7):
            raise ValueError("expected RSTn at %d, got FF%02X" % (self.pos, m))
        self.pos += 2
        return m


def build_huffman(counts, symbols):
    table = {}
    code = 0
    k = 0
    for length in range(1, 17):
        for _ in range(counts[length - 1]):
            table[(length, code)] = symbols[k]
            k += 1
            code += 1
        code <<= 1
    return table


def huff(reader, table):
    code = 0
    for length in range(1, 17):
        code = (code << 1) | reader.bit()
        if (length, code) in table:
            return table[(length, code)]
    raise ValueError("bad Huffman code")


def extend(v, n):
    return v if v >= (1 << (n - 1)) else v - (1 << n) + 1


def decode(data, start):
    """Decode a baseline JPEG at `start`; return (wblocks, hblocks, luma DC list)."""
    i = start + 2
    dc_tables = {}
    ac_tables = {}
    sof = None
    restart_interval = 0
    scan = None
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i + 1 > len(data):
            break
        m = data[i]; i += 1
        if m == 0xD9:
            break
        if m == 0xD8 or 0xD0 <= m <= 0xD7:
            continue
        L = (data[i] << 8) | data[i + 1]
        seg = data[i + 2:i + L]
        if m == 0xC0:
            h = (seg[1] << 8) | seg[2]
            w = (seg[3] << 8) | seg[4]
            nc = seg[5]
            comps = []
            for c in range(nc):
                cid = seg[6 + 3 * c]
                hv = seg[7 + 3 * c]
                tq = seg[8 + 3 * c]
                comps.append((cid, hv >> 4, hv & 15, tq))
            sof = (w, h, comps)
        elif m == 0xC4:
            p = 0
            while p < len(seg):
                tc_th = seg[p]
                counts = seg[p + 1:p + 17]
                n = sum(counts)
                table = build_huffman(counts, seg[p + 17:p + 17 + n])
                if tc_th >> 4 == 0:
                    dc_tables[tc_th & 15] = table
                else:
                    ac_tables[tc_th & 15] = table
                p += 17 + n
        elif m == 0xDD:
            restart_interval = (seg[0] << 8) | seg[1]
        elif m == 0xDA:
            ns = seg[0]
            scan = []
            for c in range(ns):
                scan.append((seg[1 + 2 * c], seg[2 + 2 * c] >> 4, seg[2 + 2 * c] & 15))
            pos = i + L
            break
        i += L
    if sof is None or scan is None:
        raise ValueError("no baseline SOF0/SOS")
    w, h, comps = sof
    if {c[0] for c in comps} - {c[0] for c in scan}:
        raise ValueError("first scan does not hold every component (non-interleaved)")
    if len(comps) == 1:
        # a single-component scan is non-interleaved: one block per MCU in raster order,
        # whatever sampling factors the SOF lists
        comps = [(comps[0][0], 1, 1, comps[0][3])]
    hmax = max(c[1] for c in comps)
    vmax = max(c[2] for c in comps)
    mcux = (w + 8 * hmax - 1) // (8 * hmax)
    mcuy = (h + 8 * vmax - 1) // (8 * vmax)
    wb = (w + 7) // 8
    hb = (h + 7) // 8
    out = [0] * (wb * hb)
    pred = {c[0]: 0 for c in comps}
    r = BitReader(data, pos)
    mcu = 0
    for my in range(mcuy):
        for mx in range(mcux):
            if restart_interval and mcu and mcu % restart_interval == 0:
                r.restart()
                for k in pred:
                    pred[k] = 0
            for cid, ch, cv, tq in comps:
                td = next(td for c, td, ta in scan if c == cid)
                ta = next(ta for c, td, ta in scan if c == cid)
                for by in range(cv):
                    for bx in range(ch):
                        size = huff(r, dc_tables[td])
                        if size:
                            pred[cid] += extend(r.bits(size), size)
                        if cid == comps[0][0]:
                            x = mx * ch + bx
                            y = my * cv + by
                            if x < wb and y < hb:
                                out[y * wb + x] = pred[cid]
                        k = 1
                        while k < 64:
                            rs = huff(r, ac_tables[ta])
                            run = rs >> 4
                            size = rs & 15
                            if size == 0:
                                if run == 15:
                                    k += 16
                                    continue
                                break
                            k += run
                            if k >= 64:
                                break
                            r.bits(size)
                            k += 1
            mcu += 1
    return wb, hb, out


def find_preview(data, max_dim=12000, max_area=100_000_000):
    """Return (area, offset, length, width, height) of the largest baseline JPEG.

    Candidates larger than `max_dim` in either direction or `max_area` pixels
    are rejected: a byte pattern inside a thumbnail or maker note can otherwise
    look like a huge JPEG.
    """
    best = None
    i = data.find(b"\xff\xd8\xff")
    while i >= 0:
        j = i + 2
        dims = None
        while j < len(data):
            if data[j] != 0xFF:
                j += 1
                continue
            while j < len(data) and data[j] == 0xFF:
                j += 1
            if j + 1 > len(data):
                break
            m = data[j]; j += 1
            if m == 0xD9:
                break
            if m == 0xD8 or 0xD0 <= m <= 0xD7:
                continue
            if j + 2 > len(data):
                break
            L = (data[j] << 8) | data[j + 1]
            if m == 0xC0 and j + 8 < len(data):
                h = (data[j + 3] << 8) | data[j + 4]
                w = (data[j + 5] << 8) | data[j + 6]
                dims = (w, h)
            if m == 0xDA:
                break
            j += L
        if dims and 1000 <= dims[0] <= max_dim and 1000 <= dims[1] <= max_dim \
                and dims[0] * dims[1] <= max_area:
            # search for EOI from the SOS, not from SOI: header segments (APPn, a
            # thumbnail) can hold FF D9, entropy-coded data cannot (FF is stuffed)
            e = data.find(b"\xff\xd9", j - 2)
            length = (e + 2 - i) if e > 0 else (len(data) - i)
            if best is None or dims[0] * dims[1] > best[0]:
                best = (dims[0] * dims[1], i, length, dims[0], dims[1])
        i = data.find(b"\xff\xd8\xff", i + 3)
    return best


def main(paths):
    if not paths or paths[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if paths else 2)
    for path in paths:
        try:
            data = open(path, "rb").read()
            if path.lower().endswith((".orf", ".ori")):
                best = find_preview(data)
                if best is None:
                    print("%s: no preview" % os.path.basename(path), file=sys.stderr)
                    continue
                start = best[1]
            else:
                start = 0
            wb, hb, dc = decode(data, start)
            print("%s: dc %dx%d  min %d  max %d  mean %.2f" % (
                os.path.basename(path), wb, hb, min(dc), max(dc), sum(dc) / len(dc)))
        except (ValueError, IndexError, KeyError, OSError) as exc:
            print("%s: %s" % (os.path.basename(path), exc), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
