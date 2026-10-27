#!/usr/bin/env python3
"""Synthetic finite-grid calibration checks, without sample files."""
from fractions import Fraction
import contextlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frozen_context_calibration as probe


class CalibrationTests(unittest.TestCase):
    def test_fraction_oracle_and_clamps(self):
        values = [1, 2, 17, 2048, 4094, 4095]
        for a, b in probe.GRID:
            actual, clamps = probe.transform(values, (a, b))
            expected = []
            clamped = 0
            for p in values:
                exact = Fraction(4096*a*p, b*(4096-p)+a*p) + Fraction(1, 2)
                rounded = exact.numerator // exact.denominator
                expected.append(max(1, min(4095, rounded)))
                clamped += not 1 <= rounded <= 4095
            self.assertEqual(actual, expected)
            self.assertEqual(clamps, clamped)

    def test_tie_is_first_and_all_candidates_retained(self):
        selected, detail = probe.choose([2048], [], 0)
        self.assertEqual(detail['selected_index'], 0)
        self.assertEqual(detail['tied_indices'], list(range(7)))
        self.assertEqual(len(detail['candidates']), 7)
        self.assertEqual(selected, probe.transform([2048], probe.GRID[0])[0])

    def test_calibration_fixed_while_evaluation_changes(self):
        ledger = [(0, [2048], '')] + [(0, [], '') for _ in range(7)] + [(0, [2048]*256, '')]
        calibration = [0] * 30 + [1] * 10
        first = probe.evaluate(ledger, calibration, [[0, 1]*30])
        second = probe.evaluate(ledger, calibration, [[1]*60])
        self.assertEqual(first['calibration'], second['calibration'])
        self.assertNotEqual(first['evaluation'], second['evaluation'])
        self.assertEqual(first['evaluation'][0]['0']['adjusted'],
                         first['evaluation'][0]['0']['shuffled'])

    def test_shuffle_is_repeatable_and_preserves_count(self):
        data = [0]*70 + [1]*30
        self.assertEqual(probe.shuffled(data), probe.shuffled(data))
        self.assertEqual(sum(probe.shuffled(data)), sum(data))
        self.assertEqual(data, [0]*70 + [1]*30)

    def test_index_and_model_costs_for_both_orders(self):
        ledger = [(0, [2048], '')] + [(0, [], '') for _ in range(7)] + [(0, [2048]*256, '')]
        result = probe.evaluate(ledger, [], [[]])['evaluation'][0]
        self.assertEqual((result['0']['frozen'], result['0']['adjusted']), (16, 19))
        self.assertEqual((result['8']['frozen'], result['8']['adjusted']), (3076, 3079))

    def test_shuffle_rejection_draw_order(self):
        rng = unittest.mock.Mock()
        rng.getrandbits.side_effect = [3, 1, 2, 0]
        with patch.object(probe.random, 'Random', return_value=rng) as factory:
            self.assertEqual(probe.shuffled([0, 1, 2]), [2, 0, 1])
        factory.assert_called_once_with(298)
        self.assertEqual([call.args[0] for call in rng.getrandbits.call_args_list], [2, 2, 2, 2])

    def test_main_real_synthetic_tiff_routes_offsets_and_rejects_failures(self):
        def fixture(last):
            body = bytearray(327681)
            body[65536] = last
            body[196608] = last ^ 3
            body[262144] = last ^ 5
            body[327680] = last ^ 7
            header = (b'II' + struct.pack('<HI', 42, 8) + struct.pack('<H', 2)
                      + struct.pack('<HHII', 273, 4, 1, 38)
                      + struct.pack('<HHII', 279, 4, 1, len(body)) + struct.pack('<I', 0))
            return header + body
        blobs = {name: fixture(i) for i, name in enumerate(('a', 'b', 'c'), 1)}
        fields = 'sha256,licence,pixls_id,pixls_name,payload_w,payload_h,size_class,variant\n'
        def manifest_rows():
            return ''.join('%s,CC0,%s,name,1,1,variable,unassigned\n' %
                           (probe.hashlib.sha256(data).hexdigest(), name) for name, data in blobs.items())
        def read(path):
            return blobs[str(path)]
        train = [probe.base.bits(bytes([blobs[x][38+65536]])) for x in ('a','b')]
        table = [probe.base.counts(x, 8) for x in train]
        summed = [[sum(t[i][b] for t in table) for b in (0,1)] for i in range(256)]
        expected = probe.hashlib.sha256(json.dumps(summed, separators=(',', ':')).encode('ascii')).hexdigest()
        ledger = [(0, [2048], '')] + [(0, [], '') for _ in range(7)] + [(0, [2048]*256, expected)]
        argv = ['--manifest','m','--discovery','a','b','--validation','c']
        def run():
            out = io.StringIO()
            with patch('builtins.open', return_value=io.StringIO(fields+manifest_rows())), \
                 patch.object(Path, 'read_bytes', autospec=True, side_effect=read), patch.object(probe, 'SIZE', 1), \
                 patch.object(probe, 'models', return_value=ledger), contextlib.redirect_stdout(out):
                code = probe.main(argv)
            return code, json.loads(out.getvalue())
        code, report = run()
        self.assertEqual(code, 0)
        self.assertEqual(report['calibration_offset'], 196608)
        self.assertEqual(report['evaluation_offsets'], [262144,327680])
        self.assertEqual(report['samples'][0]['input']['window_offset'], 196608)
        self.assertEqual(len(report['samples'][0]['evaluation']), 2)
        short = bytearray(blobs['c'][:-1])
        short[30:34] = struct.pack('<I', 327680)
        blobs['c'] = bytes(short)
        code, report = run()
        self.assertEqual(code, 1)
        self.assertFalse(report['complete'])
        self.assertEqual(report['failures'], [{'role':'validation', 'ordinal':1,
                                               'offset':327680, 'error':'ValueError'}])
        blobs['c'] = blobs['a']
        code, report = run()
        self.assertEqual(code, 1)
        self.assertFalse(report['complete'])
        blobs['c'] = fixture(3)
        with patch.object(probe, 'EXPECTED', 'wrong'):
            with self.assertRaises(ValueError):
                probe.models(train)

    def test_invalid_manifest_yields_incomplete_no_private_text(self):
        out = io.StringIO()
        with patch('builtins.open', side_effect=OSError('PRIVATE_PATH')), contextlib.redirect_stdout(out):
            code = probe.main(['--manifest','PRIVATE_PATH','--discovery','a','b','--validation','c'])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out.getvalue()), {'complete': False, 'error': 'invalid input or frozen model'})
        self.assertNotIn('PRIVATE_PATH', out.getvalue())


if __name__ == '__main__':
    unittest.main()
