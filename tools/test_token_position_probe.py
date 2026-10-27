#!/usr/bin/env python3
"""Synthetic tests for the nominal-position aggregate probe; no samples needed."""
import contextlib
import io
import json
import os
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_position_probe as probe


class PositionTests(unittest.TestCase):
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
            conversion = patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated, case=samples[-1][0][:4]), patch.object(probe, 'report') as measured, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    with patch.object(sys, 'argv', ['probe'] + args):
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
        with patch.object(probe, 'report', side_effect=echo), contextlib.redirect_stdout(out):
            with patch.object(sys, 'argv', ['probe'] + args):
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
            with self.subTest(names=names), patch.object(sys, 'argv', argv), \
                 patch.object(probe, 'LIMIT', 2), patch('builtins.open', side_effect=open_fixture), \
                 contextlib.redirect_stdout(output):
                status = probe.main()
                result = json.loads(output.getvalue())
                self.assertEqual(status, expected)
                self.assertEqual([r['prefix_shortfall'] for r in result['samples']], shortfalls)
                self.assertEqual(len(result['failures']), int('missing' in names))
                self.assertNotIn('private diagnostic', output.getvalue())

    def test_independent_histograms(self):
        tokens = [(i % 19, (7 * i) % 32) for i in range(112)]
        for width in (25, 27, 32):
            result = probe.position_statistics(tokens, width)
            used = len(tokens) // width * width
            for bin_index, cell in enumerate(result["positions_0_to_23_and_remainder"]):
                selected = [(q, s) for i, (q, s) in enumerate(tokens[:used])
                            if (i % width == bin_index if bin_index < 24 else i % width >= 24)]
                ordinary = [(q, s) for q, s in selected if q < 17]
                self.assertEqual(cell["candidate_tokens"], len(selected))
                self.assertEqual(cell["escape_omitted_tokens"], len(selected) - len(ordinary))
                self.assertEqual(cell["ordinary_q_counts_0_to_16"], [sum(q == k for q, _ in ordinary) for k in range(17)])
                self.assertEqual(cell["suffix_counts_0_to_31"], [sum(s == k for _, s in ordinary) for k in range(32)])
                self.assertEqual(cell["q_sum"], sum(q for q, _ in ordinary))
                self.assertEqual(cell["unsigned_suffix_sum"], sum(s for _, s in ordinary))
            self.assertEqual(result["incomplete_nominal_tail_escapes"], sum(q >= 17 for q, _ in tokens[used:]))

    def test_escape_keeps_position_and_tail(self):
        tokens = [(0, 0)] * 55
        tokens[0], tokens[1], tokens[25], tokens[50] = (17, 31), (1, 7), (2, 3), (18, 31)
        result = probe.position_statistics(tokens, 25)
        cells = result["positions_0_to_23_and_remainder"]
        self.assertEqual(cells[0]["escape_omitted_tokens"], 1)
        self.assertEqual(cells[0]["q_mean"], 2)
        self.assertEqual(cells[1]["unsigned_suffix_sum"], 7)
        self.assertEqual(result["incomplete_nominal_tail_tokens"], 5)
        self.assertEqual(result["incomplete_nominal_tail_escapes"], 1)
        self.assertEqual(result["parsed_escapes"], 2)

    def test_pool_and_planted_profile(self):
        tokens = [(4 if i % 30 < 10 else 0, 20 if i % 30 < 10 else 2) for i in range(90)]
        result = probe.position_statistics(tokens, 30)
        pools = result["pools"]
        self.assertEqual(pools["first10"]["q_mean"], 4)
        self.assertEqual(pools["remainder_after24"]["q_mean"], 0)
        self.assertEqual(pools["first24"]["unsigned_suffix_sum"], 3 * (10 * 20 + 14 * 2))
        self.assertEqual(pools["all_complete_rows"]["retained_tokens"], 90)
        self.assertEqual(pools["all_complete_rows"]["suffix_counts_0_to_31"],
                         [sum(s == k for _, s in tokens) for k in range(32)])

    def test_empty_short_all_escape_and_invalid(self):
        for tokens in ([], [(0, 3)] * 24, [(17, 31)] * 50):
            result = probe.position_statistics(tokens, 25)
            self.assertIsNone(result["pools"]["all_complete_rows"]["q_mean"])
            self.assertIsNone(result["pools"]["all_complete_rows"]["unsigned_suffix_mean"])
        for tokens, width in (([], 24), ([], True), ([(-1, 0)], 25), ([(0, 32)], 25), ([(True, 0)], 25)):
            with self.assertRaises(ValueError):
                probe.position_statistics(tokens, width)

    def test_cli_preserves_success_and_sanitizes_failure(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["probe", "--sample", "1", "public", "good", "--sample", "2", "public", "bad"]), patch.object(probe, "report", side_effect=[{"pixls_id": "1"}, ValueError("SECRET_PATH")]), contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(), 1)
        text = output.getvalue()
        self.assertNotIn("SECRET_PATH", text)
        result = json.loads(text)
        self.assertEqual(result["samples"], [{"pixls_id": "1"}])
        self.assertEqual(result["failures"], [{"pixls_id": "2", "error": "ValueError"}])


if __name__ == "__main__":
    unittest.main()
