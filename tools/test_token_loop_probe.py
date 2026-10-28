#!/usr/bin/env python3
"""Synthetic tests for tools/token_loop_probe.py.

No sample files, no image data, no writes. Run either directly or with
`python -I -B tools/token_loop_probe.py --self-test`.
"""
import os
import contextlib
import io
import json
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_loop_probe as probe


class MappingTests(unittest.TestCase):
    def test_id_conversion_failure_is_argument_error_before_measurement(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        cases = [('2', True)]
        if limit:
            cases.append(('9' * (limit + 1), False))
        for sid, simulated in cases:
            args = ['--sample', '1', 'public', 'unused', '--sample', sid, 'public', 'unused']
            out, err = io.StringIO(), io.StringIO()
            conversion = patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated), patch.object(probe, 'measure_sample') as measured, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(args)
                self.assertEqual(caught.exception.code, 2)
                measured.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private detail', err.getvalue())

    def test_leading_zero_id_passes_as_canonical_integer(self):
        output = io.StringIO()
        with patch.object(probe, 'measure_sample', return_value={'prefix_complete': True, 'mappings': {}}) as measured, contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(['--sample', '01', 'public', 'unused']), 0)
        self.assertEqual(measured.call_args.args[0], 1)
        self.assertEqual(type(measured.call_args.args[0]), int)


    def test_u(self):
        self.assertEqual(probe.map_value(0, 0, "u"), 0)
        self.assertEqual(probe.map_value(17, 31, "u"), 17 * 32 + 31)

    def test_signed_digit(self):
        self.assertEqual(probe.map_value(0, 0, "signed_digit"), 0)
        self.assertEqual(probe.map_value(0, 31, "signed_digit"), 4 * 3 + 3 - 8)
        self.assertEqual(probe.map_value(0, 16, "signed_digit"), 8)

    def test_signed_low3(self):
        self.assertEqual(probe.map_value(0, 0, "signed_low3"), 0)
        self.assertEqual(probe.map_value(0, 7, "signed_low3"), -1)
        self.assertEqual(probe.map_value(0, 8, "signed_low3"), 0)

    def test_mapped_values_length_mismatch(self):
        with self.assertRaises(probe.ProbeError):
            probe.mapped_values([0, 1], [0], "u")


