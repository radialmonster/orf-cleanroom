#!/usr/bin/env python3
"""Independent finite oracles for run_reorder_search; stdlib, synthetic only."""
import fractions
import contextlib
import hashlib
import io
import json
import struct
import itertools
import os
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_reorder_search as probe


def oracle(bits):
    lengths = [[], []]
    if bits:
        start = 0
        for i in range(1, len(bits) + 1):
            if i == len(bits) or bits[i] != bits[start]:
                lengths[bits[start]].append(i - start)
                start = i
    pairs = [sum(bits[i] == a and bits[i + 1] == b for i in range(len(bits) - 1))
             for a in (0, 1) for b in (0, 1)]
    return len(bits), bits.count(1), bits[:1] + bits[-1:], [sorted(x) for x in lengths], pairs


class TestRunSearch(unittest.TestCase):
    def test_invalid_sample_precedes_all_work(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        cases = [('0', 'public', '0' * 64, False), ('\u0661', 'public', '0' * 64, False),
                 ('1', '', '0' * 64, False), ('1', 'private/path', '0' * 64, False),
                 ('1', 'private\\path', '0' * 64, False), ('1', 'bad\nname', '0' * 64, False),
                 ('1', 'public', 'bad', False), ('1', 'public', '0' * 64, True)]
        if limit:
            cases.append(('9' * (limit + 1), 'public', '0' * 64, False))
        for sid, name, digest, simulated in cases:
            out, err = io.StringIO(), io.StringIO()
            conversion = patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(sid=sid[:4], name=name, simulated=simulated), \
                 patch.object(probe, 'read_window') as read, patch.object(probe, 'analyse') as analyse, \
                 conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(['--sample', sid, name, digest, 'unused'])
                self.assertEqual(caught.exception.code, 2)
                read.assert_not_called()
                analyse.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_valid_identity_and_synthetic_mode(self):
        name = 'OM - Élite "camera" (4:3).ORF'
        for sample in (False, True):
            args = ['--sample', '01', name, '0' * 64, 'unused'] if sample else []
            out = io.StringIO()
            with self.subTest(sample=sample), patch.object(probe, 'analyse', return_value={}) as analyse, \
                 patch.object(probe, 'read_window', return_value=(b'', {})) as read, contextlib.redirect_stdout(out):
                self.assertEqual(probe.main(args), 0)
            records = json.loads(out.getvalue())['records']
            self.assertEqual(analyse.call_count, 4 if sample else 3)
            self.assertEqual(read.call_count, int(sample))
            if sample:
                self.assertEqual((records[-1]['pixls_id'], records[-1]['pixls_name']), ('01', name))

    def test_exhaustive_small_binary_invariants(self):
        for n in range(10):
            for xs in itertools.product((0, 1), repeat=n):
                bits = list(xs)
                expected = oracle(bits)
                inv = probe.invariants(bits)
                self.assertEqual((inv['bits'], inv['ones'], inv['endpoints'],
                                  inv['runs_by_symbol'], sum(inv['transition_counts'], [])), expected)
                for seed in (0, 23):
                    self.assertEqual(oracle(probe.reorder_runs(bits, random.Random(seed))), expected)

    def test_run_order_can_change_and_constant_is_retained(self):
        bits = [0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1]
        self.assertTrue(any(probe.reorder_runs(bits, random.Random(seed)) != bits for seed in range(10)))
        for bit in (0, 1):
            self.assertEqual(probe.reorder_runs([bit] * 100, random.Random(3)), [bit] * 100)
        # Alternating unit runs permit no change although phase score is large.
        self.assertEqual(probe.reorder_runs([0, 1] * 2048, random.Random(4)), [0, 1] * 2048)

    def test_exact_rational_candidate_oracle(self):
        rng = random.Random(713)
        bits = [rng.randrange(2) for _ in range(4096)]
        rows = probe.candidates(bits)
        keys = []
        for window in range(2):
            start = window * 2048
            total = sum(bits[i] for i in range(start, start + 2048))
            for width in range(2, 13):
                for phase in range(width):
                    keys.append((window, width, phase))
                    selected = [bits[i] for i in range(start, start + 2048) if (i - start) % width == phase]
                    n, a = len(selected), sum(selected)
                    m, b = 2048 - n, total - a
                    exact = fractions.Fraction((a * m - b * n) ** 2 * 2048,
                                               n * m * total * (2048 - total))
                    row = rows[len(keys) - 1]
                    self.assertEqual((row['selected_n'], row['selected_ones'], row['other_n'], row['other_ones']),
                                     (n, a, m, b))
                    self.assertAlmostEqual(row['score'], float(exact), places=11)
        self.assertEqual([(r['window'], r['width'], r['phase']) for r in rows], keys)
        self.assertEqual(len(rows), 154)

    def test_complete_replicate_search_and_tail_oracle(self):
        buf = bytes(range(256)) * 2
        report = probe.analyse(buf)
        bits = probe.bits_of(buf)
        observed = probe.candidates(bits)
        maximum = max(row['score'] for row in observed)
        rng = random.Random(probe.SEED)
        exceed = 0
        for row in report['replicate_maxima']:
            regenerated = probe.reorder_runs(bits, rng)
            all_rows = probe.candidates(regenerated)
            self.assertEqual(row['score'], max(candidate['score'] for candidate in all_rows))
            self.assertEqual({k: v for k, v in row.items() if k != 'replicate'},
                             probe.summarize_winner(all_rows))
            exceed += row['score'] >= maximum
        self.assertEqual(report['exceedances_ge'], exceed)
        self.assertEqual(report['plus_one_rank_diagnostic'], (exceed + 1) / 128)
        self.assertEqual(report['invariants_checked_replicates'], 127)

    def test_hash_gate_and_logical_strip_order(self):
        # Minimal public-TIFF-style fixture, not a sample or decoder output.
        data = bytearray(5200)
        data[:8] = struct.pack('<2sHI', b'II', 42, 8)
        struct.pack_into('<H', data, 8, 4)
        for i, (tag, count, value) in enumerate([(0x100, 1, 1), (0x101, 1, 1),
                                                (0x111, 2, 80), (0x117, 2, 88)]):
            struct.pack_into('<HHII', data, 10 + 12 * i, tag, 4, count, value)
        struct.pack_into('<I', data, 58, 0)
        struct.pack_into('<II', data, 80, 3000, 128)
        struct.pack_into('<II', data, 88, 2200, 2200)
        data[3000:5200] = bytes([1]) * 2200
        data[128:2328] = bytes([2]) * 2200
        digest = hashlib.sha256(data).hexdigest()
        # 4400 bytes is insufficient for [4096,4608).
        with self.assertRaises(ValueError):
            probe.read_data(data, digest)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            probe.read_data(data, '0' * 64)
        struct.pack_into('<II', data, 88, 2200, 2400)
        data[128:2528] = bytes([2]) * 2400
        # Still short: 4600 < 4608, no implicit zero padding permitted.
        with self.assertRaisesRegex(ValueError, 'short payload'):
            probe.read_data(data, hashlib.sha256(data).hexdigest())
        struct.pack_into('<II', data, 88, 2200, 2500)
        data[128:2628] = bytes([2]) * 2500
        window, metadata = probe.read_data(data, hashlib.sha256(data).hexdigest())
        self.assertEqual(window, bytes([2]) * 512)
        self.assertEqual(metadata['payload_bytes'], 4700)
        struct.pack_into('<II', data, 80, 3000, 2000)
        with self.assertRaisesRegex(ValueError, 'overlapping strips'):
            probe.read_data(data, hashlib.sha256(data).hexdigest())
        struct.pack_into('<II', data, 80, 3000, 9000)
        with self.assertRaisesRegex(ValueError, 'invalid strip bounds'):
            probe.read_data(data, hashlib.sha256(data).hexdigest())

    def test_degenerate_and_window_boundary(self):
        report = probe.analyse(bytes(512))
        self.assertEqual(report['winner']['score'], 0)
        self.assertEqual(report['exceedances_ge'], 127)
        self.assertEqual(report['plus_one_rank_diagnostic'], 1)
        self.assertEqual(report['winner']['window'], 0)
        self.assertEqual(report['winner']['tie_count'], 154)
        self.assertTrue(report['winner']['any_tied_width_boundary'])
        self.assertTrue(all(row['tie_count'] == 154 for row in report['replicate_maxima']))
        with self.assertRaises(ValueError):
            probe.candidates([0] * 4095)
        self.assertEqual(probe.wilson(0, 127)[0], 0)
        self.assertEqual(probe.wilson(127, 127)[1], 1)


if __name__ == '__main__':
    unittest.main()
