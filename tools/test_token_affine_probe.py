#!/usr/bin/env python3
"""Synthetic exact-rank, affine, orientation and selection controls; no samples."""
import itertools
import contextlib
import io
import json
import os
import random
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_affine_probe as probe  # noqa: E402


def rank_by_span(rows):
    span = {0}
    for row in rows:
        span |= {value ^ row for value in span}
    return (len(span) - 1).bit_length()


def rank(rows):
    basis = probe.Basis()
    for row in rows:
        basis.add(row)
    return basis.rank()


class TestAffine(unittest.TestCase):
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
            with self.subTest(simulated=simulated, case=samples[-1][0][:4]), mock.patch.object(probe, 'report') as report, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    with mock.patch.object(sys, 'argv', ['probe'] + args):
                        probe.main()
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
        with mock.patch.object(probe, 'report', side_effect=echo), contextlib.redirect_stdout(out):
            with mock.patch.object(sys, 'argv', ['probe'] + args):
                status = probe.main()
        self.assertEqual(status, 0)
        sample = json.loads(out.getvalue())['samples'][0]
        self.assertEqual((sample['pixls_id'], sample['pixls_name']), ('01', name))


    def test_rank_exhaustive_small_and_random(self):
        for rows in itertools.product(range(8), repeat=4):
            self.assertEqual(rank(rows), rank_by_span(rows))
        rng = random.Random(29)
        for _ in range(100):
            rows = [rng.randrange(32) for _ in range(10)]
            self.assertEqual(rank(rows), rank_by_span(rows))

    def test_affine_and_contradiction_bruteforce(self):
        for outputs in itertools.product((0, 1), repeat=4):
            contexts = [4 | value for value in range(4)]
            augmented = [x | (y << 3) for x, y in zip(contexts, outputs)]
            possible = any(all((bin(x & coefficients).count("1") % 2) == y
                               for x, y in zip(contexts, outputs))
                           for coefficients in range(8))
            self.assertEqual(rank(contexts) == rank(augmented), possible)
        self.assertEqual(rank([1, 1]), 1)
        self.assertEqual(rank([1, 3]), 2)  # same input, opposite outputs

    def test_planted_affine_and_parity(self):
        rng = random.Random(1224)
        suffixes = [rng.randrange(32) for _ in range(12)]
        # b2(t)=b4(t-1) XOR b2(t-12) XOR 1. b4 is arbitrary.
        for t in range(12, 500):
            bit = ((suffixes[t - 1] >> 4) ^ (suffixes[t - 12] >> 2) ^ 1) & 1
            suffixes.append((rng.randrange(2) << 4) | (bit << 2))
        result = probe.measure([(0, s) for s in suffixes])
        for cell in result["systems"]:
            self.assertEqual(cell["retained_rows"], 488 if cell["stratum"] == "pooled" else 244)
            if cell["target"] == "b2":
                self.assertTrue(cell["exact_affine_consistent"])
            else:
                self.assertFalse(cell["exact_affine_consistent"])

    def test_window_orientation_selection_independent_lists(self):
        rng = random.Random(2912)
        tokens = [(0, rng.randrange(32)) for _ in range(80)]
        for index in (0, 12, 26, 27, 79):
            tokens[index] = (17, tokens[index][1])
        got = probe.measure(tokens)
        self.assertEqual(got["candidate_windows"], 68)
        self.assertEqual(got["parsed_escapes"], 5)
        for cell in got["systems"]:
            rows, augmented, omitted = [], [], 0
            for t in range(12, len(tokens)):
                if cell["stratum"] != "pooled" and (t % 2 == 1) != (cell["stratum"] == "odd"):
                    continue
                if any(q >= 17 for q, _ in tokens[t - 12:t + 1]):
                    omitted += 1
                    continue
                features = []
                for lag in range(1, 13):
                    features.extend([(tokens[t - lag][1] >> bit) & 1 for bit in (2, 4)])
                features.append(1)
                x = sum(value * 2 ** column for column, value in enumerate(features))
                y = (tokens[t][1] >> int(cell["target"][1:])) & 1
                rows.append(x)
                augmented.append(x + y * 2 ** 25)
            self.assertEqual(cell["retained_rows"], len(rows))
            self.assertEqual(cell["omitted_escape_windows"], omitted)
            self.assertEqual(cell["context_rank"], rank(rows))
            self.assertEqual(cell["augmented_rank"], rank(augmented))

    def test_empty_short_all_escape(self):
        for tokens in ([], [(0, 0)] * 12, [(17, 0)] * 40):
            for cell in probe.measure(tokens)["systems"]:
                self.assertIsNone(cell["exact_affine_consistent"])
                self.assertEqual(cell["context_rank"], 0)
        self.assertRaises(ValueError, probe.Basis().add, -1)

    def test_container_reports_and_bounds(self):
        for order, mark in (("<", b"II"), (">", b"MM")):
            entries = [(0x100, 100), (0x101, 100), (0x111, 74), (0x117, 80)]
            data = mark + struct.pack(order + "HIH", 42, 8, 4)
            data += b"".join(struct.pack(order + "HHII", tag, 4, 1, value)
                             for tag, value in entries)
            data += struct.pack(order + "I", 0)
            data += bytes(74 - len(data)) + bytes([0xff]) * 80
            with mock.patch("builtins.open", side_effect=lambda *args, **kwargs: io.BytesIO(data)):
                report = probe.report("1", "synthetic.ORF", "ignored")
            self.assertEqual(report["payload_w"], 100)
            self.assertEqual(report["returned_tokens"], 106)
            self.assertEqual(report["bits_consumed"], 636)
            self.assertEqual(report["statistics"]["candidate_windows"], 94)
            with mock.patch("builtins.open", side_effect=lambda *args, **kwargs: io.BytesIO(data[:-1])):
                self.assertRaises(ValueError, probe.report, "1", "synthetic.ORF", "ignored")

    def test_cli_validates_all_ids_before_reads(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["probe", "--sample", "1", "name", "path",
                                             "--sample", "bad", "name", "path"]), \
                mock.patch.object(probe, "report") as report, \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as error:
                probe.main()
        self.assertEqual(error.exception.code, 2)
        report.assert_not_called()
        self.assertEqual(stdout.getvalue(), "")

    def run_cli(self, results):
        arguments = ["probe"]
        for index in range(len(results)):
            arguments.extend(["--sample", str(index + 1), "public-%d" % index, "private-path"])
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", arguments), \
                mock.patch.object(probe, "report", side_effect=results), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = probe.main()
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("private-path", stdout.getvalue())
        return status, json.loads(stdout.getvalue())

    def test_cli_retains_all_successes_and_sanitized_failures(self):
        complete = {"prefix_complete": True, "statistics": {"sentinel": 42}}
        status, output = self.run_cli([
            complete, OSError("private-path"), ValueError("private-path"), complete])
        self.assertEqual(status, 1)
        self.assertEqual(output["samples"], [complete, complete])
        self.assertEqual(output["failures"], [
            {"pixls_id": "2", "pixls_name": "public-1", "error": "OSError"},
            {"pixls_id": "3", "pixls_name": "public-2", "error": "ValueError"}])
        status, output = self.run_cli([complete, complete])
        self.assertEqual(status, 0)
        self.assertEqual(output["samples"], [complete, complete])
        self.assertEqual(output["failures"], [])
        status, output = self.run_cli([OSError("private-path")])
        self.assertEqual(status, 1)
        self.assertEqual(output["samples"], [])

    def test_short_and_empty_prefixes_keep_diagnostic_ranks_but_fail_cli(self):
        # Real scanner path, mocked container only; repeated six-bit 100000 codewords have
        # an exact affine fit on their observed rows, even for a short prefix.
        for payload, count in ((bytes([0x82, 0x08, 0x20]) * 4, 16), (bytes(12), 0)):
            tags = {0x100: [100], 0x101: [100], 0x111: [0], 0x117: [len(payload)]}
            with mock.patch("builtins.open", return_value=io.BytesIO(payload)), \
                    mock.patch.object(probe, "Tiff") as tiff:
                tiff.return_value.all_ifds.return_value = [tags]
                report = probe.report("1", "synthetic", "ignored")
            self.assertEqual(report["returned_tokens"], count)
            self.assertEqual(report["token_shortfall"], probe.LIMIT - count)
            self.assertFalse(report["prefix_complete"])
            if count:
                self.assertTrue(report["statistics"]["systems"][0]["exact_affine_consistent"])
            else:
                self.assertIsNone(report["statistics"]["systems"][0]["exact_affine_consistent"])
            status, output = self.run_cli([report])
            self.assertEqual(status, 1)
            self.assertEqual(output["samples"], [report])
            self.assertEqual(output["failures"], [])

    def test_full_prefix_marks_complete_without_changing_statistics(self):
        tags = {0x100: [100], 0x101: [100], 0x111: [0], 0x117: [12]}
        tokens = [(0, 0)] * probe.LIMIT
        with mock.patch("builtins.open", return_value=io.BytesIO(bytes(12))), \
                mock.patch.object(probe, "Tiff") as tiff, \
                mock.patch.object(probe, "scan_prefix", return_value=(tokens, 6 * probe.LIMIT)):
            tiff.return_value.all_ifds.return_value = [tags]
            report = probe.report("1", "synthetic", "ignored")
        self.assertTrue(report["prefix_complete"])
        self.assertEqual(report["token_shortfall"], 0)
        self.assertEqual(report["bits_consumed"], 6 * probe.LIMIT)
        self.assertEqual(report["statistics"]["candidate_windows"], probe.LIMIT - 12)
        for cell in report["statistics"]["systems"]:
            expected = probe.LIMIT - 12 if cell["stratum"] == "pooled" else (probe.LIMIT - 12) // 2
            self.assertEqual(cell["retained_rows"], expected)
            self.assertEqual(cell["omitted_escape_windows"], 0)
            self.assertEqual((cell["context_rank"], cell["augmented_rank"]), (1, 1))
            self.assertTrue(cell["exact_affine_consistent"])
        status, output = self.run_cli([report])
        self.assertEqual(status, 0)
        self.assertEqual(output["samples"], [report])


if __name__ == "__main__":
    unittest.main()
