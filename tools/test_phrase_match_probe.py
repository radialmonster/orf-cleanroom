"""Synthetic controls for phrase support and exact permutation means."""
import hashlib
import io
import itertools
import json
import os
import struct
import sys
import unittest
from fractions import Fraction
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import phrase_match_probe as probe


class Tests(unittest.TestCase):
    def test_exact_means_and_phrase_components(self):
        a = ('A', 'A', 'B')
        b = ('A', 'B', 'B')
        self.assertEqual(Fraction(sum(x[0] == x[1] for x in itertools.permutations(a)), 6), Fraction(1, 3))
        self.assertEqual(Fraction(sum(x[0] == y[0] for x in itertools.permutations(a) for y in itertools.permutations(b)), 36), Fraction(4, 9))
        vals = [0,0, 0,0, 1,1, 0,0, 1,1, 1,1, 0,0, 0,0, 1,1]
        rows = probe.measure([(0, x) for x in vals], 6, 0)['lags']
        self.assertEqual(rows[0]['E'], probe.rational(Fraction(10, 9)))
        self.assertEqual(rows[1]['E'], probe.rational(Fraction(4, 3)))
        self.assertEqual(rows[2]['E'], probe.rational(Fraction(5, 3)))
        self.assertEqual(rows[0]['M'], rows[0]['first_equal'])

    def test_phases_omissions_and_unknown(self):
        for phase in (0, 1):
            tokens = [(0, i % 3) for i in range(27)]
            tokens[17] = (17, 0)
            result = probe.measure(tokens, 8, phase)
            self.assertEqual(result['excluded_tail_tokens'], 3)
            self.assertGreater(result['omitted_targets'], 0)
            self.assertEqual(len({x['P'] for x in result['lags']}), 1)
            self.assertEqual(probe.measure([(17, 0)] * 24, 8, phase)['status'], 'empty_support')
        with self.assertRaises(ValueError):
            probe.measure([], 7, 0)

    def test_phase_one_block_edge_not_escape_omission(self):
        result = probe.measure([(0, 0)] * 24, 8, 1)
        self.assertEqual(result['candidate_targets'], 2)
        self.assertEqual(result['omitted_targets'], 0)
        self.assertEqual(result['retained_targets'], 2)

    def test_cli_output_and_redaction(self):
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--phase', 'discovery', '--sample', '3800', 'secret', '--sample', '1331', 'secret', '--sample', '3210', 'secret']), \
             mock.patch.object(probe, 'report', side_effect=OSError('secret')), mock.patch('sys.stdout', output):
            self.assertEqual(probe.main(), 1)
        self.assertNotIn('secret', output.getvalue())
        self.assertEqual(len(json.loads(output.getvalue())['samples']), 3)

    def test_real_locator_and_parser_synthetic_container(self):
        def fixture(n):
            bits = '100000' * n
            bits += '0' * (-len(bits) % 8)
            payload = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
            entries = [(0x100, 8), (0x101, 8), (0x111, 62), (0x117, len(payload))]
            return b'II' + struct.pack('<HIH', 0x4f52, 8, len(entries)) + b''.join(
                struct.pack('<HHII', tag, 4, 1, value) for tag, value in entries) + bytes(4) + payload
        data = fixture(64)
        digest = hashlib.sha256(data).hexdigest()
        mapping = {sid: ('public.ORF', digest) for sid in ('3800', '1331', '3210')}
        output = io.StringIO()
        with mock.patch.object(probe, 'LIMIT', 64), mock.patch.dict(probe.SAMPLES, mapping), \
             mock.patch('builtins.open', mock.mock_open(read_data=data)), \
             mock.patch.object(sys, 'argv', ['probe', '--phase', 'discovery', '--sample', '3800', 'x', '--sample', '1331', 'x', '--sample', '3210', 'x']), \
             mock.patch('sys.stdout', output):
            self.assertEqual(probe.main(), 0)
        report = json.loads(output.getvalue())['samples'][0]
        self.assertEqual((report['payload_bytes'], report['returned_tokens'], report['bits_consumed']), (48, 64, 384))
        self.assertEqual([item['phase'] for item in report['phases']], [0, 1])
        short_data = fixture(16)
        with mock.patch.object(probe, 'LIMIT', 64), \
             mock.patch.dict(probe.SAMPLES, {'3800': ('public.ORF', hashlib.sha256(short_data).hexdigest())}), \
             mock.patch('builtins.open', mock.mock_open(read_data=short_data)):
            short = probe.report('3800', 'unused')
        self.assertEqual((short['status'], short['reason'], short['returned_tokens'], short['bits_consumed']),
                         ('unknown', 'short_input', 16, 96))
        self.assertNotIn('phases', short)


if __name__ == '__main__':
    unittest.main()
