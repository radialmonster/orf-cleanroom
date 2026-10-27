#!/usr/bin/env python3
"""Independent synthetic checks for token_scale_probe; stdlib, no sample files."""
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
import token_scale_probe as probe


def container(payload):
    """Original minimal TIFF fixture, in memory only; five inline LONG tags."""
    offset = 8 + 2 + 12 * 5 + 4
    tags = ((0x100, 20), (0x101, 20), (0x103, 1),
            (0x111, offset), (0x117, len(payload)))
    return (b"II" + struct.pack("<HIH", 42, 8, len(tags))
            + b"".join(struct.pack("<HHII", tag, 4, 1, value) for tag, value in tags)
            + bytes(4) + payload)


class ScaleTests(unittest.TestCase):
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
                    probe.main(args)
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
            status = probe.main(args)
        self.assertEqual(status, 0)
        sample = json.loads(out.getvalue())['samples'][0]
        self.assertEqual((sample['pixls_id'], sample['pixls_name']), ('01', name))


    def test_independent_tables_and_loss(self):
        rng = random.Random(83)
        blocks = [(index, [rng.randrange(2) for _ in range(29)]) for index in (0, 3, 4, 9)]
        scores = probe.fitted_scores(blocks)
        for result in scores:
            counts = [collections.Counter(), collections.Counter()]
            window = result["window"]
            for index, bits in blocks:
                text = "".join(map(str, bits))
                for t in range(16, len(text)):
                    key = text[t-window:t].count("1") if window else 0
                    if result["joint_lag1"]:
                        key += int(text[t-1]) * (window + 1)
                    counts[index % 2][key, int(text[t])] += 1
            for label, counter in zip(("train", "test"), counts):
                actual = result[label + "_context_by_target"]
                self.assertEqual(actual, [[counter[c, y] for y in range(2)] for c in range(len(actual))])
            expected = 0
            for (context, y), n in counts[1].items():
                total = sum(counts[0][context, other] for other in (0, 1))
                expected += n * (math.log2(total + 1) - math.log2(counts[0][context, y] + .5))
            expected /= sum(counts[1].values())
            self.assertAlmostEqual(result["loss_bits"], expected, places=13)
            self.assertEqual(result["train_targets"], 26)
            self.assertEqual(result["test_targets"], 26)
            self.assertAlmostEqual(result["gain_vs_frequency_bits"], scores[0]["loss_bits"] - expected, places=13)
            self.assertAlmostEqual(result["gain_vs_lag1_bits"], scores[1]["loss_bits"] - expected, places=13)

    def test_selection_preserves_split_and_censors_boundaries(self):
        tokens = [(0, 0)] * (4 * probe.BLOCK + 7)
        tokens[probe.BLOCK] = (17, 0)
        tokens[-1] = (19, 0)
        blocks, counts = probe.select_blocks(tokens)
        self.assertEqual([index for index, _ in blocks], [0, 2, 3])
        self.assertEqual(counts["train_blocks"], 2)
        self.assertEqual(counts["test_blocks"], 1)
        self.assertEqual(counts["escape_omitted_test_blocks"], 1)
        self.assertEqual(counts["tail_tokens"], 7)
        self.assertEqual(counts["tail_escapes"], 1)
        self.assertEqual(counts["parsed_escapes"], 2)
        for model in probe.fitted_scores(blocks):
            self.assertEqual(model["train_targets"], 224)
            self.assertEqual(model["test_targets"], 112)

    def test_long_count_helps_slow_mixture(self):
        rng = random.Random(195)
        blocks = []
        for index in range(1024):
            p = .12 if (index // 2) % 2 else .88
            blocks.append((index, [int(rng.random() < p) for _ in range(probe.BLOCK)]))
        scores = {r["model"]: r for r in probe.fitted_scores(blocks)}
        self.assertGreater(scores["lag1_count8"]["gain_vs_lag1_bits"], .1)
        self.assertGreater(scores["lag1_count16"]["gain_vs_lag1_bits"], .1)

    def test_long_count_does_not_help_independent_or_markov(self):
        rng = random.Random(311)
        iid, markov = [], []
        for index in range(1024):
            iid.append((index, [rng.randrange(2) for _ in range(probe.BLOCK)]))
            bits = [rng.randrange(2)]
            for _ in range(1, probe.BLOCK):
                bits.append(bits[-1] if rng.random() < .8 else 1 - bits[-1])
            markov.append((index, bits))
        for blocks in (iid, markov):
            scores = {r["model"]: r for r in probe.fitted_scores(blocks)}
            for name in ("lag1_count8", "lag1_count16"):
                self.assertLess(scores[name]["gain_vs_lag1_bits"], .005)
        self.assertGreater(probe.fitted_scores(markov)[1]["gain_vs_frequency_bits"], .2)

    def test_empty_unseen_and_negative_transfer(self):
        for blocks in ([], [(0, [0] * 128)], [(1, [0] * 128)]):
            for row in probe.fitted_scores(blocks):
                self.assertIsNone(row["loss_bits"])
                self.assertIsNone(row["gain_vs_frequency_bits"])
        result = probe.score([[2, 0], [0, 0]], [[0, 0], [1, 3]])
        self.assertEqual(result["loss_bits"], 1)
        self.assertEqual(result["test_targets_with_unseen_context"], 4)
        # The long context's learned law reverses on the holdout.
        train = [(i, [0] * 64 + [1] * 64) for i in range(0, 32, 2)]
        test = [(i, [i % 2, (i + 1) % 2] * 64) for i in range(1, 32, 2)]
        self.assertLess(probe.fitted_scores(train + test)[3]["gain_vs_frequency_bits"], 0)

    def test_permutations_deterministic_preserve_input_and_mixture(self):
        blocks = [(i, [i // 2 % 2] * probe.BLOCK) for i in range(8)]
        before = [(i, bits[:]) for i, bits in blocks]
        measured = probe.measure(blocks)
        self.assertEqual(blocks, before)
        self.assertEqual(measured, probe.measure(blocks))
        for replicate in measured["permutations"]:
            for original, permuted in zip(measured["observed"], replicate):
                self.assertEqual(original["loss_bits"], permuted["loss_bits"])
        self.assertEqual(len(measured["permutations"]), 16)
        self.assertEqual(measured["permutation_means"][5]["loss_bits"], measured["observed"][5]["loss_bits"])

    def test_cli_rejects_invalid_and_duplicate_ids(self):
        for ids in (("0",), ("\u00b2",), ("\u0662",), ("1", "1"), ("1", "01")):
            args = [value for sid in ids for value in ("--sample", sid, "public", "unused")]
            with mock.patch.object(probe, "report") as reader, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                probe.main(args)
            self.assertEqual(caught.exception.code, 2)
            reader.assert_not_called()

    def test_real_bounded_report_full_short_empty_and_truncated_suffix(self):
        # This three-byte pattern encodes four q=0,s=0 candidates.
        payload = bytes([0x82, 0x08, 0x20]) * 100
        for target, complete in ((400, True), (401, False)):
            with mock.patch("builtins.open", mock.mock_open(read_data=container(payload))), mock.patch.object(probe, "LIMIT", target):
                result = probe.report("1", "public", "unused")
            self.assertEqual(result["prefix_complete"], complete)
            self.assertEqual(result["returned_tokens"], 400)
            self.assertEqual(result["shortfall_tokens"], target - 400)
            self.assertEqual(result["bits_consumed"], 2400)
            self.assertEqual(result["selection"]["complete_blocks"], 3)
            self.assertIsNotNone(result["statistics"]["observed"][0]["loss_bits"])
        for payload, count, endpoint in ((bytes(3), 0, 0), (bytes([0x81]), 1, 6)):
            with mock.patch("builtins.open", mock.mock_open(read_data=container(payload))):
                result = probe.report("1", "public", "unused")
            self.assertFalse(result["prefix_complete"])
            self.assertEqual(result["returned_tokens"], count)
            self.assertEqual(result["bits_consumed"], endpoint)
            self.assertIsNone(result["statistics"]["observed"][0]["loss_bits"])

    def test_cli_full_short_and_mixed_completion(self):
        for completions, expected_code in (([True], 0), ([False], 1), ([True, False], 1)):
            results = [{"pixls_id": str(i + 1), "prefix_complete": value,
                        "statistics": {"observed_diagnostic": True}}
                       for i, value in enumerate(completions)]
            args = [value for i in range(len(results)) for value in
                    ("--sample", str(i + 1), "public", "unused")]
            output = io.StringIO()
            with mock.patch.object(probe, "report", side_effect=results), contextlib.redirect_stdout(output):
                code = probe.main(args)
            self.assertEqual(code, expected_code)
            data = json.loads(output.getvalue())
            self.assertEqual(data["samples"], results)
            self.assertEqual(data["errors"], [{"pixls_id": str(i + 1), "pixls_name": "public",
                                              "error_type": "IncompletePrefix"}
                                             for i, value in enumerate(completions) if not value])

    def test_real_report_cli_rejects_short_and_empty_without_losing_diagnostics(self):
        for payload, count in ((bytes([0x82, 0x08, 0x20]) * 100, 400),
                               (bytes(3), 0)):
            output = io.StringIO()
            with mock.patch("builtins.open", mock.mock_open(read_data=container(payload))), contextlib.redirect_stdout(output):
                code = probe.main(["--sample", "1", "public", "unused"])
            self.assertEqual(code, 1)
            result = json.loads(output.getvalue())
            self.assertEqual(result["samples"][0]["returned_tokens"], count)
            self.assertFalse(result["samples"][0]["prefix_complete"])
            self.assertEqual(result["errors"][0]["error_type"], "IncompletePrefix")
            loss = result["samples"][0]["statistics"]["observed"][0]["loss_bits"]
            self.assertEqual(loss is None, count == 0)

    def test_mixed_cli_keeps_success_and_sanitizes_errors(self):
        def fake_report(sid, name, path):
            if sid == "2":
                raise OSError("private/path/should/not/appear")
            return {"pixls_id": sid, "prefix_complete": True, "statistics": {}}
        output = io.StringIO()
        with mock.patch.object(probe, "report", side_effect=fake_report), contextlib.redirect_stdout(output):
            code = probe.main(["--sample", "1", "public", "unused", "--sample", "2", "public", "unused"])
        self.assertEqual(code, 1)
        self.assertNotIn("private", output.getvalue())
        report = json.loads(output.getvalue())
        self.assertEqual(report["samples"], [{"pixls_id": "1", "prefix_complete": True, "statistics": {}}])
        self.assertEqual(report["errors"], [{"pixls_id": "2", "pixls_name": "public", "error_type": "OSError"}])
        self.assertEqual(len(report["source_sha256"]), 3)


if __name__ == "__main__":
    unittest.main()
