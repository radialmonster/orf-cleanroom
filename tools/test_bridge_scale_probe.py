"""Synthetic common-support, pooled arithmetic and container checks."""
import hashlib
import itertools
import os
import struct
import sys
import unittest
from fractions import Fraction
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge_scale_probe as p


def fixture(n):
    bits = ''.join('1' + format(i % 32, '05b') for i in range(n))
    bits += '0' * (-len(bits) % 8)
    payload = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    entries = [(0x100, 32), (0x101, 32), (0x111, 62), (0x117, len(payload))]
    return b'II' + struct.pack('<HIH', 0x4f52, 8, len(entries)) + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in entries) + bytes(4) + payload


class Tests(unittest.TestCase):
    def test_support_and_legacy(self):
        tokens = [(0, i % 32) for i in range(1024)]
        tokens[511] = (17, 0)
        with mock.patch.object(p, 'LIMIT', 1024):
            result = p.measure(tokens)
        self.assertEqual(result['superblock_keep'], [False, True])
        self.assertEqual(len(result['cells']), 15)
        for cell in result['cells']:
            self.assertEqual(cell['blocks'], 512 // cell['scale'])
            if cell['scale'] == 128:
                terms = []
                for start in range(512, 1024, 128):
                    _, a, v = p.legacy.bridge_energy_terms([p.legacy.map_suffix(s, cell['mapping']) for _, s in tokens[start:start+128]])
                    terms.append((a, v))
                self.assertEqual((cell['sum_A'], cell['sum_V']), (sum(a for a, _ in terms), sum(v for _, v in terms)))

    def test_exact_enumeration_and_unknown(self):
        values = [0, 0, 1, 2]
        n, a, v = p.legacy.bridge_energy_terms(values)
        expected = sum((p.legacy.energies(n, p.legacy.bridge_energy_terms(x)[1], v)[0] for x in itertools.permutations(values)), Fraction()) / 24
        self.assertEqual(expected, p.legacy.energies(n, a, v)[1])
        with mock.patch.object(p, 'LIMIT', 512):
            constant = p.measure([(0, 0)] * 512)
            self.assertTrue(all(c['R'] is None and c['zero_variance_blocks'] == c['blocks'] for c in constant['cells']))
            self.assertEqual(p.measure([(17, 0)] * 512)['status'], 'unknown_empty')
            self.assertEqual(p.measure([])['status'], 'unknown_short')

    def test_real_locator_parser_and_short(self):
        data = fixture(512)
        with mock.patch.object(p, 'LIMIT', 512), mock.patch.dict(p.SAMPLES, {'1993': ('public', hashlib.sha256(data).hexdigest())}), \
             mock.patch('builtins.open', mock.mock_open(read_data=data)):
            result = p.report('1993', 'unused')
        self.assertEqual((result['status'], result['returned_tokens'], result['bits_consumed'], result['payload_bytes']), ('ok', 512, 3072, 384))
        data = fixture(16)
        with mock.patch.object(p, 'LIMIT', 512), mock.patch.dict(p.SAMPLES, {'1993': ('public', hashlib.sha256(data).hexdigest())}), \
             mock.patch('builtins.open', mock.mock_open(read_data=data)):
            result = p.report('1993', 'unused')
        self.assertEqual((result['reason'], result['returned_tokens']), ('short_input', 16))


if __name__ == '__main__':
    unittest.main()
