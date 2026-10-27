#!/usr/bin/env python3
"""Synthetic controls for the phase-offset diagnostic; stdlib, no writes."""
import math
import contextlib
import io
import json
import os
import random
import sys
import unittest
from unittest.mock import patch
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_phase_surrogate_probe as probe
import token_phase_context_probe as reference


class PhaseSurrogateTests(unittest.TestCase):
    def test_identity_rejected_before_any_measurement(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        cases = [([('1', 'public'), ('0', 'public')], False),
                 ([('1', 'public'), ('\u0661', 'public')], False),
                 ([('1', 'public'), ('01', 'public')], False),
                 ([('1', 'public'), ('2', '')], False),
                 ([('1', 'public'), ('2', 'private/path')], False),
                 ([('1', 'public'), ('2', 'private\\path')], False),
                 ([('1', 'public'), ('2', 'bad\nname')], False),
                 ([('1', 'public'), ('2', 'public')], True)]
        if limit:
            cases.append(([('1', 'public'), ('9' * (limit + 1), 'public')], False))
        for samples, simulated in cases:
            args = []
            for sid, name in samples:
                args += ['--sample', sid, name, 'unused']
            out, err = io.StringIO(), io.StringIO()
            conversion = patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated, case=samples[-1][0][:4]), patch.object(probe, 'report') as measured, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(args)
                self.assertEqual(caught.exception.code, 2)
                measured.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_valid_public_identity_spelling_is_preserved(self):
        name = 'OM - Élite "camera" (4:3).ORF'
        def echo(sid, public=None, path=None, *args):
            return {'pixls_id': sid, 'pixls_name': public, 'prefix_complete': True, 'prefix_shortfall': 0}
        args = ['--sample', '01', name, 'unused']
        out = io.StringIO()
        with patch.object(probe, 'report', side_effect=echo), contextlib.redirect_stdout(out):
            status = probe.main(args)
        self.assertEqual(status, 0)
        sample = json.loads(out.getvalue())['samples'][0]
        self.assertEqual((sample['pixls_id'], sample['pixls_name']), ('01', name))


    def test_observed_matches_existing_estimator_and_accounting(self):
        tokens = [(0, (t*t+7*t+t//9) % 32) for t in range(4*128+5)]
        tokens[128+50] = (17, 0)
        tokens[-1] = (18, 0)
        result = probe.measure(tokens)
        old = reference.heldout_statistics(tokens)
        for key in result['selection']:
            self.assertEqual(result['selection'][key], old[key])
        for row, expected in zip(result['moduli'], old['moduli']):
            for key in ('training_context_by_phase_by_target', 'test_context_by_phase_by_target',
                        'context_baseline', 'context_plus_phase', 'gain_vs_context_bits'):
                self.assertEqual(row['observed'][key], expected[key])
            for surrogate in row['surrogates']:
                self.assertEqual(surrogate['context_baseline'], expected['context_baseline'])
                self.assertEqual([sum(h) for h in surrogate['offset_histogram_train_test']], [2, 1])

    def test_shift_tables_against_independent_target_oracle(self):
        blocks = [(i % 2, [(i*128+t, (t+t//3) % 4, (t//2) % 2)
                            for t in range(2, 128)]) for i in range(4)]
        for m in range(2, 9):
            offsets = [i % m for i in (1, 3, 6, 9)]
            result = probe.combine(probe.block_tables(blocks, m), m, offsets)
            counts = Counter((split, c, (t+offset) % m, y)
                             for (split, triples), offset in zip(blocks, offsets)
                             for t, c, y in triples)
            for split, key in enumerate(('training_context_by_phase_by_target', 'test_context_by_phase_by_target')):
                for c in range(4):
                    for p in range(m):
                        for y in range(2):
                            self.assertEqual(result[key][c][p][y], counts[split, c, p, y])
            # Independent event-wise log-loss calculation.
            losses = []
            for split, triples in blocks:
                if split:
                    offset = offsets[blocks.index((split, triples))]
                    for t, c, y in triples:
                        p = (t+offset) % m
                        n0, n1 = counts[0,c,p,0], counts[0,c,p,1]
                        losses.append(-math.log2(((n0,n1)[y]+0.5)/(n0+n1+1)))
            self.assertAlmostEqual(sum(losses)/len(losses), result['context_plus_phase']['heldout_log_loss_bits'], places=12)

    def test_planted_phase_and_context_only(self):
        for context_only in (False, True):
            blocks = [(i % 2, [(t, (t//2) % 4,
                               ((t//2) % 4) & 1 if context_only else t % 2)
                              for t in range(128)]) for i in range(64)]
            tables = probe.block_tables(blocks, 2)
            observed = probe.combine(tables, 2, [0]*64)['gain_vs_context_bits']
            # Exactly balanced shifts in each split erase global parity alignment.
            control = probe.combine(tables, 2, [(i//2) % 2 for i in range(64)])['gain_vs_context_bits']
            if context_only:
                self.assertLess(observed, 0)
                self.assertEqual(observed, control)
            else:
                self.assertGreater(observed, 0.99)
                self.assertEqual(control, 0)  # both models predict exactly one half

    def test_seed_determinism_and_rank_accounting(self):
        tokens = [(0, (t*t+t//3) % 32) for t in range(6*128)]
        a, b = probe.measure(tokens), probe.measure(tokens)
        self.assertEqual(a, b)
        blocks, _ = probe.select_blocks(tokens)
        for row in a['moduli']:
            m = row['modulus']
            self.assertEqual(sum(row['descriptive_rank_counts'].values()), probe.REPLICATES)
            for r, surrogate in enumerate(row['surrogates']):
                rng = random.Random(probe.SEED+r)
                offsets = [rng.randrange(m) for _ in blocks]
                expected = [[offsets[split::2].count(p) for p in range(m)] for split in range(2)]
                self.assertEqual(surrogate['offset_histogram_train_test'], expected)

    def test_empty_no_train_no_test_and_invalid(self):
        for tokens in ([], [(0,0)]*128, [(17,0)]*128+[(0,0)]*128):
            for row in probe.measure(tokens)['moduli']:
                self.assertIsNone(row['descriptive_rank_counts'])
                self.assertIsNone(row['observed']['gain_vs_context_bits'])
                self.assertTrue(all(s['gain_vs_context_bits'] is None for s in row['surrogates']))
        for tokens in ([(True,0)], [(0,32)], [(-1,0)], [(0,False)]):
            with self.assertRaises(ValueError):
                probe.measure(tokens)
        for offsets in ([0], [-1,0], [0,2], [False,0]):
            with self.assertRaises(ValueError):
                probe.combine(probe.block_tables([(0,[]),(1,[])], 2), 2, offsets)


if __name__ == '__main__':
    unittest.main()
