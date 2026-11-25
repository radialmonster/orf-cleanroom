"""Synthetic base, overlap and strict inner-shape controls."""
import os
import struct
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import legacy_block_shape as p


def directory(data, at, entries):
    struct.pack_into('<H', data, at, len(entries))
    for i, (tag, typ, n, value) in enumerate(entries):
        struct.pack_into('<HHII', data, at+2+12*i, tag, typ, n, value)
    struct.pack_into('<I', data, at+2+12*len(entries), 0)


def fixture(base_type='absolute', header=b'OLYMP\0\x02\0', absent=False):
    data = bytearray(1200)
    data[:8] = b'IIRO' + struct.pack('<I', 8)
    directory(data, 8, [(0x8769, 4, 1, 64)])
    directory(data, 64, [(0x927c, 7, 600, 200)])
    data[200:208] = header
    entries = [] if absent else [(0x2040, 7, 32, 400 if base_type == 'absolute' else 200),
                                (0x2050, 7, 32, 500 if base_type == 'absolute' else 300)]
    directory(data, 208, entries)
    directory(data, 400, [(1, 3, 1, 7)])
    directory(data, 500, [(2, 4, 1, 8)])
    return bytes(data)


class Tests(unittest.TestCase):
    def test_unique_bases_and_ambiguity(self):
        entries = {0x2040: (7, 32, 400), 0x2050: (7, 32, 500)}
        result = p.bases(200, 600, 38, entries, [])
        self.assertEqual(result['status'], 'ambiguous')
        self.assertEqual(p.bases(200, 400, 38, entries, [])['selected'], 'absolute')
        entries = {0x2040: (7, 32, 200), 0x2050: (7, 32, 300)}
        self.assertEqual(p.bases(200, 400, 38, entries, [])['selected'], 'makernote_relative')

    def test_unavailable_and_overlap(self):
        self.assertEqual(p.bases(200, 400, 38, {}, [])['reason'], 'top_entry_absent')
        entries = {0x2040: (7, 32, 400), 0x2050: (7, 32, 410)}
        self.assertEqual(p.bases(200, 400, 38, entries, [])['status'], 'no_common_base')
        entries = {0x2040: (7, 32, 220), 0x2050: (7, 32, 300)}
        self.assertIn('header_or_top_overlap', p.bases(200, 400, 38, entries, [])['candidates']['absolute']['reasons'])
        entries = {0x2040: (7, 32, 400), 0x2050: (7, 32, 500)}
        self.assertIn('strip_overlap', p.bases(200, 600, 38, entries, [(400, 410)])['candidates']['absolute']['reasons'])

    def test_inner_shape_failures(self):
        block = bytearray(48)
        directory(block, 0, [(1, 3, 1, 7)])
        self.assertEqual(p.shape(block, 'little')['status'], 'match')
        struct.pack_into('<I', block, 10, 17)
        struct.pack_into('<H', block, 4, 5)
        bad = p.shape(block, 'little')
        self.assertEqual((bad['reason'], bad['entry_count'], bad['required_table_bytes'], bad['failed_entry']),
                         ('value_bounds', 1, 18, 0))
        self.assertEqual(p.shape(bytes(32), 'little')['reason'], 'entry_count')

    def test_declared_absence_and_unsupported_header(self):
        geo = {'width': 10, 'height': 10, 'strip_offsets': [1000], 'strip_byte_counts': [20]}
        with mock.patch.object(p, 'independent_strips', return_value=(geo, b'')):
            with mock.patch.object(p, 'shape', side_effect=AssertionError('inner was read')):
                self.assertEqual(p.measure(fixture(absent=True))['extent_comparison']['reason'], 'top_entry_absent')
                self.assertEqual(p.measure(fixture(header=b'UNKNOWN!'))['status'], 'unsupported_header')


if __name__ == '__main__':
    unittest.main()
