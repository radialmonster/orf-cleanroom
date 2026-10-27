#!/usr/bin/env python3
"""Meaningful synthetic normalization/count/holdout tests; no camera input."""
from fractions import Fraction
import contextlib
import hashlib
import io
import itertools
import math
from pathlib import Path
import sys
import struct
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import frozen_bit_context as probe


class ContextTests(unittest.TestCase):
    def test_cli_rejects_truncated_and_malformed_csv(self):
        header = 'sha256,licence,pixls_id,pixls_name,payload_w,payload_h,size_class,variant\n'
        for row in ('abc,CC0,1,name,2,2,variable\n', 'abc,CC0,1,"unterminated\n'):
            with self.subTest(row=row), patch('builtins.open', return_value=io.StringIO(header + row)), \
                    patch.object(probe, 'load_window') as load, contextlib.redirect_stdout(io.StringIO()) as out, \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(probe.main(['--manifest', 'manifest', '--discovery', 'a', '--validation', 'b']), 1)
                load.assert_not_called()
                self.assertEqual(out.getvalue(), '')

    def test_manifest_allows_duplicate_rows_and_blank_optional_values(self):
        header = 'sha256,licence,pixls_id,pixls_name,payload_w,payload_h,size_class,variant\n'
        rows = 'abc,CC0,1,public.ORF,,,,\nabc,CC0,1,public.ORF,2,2,variable,unassigned\n'
        def window(path, manifest, offset, size):
            self.assertEqual(len(manifest), 2)
            self.assertEqual(manifest[0]['payload_w'], '')
            return [0, 1], {'sha256': path}
        with patch('builtins.open', return_value=io.StringIO(header + rows)), \
                patch.object(probe, 'load_window', side_effect=window), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(probe.main(['--manifest', 'manifest', '--discovery', 'a', '--validation', 'b']), 0)

    def test_cli_rejects_duplicate_and_missing_manifest_columns_before_samples(self):
        fields = ['sha256', 'licence', 'pixls_id', 'pixls_name', 'payload_w', 'payload_h', 'size_class', 'variant']
        for header in (fields + ['pixls_id'], fields[:-1], ['sha256', 'licence']):
            with self.subTest(header=header), patch('builtins.open', return_value=io.StringIO(','.join(header) + '\n')), \
                    patch.object(probe, 'load_window') as load, contextlib.redirect_stdout(io.StringIO()) as out, \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(probe.main(['--manifest', 'manifest', '--discovery', 'a', '--validation', 'b']), 1)
                load.assert_not_called()
                self.assertEqual(out.getvalue(), '')

    def test_cli_rejects_duplicate_identity_header_with_real_synthetic_inputs(self):
        data = (b'II' + struct.pack('<HI', 42, 8) + struct.pack('<H', 2)
                + struct.pack('<HHII', 273, 4, 1, 38)
                + struct.pack('<HHII', 279, 4, 1, 2) + struct.pack('<I', 0) + b'ab')
        other = data[:-2] + b'cd'
        header = 'sha256,licence,pixls_id,pixls_name,payload_w,payload_h,size_class,variant,pixls_id\n'
        rows = ''.join('%s,CC0,%s,public.ORF,2,2,variable,unassigned,wrong%s\n' %
                       (hashlib.sha256(blob).hexdigest(), i, i)
                       for i, blob in ((1, data), (2, other)))
        out, err = io.StringIO(), io.StringIO()
        with patch('builtins.open', return_value=io.StringIO(header + rows)), \
                patch.object(probe.Path, 'read_bytes', side_effect=[data, other]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(probe.main(['--manifest', 'manifest', '--discovery', 'a', '--validation', 'b',
                                         '--offset', '0', '--bytes', '1']), 1)
        self.assertEqual(out.getvalue(), '')

    def test_exhaustive_independent_context_counts(self):
        for length in range(9):
            for seq in itertools.product((0, 1), repeat=length):
                for order in range(5):
                    expected = [[0, 0] for _ in range(1 << order)]
                    for i, bit in enumerate(seq):
                        prefix = (0,) * order + seq[:i]
                        context = prefix[-order:] if order else ()
                        index = int(''.join(map(str, context)), 2) if context else 0
                        expected[index][bit] += 1
                    self.assertEqual(probe.counts(seq, order), expected)

    def test_normalization_and_independent_likelihood(self):
        for order in range(4):
            probabilities = [511 + 300 * c for c in range(1 << order)]
            for length in range(7):
                total = Fraction(0)
                for seq in itertools.product((0, 1), repeat=length):
                    probability = Fraction(1)
                    for i, bit in enumerate(seq):
                        context = ((0,) * order + seq[:i])[-order:] if order else ()
                        index = int(''.join(map(str, context)), 2) if context else 0
                        p = probabilities[index]
                        probability *= Fraction(p if bit else 4096 - p, 4096)
                    total += probability
                    actual = probe.nll(probe.counts(seq, order), probabilities)
                    self.assertAlmostEqual(actual, -math.log2(probability), places=11)
                self.assertEqual(total, 1)

    def test_quantization_and_unseen_context(self):
        self.assertEqual(probe.fit([[0, 0], [100000, 0], [0, 100000]]), [2048, 1, 4095])
        for zero in range(20):
            for one in range(20):
                exact = Fraction((one + 1) * 4096, zero + one + 2)
                expected = (exact + Fraction(1, 2)).numerator // (exact + Fraction(1, 2)).denominator
                self.assertEqual(probe.fit([[zero, one]])[0], expected)

    def test_validation_cannot_change_discovery_selection(self):
        a = probe.experiment([[0, 1] * 128], [[0] * 256])
        b = probe.experiment([[0, 1] * 128], [[1, 0] * 128])
        self.assertEqual(a['frozen_order'], b['frozen_order'])
        for x, y in zip(a['ledger'], b['ledger']):
            self.assertEqual(x['discovery_score'], y['discovery_score'])
            self.assertEqual(x['discovery_table_sha256'], y['discovery_table_sha256'])

    def test_literal_and_shuffle_count_control(self):
        result = probe.experiment([[0, 1] * 64], [[0, 0, 1] * 50])
        zero = result['ledger'][0]
        self.assertEqual(zero['validation_score'], zero['shuffled_validation_score'])
        self.assertEqual(result['validation_literal_bits'], 150)
        self.assertEqual(zero['discovery_count_total'], 128)
        self.assertEqual(probe.bits(bytes([128, 1])), [1] + [0] * 14 + [1])

    def test_source_built_multistrip_and_input_guards(self):
        # Two LONG[2] tags, offsets in deliberately reverse physical order.
        data = (b'II' + struct.pack('<HI', 42, 8) + struct.pack('<H', 2)
                + struct.pack('<HHII', 273, 4, 2, 38)
                + struct.pack('<HHII', 279, 4, 2, 46) + struct.pack('<I', 0)
                + struct.pack('<II', 58, 54) + struct.pack('<II', 2, 2) + b'abXXcd')
        row = {'sha256': hashlib.sha256(data).hexdigest(), 'licence': 'CC0',
               'pixls_id': 'synthetic', 'pixls_name': 'source-built TIFF',
               'payload_w': '2', 'payload_h': '2', 'size_class': 'synthetic',
               'variant': 'unassigned'}
        with patch.object(probe.Path, 'read_bytes', return_value=data):
            window, identity = probe.load_window('synthetic', [row], 1, 2)
            self.assertEqual(window, probe.bits(b'da'))
            self.assertEqual(identity['strip_count'], 2)
            self.assertEqual(identity['manifest_signature']['payload_w'], '2')
            for manifest, offset, size in (([], 0, 1), ([dict(row, licence='unknown')], 0, 1),
                                           ([dict(row, sha256='wrong')], 0, 1), ([row], 3, 2)):
                with self.assertRaises(ValueError):
                    probe.load_window('synthetic', manifest, offset, size)
            duplicate = dict(row, pixls_id='second', payload_w='999')
            _, identity = probe.load_window('synthetic', [row, duplicate], 1, 2)
            self.assertEqual(identity['pixls_id'], 'synthetic')
            self.assertEqual(identity['manifest_signature']['payload_w'], '2')
        malformed = data[:38] + struct.pack('<I', 100) + data[42:]
        badrow = dict(row, sha256=hashlib.sha256(malformed).hexdigest())
        with patch.object(probe.Path, 'read_bytes', return_value=malformed):
            with self.assertRaisesRegex(ValueError, 'strip outside file'):
                probe.load_window('synthetic', [badrow], 0, 1)
        overlap = data[:38] + struct.pack('<II', 54, 55) + data[46:]
        badrow = dict(row, sha256=hashlib.sha256(overlap).hexdigest())
        with patch.object(probe.Path, 'read_bytes', return_value=overlap):
            with self.assertRaisesRegex(ValueError, 'overlapping strips'):
                probe.load_window('synthetic', [badrow], 0, 1)

    def test_cli_redacts_manifest_failure(self):
        private = 'DO_NOT_PUBLISH_PRIVATE_PATH'
        err, out = io.StringIO(), io.StringIO()
        with patch('builtins.open', side_effect=OSError(private)):
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
                self.assertEqual(probe.main(['--manifest', private, '--discovery', 'a',
                                             '--validation', 'b']), 1)
        self.assertNotIn(private, err.getvalue())
        self.assertIn('invalid input:', err.getvalue())
        self.assertEqual(out.getvalue(), '')

    def test_cli_redacts_sample_failure(self):
        private = 'DO_NOT_PUBLISH_PRIVATE_PATH'
        for failure in (OSError(private), ValueError(private), struct.error(private),
                        KeyError(private), UnicodeError(private)):
            err, out = io.StringIO(), io.StringIO()
            with patch('builtins.open', return_value=io.StringIO('sha256,licence,pixls_id,pixls_name,payload_w,payload_h,size_class,variant\n')):
                with patch.object(probe, 'load_window', side_effect=failure):
                    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
                        self.assertEqual(probe.main(['--manifest', 'unused', '--discovery',
                                                     private, '--validation', 'b']), 1)
            self.assertNotIn(private, err.getvalue())
            self.assertIn('invalid input:', err.getvalue())
            self.assertEqual(out.getvalue(), '')

    def test_cli_rejects_duplicate_hashes(self):
        argv = ['probe', '--manifest', 'synthetic.csv', '--discovery', 'a', '--validation', 'b']
        with patch.object(sys, 'argv', argv), patch('builtins.open', return_value=io.StringIO('sha256,licence,pixls_id,pixls_name,payload_w,payload_h,size_class,variant\n')):
            with patch.object(probe, 'load_window', return_value=([0], {'sha256': 'same'})):
                with patch.object(sys, 'stderr', io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        probe.main()
                    self.assertEqual(error.exception.code, 2)

    def test_cli_validation_offset_routing_and_default(self):
        argv = ['probe', '--manifest', 'synthetic.csv', '--discovery', 'a', 'b',
                '--validation', 'c', 'd', '--offset', '20', '--bytes', '2']
        for extra, expected in (([], [20, 20, 20, 20]),
                                (['--validation-offset', '40'], [20, 20, 40, 40]),
                                (['--validation-offset', '0'], [20, 20, 0, 0])):
            def window(path, manifest, offset, size):
                return [0, 1], {'sha256': path, 'window_offset': offset}
            with patch.object(sys, 'argv', argv + extra), patch('builtins.open', return_value=io.StringIO('sha256,licence,pixls_id,pixls_name,payload_w,payload_h,size_class,variant\n')):
                with patch.object(probe, 'load_window', side_effect=window) as loader:
                    with patch.object(sys, 'stdout', io.StringIO()) as output:
                        probe.main()
                    self.assertEqual([call.args[2] for call in loader.call_args_list], expected)
                    self.assertIn('"window_offset": %d' % expected[-1], output.getvalue())
        for flag in ('--offset', '--validation-offset'):
            with patch.object(sys, 'argv', argv + [flag, '-1']):
                with patch.object(sys, 'stderr', io.StringIO()), patch.object(probe, 'load_window') as loader:
                    with self.assertRaises(SystemExit) as error:
                        probe.main()
                    self.assertEqual(error.exception.code, 2)
                    loader.assert_not_called()

    def test_invalid_inputs(self):
        for discovery, validation in (([], [[1]]), ([[1]], []), ([[]], [[1]])):
            with self.assertRaises(ValueError):
                probe.experiment(discovery, validation)
        with self.assertRaises(ValueError):
            probe.counts([2], 0)


if __name__ == '__main__':
    unittest.main()
