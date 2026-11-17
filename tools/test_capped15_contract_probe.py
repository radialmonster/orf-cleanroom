"""Synthetic byte-stream tests for fixed A15 contract; no camera input."""
import os
import random
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capped15_contract_probe as probe
import patent_capped_prefix_probe as legacy


def encode(values, cap=15):
    bits = '0' * (8 * ((cap + 24) // 8) + 7) + '1'
    for v in values:
        q = v >> 5
        bits += ('0' * q + '1' + format(v & 31, '05b') if q < cap else
                 '0' * cap + format(v, '012b'))
    return bits


def pack(bits):
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


class Synthetic(unittest.TestCase):
    def test_values_and_end(self):
        rng = random.Random(19760315)
        for _ in range(200):
            seq = [rng.randrange(4096) for _ in range(20)]
            bits = encode(seq)
            bits += '1' * (-len(bits) % 8)
            got = probe.scan(pack(bits), len(seq))
            self.assertEqual(got['completed'], len(seq))
            self.assertEqual(got['completed_endpoint'], len(encode(seq)))
            self.assertEqual(got['unread_bits'], len(bits) - len(encode(seq)))
            self.assertEqual(got['status'], 'strict_end' if len(bits) == len(encode(seq)) else 'remaining_bits')

    def test_invalid_and_truncated_at_known_boundaries(self):
        mark = '0' * 39 + '1'
        invalid = mark + '0' * 15 + '0' * 12 + '1' * 5
        got = probe.scan(pack(invalid), 1)
        self.assertEqual((got['status'], got['completed_endpoint'], got['word_start'],
                          got['examined_position'], got['invalid_value']),
                         ('invalid_escape', 40, 40, 67, 0))
        for suffix, expected in [('', 'truncated_ordinary'), ('0' * 16, 'truncated_escape'),
                                 ('1' + '0' * 7, 'truncated_ordinary')]:
            bits = mark + suffix
            count = 2 if suffix.startswith('1') else 1
            self.assertEqual(probe.scan(pack(bits), count)['status'], expected)
        self.assertEqual(probe.scan(b'\0' * 4, 1)['status'], 'truncated_marker')
        self.assertEqual(probe.scan(b'\0' * 5, 1)['status'], 'marker_mismatch')

    def test_old_a12_tool_untouched(self):
        bits = encode([0, 0, 0, 0], cap=12)
        old = legacy.parse(pack(bits), 12, 4)
        self.assertEqual((old['words'], old['consumed_bits'], old['stop']), (4, 64, 'end'))

    def test_capped_values_at_unaligned_word_starts(self):
        for prior in (0, 32):
            prefix = encode([prior])
            self.assertIn(len(prefix) % 8, (6, 7))
            for invalid_value in (17, 31, 479):
                bits = prefix + '0' * 15 + format(invalid_value, '012b')
                bits += '1' * (-len(bits) % 8)
                got = probe.scan(pack(bits), 2)
                self.assertEqual((got['status'], got['invalid_value'], got['word_start']),
                                 ('invalid_escape', invalid_value, len(prefix)))
            for value in (481, 2049, 4095):
                bits = encode([prior, value])
                bits += '1' * (-len(bits) % 8)
                got = probe.scan(pack(bits), 2)
                self.assertEqual(got['completed'], 2)
                self.assertEqual(got['escapes'], 1)
                self.assertEqual(got['completed_endpoint'], len(encode([prior, value])))

    def test_metadata_rejects_bad_counts(self):
        class Fake:
            def __init__(self, data):
                pass
            def all_ifds(self):
                return [{0x117: None}, {0x117: [24], 0x111: [0], 0x100: [5240], 0x101: [3912]}]
        with mock.patch.object(probe, 'Tiff', Fake):
            with self.assertRaises(ValueError):
                probe.locate(b'\0' * 24)


if __name__ == '__main__':
    unittest.main()
