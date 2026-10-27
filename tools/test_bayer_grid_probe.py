#!/usr/bin/env python3
"""Lead #338 bayer_grid_probe tests: synthetic payloads only."""
import os
import contextlib
import hashlib
import io
import json
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bayer_grid_probe as probe  # noqa: E402


def pack(tokens):
    """(q, suffix) tokens -> payload bytes, zero-padded at the end."""
    bits = "".join("0" * q + "1" + format(s, "05b") for q, s in tokens)
    bits += "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def checkerboard(width, height):
    return [(0, 0 if (i // width + i % width) % 2 else 8) for i in range(width * height)]


class Tests(unittest.TestCase):
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
        with patch.object(sys, 'argv', ['probe', 'synthetic', '--window', '0:1']), \
             patch('builtins.open', side_effect=open_input), contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(), 0)
        result = json.loads(output.getvalue())['results'][0]
        self.assertEqual(len(reads), 1)
        self.assertEqual(result['sha256'], hashlib.sha256(first).hexdigest())
        self.assertEqual(result['whole_payload']['tokens'], len(probe.parse(b'\xff\xff')[0]))

    def test_parse_counts_and_residual(self):
        toks = [(39, 0), (2, 5), (17, 31), (0, 1)]
        qs, ss, used = probe.parse(pack(toks))
        self.assertEqual(list(qs), [39, 2, 17, 0])
        self.assertEqual(list(ss), [probe.ESCAPE, 5, probe.ESCAPE, 1])
        self.assertEqual(used, 45 + 8 + 23 + 6)

    def test_incomplete_final_token_rejected(self):
        payload = bytes([0x8C, 0x10])  # 100011, then 00000 1 with only 4 bits after the stop bit
        qs, ss, used = probe.parse(payload)
        self.assertEqual(list(qs), [0])
        self.assertEqual(used, 6)

    def test_checkerboard_grid(self):
        w, h = 8, 12
        r = probe.analyze(pack(checkerboard(w, h)), w, h, 10 ** 6, 1, [(2, 6)], 0, 6)
        toks = checkerboard(w, h)
        for g in r["grid_real"]:
            # Direct oracle; row wrap-around pairs are included, as in the probe.
            pairs = [(toks[i][1], toks[i - g["lag"]][1]) for i in range(4 * w, w * h)]
            self.assertEqual((g["P"], g["M"]), (len(pairs), sum(a == b for a, b in pairs)))
        rates = {(g["dy"], g["dx"]): g["rate"] for g in r["grid_real"]}
        self.assertEqual(rates[(1, 0)], 0.0)
        self.assertEqual(rates[(2, 0)], 1.0)
        self.assertEqual(rates[(0, 1)], 0.125)  # only the row wrap-around pair matches
        self.assertEqual(r["whole_payload"]["tokens_minus_sites"], 0)
        cells = r["site_tables"][0]["cells"]
        self.assertEqual(cells["00"]["top"][0], [0, 8, 8])
        self.assertEqual(cells["01"]["top"][0], [0, 0, 8])
        self.assertTrue(r["site_tables"][0]["complete"])

    def test_shuffle_keeps_block_histograms_and_escapes(self):
        ss = probe.array("B", [1, 2, probe.ESCAPE, 3, 4, 5, 6, probe.ESCAPE])
        out = probe.shuffled(ss, 4, 7)
        self.assertEqual(sorted(out[:4]), sorted(ss[:4]))
        self.assertEqual(sorted(out[4:]), sorted(ss[4:]))
        self.assertEqual(out[2], probe.ESCAPE)
        self.assertEqual(out[7], probe.ESCAPE)
        self.assertEqual(list(probe.shuffled(ss, 4, 7)), list(out))

    def test_large_q_and_incomplete_window(self):
        w, h = 4, 6
        toks = [(9, 0)] + checkerboard(w, h)[1:]
        r = probe.analyze(pack(toks), w, h, 100, 1, [(4, 9)], 0, 6)
        self.assertEqual(r["large_q"]["count"], 1)
        self.assertEqual(r["large_q"]["first"], [[0, 9]])
        self.assertFalse(r["site_tables"][0]["complete"])


if __name__ == "__main__":
    unittest.main()
