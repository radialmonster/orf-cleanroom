#!/usr/bin/env python3
"""Synthetic correctness checks for token_context_probe; no sample files needed."""
import contextlib
import copy
import io
import json
import math
import os
import random
import struct
import sys
import unittest
from collections import Counter
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_context_probe as probe


class ContextChecks(unittest.TestCase):
    def test_cli_complete_short_and_unreadable_inputs(self):
        def fixture(payload):
            tags = ((256, 8), (257, 1), (273, 62), (279, len(payload)))
            return (b'II' + struct.pack('<HIH', 42, 8, len(tags))
                    + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags)
                    + struct.pack('<I', 0) + payload)

        fixtures = {'complete': fixture(b'\xff\xff'), 'short': fixture(b'\xff')}
        original_open = open

        def open_fixture(path, *args, **kwargs):
            if path in fixtures:
                return io.BytesIO(fixtures[path])
            if path == 'missing':
                raise OSError('private diagnostic')
            return original_open(path, *args, **kwargs)

        for names, expected_status, expected_shortfalls in (
                (('complete',), 0, [0]), (('short',), 1, [1]),
                (('complete', 'short', 'missing'), 1, [0, 1]),
                (('missing',), 1, [])):
            argv = ['probe']
            for i, name in enumerate(names, 1):
                argv += ['--sample', str(i), 'public', name]
            output = io.StringIO()
            with self.subTest(names=names), mock.patch.object(sys, 'argv', argv), \
                    mock.patch.object(probe, 'LIMIT', 2), mock.patch('builtins.open', side_effect=open_fixture), \
                    contextlib.redirect_stdout(output):
                status = probe.main()
                result = json.loads(output.getvalue())
                self.assertEqual(status, expected_status)
                self.assertEqual([r['prefix_shortfall'] for r in result['samples']], expected_shortfalls)
                self.assertEqual(len(result['failures']), int('missing' in names))
                self.assertNotIn('private diagnostic', output.getvalue())

    def test_independent_tables_and_loss(self):
        rng = random.Random(104)
        blocks = [(i, [rng.randrange(32) for _ in range(128)]) for i in (0, 3, 4, 9)]
        for result in probe.fit_score(blocks):
            taps = result["context_taps_first_is_msb"]
            by_split = [Counter(), Counter()]
            for index, block in blocks:
                strings = [format(value, "05b") for value in block]
                for t in range(5, len(block)):
                    context = "".join(strings[t - lag][4 - bit] for bit, lag in taps)
                    key = int(context, 2) if context else 0
                    value = int(strings[t][4 - result["target_bit"]])
                    by_split[index % 2][(key, value)] += 1
            train = result["training_counts_context_by_outcome"]
            test = result["test_counts_context_by_outcome"]
            for split, table in enumerate((train, test)):
                self.assertEqual(table, [[by_split[split][(c, y)] for y in (0, 1)] for c in range(2 ** len(taps))])
            # Independent per-observation probability calculation, using logs
            # of numerator and denominator separately rather than their ratio.
            total_loss = 0
            for (context, outcome), n in by_split[1].items():
                denominator = sum(by_split[0][(context, y)] for y in (0, 1)) + 1
                numerator = by_split[0][(context, outcome)] + 0.5
                total_loss += n * (math.log2(denominator) - math.log2(numerator))
            expected = total_loss / sum(by_split[1].values())
            self.assertAlmostEqual(result["heldout_log_loss_bits"], expected, places=13)
            self.assertEqual(result["test_targets"], 246)

    def test_selection_preserves_original_parity(self):
        tokens = [(0, 0)] * (5 * 128 + 1)
        tokens[128] = (17, 1)
        tokens[-1] = (18, 2)
        blocks, selection = probe.select_blocks(tokens)
        self.assertEqual([i for i, _ in blocks], [0, 2, 3, 4])
        self.assertEqual(selection["retained_train_test_blocks"], [3, 1])
        self.assertEqual(selection["escape_omitted_train_test_blocks"], [0, 1])
        self.assertEqual(selection["tail_tokens"], 1)
        self.assertEqual(selection["tail_escapes"], 1)
        self.assertEqual(selection["parsed_escapes"], 2)
        result = probe.fit_score(blocks)[0]
        self.assertEqual(result["training_targets"], 369)
        self.assertEqual(result["test_targets"], 123)

    def test_planted_copy_and_negative_transfer(self):
        rng = random.Random(317)
        blocks = []
        inverted = []
        for index in range(20):
            high = [rng.randrange(2) for _ in range(128)]
            block = [(high[t] << 4) | ((high[t - 1] if t else 0) << 2) for t in range(128)]
            blocks.append((index, block))
            inverted.append((index, [s ^ 4 for s in block] if index % 2 else list(block)))
        normal = {row["name"]: row for row in probe.fit_score(blocks)}
        changed = {row["name"]: row for row in probe.fit_score(inverted)}
        self.assertGreater(normal["b2_two"]["gain_vs_empty_bits"], 0.9)
        self.assertLess(changed["b2_two"]["gain_vs_empty_bits"], -5)
        self.assertLess(normal["b2_two"]["heldout_log_loss_bits"], 0.02)

    def test_common_targets_no_boundary_contexts_and_unseen(self):
        rows = probe.fit_score([(0, [0] * 128), (1, [31] * 128)])
        self.assertTrue(all(row["training_targets"] == row["test_targets"] == 123 for row in rows))
        self.assertEqual(rows[2]["test_targets_in_unseen_training_contexts"], 123)
        self.assertEqual(rows[2]["heldout_log_loss_bits"], 1)
        for row in probe.fit_score([]):
            self.assertIsNone(row["heldout_log_loss_bits"])
            self.assertIsNone(row["gain_vs_empty_bits"])
        for row in probe.fit_score([(1, [0] * 128)]):
            self.assertEqual(row["heldout_log_loss_bits"], 1)
            self.assertFalse(row["fitted_transfer"])
            self.assertIsNone(row["gain_vs_empty_bits"])

    def test_permutation_determinism_and_no_mutation(self):
        rng = random.Random(9)
        blocks = [(i, [rng.randrange(32) for _ in range(16)]) for i in range(4)]
        original = copy.deepcopy(blocks)
        first = probe.measure(blocks)
        self.assertEqual(first, probe.measure(blocks))
        self.assertEqual(blocks, original)
        for row in first:
            self.assertEqual(len(row["permuted_scores"]), 16)
        constants = probe.measure([(0, [0] * 128), (1, [0] * 128)])
        for row in constants:
            self.assertEqual([x["heldout_log_loss_bits"] for x in row["permuted_scores"]], [row["heldout_log_loss_bits"]] * 16)

    def test_cli_mixed_success_and_invalid_id(self):
        args = ["probe", "--sample", "1", "public", "valid", "--sample", "2", "public", "private-path"]
        stream = io.StringIO()
        with mock.patch.object(sys, "argv", args), mock.patch.object(probe, "report", side_effect=[{"pixls_id": "1", "prefix_shortfall": 0}, OSError("private-path")]), contextlib.redirect_stdout(stream):
            self.assertEqual(probe.main(), 1)
        result = json.loads(stream.getvalue())
        self.assertEqual(result["samples"], [{"pixls_id": "1", "prefix_shortfall": 0}])
        self.assertEqual(result["failures"], [{"pixls_id": "2", "error": "OSError"}])
        self.assertNotIn("private-path", stream.getvalue())
        with mock.patch.object(sys, "argv", ["probe", "--sample", "0", "public", "x"]), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            probe.main()
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