class LoopTests(unittest.TestCase):
    def test_global_shuffle_is_deterministic_and_crosses_rows(self):
        values = [0, 0, 0, 0, 1, 1, 1, 1]
        result = probe.shuffled_global(values, random.Random(7))
        self.assertEqual(result, probe.shuffled_global(values, random.Random(7)))
        self.assertEqual(sorted(result), sorted(values))
        self.assertNotEqual(result[:4], values[:4])
        self.assertEqual(values, [0, 0, 0, 0, 1, 1, 1, 1])

    def test_cli_selects_global_mode(self):
        output = io.StringIO()
        with patch.object(probe, 'measure_sample', return_value={'prefix_complete': True, 'mappings': {}}) as measured, contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(['--sample', '1', 'public', 'unused', '--null-mode', 'global']), 0)
        self.assertEqual(measured.call_args.args[-1], 'global')
        self.assertEqual(json.loads(output.getvalue())['settings']['null_mode'], 'global')

    def test_measurement_global_null_and_default(self):
        sig = {'size_class': 'variable', 'compression_tag': 1, 'payload_w': 4,
               'payload_h': 2, 'payload_bytes': 8, 'payload_offset': 0,
               'sha256': 'x', 'bpp': 8}
        q = [0] * 8; suffix = [0] * 4 + [1] * 4
        with patch.object(probe.orf_signature, 'signature', return_value=sig), \
             patch.object(probe.orf_tokens, 'locate', return_value=(4, 2, b'12345678')), \
             patch.object(probe.orf_tokens, 'parse', return_value=(q, suffix, [], 48)), \
             patch.object(probe, 'sha256_file', return_value='x'):
            default = probe.measure_sample(1, 'fixture', 'unused', 2, 1)
            explicit = probe.measure_sample(1, 'fixture', 'unused', 2, 1, 'within-row')
            global_result = probe.measure_sample(1, 'fixture', 'unused', 2, 1, 'global')
        self.assertEqual(default, explicit)
        vals = list(suffix); random.Random(probe.SEED_BASE + 1000).shuffle(vals)
        self.assertNotEqual(vals[:4], suffix[:4])
        outputs = []
        for row in (vals[:4], vals[4:]):
            prev = prev2 = 0
            for value in row:
                current = 2 * prev - prev2 + value
                outputs.append(current); prev2, prev = prev, current
        self.assertEqual(global_result['mappings']['u']['P1']['null_ranges'],
                         [max(outputs) - min(outputs)])

    def test_p1_constant(self):
        self.assertEqual(probe.range_p1([1, 1, 1, 1], 4, 1), 9)

    def test_p1_resets_per_row(self):
        # Two identical rows give the same range as one row, not a longer ramp.
        self.assertEqual(probe.range_p1([1, 1, 1, 1, 1, 1, 1, 1], 4, 2), 9)

    def test_p1_zero(self):
        self.assertEqual(probe.range_p1([0] * 8, 4, 2), 0)

    def test_p2_parity(self):
        self.assertEqual(probe.range_p2([1, 10, 1, 10], 4, 1), 29)

    def test_p2_zero(self):
        self.assertEqual(probe.range_p2([0] * 8, 4, 2), 0)

    def test_l1_expected(self):
        self.assertEqual(probe.range_l1([1, 1, 1, 1], 2, 2), 5)

    def test_l1_zero(self):
        self.assertEqual(probe.range_l1([0] * 6, 2, 3), 0)

    def test_l2_expected(self):
        self.assertEqual(probe.range_l2([1] * 6, 2, 3), 3)

    def test_l2_zero(self):
        self.assertEqual(probe.range_l2([0] * 6, 2, 3), 0)

    def test_r1_expected(self):
        self.assertEqual(probe.range_r1([1, 1, 1, 1], 4, 1), 3)

    def test_r1_resets_per_row(self):
        self.assertEqual(probe.range_r1([1, 1, 1, 1, 1, 1, 1, 1], 4, 2), 3)

    def test_r1_range_excludes_initial_zero_and_depends_on_order(self):
        self.assertEqual(probe.range_r1([1, 10], 2, 1), 10)
        self.assertEqual(probe.range_r1([10, 1], 2, 1), 1)

    def test_r2_parity(self):
        self.assertEqual(probe.range_r2([1, 10, 1, 10], 4, 1), 19)

    def test_lk05(self):
        self.assertAlmostEqual(probe.range_lk05([1, 1, 1, 1], 4, 1), 0.875)

    def test_lk09(self):
        self.assertAlmostEqual(probe.range_lk09([1, 1, 1, 1], 4, 1), 2.439)

    def test_all_ranges_keys(self):
        got = probe.all_ranges([0] * 8, 4, 2)
        self.assertEqual(set(got), set(probe.LOOPS))
        self.assertTrue(all(v == 0 for v in got.values()))


class ShuffleTests(unittest.TestCase):
    def test_rows_preserved_and_deterministic(self):
        values = list(range(1, 9))
        a = probe.shuffled_rows(values, 4, 2, random.Random(123))
        b = probe.shuffled_rows(values, 4, 2, random.Random(123))
        self.assertEqual(a, b)
        self.assertEqual(sorted(a[0:4]), [1, 2, 3, 4])
        self.assertEqual(sorted(a[4:8]), [5, 6, 7, 8])

    def test_shuffle_changes_order(self):
        values = [1, 2, 3, 4, 5, 6, 7, 8]
        # Search a few seeds for a non-identity permutation; fixed and cheap.
        changed = False
        for seed in range(20):
            if probe.shuffled_rows(values, 4, 2, random.Random(seed)) != values:
                changed = True
                break
        self.assertTrue(changed)


class MeanTests(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(probe.mean([1, 2, 3]), 2.0)

    def test_empty_mean(self):
        self.assertIsNone(probe.mean([]))


if __name__ == "__main__":
    unittest.main()
