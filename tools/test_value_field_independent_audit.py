"""Synthetic guard, omissions and aggregate controls."""
import unittest
import os
import sys
import io
import hashlib
import json
import contextlib
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_field_independent_audit as reference


def payload(bits):
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


class Tests(unittest.TestCase):
    def test_cli_hash_gate(self):
        data = b'synthetic'
        digest = hashlib.sha256(data).hexdigest()
        result = {'status': 'ok', 'sentinel': 4}
        with mock.patch.object(reference, 'open', return_value=io.BytesIO(data), create=True), \
             mock.patch.object(reference, 'independent_strips', return_value=({'width': 6, 'height': 1000}, b'payload')), \
             mock.patch.object(reference, 'parse', return_value=([1], None)), \
             mock.patch.object(reference, 'evaluate', return_value=result):
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', ['audit', '--sample', 'public.ORF', digest, 'private']), contextlib.redirect_stdout(out):
                self.assertEqual(reference.main(), 0)
            self.assertEqual(json.loads(out.getvalue())['result'], result)
            self.assertNotIn('private', out.getvalue())
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', ['audit', '--sample', 'public.ORF', '0'*64, 'private']), contextlib.redirect_stdout(out):
                self.assertEqual(reference.main(), 1)
            self.assertEqual(json.loads(out.getvalue())['status'], 'unknown')

    def test_all_32_gray_values(self):
        expected = [(1,1,1), (1,1,0), (0,1,0), (0,1,1),
                    (0,0,1), (0,0,0), (1,0,0), (1,0,1)]
        for block, (y, x, ny) in enumerate(expected):
            n = ny ^ y
            b = (y << 4) | ((1 - n) << 3)
            for low in range(4):
                self.assertEqual(reference.assembled((x << 2) | low, b), -20 + 4*block + low)

    def test_guard_and_escape(self):
        data = payload('1' + '100001' + '0'*12 + '1'*12 + '100010' + '1'*24)
        words, error = reference.parse(data, 3)
        self.assertIsNone(error)
        self.assertEqual(list(words), [1, -1, 2])
        self.assertEqual(reference.parse(b'\0'*8, 1)[1], 'missing_marker')
        self.assertEqual(reference.parse(payload('1'+'100001'), 1)[1], 'short_guarded_parse')

    def test_formula_and_omissions(self):
        width, rows = 6, 4
        words = [i % 32 for i in range((rows+1)*width)]
        words[8] = -1
        result = reference.evaluate(words, width, rows, top=1, edge=1)
        self.assertEqual(result['valued'] + result['skipped'], 12)
        self.assertGreater(result['skipped'], 0)
        self.assertLess(result['lags']['1']['pairs'], result['valued'])
        self.assertEqual(sum(result['histogram'].values()), result['valued'])

    def test_empty_and_zero_variance(self):
        self.assertEqual(reference.evaluate([], 2, 4)['reason'], 'insufficient_support')
        result = reference.evaluate([0]*30, 6, 4, top=1, edge=1)
        self.assertEqual(result['reason'], 'zero_variance')
        self.assertIsNone(result['lags']['1']['r'])

    def test_pair_support_and_null_partner(self):
        width, rows = 6, 4
        words = [i % 32 for i in range((rows+1)*width)]
        result = reference.evaluate(words, width, rows, top=1, edge=1)
        self.assertEqual(result['lags']['1']['pairs'], 9)
        self.assertEqual(result['lags']['2']['pairs'], 6)
        self.assertEqual(result['lags']['W']['pairs'], 8)
        normal = reference.evaluate(words, width, rows, top=1, edge=1)
        shifted = reference.evaluate(words, width, rows, top=1, edge=1, null=True)
        self.assertNotEqual(normal['histogram'], shifted['histogram'])
        masked = [-1] * len(words)
        masked[7:10] = [0, 1, 2]
        one = reference.evaluate(masked, width, rows, top=1, edge=1)
        self.assertEqual(one['lags']['1']['pairs'], 1)
        self.assertEqual(one['lags']['1']['status'], 'insufficient_pairs')

    def test_constant_class_and_same_mean_nonconstant_control(self):
        width, rows = 8, 6
        # Even candidate sites read 0; odd sites read -4.
        words = [8 if (r+c) % 2 else 0
                 for r in range(rows+1) for c in range(width)]
        result = reference.evaluate(words, width, rows, top=1, edge=1)
        self.assertEqual(result['classes'][1]['histogram']['-4'], 15)
        self.assertEqual(sum(n != 0 for n in result['classes'][1]['histogram'].values()), 1)
        shorter = reference.evaluate(words, width, rows=3, top=1, edge=1)
        self.assertEqual(shorter['classes'][1]['histogram']['-4'], 6)
        # The two odd sites now read -5 and -3. Their mean stays -4,
        # while the exact class histogram must reject constancy.
        words[10] = 7
        words[12] = 9
        control = reference.evaluate(words, width, rows, top=1, edge=1)
        self.assertEqual(control['classes'][1]['mean'], -4)
        self.assertEqual(control['classes'][1]['histogram']['-5'], 1)
        self.assertEqual(control['classes'][1]['histogram']['-3'], 1)
        self.assertEqual(control['classes'][1]['histogram']['-4'], 13)


if __name__ == '__main__':
    unittest.main()
