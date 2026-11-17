"""Synthetic matched-boundary, selection and exact q0-ledger checks."""
import os
import sys
import unittest
from unittest import mock
import contextlib
import hashlib
import io
import json
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matched_boundary_coalescence as probe


def pack(bits):
    padded = bits + '0' * (-len(bits) % 8)
    return int(padded, 2).to_bytes(len(padded) // 8, 'big') if padded else b''


def word(q, suffix):
    return '0' * q + '1' + format(suffix, '05b')


class Synthetic(unittest.TestCase):
    def test_cli_generated_tiff_short_prefix(self):
        payload = bytes([255]) * 12
        tags = ((256, 100), (257, 1), (259, 1), (273, 74), (279, len(payload)))
        data = (b'II' + struct.pack('<HIH', 42, 8, len(tags))
                + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags)
                + struct.pack('<I', 0) + payload)
        real_open = open
        def open_fixture(path, *args, **kwargs):
            return io.BytesIO(data) if path == 'fixture' else real_open(path, *args, **kwargs)
        argv = ['probe', '--sample', 'public', hashlib.sha256(data).hexdigest(), 'fixture', '--tokens', '262144']
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', argv), mock.patch('builtins.open', side_effect=open_fixture), contextlib.redirect_stdout(output):
            status = probe.main()
        report = json.loads(output.getvalue())
        self.assertEqual(status, 1)
        self.assertFalse(report['result']['prefix_complete'])
        self.assertEqual(report['result']['parsed_tokens'], 16)
        self.assertIsNone(report['result']['matched_pairs'])
        self.assertEqual(report['sha256'], hashlib.sha256(data).hexdigest())

    def test_ones_meets_later_start(self):
        buf = bytes([255]) * 32
        pair = probe.horizons(buf, 0, len(buf) * 8)
        self.assertEqual(probe.first_shared(0, pair), (12, 2, 0))

    def test_earliest_multiple_and_boundary_only(self):
        def fake(starts):
            return [(0, 0, a, b) for a, b in zip(starts, starts[1:])]
        left = list(range(0, 240, 10)) + [250]
        right = list(range(12, 252, 10)) + [250]
        # Artificial boundary sets isolate set intersection and index handling.
        pair = (fake(left), fake(right))
        self.assertEqual(probe.first_shared(0, pair), (250, 24, 24))
        self.assertIsNone(probe.first_shared(0, (fake(left), fake(list(range(12, 262, 10))))))
        right = [12] + list(range(20, 260, 10))
        self.assertEqual(probe.first_shared(0, (fake(left), fake(right))), (20, 2, 1))

    def test_short_prefix_and_horizon(self):
        self.assertFalse(probe.measure(pack(word(0, 0)), 2)['prefix_complete'])
        self.assertIsNone(probe.horizons(bytes([255]), 0, 8))

    def test_controls_reuse_and_ledgers(self):
        bits = word(0, 3) + word(0, 1) * 39 + word(17, 3) + word(17, 3) + word(0, 1) * 60
        report = probe.measure(pack(bits), 102)
        self.assertTrue(report['prefix_complete'])
        self.assertEqual((report['anchors'], report['no_match'], report['short_horizon'], report['matched_pairs']), (2, 0, 0, 2))
        self.assertEqual((report['unique_controls'], report['reused_control_pairs']), (1, 1))
        for side in ('escape', 'control'):
            stats = report[side]
            self.assertEqual(stats['found'] + stats['not_found'], 2)
            for field in ('distance_bits', 'index0', 'index12', 'shared_words'):
                self.assertEqual(sum(stats[field].values()), stats['found'])
            self.assertEqual(stats['q0_difference'], stats['found_pre_difference'] + stats['found_tail_difference'] + stats['not_found_difference'])
        paired = report['paired']
        self.assertEqual(report['paired_q0_difference_sum'], paired['both_pre_difference'] + paired['both_tail_difference'] + paired['other_difference'])

    def test_first_anchor_no_control_and_exact_completion(self):
        first = probe.measure(pack(word(17, 2) + word(0, 0) * 60), 61)
        self.assertEqual((first['anchors'], first['no_match']), (1, 1))
        # A q=0 control at bit zero has both horizons ending at bit 162;
        # the escape starts exactly there and is therefore eligible.
        bits = word(0, 0) + word(0, 1) * 26 + word(17, 0) + word(0, 1) * 60
        report = probe.measure(pack(bits), 88)
        self.assertEqual((report['anchors'], report['matched_pairs']), (1, 1))

    def test_boundary_only_and_mixed_pair_ledgers(self):
        def words(boundaries, q):
            return [(q, 0, a, b) for a, b in zip(boundaries, boundaries[1:])]
        def boundary_only(start):
            left = [start + 10 * i for i in range(24)] + [start + 250]
            right = [start + 12 + 10 * i for i in range(24)] + [start + 250]
            return words(left, 0), words(right, 1)
        def not_found(start):
            return (words([start + 10 * i for i in range(25)], 0),
                    words([start + 12 + 10 * i for i in range(25)], 1))
        control = probe.horizons(bytes([255]) * 100, 10, 800)
        rows = [(0, 3, 0, 10), (17, 3, 200, 220),
                (17, 3, 400, 420), (1, 0, 599, 600)]
        pairs = {10: control, 220: boundary_only(220), 420: not_found(420)}
        with mock.patch.object(probe, 'scan', return_value=rows), \
             mock.patch.object(probe, 'horizons', side_effect=lambda _b, start, _end: pairs[start]):
            result = probe.measure(bytes(100), 4)
        self.assertEqual(result['paired']['both'], 1)
        self.assertEqual(result['paired']['control_only'], 1)
        self.assertEqual(result['escape']['shared_words'], {'0': 1})
        self.assertEqual(result['control']['immediate_later_start'], 2)
        self.assertEqual(result['escape']['found_tail_difference'], 0)
        self.assertEqual(result['escape']['not_found_difference'], -24)
        self.assertEqual(result['paired_q0_difference_sum'],
                         result['paired']['both_pre_difference'] + result['paired']['both_tail_difference'] + result['paired']['other_difference'])


if __name__ == '__main__':
    unittest.main()
