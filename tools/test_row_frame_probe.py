#!/usr/bin/env python3
"""Generated payloads for row_frame_probe: strips, chain tolerance, word bounds."""
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from row_frame_probe import analyse, analyse_payload, chain, pitch_and_tolerance  # noqa: E402

W = 40
GROUP_ROW = "10000000" * 6 + "100000" * (W - 6)   # six 8-bit fields, then 6-bit words


def to_bytes(bits):
    bits += "1" * (-len(bits) % 8)                 # pad with ones: no extra zeros or words
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def rows(n, marker="0" * 39 + "1"):
    return marker + GROUP_ROW * n


def container(strips, width, height, gap=b"\xff"):
    """Little-endian TIFF, one IFD with the given strips separated by gap."""
    n = len(strips)
    arrays_at = 8 + 2 + 12 * 4 + 4
    pos = arrays_at + 8 * n
    offsets, body = [], b""
    for i, s in enumerate(strips):
        body += gap if i else b""
        offsets.append(pos + len(body))
        body += s
    one = n == 1
    entries = [(0x100, width), (0x101, height),
               (0x111, offsets[0] if one else arrays_at),
               (0x117, len(strips[0]) if one else arrays_at + 4 * n)]
    out = b"II*\x00" + struct.pack("<IH", 8, 4)
    for tag, v in entries:
        out += struct.pack("<HHII", tag, 4, 1 if tag < 0x111 else n, v)
    out += struct.pack("<I", 0)
    out += b"".join(struct.pack("<I", o) for o in offsets)
    out += b"".join(struct.pack("<I", len(s)) for s in strips)
    return out + body


def as_dict(pairs):
    return dict(pairs)


class ChainTests(unittest.TestCase):
    def test_tolerance_is_max_64_or_one_percent(self):
        self.assertEqual(pitch_and_tolerance(40), (252, 64))
        self.assertEqual(pitch_and_tolerance(5220), (31332, 313))

    def test_selected_chain_tolerance_edges(self):
        p, b = 1000, 64
        self.assertEqual(len(chain([0, p, 2 * p + b], p, b)), 3)
        self.assertEqual(len(chain([0, p, 2 * p - b], p, b)), 3)
        self.assertEqual(chain([0, p, 2 * p + b + 1], p, b), [0, p])
        self.assertEqual(chain([0, p, 2 * p - b - 1], p, b), [0, p])

    def test_close_second_match_is_dropped(self):
        self.assertEqual(chain([0, 8, 1000, 1008], 1000, 64), [0, 1000])

    def test_no_chain(self):
        self.assertEqual(chain([], 1000, 64), [])
        self.assertEqual(chain([0], 1000, 64), [])


class PayloadTests(unittest.TestCase):
    def test_generated_rows_are_exact_under_both_readings(self):
        r = as_dict(analyse_payload(to_bytes(rows(5)), W, 5, 10))
        self.assertEqual(r["status"], "ok")
        self.assertEqual((r["selected_starts"], r["selected_intervals"]), (5, 4))
        self.assertEqual((r["intervals_exact_k5"], r["intervals_exact_head"]), (4, 4))
        self.assertEqual(r["complete_k5_minus_wh"], "+0")
        self.assertEqual(r["residual_bits"], 4)     # the four padding ones
        # the 24-bit guard stops before the last words: guarded and complete differ
        self.assertNotEqual(r["guard24_k5_minus_wh"], r["complete_k5_minus_wh"])

    def test_empty_and_all_zero_payloads(self):
        for payload in (b"", b"\0" * 64):
            r = as_dict(analyse_payload(payload, W, 5, 10))
            self.assertEqual(r["status"], "no_marker")
            self.assertEqual(r["payload_bits"], 8 * len(payload))

    def test_truncated_last_row_is_bounded(self):
        bits = rows(3)[:-3]                         # last word cut inside its suffix
        r = as_dict(analyse_payload(to_bytes(bits), W, 3, 10))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["intervals_exact_k5"], 2)
        self.assertGreater(r["residual_bits"], 0)

    def test_escape_cut_at_the_end_is_incomplete(self):
        bits = rows(2) + "0" * 12 + "1010"           # escape with 4 of 12 raw bits
        self.assertEqual(len(bits) % 8, 0)
        r = as_dict(analyse_payload(to_bytes(bits), W, 2, 10))
        self.assertEqual(r["complete_k5_minus_wh"], "+0")
        self.assertGreater(r["residual_bits"], 0)


class ContainerTests(unittest.TestCase):
    def test_separated_strips_match_the_joined_payload(self):
        payload = to_bytes(rows(4))
        cut = len(payload) // 2
        one = as_dict(analyse(container([payload], W, 4), 10))
        two = as_dict(analyse(container([payload[:cut], payload[cut:]], W, 4), 10))
        for key in ("sha256",):
            one.pop(key), two.pop(key)
        self.assertEqual(one, two)
        self.assertEqual(one["intervals_exact_k5"], 3)

    def test_overlapping_strips_are_rejected(self):
        data = bytearray(container([b"\x01\x02", b"\x03"], W, 1))
        arrays_at = 8 + 2 + 12 * 4 + 4
        first = struct.unpack_from("<I", data, arrays_at)[0]
        struct.pack_into("<I", data, arrays_at + 4, first + 1)
        with self.assertRaises(ValueError):
            analyse(bytes(data), 10)


if __name__ == "__main__":
    unittest.main()
