#!/usr/bin/env python3
"""Synthetic controls for token_phase_context_probe; stdlib, no file writes."""
import contextlib
import io
import json
import math
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_phase_context_probe as probe


class PhaseContextTests(unittest.TestCase):
    def test_public_identity_validation(self):
        for second in [('01', 'public'), ('2', ''), ('2', 'private/name'),
                       ('2', 'private\\name'), ('2', 'private\nname')]:
            argv = ['probe', '--sample', '1', 'public', 'unused', '--sample', *second, 'unused']
            out, err = io.StringIO(), io.StringIO()
            with self.subTest(second=second):
                with mock.patch.object(sys, 'argv', argv), mock.patch.object(probe, 'report', return_value={'prefix_shortfall': 0}) as report, \
                        contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as raised:
                    probe.main()
                self.assertEqual(raised.exception.code, 2)
                report.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())
        def fake_report(sample_id, public_name, path):
            return {'pixls_id': sample_id, 'pixls_name': public_name, 'prefix_shortfall': 0}
        out = io.StringIO()
        with mock.patch.object(sys, 'argv', ['probe', '--sample', '01', 'Camera "é" (4:3).ORF', 'unused']), \
                mock.patch.object(probe, 'report', side_effect=fake_report), \
                contextlib.redirect_stdout(out):
            self.assertEqual(probe.main(), 0)
        row = json.loads(out.getvalue())['samples'][0]
        self.assertEqual((row['pixls_id'], row['pixls_name']), ('01', 'Camera "é" (4:3).ORF'))
        with mock.patch.object(sys, 'argv', ['probe', '--sample', '1', 'public', 'unused']), \
                mock.patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True), \
                mock.patch.object(probe, 'report') as report, contextlib.redirect_stderr(io.StringIO()) as err, \
                self.assertRaises(SystemExit) as raised:
            probe.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertNotIn('private detail', err.getvalue())
        report.assert_not_called()

    def test_balanced_xor(self):
        table = [[[0, 0] for _ in range(2)] for _ in range(4)]
        for c in range(4):
            for p in range(2):
                table[c][p][(c & 1) ^ p] = 10
        result = probe.table_statistics(table)
        self.assertEqual(result['plugin_phase_mi_bits'], 0)
        self.assertEqual(result['plugin_conditional_phase_mi_bits'], 1)
        self.assertEqual(result['context_counts'], [20] * 4)

    def test_context_only_and_independent(self):
        table = [[[10 if y == (c & 1) else 0 for y in range(2)]
                  for _ in range(3)] for c in range(4)]
        self.assertEqual(probe.table_statistics(table)['plugin_conditional_phase_mi_bits'], 0)
        table = [[[5, 5] for _ in range(3)] for _ in range(4)]
        self.assertEqual(probe.table_statistics(table)['plugin_conditional_phase_mi_bits'], 0)

    def test_direct_contingency_identity(self):
        table = [[[(c + p) % 5, (2 * c + p + 1) % 7] for p in range(7)] for c in range(4)]
        n = sum(count for stratum in table for row in stratum for count in row)
        expected = 0
        for stratum in table:
            nc = sum(map(sum, stratum))
            for row in stratum:
                for y, count in enumerate(row):
                    if count:
                        ny = sum(pair[y] for pair in stratum)
                        expected += count / n * math.log2(count * nc / (sum(row) * ny))
        self.assertAlmostEqual(probe.table_statistics(table)['plugin_conditional_phase_mi_bits'], expected, places=13)

    def test_selection_absolute_indices_and_context(self):
        tokens = [(0, s) for s in [0, 16, 4, 20, 0, 4, 16, 20]]
        tokens[3] = (17, 20)
        result = probe.phase_context_statistics(tokens)
        self.assertEqual(result['initial_context_unavailable'], 2)
        self.assertEqual(result['escape_omitted_triples'], 3)
        self.assertEqual(result['retained_triples'], 3)
        # Retained absolute targets 2,6,7; contexts 2,0,3 and targets 1,0,1.
        table = result['moduli'][0]['context_by_phase_by_target']
        self.assertEqual(table[2][0][1], 1)
        self.assertEqual(table[0][0][0], 1)
        self.assertEqual(table[3][1][1], 1)
        self.assertEqual(sum(result['moduli'][0]['context_counts']), 3)

    def test_empty_and_short(self):
        for tokens in ([], [(0, 0)], [(0, 0), (0, 0)], [(17, 0)] * 5):
            result = probe.phase_context_statistics(tokens)
            self.assertEqual(result['retained_triples'], 0)
            self.assertTrue(all(x['plugin_conditional_phase_mi_bits'] is None for x in result['moduli']))

    def test_invalid(self):
        for tokens in ([(True, 0)], [(0, 32)], [(-1, 0)], [(0, False)]):
            with self.assertRaises(ValueError):
                probe.phase_context_statistics(tokens)
        for table in ([], [[[1, 2]]] * 3, [[[1, -1]]] * 4):
            with self.assertRaises(ValueError):
                probe.table_statistics(table)


