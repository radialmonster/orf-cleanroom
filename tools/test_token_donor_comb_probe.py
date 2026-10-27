#!/usr/bin/env python3
"""Synthetic donor/parity and CLI controls for #30's nominal-lattice probe."""
import contextlib
import io
import json
import os
import random
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_donor_comb_probe as probe


class DonorTests(unittest.TestCase):
    def test_invalid_identities_precede_all_reports(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        cases = [([('1', 'public'), ('01', 'public')], False),
                 ([('1', 'public'), ('0', 'public')], False),
                 ([('1', 'public'), ('\u0661', 'public')], False),
                 ([('1', 'public'), ('2', '')], False),
                 ([('1', 'public'), ('2', 'private/path')], False),
                 ([('1', 'public'), ('2', 'private\\path')], False),
                 ([('1', 'public'), ('2', 'bad\nname')], False),
                 ([('1', 'public'), ('2', 'public')], True)]
        if limit:
            cases.append(([('1', 'public'), ('9' * (limit + 1), 'public')], False))
        for samples, simulated in cases:
            argv = ['probe']
            for sid, name in samples:
                argv += ['--sample', sid, name, 'unused']
            out, err = io.StringIO(), io.StringIO()
            conversion = patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated, case=samples[-1][0][:4]), patch.object(sys, 'argv', argv), \
                 patch.object(probe, 'report') as report, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main()
                self.assertEqual(caught.exception.code, 2)
                report.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_valid_identity_spelling_preserved(self):
        name = 'OM - Élite "camera" (4:3).ORF'
        def echo(sid, public, path):
            return {'pixls_id': sid, 'pixls_name': public, 'prefix_shortfall': 0}
        out = io.StringIO()
        with patch.object(sys, 'argv', ['probe', '--sample', '01', name, 'unused']), \
             patch.object(probe, 'report', side_effect=echo), contextlib.redirect_stdout(out):
            self.assertEqual(probe.main(), 0)
        sample = json.loads(out.getvalue())['samples'][0]
        self.assertEqual((sample['pixls_id'], sample['pixls_name']), ('01', name))

    def test_planted_lag_and_class(self):
        # Repeat a nonconstant random row every two rows: lag 2W is exact.
        rng = random.Random(23)
        width = 31
        base = [rng.randrange(2) for _ in range(2 * width)]
        tokens = [(0, 4 * base[t % len(base)]) for t in range(4096)]
        result = probe.donor_statistics(tokens, width)
        for cell in result["lags"][1]["classes"]:
            self.assertEqual(cell["pearson"], 1)
            self.assertEqual(cell["donor_by_target_b2"][0][1], 0)
            self.assertEqual(cell["donor_by_target_b2"][1][0], 0)
        for entry in result["lags"]:
            self.assertEqual(sum(c["candidate_pairs"] for c in entry["classes"]), len(tokens) - entry["lag"])

    def test_independent_direct_enumeration(self):
        rng = random.Random(24)
        tokens = [(17 if t % 47 == 0 else 0, rng.randrange(32)) for t in range(513)]
        for width in (4, 5):
            result = probe.donor_statistics(tokens, width)
            for entry in result["lags"]:
                lag = entry["lag"]
                for cell in entry["classes"]:
                    indices = [t for t in range(lag, len(tokens))
                               if (t // width) % 2 == cell["nominal_row_parity"]
                               and (t % width) % 2 == cell["nominal_column_parity"]]
                    pairs = [(tokens[t - lag][1] // 4 % 2, tokens[t][1] // 4 % 2)
                             for t in indices if tokens[t - lag][0] < 17 and tokens[t][0] < 17]
                    expected = [[pairs.count((a, b)) for b in (0, 1)] for a in (0, 1)]
                    self.assertEqual(cell["donor_by_target_b2"], expected)
                    self.assertEqual(cell["candidate_pairs"], len(indices))
                    self.assertEqual(cell["endpoint_escape_omitted_pairs"], len(indices) - len(pairs))

    def test_planted_row_parity_difference(self):
        rng = random.Random(25)
        width = 30
        base = [rng.randrange(2) for _ in range(2 * width)]
        tokens = []
        for t in range(4096):
            row = t // width
            bit = base[t % (2 * width)] ^ ((row // 2) % 2 if row % 2 else 0)
            tokens.append((0, 4 * bit))
        for cell in probe.donor_statistics(tokens, width)["lags"][1]["classes"]:
            self.assertEqual(cell["pearson"], -1 if cell["nominal_row_parity"] else 1)

    def test_balanced_and_degenerate(self):
        self.assertEqual(probe.correlation([[7, 7], [7, 7]]), 0)
        self.assertEqual(probe.correlation([[0, 8], [8, 0]]), -1)
        for tokens in ([], [(0, 0)] * 64, [(17, 4)] * 64):
            result = probe.donor_statistics(tokens, 4)
            self.assertTrue(all(c["pearson"] is None for e in result["lags"] for c in e["classes"]))

    def test_invalid(self):
        for tokens, width in (([], 1), ([(0, 32)], 4), ([(-1, 0)], 4), ([(0, True)], 4)):
            with self.assertRaises(ValueError):
                probe.donor_statistics(tokens, width)

    def test_main_status_and_sanitized_error(self):
        def fake_report(sample_id, name, path):
            if path == "missing":
                raise OSError("private path must not leak")
            return {"pixls_id": sample_id, "prefix_shortfall": int(path == "short")}
        for paths, expected in ((["complete"], 0), (["short"], 1), (["complete", "short"], 1), (["complete", "missing"], 1)):
            argv = ["probe"]
            for index, path in enumerate(paths):
                argv += ["--sample", str(index + 1), "public", path]
            output = io.StringIO()
            with patch.object(sys, "argv", argv), patch.object(probe, "report", fake_report), contextlib.redirect_stdout(output):
                self.assertEqual(probe.main(), expected)
            text = output.getvalue()
            self.assertNotIn("private path", text)
            self.assertEqual(len(json.loads(text)["samples"]), sum(p != "missing" for p in paths))

    def test_actual_main_in_memory_tiff(self):
        # Real locator/scanner/report paths: only file reads are replaced.
        def tiff(payload):
            offset = 8 + 2 + 6 * 12 + 4
            tags = ((256, 4), (257, 2), (259, 1), (273, offset),
                    (278, 2), (279, len(payload)))
            return (b"IIRO" + struct.pack("<I", 8) + struct.pack("<H", len(tags))
                    + b"".join(struct.pack("<HHII", tag, 4, 1, value) for tag, value in tags)
                    + struct.pack("<I", 0) + payload)
        fixtures = {"complete": tiff(bytes([255]) * (probe.LIMIT * 6 // 8)),
                    "short": tiff(bytes([255, 255])), "invalid": b"invalid"}
        original_open = open

        def read_fixture(path, mode="r", *args, **kwargs):
            if path in fixtures:
                self.assertEqual(mode, "rb")
                return io.BytesIO(fixtures[path])
            return original_open(path, mode, *args, **kwargs)

        for paths, status in ((["complete"], 0), (["short"], 1),
                              (["complete", "short", "invalid"], 1)):
            argv = ["probe"]
            for i, path in enumerate(paths):
                argv.extend(["--sample", str(i + 1), "public", path])
            output = io.StringIO()
            with patch.object(sys, "argv", argv), patch("builtins.open", read_fixture), contextlib.redirect_stdout(output):
                self.assertEqual(probe.main(), status)
            result = json.loads(output.getvalue())
            for report in result["samples"]:
                complete = paths[int(report["pixls_id"]) - 1] == "complete"
                n = probe.LIMIT if complete else 2
                self.assertEqual(report["prefix_shortfall"], probe.LIMIT - n)
                self.assertEqual(report["bits_consumed"], 6 * n)
                self.assertEqual(report["statistics"]["parsed_tokens"], n)
                for entry in report["statistics"]["lags"]:
                    self.assertEqual(sum(c["retained_pairs"] for c in entry["classes"]), max(0, n - entry["lag"]))
            self.assertEqual(len(result["failures"]), paths.count("invalid"))


if __name__ == "__main__":
    unittest.main()
