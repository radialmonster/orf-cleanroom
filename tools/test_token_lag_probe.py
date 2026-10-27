#!/usr/bin/env python3
"""Synthetic tests for lead #29 lag probe; no external inputs or outputs."""
import collections
import contextlib
import io
import json
import math
import os
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_lag_probe as probe


class LagTests(unittest.TestCase):
    def test_identity_rejected_before_any_report(self):
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
            conversion = mock.patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated, case=samples[-1][0][:4]), mock.patch.object(probe, 'report') as measured, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    with mock.patch.object(sys, 'argv', ['probe'] + args):
                        probe.main()
                self.assertEqual(caught.exception.code, 2)
                measured.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_valid_public_identity_spelling_is_preserved(self):
        name = 'OM - Élite "camera" (4:3).ORF'
        def echo(sid, public, path):
            return {'pixls_id': sid, 'pixls_name': public, 'prefix_complete': True, 'prefix_shortfall': 0}
        args = ['--sample', '01', name, 'unused']
        out = io.StringIO()
        with mock.patch.object(probe, 'report', side_effect=echo), contextlib.redirect_stdout(out):
            with mock.patch.object(sys, 'argv', ['probe'] + args):
                status = probe.main()
        self.assertEqual(status, 0)
        sample = json.loads(out.getvalue())['samples'][0]
        self.assertEqual((sample['pixls_id'], sample['pixls_name']), ('01', name))


    def test_cli_prefix_status_and_preserved_reports(self):
        def fixture(payload):
            tags = ((256, 25), (257, 1), (273, 62), (279, len(payload)))
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
        for names, expected, shortfalls in ((('complete',), 0, [0]), (('short',), 1, [1]),
                                            (('complete', 'short'), 1, [0, 1]),
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
                self.assertEqual(status, expected)
                self.assertEqual([r['prefix_shortfall'] for r in result['samples']], shortfalls)
                self.assertEqual(len(result['failures']), int('missing' in names))
                self.assertNotIn('private diagnostic', output.getvalue())

    def test_independent_pair_enumeration(self):
        blocks = [[(i % 4, (i * 7) % 32) for i in range(128)],
                  [(i % 3, (i * 5) % 32) for i in range(128)]]
        for cell in probe.lag_tables(blocks):
            lag = cell["lag"]
            for name, field in (("q_positive", 0), ("low3", 1)):
                counts = collections.Counter()
                for block in blocks:
                    for j in range(lag, len(block)):
                        a, b = block[j - lag][field], block[j][field]
                        if field == 0:
                            a, b = int(a > 0), int(b > 0)
                        else:
                            a, b = a & 7, b & 7
                        counts[a, b] += 1
                table = cell[name + "_counts"]
                self.assertEqual(sum(counts.values()), 2 * (128 - lag))
                for a in range(len(table)):
                    for b in range(len(table)):
                        self.assertEqual(table[a][b], counts[a, b])
                def entropy(values):
                    total = sum(values)
                    return -sum(c / total * math.log2(c / total) for c in values if c)
                rows, cols = collections.Counter(), collections.Counter()
                for (a, b), count in counts.items():
                    rows[a] += count
                    cols[b] += count
                expected = entropy(rows.values()) + entropy(cols.values()) - entropy(counts.values())
                self.assertAlmostEqual(cell[name + "_mi_bits"], expected, places=12)

    def test_no_cross_block_or_escape_pairs(self):
        tokens = [(0, 0)] * 128 + [(17, 7)] * 128 + [(1, 7)] * 128 + [(18, 4)]
        blocks, counts = probe.select_blocks(tokens)
        self.assertEqual(counts["retained_tokens"], 256)
        self.assertEqual(counts["escape_omitted_blocks"], 1)
        self.assertEqual(counts["tail_tokens"], 1)
        self.assertEqual(counts["tail_escapes"], 1)
        self.assertEqual(counts["parsed_escapes"], 129)
        for cell in probe.measure(blocks):
            self.assertEqual(cell["pairs"], 2 * (128 - cell["lag"]))
            self.assertEqual(cell["q_positive_counts"][0][1], 0)
            self.assertEqual(cell["q_positive_mi_bits"], 1)
            self.assertEqual(cell["q_positive_permuted_mi_bits"], [1] * 16)

    def test_null_permutation_and_input_preservation(self):
        blocks = [[(i % 2, i % 8) for i in range(128)]]
        before = [list(block) for block in blocks]
        first = probe.measure(blocks)
        self.assertEqual(blocks, before)
        self.assertEqual(first, probe.measure(blocks))
        self.assertEqual(first[0]["q_positive_mi_bits"], probe.mutual_information([[0, 64], [63, 0]]))
        self.assertLess(first[0]["q_positive_permuted_mean_bits"], 0.1)

    def test_empty_and_degenerate(self):
        for cell in probe.measure([]):
            self.assertEqual(cell["pairs"], 0)
            self.assertIsNone(cell["q_positive_mi_bits"])
            self.assertIsNone(cell["low3_permuted_mean_bits"])
        for cell in probe.measure([[(0, 0)] * 128]):
            self.assertEqual(cell["q_positive_mi_bits"], 0)
            self.assertEqual(cell["low3_mi_bits"], 0)

    def test_mixed_failure_cli(self):
        with mock.patch.object(sys, "argv", ["probe", "--sample", "1", "a", "a",
                                             "--sample", "2", "b", "b"]):
            with mock.patch.object(probe, "report", side_effect=[{"pixls_id": "1"}, ValueError("private")]):
                with mock.patch("builtins.print") as printer:
                    self.assertEqual(probe.main(), 1)
                    payload = printer.call_args[0][0]
                    self.assertIn('"pixls_id": "1"', payload)
                    self.assertIn('"error": "ValueError"', payload)
                    self.assertNotIn("private", payload)


if __name__ == "__main__":
    unittest.main()
