#!/usr/bin/env python3
"""Independent synthetic checks for #29 item-4 pairwise lag probe."""
import collections
import contextlib
import io
import json
import math
import os
import random
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from token_bit_chain_probe import BITS, LAGS, measure, tables  # noqa: E402
import token_bit_chain_probe as probe  # noqa: E402
from suffix_joint_probe import BLOCK, REPLICATES, select_blocks  # noqa: E402


def entropy(labels):
    counts = collections.Counter(labels)
    n = len(labels)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


class ChainTests(unittest.TestCase):
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

    def test_every_ordered_table_and_entropy(self):
        blocks = [[(7 * i + i // 3) % 32 for i in range(31)], [0, 4, 16, 20] * 7]
        results = measure(blocks)
        self.assertEqual(len(results), 20)
        for r in results:
            pairs = []
            for block in blocks:
                lag = r["lag_tokens"]
                pairs.extend(((block[i - lag] >> r["source_bit"]) % 2,
                              (block[i] >> r["target_bit"]) % 2) for i in range(lag, len(block)))
            counter = collections.Counter(pairs)
            expected = [[counter[(a, b)] for b in (0, 1)] for a in (0, 1)]
            self.assertEqual(r["joint_source_rows_target_columns"], expected)
            self.assertEqual(r["pair_count"], len(pairs))
            mi = entropy([a for a, b in pairs]) + entropy([b for a, b in pairs]) - entropy(pairs)
            self.assertAlmostEqual(r["plugin_mi_bits"], mi, places=12)

    def test_direction_and_planted_delayed_copy(self):
        rng = random.Random(8801)
        blocks = []
        for _ in range(8):
            bits = [rng.randrange(2) for _ in range(BLOCK + 1)]
            blocks.append([4 * bits[i + 1] + 16 * bits[i] for i in range(BLOCK)])
        report = {(r["lag_tokens"], r["source_bit"], r["target_bit"]): r for r in measure(blocks)}
        planted = report[(1, 2, 4)]
        self.assertGreater(planted["plugin_mi_bits"], .99)
        self.assertEqual(planted["pearson"], 1)
        self.assertLess(max(planted["permuted_plugin_mi_bits"]), .03)
        self.assertLess(report[(1, 4, 2)]["plugin_mi_bits"], .03)

    def test_no_boundary_or_escape_gap_pairs(self):
        tokens = [(0, 0)] * BLOCK + [(17, 20)] * BLOCK + [(0, 20)] * BLOCK + [(0, 4)] * 3
        blocks, counts = select_blocks(tokens)
        self.assertEqual(counts["escape_omitted_blocks"], 1)
        self.assertEqual(counts["tail_tokens"], 3)
        for (lag, source, target), table in tables(blocks).items():
            self.assertEqual(table, [[BLOCK - lag, 0], [0, BLOCK - lag]])

    def test_permutation_marginals_and_input_unchanged(self):
        blocks = [[0] * BLOCK, [20] * BLOCK]
        original = [list(b) for b in blocks]
        result = measure(blocks)
        self.assertEqual(blocks, original)
        self.assertEqual(result, measure(blocks))
        for r in result:
            self.assertEqual(r["plugin_mi_bits"], 1)
            self.assertEqual(r["permuted_plugin_mi_bits"], [1] * REPLICATES)

    def test_empty_short_and_degenerate(self):
        self.assertEqual(LAGS, (1, 2, 3, 4, 5))
        self.assertEqual(BITS, (2, 4))
        for r in measure([[], [20]]):
            self.assertEqual(r["pair_count"], 0)
            self.assertIsNone(r["plugin_mi_bits"])
            self.assertIsNone(r["pearson"])
            self.assertEqual(r["permuted_plugin_mi_bits"], [None] * REPLICATES)
            self.assertIsNone(r["permuted_mi_mean_bits"])
        for r in measure([[20] * BLOCK]):
            self.assertEqual(r["plugin_mi_bits"], 0)
            self.assertIsNone(r["pearson"])

    def run_actual_cli(self, counts):
        # Original in-memory TIFFs; no disk fixtures or child processes.
        fixtures = {}
        for index, count in enumerate(counts):
            if count is None:
                continue
            bits = '100000' * count
            bits += '0' * ((-len(bits)) % 8)
            payload = (int(bits, 2).to_bytes(len(bits) // 8, 'big')
                       if bits else b'\x00')
            data = b'II' + struct.pack('<HIH', 42, 8, 4)
            for tag, value in ((256, 8), (257, 1), (273, 62), (279, len(payload))):
                data += struct.pack('<HHII', tag, 4, 1, value)
            fixtures['fixture-%d' % index] = data + struct.pack('<I', 0) + payload
        original_open = open

        def read_fixture(path, mode='r', *args, **kwargs):
            if path in fixtures:
                self.assertEqual(mode, 'rb')
                return io.BytesIO(fixtures[path])
            if path == 'fixture-%d' % (len(counts) - 1) and counts[-1] is None:
                raise OSError('PRIVATE_INPUT_DETAILS')
            return original_open(path, mode, *args, **kwargs)

        argv = ['probe']
        for index in range(len(counts)):
            argv.extend(['--sample', str(index + 1), 'public-%d' % index,
                         'fixture-%d' % index])
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', argv), mock.patch.object(probe, 'LIMIT', 256):
            with mock.patch('builtins.open', side_effect=read_fixture):
                with contextlib.redirect_stdout(output):
                    status = probe.main()
        self.assertNotIn('PRIVATE_INPUT_DETAILS', output.getvalue())
        self.assertNotIn('fixture-', output.getvalue())
        return status, json.loads(output.getvalue())

    def test_actual_cli_exact_complete_prefix(self):
        status, result = self.run_actual_cli([256])
        self.assertEqual(status, 0)
        sample = result['samples'][0]
        self.assertEqual((sample['returned_tokens'], sample['prefix_shortfall']), (256, 0))
        self.assertEqual(sample['bits_consumed'], 1536)
        self.assertEqual(sample['selection']['retained_blocks'], 2)
        self.assertEqual(sample['statistics'][0]['pair_count'], 254)
        self.assertEqual(sample['statistics'][0]['plugin_mi_bits'], 0)

    def test_actual_cli_short_prefix_retains_diagnostics(self):
        status, result = self.run_actual_cli([255])
        self.assertEqual(status, 1)
        sample = result['samples'][0]
        self.assertEqual((sample['returned_tokens'], sample['prefix_shortfall']), (255, 1))
        self.assertEqual(sample['bits_consumed'], 1530)
        self.assertEqual(sample['selection']['tail_tokens'], 127)
        self.assertEqual(sample['statistics'][0]['pair_count'], 127)
        self.assertEqual(sample['statistics'][0]['plugin_mi_bits'], 0)
        self.assertEqual(result['failures'], [])

    def test_actual_cli_empty_prefix(self):
        status, result = self.run_actual_cli([0])
        self.assertEqual(status, 1)
        sample = result['samples'][0]
        self.assertEqual((sample['returned_tokens'], sample['prefix_shortfall']), (0, 256))
        self.assertEqual(sample['bits_consumed'], 0)
        self.assertTrue(all(row['pair_count'] == 0 for row in sample['statistics']))
        self.assertTrue(all(row['plugin_mi_bits'] is None for row in sample['statistics']))

    def test_actual_cli_mixed_complete_and_short(self):
        status, result = self.run_actual_cli([256, 255])
        self.assertEqual(status, 1)
        self.assertEqual([r['prefix_shortfall'] for r in result['samples']], [0, 1])
        self.assertEqual(result['failures'], [])

    def test_actual_cli_mixed_input_exception_retains_short_and_complete(self):
        status, result = self.run_actual_cli([256, 255, None])
        self.assertEqual(status, 1)
        self.assertEqual([r['prefix_shortfall'] for r in result['samples']], [0, 1])
        self.assertEqual(result['failures'], [{'pixls_id': '3', 'error': 'OSError'}])

    def test_cli_retains_success_and_sanitizes_failure(self):
        output = io.StringIO()
        argv = ["probe", "--sample", "1", "public-good", "local-good",
                "--sample", "2", "public-bad", "private-missing-path"]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(
                probe, "report", side_effect=[{"pixls_id": "1"}, OSError("private-missing-path")]):
            with contextlib.redirect_stdout(output):
                status = probe.main()
        self.assertEqual(status, 1)
        self.assertNotIn("private-missing-path", output.getvalue())
        result = json.loads(output.getvalue())
        self.assertEqual(result["samples"], [{"pixls_id": "1"}])
        self.assertEqual(result["failures"], [{"pixls_id": "2", "error": "OSError"}])


if __name__ == "__main__":
    unittest.main()
