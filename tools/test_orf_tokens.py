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

    def test_scan_matches_parse(self):
        # the compact one-byte-per-token streams used by --all equal the plain lists
        spec = [(0, 5), (3, 31), (45, 7), (1, 0), (20, 9), (0, 1)]
        buf = bits_to_bytes("".join(token(q, s) for q, s in spec) + "1" * 16)
        qs, ss, marks, pos = t.parse(buf, 99, 2)
        qa, sa, esc_q = t.array.array("B"), t.array.array("B"), t.collections.Counter()
        marks2, pos2 = t.scan(buf, 99, 2, 0, None, qa, sa, 40, esc_q, 32)
        self.assertEqual((marks, pos), (marks2, pos2))
        self.assertEqual(list(qa), [min(q, 40) for q in qs])
        self.assertEqual(list(sa), [s + 32 * (q >= t.ESC_Q) for q, s in zip(qs, ss)])
        self.assertEqual(dict(esc_q), {45: 1, 20: 1})

    def test_mi_on_views_matches_lists(self):
        xs = [(7 * i + i * i // 5) % 4 for i in range(300)]
        ys = [(3 * i + i // 7) % 8 for i in range(300)]
        for lag in (0, 1, 3):
            self.assertEqual(t.mi_base(xs, ys, lag),
                             t.mi_base(memoryview(bytes(xs)), memoryview(bytes(ys)), lag))

    def test_pearson(self):
        self.assertAlmostEqual(t.pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0)
        self.assertAlmostEqual(t.pearson([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)


if __name__ == "__main__":
    unittest.main()
