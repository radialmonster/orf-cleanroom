"""Synthetic brute-anchor and phase-intersection checks for common-row phase."""
from itertools import product
import contextlib
import hashlib
import io
import json
import os
import struct
import sys
import time
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_row_phase as probe


def brute(values, maximum):
    if len(values) <= 2:
        return True
    for first, second in product(range(maximum + 1), repeat=2):
        a, b = first, second
        for value in values[2:]:
            a, b = b, 2*b-a+value
            if not 0 <= b <= maximum:
                break
        else:
            return True
    return False


def brute_phases(values, width, start, maximum):
    result = set()
    for phi in range(width):
        cut = (phi - start) % width
        pieces = (values[:cut], values[cut:]) if 0 < cut < len(values) else (values,)
        if all(brute(piece[p::2], maximum) for piece in pieces for p in (0, 1)):
            result.add(phi)
    return result


class Synthetic(unittest.TestCase):
    def test_generated_tiff_cli_shortfall(self):
        bits = '100000' * 15
        payload = int(bits + '0' * (-len(bits) % 8), 2).to_bytes((len(bits) + 7) // 8, 'big')
        tags = ((256, 100), (257, 1), (259, 1), (273, 74), (279, len(payload)))
        data = (b'II' + struct.pack('<HIH', 42, 8, len(tags))
                + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags)
                + struct.pack('<I', 0) + payload)
        real_open = open
        def open_fixture(path, *args, **kwargs):
            return io.BytesIO(data) if path == 'fixture' else real_open(path, *args, **kwargs)
        output = io.StringIO()
        with mock.patch.object(probe, 'WINDOW', 4), mock.patch.object(probe, 'STARTS', (0, 4, 8, 12)), \
             mock.patch.object(sys, 'argv', ['probe', '--sample', '1', 'public.ORF', 'fixture']), \
             mock.patch('builtins.open', side_effect=open_fixture), contextlib.redirect_stdout(output):
            status = probe.main()
        result = json.loads(output.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(result['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual([w['returned_tokens'] for w in result['result']['windows']], [4, 4, 4, 3])
        self.assertEqual(result['result']['windows'][-1]['status'], 'short')
        self.assertFalse(result['result']['complete_survival'])

    def test_exhaustive_prefix_suffix_and_phases(self):
        for n in range(7):
            width = n + 1 if n % 2 else n + 2
            for values in product((-2, 0, 2), repeat=n):
                for maximum in (0, 1):
                    p, s = probe.lane_limits(values, maximum)
                    self.assertEqual(p, max(i for i in range(n + 1) if brute(values[:i], maximum)))
                    self.assertEqual(s, min(i for i in range(n + 1) if brute(values[i:], maximum)))
                    for start in (0, 1, width - 1):
                        phases, _ = probe.phase_set(values, width, start, maximum)
                        self.assertEqual(phases, brute_phases(values, width, start, maximum))

    def test_reverse_and_incompatible_cuts(self):
        self.assertEqual(probe.lane_limits([0, 0, 0, 0, 3], 1), (4, 3))
        a, b = [0, 0, 3, 0, 0, 0], [0, 0, 0, 0, 3, 3]
        values = [x for pair in zip(a, b) for x in pair]
        phases, _ = probe.phase_set(values, 14, 0, 1)
        self.assertEqual(phases, set())
        values = [x for pair in zip(a, a) for x in pair]
        first, _ = probe.phase_set(values, 14, 0, 1)
        second, _ = probe.phase_set(values, 14, 7, 1)
        self.assertEqual((first, second), ({2, 3, 4}, {9, 10, 11}))
        self.assertFalse(first & second)

    def test_unknown_and_rejection_dominance(self):
        tokens = [(0, 0)] * 4 + [(17, 0)] * 4
        with mock.patch.object(probe, 'phase_set', return_value=(set(), {'partial_rejection': False})):
            result = probe.measure(tokens, 6, starts=(0, 4), requested=4)
        self.assertEqual((result['conclusion'], result['possible_phase_count']), ('rejected', 0))
        self.assertEqual(result['windows'][1]['status'], 'escape')
        result = probe.measure([(17, 0)] * 8, 6, starts=(0, 4), requested=4)
        self.assertEqual((result['conclusion'], result['possible_phase_count'], result['complete_survival']), ('undefined', 6, False))
        with mock.patch.object(probe, 'phase_set', side_effect=TimeoutError()):
            result = probe.measure([(0, 0)] * 8, 6, starts=(0, 4), requested=4)
        self.assertTrue(all(w['status'] == 'timeout' for w in result['windows']))
        self.assertEqual(result['possible_phase_count'], 6)
        with mock.patch.object(probe, 'lane_limits', side_effect=[(1, 2), TimeoutError()]):
            result = probe.measure([(0, 0)] * 4, 6, starts=(0,), requested=4)
        self.assertEqual(result['windows'][0]['status'], 'partial_reject_timeout')
        self.assertEqual(result['windows'][0]['details']['prefix_lengths'], [1, None])
        self.assertEqual((result['conclusion'], result['possible_phase_count']), ('rejected', 0))

    def test_width_and_deadline(self):
        with self.assertRaises(ValueError):
            probe.measure([], 5, starts=(), requested=4)
        with self.assertRaises(ValueError):
            probe.measure([], 4, starts=(), requested=4)
        with mock.patch.object(probe.time, 'monotonic', return_value=10):
            with self.assertRaises(TimeoutError):
                probe.prefix_length([0, 0], 3, 10)
            result = probe.measure([(0, 0)] * 4, 6, starts=(0,), requested=4, file_deadline=10)
            self.assertEqual(result['windows'][0]['status'], 'file_budget_not_run')


def pilot():
    """Synthetic worst-case 16 complete 2048-point prefix scans; no samples."""
    start = time.monotonic()
    for _ in range(16):
        assert probe.prefix_length([0] * 2048, 65535) == 2048
    print(json.dumps({'scope': 'synthetic sixteen all-zero lanes',
                      'pair_updates': 16 * 2048 * 2047 // 2,
                      'seconds': time.monotonic() - start}))


if __name__ == '__main__':
    if sys.argv[1:] == ['--pilot']:
        pilot()
    else:
        unittest.main()
