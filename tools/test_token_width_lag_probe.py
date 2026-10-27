#!/usr/bin/env python3
"""Synthetic tests for nominal token-width lag measurements; no file writes."""
import contextlib
import io
import json
import math
import os
import random
import struct
import sys
import unittest
from unittest.mock import patch
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_width_lag_probe as probe


class WidthLagTests(unittest.TestCase):
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
            with self.subTest(simulated=simulated, case=samples[-1][0][:4]), patch.object(probe, 'report') as report, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(args)
                self.assertEqual(caught.exception.code, 2)
                report.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_valid_public_identity_spelling_is_preserved(self):
        name = 'OM - Élite "camera" (4:3).ORF'
        def echo(sid, public, path, *args):
            return {'pixls_id': sid, 'pixls_name': public, 'prefix_complete': True, 'token_shortfall': 0, 'shortfall_tokens': 0}
        args = ['--sample', '01', name, 'unused']
        out = io.StringIO()
        with patch.object(probe, 'report', side_effect=echo), contextlib.redirect_stdout(out):
            status = probe.main(args)
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
            args = []
            for i, name in enumerate(names, 1):
                args += ['--sample', str(i), 'public', name]
            output = io.StringIO()
            with self.subTest(names=names), patch.object(probe, 'LIMIT', 2), \
                 patch('builtins.open', side_effect=open_fixture), contextlib.redirect_stdout(output):
                status = probe.main(args)
                result = json.loads(output.getvalue())
                self.assertEqual(status, expected)
                self.assertEqual([r['shortfall_tokens'] for r in result['samples']], shortfalls)
                self.assertEqual(len(result['failures']), int('missing' in names))
                self.assertNotIn('private diagnostic', output.getvalue())

    def test_independent_enumeration_all_cells(self):
        rng = random.Random(7)
        tokens = [(17 if t in (9, 38, 43) else rng.randrange(4), rng.randrange(32)) for t in range(79)]
        for width in (3, 4, 8):
            for row in probe.measure(tokens, width):
                lag, bit = row["lag_tokens"], row["past_bit"]
                for cell in row["strata_then_pooled"]:
                    parity = cell["target_nominal_parity"]
                    indices = [t for t in range(lag, len(tokens))
                               if parity is None or [(t // width) & 1, (t % width) & 1] == parity]
                    pairs = [(int(format(tokens[t-lag][1], "05b")[4-bit]),
                              int(format(tokens[t][1], "05b")[2]))
                             for t in indices if max(tokens[t-lag][0], tokens[t][0]) < 17]
                    counts = Counter(pairs)
                    self.assertEqual(cell["past_by_current_counts"], [[counts[a,b] for b in (0,1)] for a in (0,1)])
                    self.assertEqual(cell["candidate_pairs"], len(indices))
                    self.assertEqual(cell["retained_pairs"], len(pairs))
                    self.assertEqual(cell["escape_endpoint_omitted_pairs"], len(indices)-len(pairs))
                    if pairs:
                        mx = sum(a for a,b in pairs)/len(pairs)
                        my = sum(b for a,b in pairs)/len(pairs)
                        vx = sum((a-mx)**2 for a,b in pairs)
                        vy = sum((b-my)**2 for a,b in pairs)
                        expected = sum((a-mx)*(b-my) for a,b in pairs)/math.sqrt(vx*vy) if vx and vy else None
                        if expected is None:
                            self.assertIsNone(cell["pearson"])
                        else:
                            self.assertAlmostEqual(cell["pearson"], expected, places=12)

    def test_no_renumbering_and_intervening_escape(self):
        tokens = [(0, (t % 2)*4) for t in range(15)]
        tokens[1] = (17, 0)
        pooled = probe.measure(tokens, 4)[0]["strata_then_pooled"][-1]
        self.assertEqual(pooled["candidate_pairs"], 11)
        self.assertEqual(pooled["escape_endpoint_omitted_pairs"], 1)
        self.assertEqual(pooled["retained_pairs"], 10)
        self.assertEqual(pooled["pearson"], 1)

    def test_planted_direction_and_negative_sign(self):
        # width=3, source b4(t-5) is opposite target b2(t), so 2W-1 is -1.
        rng = random.Random(9)
        high = [rng.randrange(2) for _ in range(90)]
        tokens = [(0, high[t]*16 + ((1-high[t-5])*4 if t>=5 else 0)) for t in range(90)]
        self.assertEqual(probe.measure(tokens, 3)[-1]["strata_then_pooled"][-1]["pearson"], -1)

    def test_empty_short_and_degenerate(self):
        for tokens in ([], [(0,0)], [(0,0)]*40, [(17,31)]*40):
            for row in probe.measure(tokens, 6):
                for cell in row["strata_then_pooled"]:
                    self.assertIsNone(cell["pearson"])
                    self.assertEqual(cell["candidate_pairs"], cell["retained_pairs"]+cell["escape_endpoint_omitted_pairs"])
        for width in (0,1,True,3.0):
            with self.assertRaises(ValueError):
                probe.measure([], width)
        with self.assertRaises(ValueError):
            probe.measure([(0,32)], 3)

    def test_pooled_is_sum_of_strata(self):
        for row in probe.measure([(0,t%32) for t in range(33)], 4):
            cells = row["strata_then_pooled"]
            for a in (0,1):
                for b in (0,1):
                    self.assertEqual(cells[-1]["past_by_current_counts"][a][b],
                                     sum(c["past_by_current_counts"][a][b] for c in cells[:4]))
            self.assertEqual(cells[-1]["candidate_pairs"], max(0,33-row["lag_tokens"]))

    def test_cli_partial_failure_sanitized(self):
        with patch.object(probe,"report",side_effect=[{"pixls_id":"1"}, OSError("private/path")]):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = probe.main(["--sample","1","public1","private1", "--sample","2","public2","private2"])
        doc = json.loads(out.getvalue())
        self.assertEqual(status,1)
        self.assertEqual(doc["failures"],[{"pixls_id":"2","error_type":"OSError"}])
        self.assertNotIn("private",out.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                probe.main(["--sample","01","n","p","--sample","1","n","p"])


if __name__ == "__main__":
    unittest.main()