class HeldoutPhaseTests(unittest.TestCase):
    def test_score_independent_observation_oracle(self):
        train, test = [[3, 7], [0, 0], [9, 1]], [[2, 4], [1, 2], [3, 1]]
        result = probe.predictive_score(train, test)
        losses = []
        for context, row in enumerate(test):
            for outcome, count in enumerate(row):
                probability = (2 * train[context][outcome] + 1) / (2 * sum(train[context]) + 2)
                losses.extend([-math.log(probability, 2)] * count)
        self.assertAlmostEqual(result['heldout_log_loss_bits'], sum(losses) / len(losses), places=13)
        self.assertEqual(result['test_targets_in_unseen_training_contexts'], 3)
        self.assertEqual((result['training_targets'], result['test_targets']), (20, 13))

    def test_balanced_conditional_phase_and_context_only(self):
        # Exact synthetic tables exercise predictive transfer separately from parsing.
        for context_only in (False, True):
            train = [[0, 0] for _ in range(8)]
            for c in range(4):
                for p in range(2):
                    train[2*c+p][(c & 1) if context_only else (c & 1) ^ p] = 100
            phase = probe.predictive_score(train, train)['heldout_log_loss_bits']
            pooled = [[train[2*c][y]+train[2*c+1][y] for y in range(2)] for c in range(4)]
            baseline = probe.predictive_score(pooled, pooled)['heldout_log_loss_bits']
            if context_only:
                self.assertLess(baseline - phase, 0)  # extra smoothing cost retained
            else:
                self.assertGreater(baseline - phase, 0.99)

    def test_tables_against_absolute_index_oracle(self):
        tokens = [(0, (t * t + 7*t + t//9) % 32) for t in range(4*128+5)]
        tokens[128+50] = (17, 0)
        tokens[-1] = (17, 0)
        result = probe.heldout_statistics(tokens)
        self.assertEqual(result['retained_train_test_blocks'], [2, 1])
        self.assertEqual(result['escape_omitted_train_test_blocks'], [0, 1])
        self.assertEqual(result['retained_train_test_targets'], [252, 126])
        self.assertEqual((result['tail_tokens'], result['tail_escapes']), (5, 1))
        for row in result['moduli']:
            m = row['modulus']
            expected = [[[[0, 0] for _ in range(m)] for _ in range(4)] for _ in range(2)]
            for t in range(len(tokens)):
                block, local = divmod(t, 128)
                if block not in (0, 2, 3) or local < 2:
                    continue
                c = ((tokens[t-1][1] & 16) // 8) + ((tokens[t-2][1] & 4) // 4)
                y = (tokens[t][1] & 4) // 4
                expected[block % 2][c][t % m][y] += 1
            self.assertEqual(row['training_context_by_phase_by_target'], expected[0])
            self.assertEqual(row['test_context_by_phase_by_target'], expected[1])
            for model in ('context_baseline', 'context_plus_phase'):
                self.assertEqual(row[model]['training_targets'], 252)
                self.assertEqual(row[model]['test_targets'], 126)

    def test_no_training_or_test_and_invalid(self):
        for tokens in ([], [(0, 0)]*128):
            result = probe.heldout_statistics(tokens)
            for row in result['moduli']:
                self.assertIsNone(row['gain_vs_context_bits'])
                self.assertIsNone(row['context_plus_phase']['heldout_log_loss_bits'])
        tokens = [(17, 0)]*128 + [(0, 0)]*128
        for row in probe.heldout_statistics(tokens)['moduli']:
            self.assertEqual(row['context_plus_phase']['heldout_log_loss_bits'], 1)
            self.assertEqual(row['context_plus_phase']['test_targets_in_unseen_training_contexts'], 126)
            self.assertIsNone(row['gain_vs_context_bits'])
        for tokens in ([(True, 0)], [(0, 32)], [(-1, 0)], [(0, False)]):
            with self.assertRaises(ValueError):
                probe.heldout_statistics(tokens)
        for train, test in (([], []), ([[0, 0]], []), ([[True, 0]], [[0, 1]])):
            with self.assertRaises(ValueError):
                probe.predictive_score(train, test)


if __name__ == '__main__':
    unittest.main()
