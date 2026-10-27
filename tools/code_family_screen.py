#!/usr/bin/env python3
"""Lead #339: bounded screen of standard containers and per-sample prefix codes on an ORF payload.

Original clean-room analysis; stdlib Python 3.8+. Aggregate JSON only; no paths, pixels or images.
Sources for the families: RFC 1950/1951/1952 (zlib, DEFLATE, gzip), bzip2 and xz/LZMA as shipped in
the Python standard library, RFC 8878 (Zstandard magic), RFC 9639 (FLAC sync), ISO 11172-3 (MPEG audio
sync), ITU-T H.264 9.1 (Exp-Golomb), Elias 1975 (gamma, delta), Apostolico & Fraenkel 1987 (Fibonacci).

  container       magic-signature counts over the payload; zlib, raw DEFLATE, gzip, bzip2 and lzma/xz
                  decompression of a 65536-byte window at every byte offset below --offsets, each with
                  output capped at 1 MiB. A hit is "complete" when the decompressor reports end of
                  stream (eof), "partial" when it produced >= 1024 bytes without reaching eof.
  compressibility zlib-9 / bz2-9 / lzma-6 size ratio of the first 4 MB, and order-0 byte entropy.
  codes           per family, a whole-payload parse from bit 0, MSB first, stopping at the first
                  codeword that does not fit. Recorded separately: prefix (first --prefix-bytes bytes:
                  consumed bits, completed codewords) and whole payload (consumed bits, completed
                  codewords, residual bits, codewords minus W*H, codewords per site).
                  Families: Rice k = 0..8 with stop bit 1 or 0; Exp-Golomb order 0..6; Elias gamma;
                  Elias delta; Fibonacci.
The payload comes from orf_tokens.locate_data. These are bounded descriptive measurements. A count near one codeword per site is consistent with a
per-sample code under that parse; it does not prove the syntax, and the container screen cannot
exclude other framings, parameters or hybrid coders.
Container geometry, payload and input hash use the same file snapshot.

    python -I -B tools/code_family_screen.py FILE [FILE ...] [--shuffle]
    python -I -B tools/test_code_family_screen.py
"""
import argparse
import bz2
from collections import Counter
import hashlib
import json
import lzma
import math
import os
import random
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens  # noqa: E402

WINDOW = 65536
CAP = 1 << 20
MIN_PARTIAL = 1024
MAGIC = (("gzip", b"\x1f\x8b\x08"), ("zlib_78da", b"\x78\xda"), ("zlib_789c", b"\x78\x9c"),
         ("bzip2", b"BZh"), ("xz", b"\xfd7zXZ\x00"), ("zstd", b"\x28\xb5\x2f\xfd"),
         ("lz4", b"\x04\x22\x4d\x18"), ("flac_sync_fixed", b"\xff\xf8"),
         ("flac_sync_variable", b"\xff\xf9"), ("zip_local_header", b"PK\x03\x04"))
FAMILIES = ([("rice_stop1", k) for k in range(9)] + [("rice_stop0", k) for k in range(9)]
            + [("exp_golomb", k) for k in range(7)] + [("elias_gamma", 0), ("elias_delta", 0),
                                                         ("fibonacci", 0)])


def try_decompress(kind, chunk):
    """-> (output bytes, reached end of stream) or None on a format error."""
    try:
        if kind in ("zlib", "raw_deflate", "gzip"):
            d = zlib.decompressobj({"zlib": 15, "raw_deflate": -15, "gzip": 31}[kind])
            out = d.decompress(chunk, CAP)
        elif kind == "bzip2":
            d = bz2.BZ2Decompressor()
            out = d.decompress(chunk, max_length=CAP)
        else:
            d = lzma.LZMADecompressor()
            out = d.decompress(chunk, max_length=CAP)
    except (zlib.error, OSError, lzma.LZMAError, EOFError, ValueError):
        return None
    return len(out), bool(d.eof)


def container(p, offsets):
    hits = []
    for off in range(min(offsets, len(p))):
        chunk = p[off:off + WINDOW]
        for kind in ("zlib", "raw_deflate", "gzip", "bzip2", "lzma"):
            r = try_decompress(kind, chunk)
            if r is None:
                continue
            size, eof = r
            if eof or size >= MIN_PARTIAL:
                hits.append({"format": kind, "offset": off, "output_bytes": size,
                             "state": "complete" if eof else "partial"})
    mpeg = sum(1 for i in range(len(p) - 1) if p[i] == 0xFF and p[i + 1] & 0xE0 == 0xE0)
    return {"magic_counts": {name: p.count(sig) for name, sig in MAGIC}, "mpeg_audio_sync": mpeg,
            "offsets_tried": min(offsets, len(p)),
            "complete_hits": sum(1 for h in hits if h["state"] == "complete"),
            "partial_hits": sum(1 for h in hits if h["state"] == "partial"), "hits": hits[:20]}


