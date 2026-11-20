#!/usr/bin/env python3
"""Synthetic TIFF fixtures for the scoped patent-tag inventory."""
import hashlib
import io
import json
import os
import struct
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patent_tag_inventory as probe


def fixture(kind=1, count=4, values=b'\0\1\2\0', link=None):
    # 16x16 gives four blocks and two packed bytes including the surplus byte.
    fields = [(256, 4, 1, 16), (257, 4, 1, 16),
              (273, 4, 1, 200), (279, 4, 1, 8)]
    if kind:
        fields.append((65000, kind, count, values))
    if link is not None:
        fields.append((34665, 4, 1, link))
    data = bytearray(208)
    struct.pack_into('<2sHIH', data, 0, b'II', 42, 8, len(fields))
    for i, (tag, typ, n, value) in enumerate(fields):
        pos = 10 + i * 12
        struct.pack_into('<HHI', data, pos, tag, typ, n)
        if isinstance(value, bytes):
            data[pos + 8:pos + 12] = value.ljust(4, b'\0')
        else:
            struct.pack_into('<I', data, pos + 8, value)
    return bytes(data)


class InventoryTests(unittest.TestCase):
    def test_unpacked_and_packed(self):
        row = probe.inventory(fixture())
        self.assertEqual(row['blocks'], 4)
        self.assertTrue(row['candidates'][0]['byte_choices_0_2'])
        row = probe.inventory(fixture(count=2, values=b'\x18\xff'))
        self.assertEqual(row['candidates'][0]['packed_choices_0_2'],
                         {'msb_first': True, 'lsb_first': True})
        row = probe.inventory(fixture(count=2, values=b'\xc0\x00'))
        self.assertFalse(row['candidates'][0]['packed_choices_0_2']['msb_first'])

    def test_wrong_type_and_count(self):
        self.assertEqual(probe.inventory(fixture(kind=7))['candidates'], [])
        self.assertEqual(probe.inventory(fixture(count=3))['candidates'], [])
        self.assertFalse(probe.inventory(fixture(values=b'\0\1\3\0'))['candidates'][0]['byte_choices_0_2'])

    def test_unresolved_link_and_invalid_candidate(self):
        with self.assertRaisesRegex(ValueError, 'ifd_bounds'):
            probe.inventory(fixture(link=500))
        data = bytearray(fixture())
        # Two bytes are inline and therefore always valid; a large geometry
        # supplies an out-of-bounds indirect candidate instead.
        struct.pack_into('<I', data, 10 + 0 * 12 + 8, 32)
        struct.pack_into('<I', data, 10 + 1 * 12 + 8, 32)
        struct.pack_into('<I', data, 10 + 4 * 12 + 4, 16)
        struct.pack_into('<I', data, 10 + 4 * 12 + 8, 1000)
        self.assertFalse(probe.inventory(bytes(data))['candidates'][0]['in_bounds'])
        self.assertEqual(probe.inventory(bytes(data))['outcome'], 'unresolved')

    def test_directory_and_candidate_overlap_strip(self):
        data = bytearray(fixture())
        struct.pack_into('<I', data, 10 + 2 * 12 + 8, 0)
        with self.assertRaisesRegex(ValueError, 'invalid_strip_extent'):
            probe.inventory(bytes(data))
        data = bytearray(fixture())
        struct.pack_into('<I', data, 10 + 2 * 12 + 8, 8)
        with self.assertRaisesRegex(ValueError, 'ifd_overlaps_strip'):
            probe.inventory(bytes(data))
        data = bytearray(fixture())
        data.extend(bytes(32))
        struct.pack_into('<I', data, 10 + 0 * 12 + 8, 32)
        struct.pack_into('<I', data, 10 + 1 * 12 + 8, 32)
        struct.pack_into('<I', data, 10 + 4 * 12 + 4, 16)
        struct.pack_into('<I', data, 10 + 4 * 12 + 8, 200)
        result = probe.inventory(bytes(data))
        self.assertTrue(result['candidates'][0]['in_bounds'])
        self.assertTrue(result['candidates'][0]['strip_overlap'])
        self.assertEqual(result['outcome'], 'unresolved')

    def test_cli_geometry_mismatch_hides_unverified_outcome(self):
        data = fixture()
        digest = hashlib.sha256(data).hexdigest()
        samples = {'1993': (digest, (16, 16), 'fixture a'),
                   '1994': (digest, (32, 16), 'fixture b')}
        arguments = ['--phase', 'discovery', '--sample', '1993', 'file-a',
                     '--sample', '1994', 'file-b']
        output = io.StringIO()
        with patch.object(probe, 'SAMPLES', samples), \
                patch('builtins.open', side_effect=lambda _path, _mode: io.BytesIO(data)), \
                redirect_stdout(output):
            self.assertEqual(probe.main(arguments), 1)
        first, second = json.loads(output.getvalue())['results']
        self.assertEqual(first['outcome'], 'compatible')
        self.assertEqual(second['status'], 'unknown')
        self.assertEqual(second['reason'], 'geometry_mismatch')
        self.assertNotIn('outcome', second)


if __name__ == '__main__':
    unittest.main()
