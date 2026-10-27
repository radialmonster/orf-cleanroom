#!/usr/bin/env python3
"""Synthetic direct-oracle and disjoint phase/period tests; no sample files."""
from array import array
import contextlib
from fractions import Fraction
import hashlib
import io
import json
import os
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_phase_stride_compare as P


class Tests(unittest.TestCase):
    def test_direct_oracle_and_period_transport(self):
        q = array('B', [(i * 17 + i // 7) % 13 for i in range(600)])
        out = P.diagnostic(q, 20, 12, 2, 5, 2)
        self.assertTrue(out['complete'])
        all_scores = []
        for row in out['best_phase_by_stride']:
            s = row['stride']
            direct = []
            for p in range(s):
                contrasts = []
                for r in range(5):
                    start = 20 + p + r * s
                    block = q[start:start+s]
                    contrasts.append(Fraction(sum(block[:2]), 2) - Fraction(sum(block[2:]), s-2))
                direct.append(sum(contrasts, Fraction()) / 5)
                all_scores.append((direct[-1], s, p))
                self.assertAlmostEqual(row['phase_means'][p], float(direct[-1]))
            self.assertAlmostEqual(row['train_mean'], max(direct))
            self.assertEqual(row['phase'], direct.index(max(direct)))
        best = max(x[0] for x in all_scores)
        expected = min((s, p) for value, s, p in all_scores if value == best)
        self.assertEqual((out['joint_selected']['stride'], out['joint_selected']['phase']), expected)
        for key in ('joint_selected', 'fixed_stride_selected', 'fixed_origin'):
            item = out[key]
            self.assertLess(item['train_end_exclusive'], out['test_barrier'])
            self.assertGreaterEqual(item['test_start'], out['test_barrier'])
            self.assertEqual((item['test_start']-20-item['phase']) % item['stride'], 0)
            self.assertLess(item['test_start'] - item['stride'], out['test_barrier'])
            values = []
            for r in range(5):
                start = item['test_start'] + r * item['stride']
                block = q[start:start + item['stride']]
                values.append(Fraction(sum(block[:2]), 2) - Fraction(sum(block[2:]), item['stride'] - 2))
            self.assertAlmostEqual(item['test_mean'], float(sum(values, Fraction()) / 5))
            self.assertEqual(item['test_end_exclusive'], item['test_start'] + 5 * item['stride'])

    def test_nonzero_cross_stride_equal_rational_tie(self):
        q = array('B', [0, 0, 0, 2, 2, 0, 1] * 100)
        out = P.diagnostic(q, 0, 4, 1, 3, 1)
        rows = {r['stride']: r for r in out['best_phase_by_stride']}
        self.assertEqual(Fraction(rows[3]['train_numerator'], rows[3]['train_denominator']), Fraction(2, 3))
        self.assertEqual(Fraction(rows[4]['train_numerator'], rows[4]['train_denominator']), Fraction(2, 3))
        maximum = max(Fraction(r['train_numerator'], r['train_denominator']) for r in rows.values())
        self.assertEqual(out['joint_selected']['stride'], min(s for s, r in rows.items() if Fraction(r['train_numerator'], r['train_denominator']) == maximum))
        self.assertEqual(out['joint_selected']['stride'], 3)

    def test_synthetic_tiff_cli_hash_and_shortfall(self):
        def fixture(payload):
            tags = ((256, 8), (257, 8), (273, 62), (279, len(payload)))
            return (b'II' + struct.pack('<HIH', 42, 8, len(tags))
                    + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags)
                    + bytes(4) + payload)
        data = fixture(b'\xff' * 100)
        digest = hashlib.sha256(data).hexdigest()
        for supplied, anchor, expected in ((digest, 0, 0), ('0' * 64, 0, 1), (digest, 1000, 1)):
            output = io.StringIO()
            with self.subTest(anchor=anchor, valid=supplied == digest), \
                 patch.object(P, 'ANCHOR', anchor), patch.object(P, 'CENTER', 4), \
                 patch.object(P, 'RADIUS', 1), patch.object(P, 'ROWS', 3), patch.object(P, 'HEAD', 1), \
                 patch('builtins.open', return_value=io.BytesIO(data)), contextlib.redirect_stdout(output):
                self.assertEqual(P.main(['--sample', '42', 'public', supplied, 'private-path']), expected)
            result = json.loads(output.getvalue())
            self.assertEqual(result['complete'], expected == 0)
            self.assertNotIn('private-path', output.getvalue())
            if supplied != digest:
                self.assertEqual(result['error'], 'ValueError')
            elif anchor:
                self.assertGreater(result['required_tokens'], result['parsed_tokens'])

    def test_constant_phase_and_changed_period(self):
        for period in (12, 13):
            q = array('B', [10 if (i-3) % period == 0 else 0 for i in range(700)])
            out = P.diagnostic(q, 0, 12, 1, 20, 1)
            self.assertEqual((out['joint_selected']['stride'], out['joint_selected']['phase']), (period, 3))
            self.assertAlmostEqual(out['joint_selected']['test_mean'], 10)
            if period == 12:
                self.assertEqual(out['heldout_joint_minus_fixed'], 0)
            else:
                self.assertGreater(out['heldout_joint_minus_fixed'], P.THRESHOLD)

    def test_zero_signal_ties_and_shortfall(self):
        out = P.diagnostic(array('B', [0] * 600), 10, 12, 2, 5, 2)
        self.assertEqual((out['joint_selected']['stride'], out['joint_selected']['phase']), (10, 0))
        self.assertEqual(out['heldout_joint_minus_fixed'], 0)
        self.assertTrue(all(r['ties'] == r['stride'] for r in out['best_phase_by_stride']))
        self.assertFalse(P.diagnostic(array('B', [0]), 10, 12, 2, 5, 2)['complete'])

    def test_heldout_changes_do_not_change_fitted_candidates(self):
        original = array('B', [(i * 7) % 11 for i in range(600)])
        first = P.diagnostic(original, 20, 12, 2, 5, 2)
        changed = array('B', original)
        for i in range(first['test_barrier'], len(changed)):
            changed[i] = (changed[i] + 5) % 11
        second = P.diagnostic(changed, 20, 12, 2, 5, 2)
        for key in ('joint_selected', 'fixed_stride_selected'):
            self.assertEqual((first[key]['stride'], first[key]['phase'], first[key]['train_mean']),
                             (second[key]['stride'], second[key]['phase'], second[key]['train_mean']))
        self.assertEqual(first['best_phase_by_stride'], second['best_phase_by_stride'])


if __name__ == '__main__':
    unittest.main()
