"""Synthetic checks for orf_tokens.parse and pearson (no sample files)."""

import os
import sys
import unittest
import contextlib
import io
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens as t  # noqa: E402


def bits_to_bytes(bits):
    bits = bits + "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def token(q, suffix):
    return "0" * q + "1" + format(suffix, "05b")


class ParseTests(unittest.TestCase):
    def test_locate_multistrip_table_order_and_length_mismatch(self):
        data = bytes(range(20))
        for offsets, counts, expected in (([2, 5], [3, 4], data[2:9]),
                                          ([2, 12], [3, 4], data[2:5] + data[12:16]),
                                          ([12, 2], [4, 3], data[12:16] + data[2:5])):
            tags = {0x100: [5], 0x101: [4], 0x111: offsets, 0x117: counts}
            with self.subTest(offsets=offsets), patch("builtins.open", return_value=io.BytesIO(data)), \
                    patch.object(t, "Tiff") as reader:
                reader.return_value.all_ifds.return_value = [tags]
                located = t.locate("synthetic")
                self.assertEqual(located[2], expected)
                self.assertEqual(t.locate_data(data), located)
        tags = {0x100: [5], 0x101: [4], 0x111: [2, 12], 0x117: [3]}
        with patch("builtins.open", return_value=io.BytesIO(data)), patch.object(t, "Tiff") as reader:
            reader.return_value.all_ifds.return_value = [tags]
            with self.assertRaises(ValueError):
                t.locate("synthetic")

    def test_locate_rejects_short_and_overlapping_extents(self):
        data = bytes(range(20))
        for offsets, counts in (([1, 18], [4, 4]), ([1, 3], [4, 4]), ([1], [0])):
            tags = {0x100: [5], 0x101: [4], 0x111: offsets, 0x117: counts}
            with self.subTest(offsets=offsets, counts=counts), \
                    patch("builtins.open", return_value=io.BytesIO(data)), patch.object(t, "Tiff") as reader:
                reader.return_value.all_ifds.return_value = [tags]
                with self.assertRaises(ValueError):
                    t.locate("synthetic")

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

    def test_token_must_fit_payload(self):
        # (0,0), then 9 zeros and a final 1: the next token's stop bit is in the
        # payload, but its 5 suffix bits would be past the end, so it must not count.
        buf = bits_to_bytes(token(0, 0) + "0" * 9 + "1")
        qs, ss, _, pos = t.parse(buf, 99, 0)
        self.assertEqual(list(zip(qs, ss)), [(0, 0)])
        self.assertLessEqual(pos, len(buf) * 8)

    def test_report_exhausted_payload_with_six_or_seven_residual_bits(self):
        args = SimpleNamespace(stride=0, max_tokens=99, rows=None, all=True,
                               escape_extra=0, escape_landing=False)
        for residual in (6, 7):
            # One q=4/3 token uses 10/9 bits; the final stop lacks a suffix.
            payload = bits_to_bytes(token(10 - residual, 0) + "0" * (residual - 1) + "1")
            output = io.StringIO()
            with self.subTest(residual=residual), patch.object(t, "locate", return_value=(1, 1, payload)):
                with contextlib.redirect_stdout(output):
                    t.report("synthetic.ORF", args)
                self.assertIn("(whole payload)", output.getvalue())
                self.assertIn("tokens / (W*H): 1.00000", output.getvalue())

    def test_report_token_limit_remains_prefix(self):
        args = SimpleNamespace(stride=0, max_tokens=1, rows=None, all=False,
                               escape_extra=0, escape_landing=False)
        payload = bits_to_bytes(token(0, 0) * 4)
        output = io.StringIO()
        with patch.object(t, "locate", return_value=(1, 1, payload)):
            with contextlib.redirect_stdout(output):
                t.report("synthetic.ORF", args)
        self.assertIn("(prefix)", output.getvalue())
        self.assertNotIn("tokens / (W*H):", output.getvalue())

    def test_report_no_complete_tokens(self):
        args = SimpleNamespace(stride=0, max_tokens=99, rows=None, all=True,
                               escape_extra=0, escape_landing=False)
        for payload in (b"\x01", b"\x00", b""):
            output = io.StringIO()
            with self.subTest(payload=payload), patch.object(t, "locate", return_value=(1, 1, payload)):
                with contextlib.redirect_stdout(output):
                    t.report("synthetic.ORF", args)
                self.assertIn("tokens parsed: 0 (whole payload)", output.getvalue())
                self.assertIn("tokens / (W*H): 0.00000", output.getvalue())
                self.assertNotIn("q histogram", output.getvalue())

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

    def test_mi_base_rotates_short_sequences(self):
        # 5000 tokens, y a function of x: the rotated baseline must be near 0, not equal
        # to the measured MI (rotation longer than the sequence used to be a no-op)
        import random
        rng = random.Random(1)
        x = bytes(rng.randrange(4) for _ in range(5000))
        v, base, n = t.mi_base(memoryview(x), memoryview(x))
        self.assertGreater(v, 1.9)
        self.assertLess(base, 0.05)
        self.assertEqual(n, 5000)

    def test_no_row_mark_without_a_token(self):
        # two tokens then 12 zero bits (no stop bit), stride 1: two row starts, not three
        buf = bits_to_bytes(token(0, 1) + token(0, 2) + "0" * 12)
        marks, _ = t.scan(buf, 10, 1, 0, None, None, None, 40)
        self.assertEqual(marks, [0, 6])

    def test_pearson(self):
        self.assertAlmostEqual(t.pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0)
        self.assertAlmostEqual(t.pearson([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)


if __name__ == "__main__":
    unittest.main()
