#!/usr/bin/env python3
"""Independent synthetic parsing/count/entropy checks; no samples required."""
import collections
import contextlib
import io
import json
import math
import os
import random
import stat
import struct
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_width_lag_probe as probe


def reference(data, k, stop, limit):
    bits = "".join(format(x, "08b") for x in data)
    pos, tokens = 0, []
    while pos < len(bits) and len(tokens) < limit:
        end = bits.find(str(stop), pos)
        if end < 0 or end + k + 1 > len(bits):
            break
        tokens.append((end - pos, int(bits[end + 1:end + 1 + k], 2)))
        pos = end + 1 + k
    return tokens, pos


def entropy(counts):
    total = sum(counts)
    return -sum(n / total * math.log2(n / total) for n in counts if n)


class Tests(unittest.TestCase):
    def test_public_identity_validation_before_reporting(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        cases = [([('1', 'public'), ('01', 'public')], False),
                 ([('1', 'public'), ('2', 'private/path')], False),
                 ([('1', 'public'), ('2', '')], False), ([('1', 'public'), ('2', 'private\\path')], False),
                 ([('1', 'public'), ('2', 'bad\nname')], False), ([('0', 'public')], False),
                 ([('1', 'public')], True)]
        if limit:
            cases.append(([('9' * (limit + 1), 'public')], False))
        for samples, simulated in cases:
            args = []
            for sid, name in samples:
                args += ['--sample', sid, name, 'unused']
            out, err = io.StringIO(), io.StringIO()
            conversion = mock.patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(samples=samples[0][0][:4], simulated=simulated), mock.patch.object(probe, 'report') as report, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(args)
                self.assertEqual(caught.exception.code, 2)
                report.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_valid_public_identity_spelling_is_preserved(self):
        name = 'OM - Élite "camera" (4:3).ORF'
        def report(sid, public, path, *args, **kwargs):
            return {'pixls_id': sid, 'pixls_name': public, 'cells': [{'token_shortfall': 0}]}
        args = ['--sample', '01', name, 'unused']
        out = io.StringIO()
        with mock.patch.object(probe, 'report', side_effect=report), contextlib.redirect_stdout(out):
            status = probe.main(args)
        self.assertEqual(status, 0)
        sample = json.loads(out.getvalue())['samples'][0]
        self.assertEqual((sample['pixls_id'], sample['pixls_name']), ('01', name))


    def test_cli_short_sweep_retains_cells_and_reports_failure(self):
        class Input(io.BytesIO):
            def fileno(self):
                return 123
        regular = types.SimpleNamespace(st_mode=stat.S_IFREG)
        entries = [(0x100, 10), (0x101, 10), (0x103, 1), (0x111, 74), (0x117, 2)]
        data = (b'II' + struct.pack('<HIH', 0x4f52, 8, 5)
                + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in entries)
                + bytes(4) + b'\x8b\x81')
        def read_input(path, *args):
            if path == 'missing':
                raise OSError('private detail')
            return Input(data)
        for rotate in (False, True):
            for names in (('short',), ('short', 'missing')):
                args = ['--block-rotation-control'] if rotate else []
                for i, name in enumerate(names, 1):
                    args += ['--sample', str(i), 'public', name]
                out = io.StringIO()
                with self.subTest(rotate=rotate, names=names), \
                     mock.patch.object(probe.os, 'stat', return_value=regular), \
                     mock.patch.object(probe.os, 'fstat', return_value=regular), \
                     mock.patch('builtins.open', side_effect=read_input), \
                     mock.patch.object(probe, 'source_hashes', return_value={}), contextlib.redirect_stdout(out):
                    status = probe.main(args)
                    result = json.loads(out.getvalue())
                    self.assertEqual(status, 1)
                    cells = result['samples'][0]['cells']
                    self.assertEqual(len(cells), 14)
                    self.assertTrue(all(c['token_shortfall'] > 0 for c in cells))
                    self.assertTrue(all(('block_rotation_control' in c) == rotate for c in cells))
                    self.assertEqual(len(result['failures']), int('missing' in names))
                    self.assertNotIn('private detail', out.getvalue())

    def test_cli_complete_and_one_short_cell(self):
        for shortfall, status in ((0, 0), (1, 1)):
            cells = [{'token_shortfall': 0} for _ in range(14)]
            cells[-1]['token_shortfall'] = shortfall
            with self.subTest(shortfall=shortfall), mock.patch.object(probe, 'report', return_value={'cells': cells}), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main(['--sample', '1', 'public', 'unused']), status)

    def test_rotation_tables_against_independent_pair_enumeration(self):
        rng = random.Random(931)
        tokens = [(rng.randrange(8), rng.randrange(32)) for _ in range(400)]
        tokens[130] = (17, 1)
        result = probe.block_rotation_control(tokens)
        self.assertEqual(result["complete_blocks"], 3)
        self.assertEqual(result["retained_blocks"], 2)
        self.assertEqual(result["omitted_escape_blocks"], 1)
        self.assertEqual(result["incomplete_tail_tokens"], 16)
        for cell in result["lags"]:
            lag = cell["lag"]
            m = 128 - lag
            self.assertEqual(cell["retained_pairs"], 2 * m)
            for label, extract, size in (("q_positive", lambda a: int(a[0] > 0), 2),
                                         ("suffix_low2", lambda a: a[1] % 4, 4)):
                expected = [collections.Counter(), collections.Counter()]
                for start in (0, 256):
                    donors = [extract(a) for a in tokens[start:start + m]]
                    targets = [extract(a) for a in tokens[start + lag:start + 128]]
                    rotated = donors[m // 2:] + donors[:m // 2]
                    expected[0].update(zip(donors, targets))
                    expected[1].update(zip(rotated, targets))
                tables = []
                for key, counts in zip(("observed_table", "control_table"), expected):
                    table = [[counts[a, b] for b in range(size)] for a in range(size)]
                    self.assertEqual(cell[label][key], table)
                    tables.append(table)
                self.assertEqual(list(map(sum, tables[0])), list(map(sum, tables[1])))
                self.assertEqual([sum(row[b] for row in tables[0]) for b in range(size)],
                                 [sum(row[b] for row in tables[1]) for b in range(size)])
                scores = [entropy(list(map(sum, table))) + entropy(
                    [sum(row[b] for row in table) for b in range(size)]) - entropy(
                    [n for row in table for n in row]) for table in tables]
                self.assertAlmostEqual(cell[label]["observed_mi_bits"], scores[0], places=12)
                self.assertAlmostEqual(cell[label]["control_mi_bits"], scores[1], places=12)
                self.assertAlmostEqual(cell[label]["observed_minus_control_mi_bits"],
                                       scores[0] - scores[1], places=12)

    def test_rotation_preserves_block_mixture_and_negative_difference(self):
        tokens = [(0, 0)] * 128 + [(1, 3)] * 128
        for cell in probe.block_rotation_control(tokens)["lags"]:
            for label in ("q_positive", "suffix_low2"):
                self.assertEqual(cell[label]["observed_mi_bits"], 1)
                self.assertEqual(cell[label]["control_mi_bits"], 1)
                self.assertEqual(cell[label]["observed_minus_control_mi_bits"], 0)
        # Period62 creates a stronger shifted than adjacent suffix association.
        rng = random.Random(432)
        pattern = [rng.randrange(4) for _ in range(62)]
        tokens = [(0, pattern[i % 62]) for i in range(128)]
        first = probe.block_rotation_control(tokens)["lags"][0]
        self.assertLess(first["suffix_low2"]["observed_minus_control_mi_bits"], 0)

    def test_rotation_empty_tail_and_escape_selection(self):
        for tokens in ([], [(0, 1)] * 127, [(17, 0)] * 128):
            result = probe.block_rotation_control(tokens)
            self.assertEqual(result["retained_blocks"], 0)
            for cell in result["lags"]:
                self.assertEqual(cell["retained_pairs"], 0)
                for label in ("q_positive", "suffix_low2"):
                    self.assertIsNone(cell[label]["observed_mi_bits"])
                    self.assertIsNone(cell[label]["control_mi_bits"])
                    self.assertIsNone(cell[label]["observed_minus_control_mi_bits"])

    def test_rotation_cli_flag_forwarding(self):
        with mock.patch.object(probe, "report", return_value={"cells": []}) as report:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main(["--block-rotation-control", "--sample", "1", "n", "p"]), 0)
            report.assert_called_once_with("1", "n", "p", rotation_control=True)

    def test_all_bytes_and_random_against_string_parser(self):
        rng = random.Random(20261021)
        buffers = [bytes([i]) for i in range(256)]
        buffers += [b"", bytes(32), b"\xff" * 32,
                    bytes(32) + b"\xff\xff", b"\xff" * 32 + bytes(2)]
        buffers += [bytes(rng.randrange(256) for _ in range(80)) for _ in range(10)]
        for k in range(2, 9):
            for stop in (0, 1):
                for data in buffers:
                    for limit in (0, 3, 500):
                        self.assertEqual(probe.parse(data, k, stop, limit),
                                         reference(data, k, stop, limit))
        for k, stop, limit in ((1, 1, 2), (9, 0, 2), (5, 2, 2), (5, 1, -1)):
            with self.assertRaises(ValueError):
                probe.parse(b"\xff", k, stop, limit)

    def test_counts_orientation_omissions_and_entropy_identity(self):
        rng = random.Random(1234)
        tokens = [(rng.randrange(20), rng.randrange(256)) for _ in range(100)]
        for cell in probe.measures(tokens):
            lag = cell["lag"]
            pairs = [(tokens[t - lag], tokens[t]) for t in range(lag, len(tokens))]
            kept = [(a, b) for a, b in pairs if a[0] < 17 and b[0] < 17]
            self.assertEqual(cell["candidate_pairs"], len(pairs))
            self.assertEqual(cell["retained_pairs"], len(kept))
            self.assertEqual(cell["omitted_escape_endpoint_pairs"], len(pairs) - len(kept))
            for key, fn, n in (("q_positive", lambda t: int(t[0] > 0), 2),
                               ("suffix_low2", lambda t: t[1] & 3, 4)):
                counts = collections.Counter((fn(a), fn(b)) for a, b in kept)
                table = [[counts[i, j] for j in range(n)] for i in range(n)]
                self.assertEqual(cell[key + "_table"], table)
                expected = entropy(list(map(sum, table))) + entropy(
                    [sum(row[j] for row in table) for j in range(n)]) - entropy(
                    [x for row in table for x in row])
                self.assertAlmostEqual(cell[key + "_mi_bits"], expected, places=12)

    def test_no_compaction_intervening_escapes_and_directed_tables(self):
        tokens = [(0, 0), (17, 1), (1, 3), (0, 2)]
        cells = probe.measures(tokens)
        self.assertEqual(cells[0]["retained_pairs"], 1)
        self.assertEqual(cells[0]["suffix_low2_table"][3][2], 1)
        self.assertEqual(cells[1]["retained_pairs"], 1)
        self.assertEqual(cells[1]["suffix_low2_table"][0][3], 1)
        self.assertEqual(cells[2]["suffix_low2_table"][0][2], 1)
        self.assertIsNone(cells[3]["q_positive_mi_bits"])
        self.assertEqual(probe.mi([[5, 0], [0, 5]]), 1)
        self.assertEqual(probe.mi([[1, 1], [1, 1]]), 0)
        self.assertEqual(probe.mi([[8, 0], [0, 0]]), 0)
        self.assertTrue(all(c["retained_pairs"] == 0 for c in probe.measures([])))

    def test_real_container_both_endians_and_truncated_strip(self):
        class Input(io.BytesIO):
            def fileno(self):
                return 123
        regular = types.SimpleNamespace(st_mode=stat.S_IFREG)
        for endian, marker in (("<", b"II"), (">", b"MM")):
            entries = [(0x100, 10), (0x101, 10), (0x103, 1), (0x111, 74), (0x117, 2)]
            data = marker + struct.pack(endian + "HIH", 0x4f52, 8, 5)
            data += b"".join(struct.pack(endian + "HHII", tag, 4, 1, value)
                             for tag, value in entries) + bytes(4) + b"\x8b\x81"
            with mock.patch.object(probe.os, "stat", return_value=regular), mock.patch.object(probe.os, "fstat", return_value=regular):
                with mock.patch("builtins.open", return_value=Input(data)):
                    result = probe.report("1", "public", "input")
                self.assertEqual((result["payload_w"], result["payload_h"], result["payload_bytes"]), (10, 10, 2))
                self.assertEqual(len(result["cells"]), 14)
                for cell in result["cells"]:
                    tokens, end = reference(data[-2:], cell["k"], cell["stop_bit"], probe.TOKENS)
                    self.assertEqual(cell["tokens"], len(tokens))
                    self.assertEqual(cell["token_shortfall"], probe.TOKENS - len(tokens))
                    self.assertEqual(cell["bits_consumed"], end)
                    self.assertEqual(cell["remaining_payload_bits"], 16 - end)
                    self.assertEqual(cell["q_ge_17"], sum(q >= 17 for q, _ in tokens))
                    self.assertEqual(cell["lags"], probe.measures(tokens))
                with mock.patch("builtins.open", return_value=Input(data[:-1])):
                    with self.assertRaises(ValueError):
                        probe.report("1", "public", "input")

    def test_cli_validation_failure_sanitization_and_retained_success(self):
        output = io.StringIO()
        with mock.patch.object(probe, "report", side_effect=[{"pixls_id": "1"}, ValueError("secret path")]):
            with contextlib.redirect_stdout(output):
                status = probe.main(["--sample", "1", "one", "file1", "--sample", "2", "two", "file2"])
        self.assertEqual(status, 1)
        parsed = json.loads(output.getvalue())
        self.assertEqual(parsed["samples"], [{"pixls_id": "1"}])
        self.assertEqual(parsed["failures"], [{"pixls_id": "2", "error": "invalid_or_unreadable_input"}])
        self.assertNotIn("secret", output.getvalue())
        for args in (["--sample", "0", "x", "f"], ["--sample", "1", "x", "f", "--sample", "1", "y", "g"]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                probe.main(args)


if __name__ == "__main__":
    unittest.main()
