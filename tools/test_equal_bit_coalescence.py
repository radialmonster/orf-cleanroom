"""Synthetic equal-bit horizons and historical selection regression."""
import hashlib
import os
import struct
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import equal_bit_coalescence as p


class Tests(unittest.TestCase):
    def test_immediate_boundary_and_censor(self):
        data = bytes([255]) * 40
        r = p.side(data, 0, 320, 36)
        self.assertEqual(r['category'], 'immediate')
        self.assertEqual((r['words0'], r['words12']), (6, 4))
        self.assertEqual((r['shared_words'], r['shared_bits']), (4, 24))
        self.assertEqual(r['q0_12'] - r['q0_0'], r['pre_difference'] + r['tail_difference'])
        self.assertEqual(p.side(data, 0, 35, 36)['status'], 'censored')

    def test_none_and_partial(self):
        data = bytes([0]) * 40
        r = p.side(data, 0, 320, 36)
        self.assertEqual((r['category'], r['words0'], r['words12']), ('none', 0, 0))
        self.assertEqual((r['residual0'], r['residual12']), (36, 24))

    def test_original_selection_unchanged(self):
        bits = ('1' + '00000') * 70 + ('0' * 17 + '1' + '00000') + ('1' + '00000') * 60
        bits += '0' * (-len(bits) % 8)
        data = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
        original = p.old.measure(data, 131)
        result = p.measure(data, 131)
        self.assertEqual(result['baseline_781'], original)
        self.assertEqual(original['matched_pairs'], 1)
        for cell in result['budgets'].values():
            self.assertEqual(cell['eligibility']['eligible/eligible'], 1)
            self.assertEqual(sum(cell['joint'].values()), 1)

    def test_checked_container_report(self):
        bits = '100000' * 70 + '0' * 17 + '100000' + '100000' * 60
        bits += '0' * (-len(bits) % 8)
        payload = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
        tags = [(0x100, 32), (0x101, 32), (0x103, 1), (0x111, 74), (0x117, len(payload))]
        data = b'II' + struct.pack('<HIH', 0x4f52, 8, len(tags))
        data += b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags)
        data += bytes(4) + payload
        identity = ('public.ORF', hashlib.sha256(data).hexdigest())
        with mock.patch.dict(p.SAMPLES, {'5283': identity}), \
             mock.patch('builtins.open', mock.mock_open(read_data=data)):
            result = p.report('5283', 'unused', 131)
            self.assertEqual(p.report('5283', 'unused', 200)['status'], 'unknown')
        self.assertEqual((result['status'], result['width'], result['height']), ('ok', 32, 32))
        self.assertEqual(result['payload_bytes'], len(payload))
        self.assertEqual(result['result']['baseline_781']['matched_pairs'], 1)


if __name__ == '__main__':
    unittest.main()
