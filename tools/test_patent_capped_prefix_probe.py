#!/usr/bin/env python3
"""Synthetic bounded-prefix and marker checks; no sample access."""
import unittest
import random
import hashlib
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patent_capped_prefix_probe import parse, shuffled_tail


def packed(bits):
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


def marker(d):
    return '0' * (8 * ((12 + 2 * d) // 8) + 7) + '1'


def word(q, suffix, d):
    if q < 12:
        return '0' * q + '1' + format(suffix, '05b')
    return '0' * 12 + format((q << 5) | suffix, '0%db' % d)


class TestPatentPrefix(unittest.TestCase):
    def test_both_widths_and_escape_boundary(self):
        for d in (12, 15):
            payload = packed(marker(d) + word(0, 0, d) + word(11, 22, d) + word(12, 0, d) + word((1 << (d-5))-1, 31, d))
            result = parse(payload, d, 4)
            self.assertTrue(result['marker_matches'])
            self.assertEqual((result['words'], result['ordinary_words'], result['escape_words']), (4, 2, 2))
            self.assertEqual(result['consumed_bits'], len(marker(d)) + 6 + 17 + 2*(12+d))
            self.assertIn(result['stop'], ('limit', 'end'))

    def test_invalid_escape_has_no_phantom_word(self):
        for d in (12, 15):
            data = packed(marker(d) + '0'*12 + format(11 << 5, '0%db' % d))
            result = parse(data, d)
            self.assertEqual(result['stop'], 'invalid_escape')
            self.assertEqual((result['words'], result['consumed_bits']), (0, len(marker(d))))
            self.assertEqual((result['stop_at_bits'], result['invalid_escape_value']), (len(marker(d)), 11 << 5))

    def test_truncated_branches(self):
        for d in (12, 15):
            self.assertEqual(parse(packed(marker(d)) + b'\x00', d)['stop'], 'truncated_ordinary')
            self.assertEqual(parse(packed(marker(d)) + b'\x00\x00', d)['stop'], 'truncated_escape')

    def test_wrong_marker_and_limit(self):
        self.assertEqual(parse(bytes(6), 15)['stop'], 'marker_missing')
        self.assertEqual(parse(packed('1' + marker(15)), 15)['stop'], 'marker_missing')
        self.assertEqual(parse(packed(marker(12)), 15)['stop'], 'marker_missing')
        data = packed(marker(15) + word(0, 1, 15) * 4)
        r = parse(data, 15, 1)
        self.assertEqual((r['stop'], r['words'], r['consumed_bits']), ('limit', 1, 54))
        self.assertEqual(r['residual_bits'], len(data)*8-54)

    def test_random_tail_can_pass_without_invalid_escape(self):
        rng = random.Random(17)
        tail = ''.join(str(rng.randrange(2)) for _ in range(2048))
        result = parse(packed(marker(15) + tail), 15)
        self.assertNotEqual(result['stop'], 'invalid_escape')
        self.assertGreater(result['words'], 0)

    def test_fixed_marker_preserving_full_tail_shuffle(self):
        data = bytes(range(16))
        actual = shuffled_tail(data, 12, 20261022)
        self.assertEqual(actual.hex(), '0001020304080c0b0d0e060507090a0f')
        self.assertEqual(hashlib.sha256(actual).hexdigest(),
                         'b6d5accd093b88304a98082d507d4f9ea2193411c6bf9f491af48d59e0e04157')
        self.assertEqual(actual[:5], data[:5])
        self.assertEqual(sorted(actual[5:]), sorted(data[5:]))
        self.assertEqual(actual, shuffled_tail(data, 12, 20261022))
        other = shuffled_tail(data, 15, 20261022)
        self.assertEqual(other[:6], data[:6])
        self.assertEqual(sorted(other[6:]), sorted(data[6:]))

    def test_exact_end_and_parameter_validation(self):
        data = packed(marker(12) + word(2, 0, 12))
        r = parse(data, 12)
        self.assertEqual((r['stop'], r['words'], r['residual_bits']), ('end', 1, 0))
        with self.assertRaises(ValueError): parse(data, 14)
        with self.assertRaises(ValueError): parse(data, 12, 0)


if __name__ == '__main__':
    unittest.main()
