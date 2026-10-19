"""Synthetic checks for orf_tokens.parse and pearson (no sample files)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens as t  # noqa: E402


def bits_to_bytes(bits):
    bits = bits + "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def token(q, suffix):
    return "0" * q + "1" + format(suffix, "05b")


class ParseTests(unittest.TestCase):
    def test_roundtrip(self):
        spec = [(0, 5), (3, 31), (1, 0), (7, 18), (0, 1)]
        buf = bits_to_bytes("".join(token(q, s) for q, s in spec) + "1" * 16)
        qs, ss, _, _ = t.parse(buf, len(spec), 0)
        self.assertEqual(list(zip(qs, ss)), spec)

    def test_escape_position(self):
        # token (2,3), then an escape with q = 20, then token (0,9)
        bits = token(2, 3) + token(20, 7) + token(0, 9) + "1" * 16
        esc = []
        qs, ss, _, _ = t.parse(bits_to_bytes(bits), 3, 0, esc_pos=esc)
        self.assertEqual(qs, [2, 20, 0])
        self.assertEqual(esc, [(8, 20)])

    def test_pearson(self):
        self.assertAlmostEqual(t.pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0)
        self.assertAlmostEqual(t.pearson([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)


if __name__ == "__main__":
    unittest.main()
