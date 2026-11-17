"""Synthetic independent enumeration and partition checks; no sample reads."""
import itertools
import contextlib
import hashlib
import io
import json
import os
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import free_anchor_second_order as probe


def brute(values, maximum):
    if len(values) < 2:
        return True
    for first in range(maximum + 1):
        for second in range(maximum + 1):
            a, b = first, second
            for e in values[2:]:
                a, b = b, 2 * b - a + e
                if not 0 <= b <= maximum:
                    break
            else:
                return True
    return False


def dp(values, maximum):
    costs = [0] + [len(values) + 1] * len(values)
    for end in range(1, len(values) + 1):
        costs[end] = min(costs[start] + 1 for start in range(end)
                         if brute(values[start:end], maximum))
    return costs[-1]


class Synthetic(unittest.TestCase):
    def test_generated_tiff_cli_and_shortfall(self):
        bits = '100000' * 15
        payload = int(bits + '0' * (-len(bits) % 8), 2).to_bytes((len(bits) + 7) // 8, 'big')
        tags = ((256, 100), (257, 1), (259, 1), (273, 74), (279, len(payload)))
        fixture = (b'II' + struct.pack('<HIH', 42, 8, len(tags))
                   + b''.join(struct.pack('<HHII', tag[0], 4, 1, tag[1]) for tag in tags)
                   + struct.pack('<I', 0) + payload)
        real_open = open
        def open_fixture(path, *args, **kwargs):
            return io.BytesIO(fixture) if path == 'fixture' else real_open(path, *args, **kwargs)
        output = io.StringIO()
        argv = ['probe', '--sample', '1', 'public.ORF', 'fixture']
        with mock.patch.object(probe, 'WINDOW', 4), mock.patch.object(probe, 'STARTS', (0, 4, 8, 12)), \
             mock.patch.object(sys, 'argv', argv), mock.patch('builtins.open', side_effect=open_fixture), \
             contextlib.redirect_stdout(output):
            status = probe.main()
        report = json.loads(output.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(report['sample']['sha256'], hashlib.sha256(fixture).hexdigest())
        self.assertEqual([w['returned_tokens'] for w in report['sample']['windows']], [4, 4, 4, 3])
        self.assertTrue(all(f['segments'] is None for f in report['sample']['windows'][-1]['families']))
        self.assertEqual(len(report['sample']['windows'][0]['families']), 8)

    def test_exhaustive_greedy_against_anchor_and_partition_oracles(self):
        for maximum in (0, 1, 3):
            for length in range(7):
                for values in itertools.product((-2, 0, 2), repeat=length):
                    self.assertEqual(probe.segments(values, maximum), dp(values, maximum))
                    if values:
                        self.assertEqual(probe.segments(values, maximum) == 1, brute(values, maximum))

    def test_mapping_and_escapes(self):
        for s in range(32):
            self.assertEqual(probe.mapped(s, 'signed_digit'), 4 * (s // 8) + s % 4 - (8 if s % 8 >= 4 else 0))
            self.assertEqual(probe.mapped(s, 'signed_low3'), s % 8 - (8 if s % 8 >= 4 else 0))
        for tokens, requested in (([(0, 0), (17, 1)], 2), ([(0, 0)], 2), ([], 0)):
            result = probe.measure(tokens, requested)
            self.assertTrue(all(f['segments'] is None and f['at_most_two_each'] is None for f in result['families']))

    def test_parity_and_vacuous(self):
        self.assertEqual([probe.segments([], 3), probe.segments([7], 3), probe.segments([7, 7], 3)], [0, 1, 1])
        tokens = [(0, s) for s in (0, 1, 2, 3, 4)]
        families = probe.measure(tokens, 5)['families']
        self.assertTrue(all(f['lane_lengths'] == ([5] if f['stride'] == 1 else [3, 2]) for f in families))
        self.assertTrue(all(f['vacuous_lanes'] == ([False] if f['stride'] == 1 else [False, True]) for f in families))
        for f in families:
            values = [probe.mapped(s, f['mapping']) for _, s in tokens]
            self.assertEqual(f['segments'], [dp(values[i::f['stride']], (1 << f['bits']) - 1) for i in range(f['stride'])])

    def test_slope_and_bounds(self):
        self.assertEqual(probe.segments([0, 0, 1, 1, 1], 6), 1)
        self.assertGreater(probe.segments([0, 0, 8], 3), 1)
        with self.assertRaises(ValueError):
            probe.segments([], -1)
        with mock.patch.object(probe.time, 'monotonic', return_value=10):
            with self.assertRaises(TimeoutError):
                probe.segments([0, 0], 3, deadline=10)
            result = probe.measure([(0, 0)] * 4, 4, file_deadline=10)
            self.assertTrue(all(f['status'] == 'timeout' and f['segments'] is None for f in result['families']))


if __name__ == '__main__':
    unittest.main()
