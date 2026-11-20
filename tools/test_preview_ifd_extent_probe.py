#!/usr/bin/env python3
"""Generated TIFF/JPEG extent cases, without image decoding."""
import os
import struct
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_ifd_extent_probe as probe


def jpeg():
    # Minimal marker-structured stream with one 1000x1000 SOF0 and scan.
    return (b'\xff\xd8\xff\xc0\x00\x0b\x08\x03\xe8\x03\xe8\x01\x01\x11\x00'
            b'\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\x12\xff\x00\x34\xff\xd0\x12\xff\xd9')


def fixture(fields, extra=b''):
    image = jpeg()
    offset = 100
    data = bytearray(100)
    struct.pack_into('<2sHIH', data, 0, b'II', 42, 8, len(fields))
    for i, (tag, typ, count, value) in enumerate(fields):
        if value == 'offset':
            value = offset
        elif value == 'length':
            value = len(image)
        struct.pack_into('<HHII', data, 10 + i * 12, tag, typ, count, value)
    return bytes(data) + image + extra


class Tests(unittest.TestCase):
    def test_exact_and_absent(self):
        pair = [(513, 4, 1, 'offset'), (514, 4, 1, 'length')]
        self.assertEqual(probe.measure(fixture(pair))['classification'], 'exact_match')
        self.assertEqual(probe.measure(fixture([]))['classification'], 'no_declared_pair')

    def test_disabled_or_orphan(self):
        row = probe.measure(fixture([(513, 4, 1, 0), (514, 4, 1, 123)]))
        self.assertEqual(row['disabled_offsets'], 1)
        row = probe.measure(fixture([(514, 4, 1, 123)]))
        self.assertEqual(row['orphan_lengths'], 1)

    def test_incomplete_or_wrong_type(self):
        for fields in ([(513, 4, 1, 'offset')],
                       [(513, 3, 1, 'offset'), (514, 4, 1, 'length')]):
            with self.assertRaises(ValueError):
                probe.measure(fixture(fields))

    def test_same_start_longer_declared_extent(self):
        data = fixture([(513, 4, 1, 'offset'), (514, 4, 1, len(jpeg()) + 2)], b'zz')
        row = probe.measure(data)
        self.assertEqual(row['classification'], 'same_start_different_length')
        self.assertEqual(row['declared'][0]['marker_status'], 'trailing_after_eoi')

    def test_missing_eoi_and_out_of_bounds(self):
        with self.assertRaises(ValueError):
            probe.measure(fixture([])[:-2])
        row = probe.measure(fixture([(513, 4, 1, 'offset'), (514, 4, 1, 9999)]))
        self.assertEqual(row['classification'], 'unknown_declared_marker')
        self.assertEqual(row['declared'][0]['marker_reason'], 'jpeg_bounds')


if __name__ == '__main__':
    unittest.main()
