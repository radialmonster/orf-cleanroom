#!/usr/bin/env python3
"""Lead #339 code_family_screen tests: synthetic bytes only."""
import bz2
import contextlib
import gzip
import hashlib
import io
import json
import os
import struct
import sys
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code_family_screen as screen  # noqa: E402


def pack(bits):
    return bytes(int((bits + "0" * 7)[i:i + 8], 2) for i in range(0, len(bits), 8))


class Codes(unittest.TestCase):
    def test_cli_hash_and_payload_share_one_input_snapshot(self):
        def tiff(payload):
            tags = ((256, 8), (257, 8), (273, 62), (279, len(payload)))
            return (b'II' + struct.pack('<HIH', 42, 8, 4)
                    + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags)
                    + bytes(4) + payload)
        first, second = tiff(b'\xff\xff'), tiff(b'\x80\x00')
        original_open, reads = open, []
        def open_input(path, *args, **kwargs):
            if path == 'synthetic':
                reads.append(path)
                return io.BytesIO(first if len(reads) == 1 else second)
            return original_open(path, *args, **kwargs)
        output = io.StringIO()
        with patch.object(sys, 'argv', ['probe', 'synthetic', '--offsets', '0']), \
             patch('builtins.open', side_effect=open_input), contextlib.redirect_stdout(output):
            self.assertEqual(screen.main(), 0)
        result = json.loads(output.getvalue())['results'][0]
        self.assertEqual(len(reads), 1)
        self.assertEqual(result['sha256'], hashlib.sha256(first).hexdigest())
        self.assertEqual(result['codes'], screen.codes(b'\xff\xff', 64, 3000000))

    def counts(self, bits, family, k, prefix_bits=10 ** 9):
        return screen.count_family(bits, family, k, prefix_bits)

    def test_rice(self):
        bits = "1" + "00000" + "001" + "11111" + "01" + "000"  # two k=5 codewords, then one that does not fit
        self.assertEqual(self.counts(bits, "rice_stop1", 5)[1], (14, 2))
        bits = "100000" + "00111111" + "0100000"
        self.assertEqual(self.counts(bits, "rice_stop1", 5)[1], (21, 3))

    def test_rice_stop0(self):
        # k=2 with ones as the unary run: 0|10, 10|11, 0|00
        self.assertEqual(self.counts("010" + "1011" + "000", "rice_stop0", 2)[1], (10, 3))

    def test_exp_golomb_and_gamma(self):
        # order-0 Exp-Golomb: 1, 010, 011, 00100
        self.assertEqual(self.counts("1" + "010" + "011" + "00100", "exp_golomb", 0)[1], (12, 4))
        self.assertEqual(self.counts("1" + "010" + "011" + "00100", "elias_gamma", 0)[1], (12, 4))
        # order-2: 1xx, 01xxx
        self.assertEqual(self.counts("110" + "01011", "exp_golomb", 2)[1], (8, 2))

    def test_elias_delta(self):
        # 1 -> "1"; 2 -> "0100"; 4 -> "01100" ; 5 -> "01101"
        self.assertEqual(self.counts("1" + "0100" + "01100" + "01101", "elias_delta", 0)[1], (15, 4))
        # a long zero run whose length field overruns the payload stops at bit 0
        self.assertEqual(self.counts("0" * 39 + "1" + "0" * 30, "elias_delta", 0)[1], (0, 0))

    def test_fibonacci(self):
        self.assertEqual(self.counts("11" + "011" + "0011" + "0", "fibonacci", 0)[1], (9, 3))

    def test_prefix_snapshot(self):
        bits = "100000" * 10
        (pb, pc), (wb, wc) = self.counts(bits, "rice_stop1", 5, prefix_bits=20)
        self.assertEqual((pb, pc, wb, wc), (18, 3, 60, 10))

    def test_codes_record(self):
        rec = screen.codes(pack("100000" * 8), 8, 3)["rice_stop1_k5"]
        self.assertEqual(rec["prefix"], {"bytes": 3, "consumed_bits": 24, "codewords": 4})
        self.assertEqual(rec["whole"]["codewords"], 8)
        self.assertEqual(rec["whole"]["codewords_minus_sites"], 0)
        self.assertEqual(rec["whole"]["residual_bits"], 0)


class Container(unittest.TestCase):
    def test_complete_and_partial_states(self):
        raw = bytes(range(256)) * 64
        for kind, blob in (("zlib", zlib.compress(raw)), ("gzip", gzip.compress(raw)),
                           ("bzip2", bz2.compress(raw))):
            size, eof = screen.try_decompress(kind, blob)
            self.assertEqual((size, eof), (len(raw), True), kind)
            size, eof = screen.try_decompress(kind, blob[:len(blob) // 2])
            self.assertFalse(eof, kind)

    def test_output_cap(self):
        blob = bz2.compress(b"\0" * (3 * screen.CAP))
        size, eof = screen.try_decompress("bzip2", blob)
        self.assertEqual(size, screen.CAP)
        self.assertFalse(eof)

    def test_screen_finds_embedded_stream(self):
        raw = bytes(range(256)) * 16
        p = b"\x01\x02\x03" + zlib.compress(raw) + b"\x00" * 10
        c = screen.container(p, 8)
        self.assertIn({"format": "zlib", "offset": 3, "output_bytes": len(raw), "state": "complete"},
                      c["hits"])
        self.assertEqual(c["magic_counts"]["zlib_789c"], 1)

    def test_garbage_has_no_hits(self):
        c = screen.container(bytes([0x80, 0x00]) * 600, 64)
        self.assertEqual((c["complete_hits"], c["partial_hits"]), (0, 0))


if __name__ == "__main__":
    unittest.main()
