"""Synthetic cost/phase and complete CLI checks for literal descriptions."""
import hashlib
import io
import json
import os
import random
import struct
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import literal_repeat_probe as p


class Tests(unittest.TestCase):
    def test_all_periods_against_literal_encoder(self):
        rng = random.Random(339)
        data = bytes(rng.randrange(256) for _ in range(83))
        bits = p.bit_string(data)
        for start in (0, 7, 131):
            for period in range(1, 257):
                template = p.template_for(bits, start, period)
                expected_template = ''.join('1' if sum(bits[i] == '1' for i in range(len(bits)) if (start+i) % period == r) * 2 > sum((start+i) % period == r for i in range(len(bits))) else '0' for r in range(period))
                self.assertEqual(template, expected_template)
                actual = p.description(data, start, template, chunk_bytes=11)
                positions = [i for i, bit in enumerate(bits) if bit != template[(start+i) % period]]
                previous = -1
                gap_bits = 0
                for i in positions:
                    gap_bits += 2 * (i-previous).bit_length() - 1
                    previous = i
                unpadded = 136 + period + gap_bits
                self.assertEqual(actual['charged_bits'], unpadded + (-unpadded) % 8)
                self.assertEqual(actual['exception_count'], len(positions))

    def test_ties_phase_and_bounds(self):
        self.assertEqual(p.template_for('01', 0, 1), '0')
        with self.assertRaises(ValueError):
            p.description(b'\0', 2**64, '0')
        with mock.patch.object(p, 'WINDOW', 4), mock.patch.dict(p.OFFSETS, {'discovery': (8, 16)}):
            with self.assertRaises(ValueError):
                p.intervals(bytes(19), '0', 'discovery')

    def test_synthetic_container_cli(self):
        payload = bytes([0xaa, 0x55]) * 40
        entries = [(0x100, 8), (0x101, 8), (0x111, 62), (0x117, len(payload))]
        data = b'II' + struct.pack('<HIH', 0x4f52, 8, 4) + b''.join(struct.pack('<HHII', tag, 4, 1, v) for tag, v in entries) + bytes(4) + payload
        digest = hashlib.sha256(data).hexdigest()
        output = io.StringIO()
        with mock.patch.object(p, 'WINDOW', 4), mock.patch.dict(p.OFFSETS, {'discovery': (8, 16)}), \
             mock.patch.dict(p.SAMPLES, {'PA210010.ORF': digest, 'PA200010.ORF': digest}), \
             mock.patch('builtins.open', mock.mock_open(read_data=data)), \
             mock.patch.object(sys, 'argv', ['probe', '--phase', 'discovery', '--sample', 'PA210010.ORF', 'unused']), \
             mock.patch('sys.stdout', output):
            self.assertEqual(p.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(len(report['training']['costs_period_1_to_256']), 256)
        self.assertEqual(report['samples'][0]['payload_bytes'], 80)
        self.assertEqual(len(report['samples']), 1)
        self.assertIsInstance(report['discovery_window_decision'], bool)
        self.assertNotIn('template', report['training'])


if __name__ == '__main__':
    unittest.main()
