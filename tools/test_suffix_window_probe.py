#!/usr/bin/env python3
"""Independent synthetic counts/entropy, selection and CLI checks for #11."""
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
import suffix_window_probe as probe


def entropy(values):
    n = len(values)
    return -sum(c / n * math.log2(c / n) for c in collections.Counter(values).values()) if n else 0


class WindowTests(unittest.TestCase):
    def test_cli_window_completion_and_separated_stride(self):
        def fixture(count):
            bits = '100000' * count
            bits += '0' * (-len(bits) % 8)
            payload = int(bits, 2).to_bytes(len(bits) // 8, 'big') if bits else b'\x00'
            tags = ((256, 100), (257, 1), (259, 1), (273, 74), (279, len(payload)))
            return (b'II' + struct.pack('<HIH', 42, 8, len(tags))
                    + b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags)
                    + struct.pack('<I', 0) + payload)
        fixtures = {'complete': fixture(16), 'partial': fixture(15),
                    'short': fixture(1), 'separated': fixture(22),
                    'separated_partial': fixture(21)}
        real_open = open
        def open_fixture(path, *args, **kwargs):
            if path in fixtures:
                return io.BytesIO(fixtures[path])
            if path == 'missing':
                raise OSError('private diagnostic')
            return real_open(path, *args, **kwargs)
        cases = ((('complete',), 4, 0, [[0, 0, 0, 0]]),
                 (('partial',), 4, 1, [[0, 0, 0, 1]]),
                 (('short',), 4, 1, [[3, 4, 4, 4]]),
                 (('complete', 'partial', 'missing'), 4, 1, [[0, 0, 0, 0], [0, 0, 0, 1]]),
                 (('missing',), 4, 1, []),
                 (('separated',), 6, 0, [[0, 0, 0, 0]]),
                 (('separated_partial',), 6, 1, [[0, 0, 0, 1]]))
        for names, stride, expected, shortfalls in cases:
            argv = ['probe', '--window-stride', str(stride)]
            for index, name in enumerate(names, 1):
                argv += ['--sample', str(index), 'public', name]
            out = io.StringIO()
            with self.subTest(names=names), mock.patch.object(sys, 'argv', argv), \
                 mock.patch.object(probe, 'WINDOW', 4), mock.patch('builtins.open', side_effect=open_fixture), \
                 contextlib.redirect_stdout(out):
                status = probe.main()
                result = json.loads(out.getvalue())
                self.assertEqual(status, expected)
                self.assertEqual([[w['shortfall_tokens'] for w in r['windows']] for r in result['samples']], shortfalls)
                self.assertEqual(len(result['failures']), int('missing' in names))
                self.assertNotIn('private diagnostic', out.getvalue())

    def test_all_tables_independent_enumeration(self):
        tokens = [(17 if i % 11 == 0 else i % 5, (7 * i + i // 3) % 32) for i in range(77)]
        with mock.patch.object(probe, "WINDOW", 20):
            reports = probe.measure(tokens)
        self.assertEqual(len(reports), 4)
        for index, r in enumerate(reports):
            selected = tokens[index * 20:(index + 1) * 20]
            self.assertEqual(r["start_token"], index * 20)
            self.assertEqual(r["returned_tokens"], len(selected))
            self.assertEqual(r["escape_tokens"], sum(q >= 17 for q, s in selected))
            for lag_report in r["lags"]:
                lag = lag_report["lag_tokens"]
                same, cross = [], []
                for cell in lag_report["pairings"]:
                    pairs = []
                    for i in range(lag, len(selected)):
                        if selected[i - lag][0] >= 17 or selected[i][0] >= 17:
                            continue
                        a, b = selected[i - lag][1], selected[i][1]
                        pairs.append((a // 8 if cell["source"] == "H" else a % 8,
                                      b // 8 if cell["target"] == "H" else b % 8))
                    counts = collections.Counter(pairs)
                    table = cell["joint_source_rows_target_columns"]
                    self.assertEqual(table, [[counts[x, y] for y in range(len(table[0]))]
                                             for x in range(len(table))])
                    self.assertEqual(lag_report["retained_pairs"], len(pairs))
                    expected = entropy([a for a, b in pairs]) + entropy([b for a, b in pairs]) - entropy(pairs)
                    self.assertAlmostEqual(cell["plugin_mi_bits"], expected, places=12)
                    (same if cell["source"] == cell["target"] else cross).append(expected)
                stronger, weaker = (same, cross) if lag == 2 else (cross, same)
                self.assertEqual(lag_report["strict_alternating_order"],
                                 all(a > b for a in stronger for b in weaker))

    def test_report_signature_bounds_and_short_input(self):
        data = bytes([255]) * 64
        tags = {0x111: [16], 0x117: [8], 0x100: [5], 0x101: [4], 0x103: [1]}
        fake_tiff = mock.Mock()
        fake_tiff.all_ifds.return_value = [tags]
        with mock.patch.object(probe, "Tiff", return_value=fake_tiff), mock.patch(
                "builtins.open", mock.mock_open(read_data=data)):
            result = probe.report("1", "public", "local")
            self.assertEqual(result["returned_tokens"], 10)
            self.assertEqual(result["bits_consumed"], 60)
            self.assertEqual(result["windows"][0]["shortfall_tokens"], probe.WINDOW - 10)
            tags[0x117] = [1000]
            with self.assertRaises(ValueError):
                probe.report("1", "public", "local")
            tags[0x117] = [8]
            tags[0x103] = [7]
            with self.assertRaises(ValueError):
                probe.report("1", "public", "local")

    def test_escapes_do_not_join_or_exclude_intervening_pair(self):
        tokens = [(0, 0), (17, 31), (0, 31)]
        report = probe.measure(tokens)[0]
        self.assertEqual(report["lags"][0]["retained_pairs"], 0)
        self.assertEqual(report["lags"][1]["retained_pairs"], 1)
        self.assertIsNone(report["all_lags_strict_alternating_order"])

    def test_no_cross_window_pairs_and_shortfalls(self):
        with mock.patch.object(probe, "WINDOW", 4):
            reports = probe.measure([(0, 0)] * 4 + [(0, 31)] * 4 + [(0, 12)])
        self.assertEqual([r["shortfall_tokens"] for r in reports], [0, 0, 3, 4])
        for r in reports[:2]:
            self.assertFalse(r["all_lags_strict_alternating_order"])
            for lag in r["lags"]:
                self.assertEqual(lag["retained_pairs"], 4 - lag["lag_tokens"])
                self.assertTrue(all(p["plugin_mi_bits"] == 0 for p in lag["pairings"]))

    def test_cli_partial_failure_and_sanitizing(self):
        output = io.StringIO()
        argv = ["probe", "--sample", "1", "public", "local", "--sample", "2", "bad", "secret-path"]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(probe, "report", side_effect=[{"pixls_id": "1"}, OSError("secret-path")]):
            with contextlib.redirect_stdout(output):
                code = probe.main()
        result = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["samples"], [{"pixls_id": "1"}])
        self.assertEqual(result["failures"], [{"pixls_id": "2", "error": "OSError"}])
        self.assertNotIn("secret-path", output.getvalue())

    def test_id_alias_rejected(self):
        with mock.patch.object(sys, "argv", ["probe", "--sample", "1", "a", "a", "--sample", "01", "b", "b"]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                probe.main()
        self.assertEqual(caught.exception.code, 2)

    def test_separated_windows_absolute_indices_and_no_gap_pairs(self):
        # Gap tokens include escapes: they are scanned but are never endpoints.
        tokens = [(0, 0)] * 4 + [(17, 31)] * 3 + [(0, 31)] * 4
        with mock.patch.object(probe, "WINDOW", 4):
            reports = probe.measure(tokens, stride=7)
        self.assertEqual([r["start_token"] for r in reports], [0, 7, 14, 21])
        self.assertEqual([r["shortfall_tokens"] for r in reports], [0, 0, 4, 4])
        for r in reports[:2]:
            self.assertEqual(r["escape_tokens"], 0)
            self.assertEqual([x["retained_pairs"] for x in r["lags"]], [3, 2, 1])
            self.assertTrue(all(p["plugin_mi_bits"] == 0 for x in r["lags"] for p in x["pairings"]))

    def test_stride_scanner_limit_and_partial_final_window(self):
        tags = {0x111: [16], 0x117: [8], 0x100: [5], 0x101: [4], 0x103: [1]}
        fake_tiff = mock.Mock()
        fake_tiff.all_ifds.return_value = [tags]
        tokens = [(0, i % 32) for i in range(24)]
        with mock.patch.object(probe, "WINDOW", 4), mock.patch.object(probe, "Tiff", return_value=fake_tiff), mock.patch(
                "builtins.open", mock.mock_open(read_data=bytes([255]) * 64)), mock.patch.object(
                probe, "scan_prefix", return_value=(tokens, 144)) as scan:
            result = probe.report("1", "public", "local", stride=7)
        self.assertEqual(scan.call_args.args[1], 25)
        self.assertEqual(result["requested_scan_tokens"], 25)
        self.assertEqual(result["windows"][-1]["returned_tokens"], 3)
        self.assertEqual(result["windows"][-1]["shortfall_tokens"], 1)

    def test_overlapping_stride_rejected(self):
        with self.assertRaises(ValueError):
            probe.measure([], stride=probe.WINDOW - 1)
        with mock.patch.object(sys, "argv", ["probe", "--window-stride", "0", "--sample", "1", "a", "a"]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                probe.main()
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