def compressibility(p):
    c = p[:4000000]
    if not c:
        return None
    h0 = -sum(n / len(c) * math.log2(n / len(c)) for n in Counter(c).values())
    return {"bytes": len(c), "zlib9": round(len(zlib.compress(c, 9)) / len(c), 4),
            "bz2_9": round(len(bz2.compress(c, 9)) / len(c), 4),
            "lzma6": round(len(lzma.compress(c, preset=6)) / len(c), 4),
            "order0_bits_per_byte": round(h0, 4)}


def next_end(bits, pos, family, k):
    """End bit of the codeword starting at pos, or None if it does not fit."""
    n = len(bits)
    if family == "fibonacci":
        j = bits.find("11", pos)
        return None if j < 0 else j + 2
    j = bits.find("0" if family == "rice_stop0" else "1", pos)
    if j < 0:
        return None
    q = j - pos
    if family in ("rice_stop1", "rice_stop0"):
        end = j + 1 + k
    elif family == "exp_golomb":
        end = j + 1 + q + k
    elif family == "elias_gamma":
        end = j + 1 + q
    else:  # Elias delta: gamma-coded length L >= 1, then L - 1 bits
        if j + 1 + q > n:
            return None
        end = j + 1 + q + int(bits[j:j + 1 + q], 2) - 1
    return end if end <= n else None


def count_family(bits, family, k, prefix_bits):
    pos = count = 0
    prefix = None
    while True:
        end = next_end(bits, pos, family, k)
        if end is None:
            break
        if prefix is None and end > prefix_bits:
            prefix = (pos, count)
        pos, count = end, count + 1
    if prefix is None:
        prefix = (pos, count)
    return prefix, (pos, count)


def codes(p, sites, prefix_bytes):
    bits = bin(int.from_bytes(p, "big"))[2:].zfill(len(p) * 8) if p else ""
    prefix_bits = min(prefix_bytes, len(p)) * 8
    out = {}
    for family, k in FAMILIES:
        (pb, pc), (wb, wc) = count_family(bits, family, k, prefix_bits)
        out["%s_k%d" % (family, k)] = {
            "prefix": {"bytes": prefix_bits // 8, "consumed_bits": pb, "codewords": pc},
            "whole": {"payload_bits": len(bits), "consumed_bits": wb, "codewords": wc,
                      "residual_bits": len(bits) - wb, "codewords_minus_sites": wc - sites,
                      "codewords_per_site": round(wc / sites, 6) if sites else None}}
    return out


def analyze(p, sites, offsets, prefix_bytes):
    return {"container": container(p, offsets), "compressibility": compressibility(p),
            "codes": codes(p, sites, prefix_bytes)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--shuffle", action="store_true",
                    help="control: shuffle the payload bytes (seed --seed) before every test")
    ap.add_argument("--seed", type=int, default=20261022, help="shuffle seed (default 20261022)")
    ap.add_argument("--offsets", type=int, default=4096, help="decompression offsets tried (default 4096)")
    ap.add_argument("--prefix-bytes", type=int, default=3000000, help="prefix size reported (default 3000000)")
    a = ap.parse_args()
    if a.offsets < 0 or a.prefix_bytes < 0:
        ap.error("--offsets and --prefix-bytes must be >= 0")
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
            p = bytearray(payload)
            if a.shuffle:
                random.Random(a.seed).shuffle(p)
            r = analyze(bytes(p), w * h, a.offsets, a.prefix_bytes)
            r.update({"sha256": input_digest, "W": w, "H": h,
                      "payload_bytes": len(p), "bits_per_site": round(len(p) * 8 / (w * h), 4)})
            results.append(r)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            failures.append({"argument": n, "error": type(exc).__name__})
    with open(os.path.abspath(__file__), "rb") as f:
        source = hashlib.sha256(f.read()).hexdigest()
    print(json.dumps({"tool_sha256": source, "python": sys.version.split()[0], "shuffled": a.shuffle,
                      "seed": a.seed if a.shuffle else None, "results": results, "failures": failures},
                     indent=1))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
