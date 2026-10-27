#!/usr/bin/env python3
"""Synthetic tests for #11's first-escape balance split; no sample files."""
import itertools
import contextlib
import io
import json
import os
import struct
import sys
import unittest
from collections import Counter
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import escape_balance_probe as P


class CliTests(unittest.TestCase):
    def test_id_conversion_failure_is_an_argument_error(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        for sample_id, simulated in [('42', True), ('9' * (limit + 1), False)]:
            if not simulated and not limit:
                continue
            out, err = io.StringIO(), io.StringIO()
            convert = mock.patch.object(P, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated), mock.patch.object(sys, 'argv', ['probe', '--sample', sample_id, 'a.ORF', 'unused']), \
                 mock.patch.object(P, 'report') as report, convert, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as raised:
                    P.main()
                self.assertEqual(raised.exception.code, 2)
                report.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private detail', err.getvalue())
                self.assertIn('sample IDs', err.getvalue())

    @staticmethod
    def tiff(payload):
        offset = 8 + 2 + 4 * 12 + 4
        tags = ((0x100, 100), (0x101, 100), (0x111, offset),
                (0x117, len(payload)))
        return (b"II" + struct.pack("<HIH", 0x4f52, 8, 4)
                + b"".join(struct.pack("<HHII", tag, 4, 1, value)
                           for tag, value in tags)
                + bytes(4) + payload)

    def invoke(self, inputs):
        real_open = open
        fixtures = {"sample-%d" % i: value for i, value in enumerate(inputs)}

        def read_fixture(path, *args, **kwargs):
            if path in fixtures:
                value = fixtures[path]
                if isinstance(value, Exception):
                    raise value
                return io.BytesIO(value)
            return real_open(path, *args, **kwargs)

        argv = ["escape_balance_probe.py"]
        for i, path in enumerate(fixtures):
            argv += ["--sample", str(i + 1), "synthetic", path]
        output = io.StringIO()
        with mock.patch.object(sys, "argv", argv), \
                mock.patch("builtins.open", side_effect=read_fixture), \
                contextlib.redirect_stdout(output):
            status = P.main()
        return status, json.loads(output.getvalue())

    def test_complete_prefix(self):
        status, report = self.invoke([self.tiff(b"\xff" * (P.LIMIT * 6 // 8))])
        self.assertEqual(status, 0)
        self.assertEqual(report["failures"], [])
        sample = report["samples"][0]
        self.assertEqual(sample["returned_tokens"], P.LIMIT)
        self.assertEqual(sample["prefix_shortfall_tokens"], 0)
        self.assertEqual(sample["statistics"]["before"]["ordinary_tokens"], P.LIMIT)

    def test_short_prefix_preserves_aggregate(self):
        status, report = self.invoke([self.tiff(b"\xff")])
        self.assertEqual(status, 1)
        self.assertEqual(report["failures"], [])
        sample = report["samples"][0]
        self.assertEqual(sample["returned_tokens"], 1)
        self.assertEqual(sample["prefix_shortfall_tokens"], P.LIMIT - 1)
        self.assertEqual(sample["bits_consumed"], 6)
        self.assertEqual(sample["statistics"]["before"]["suffix_counts_0_to_31"],
                         [0] * 31 + [1])

    def test_no_complete_token_preserves_empty_groups(self):
        status, report = self.invoke([self.tiff(b"\x01")])
        self.assertEqual(status, 1)
        sample = report["samples"][0]
        self.assertEqual(sample["returned_tokens"], 0)
        self.assertEqual(sample["bits_consumed"], 0)
        for label in ("before", "after"):
            self.assertEqual(sample["statistics"][label]["p_one_b4_to_b0"], [None] * 5)

    def test_mixed_complete_short_and_exception(self):
        complete = self.tiff(b"\xff" * (P.LIMIT * 6 // 8))
        status, report = self.invoke([complete, self.tiff(b"\xff"),
                                      OSError("private fixture detail")])
        self.assertEqual(status, 1)
        self.assertEqual([s["returned_tokens"] for s in report["samples"]], [P.LIMIT, 1])
        self.assertEqual(report["failures"], [{"pixls_id": "3", "error": "OSError"}])
        self.assertNotIn("private fixture detail", json.dumps(report))

    def test_mixed_complete_and_short_without_exception(self):
        complete = self.tiff(b"\xff" * (P.LIMIT * 6 // 8))
        status, report = self.invoke([complete, self.tiff(b"\xff")])
        self.assertEqual(status, 1)
        self.assertEqual(len(report["samples"]), 2)
        self.assertEqual(report["failures"], [])

    def test_exception_only_is_sanitized(self):
        status, report = self.invoke([OSError("private fixture detail")])
        self.assertEqual(status, 1)
        self.assertEqual(report["samples"], [])
        self.assertEqual(report["failures"], [{"pixls_id": "1", "error": "OSError"}])


class BalanceTests(unittest.TestCase):
    def test_hand_counts(self):
        result = P.measure([(0, 1), (16, 2), (17, 31), (0, 3), (18, 0), (1, 31)])
        self.assertEqual(result["first_escape_token_index_zero_based"], 2)
        self.assertEqual(result["escape_tokens_excluded"], 2)
        self.assertEqual(result["before"]["ones_b4_to_b0"], [0, 0, 0, 1, 1])
        self.assertEqual(result["after"]["ones_b4_to_b0"], [1, 1, 1, 2, 2])
        self.assertEqual(result["after"]["p_one_b4_to_b0"], [.5, .5, .5, 1, 1])

    def test_exhaustive_independent_partition(self):
        alphabet = [(0, 0), (16, 31), (17, 1), (18, 30)]
        for length in range(6):
            for tokens in itertools.product(alphabet, repeat=length):
                indices = [i for i, token in enumerate(tokens) if token[0] >= 17]
                cut = indices[0] if indices else len(tokens)
                expected = [Counter(s for q, s in tokens[:cut] if q < 17),
                            Counter(s for q, s in tokens[cut:] if q < 17)]
                actual = P.measure(tokens)
                self.assertEqual(actual["escape_tokens_excluded"], len(indices))
                for label, counts in zip(("before", "after"), expected):
                    self.assertEqual(actual[label]["suffix_counts_0_to_31"],
                                     [counts[s] for s in range(32)])
                    self.assertEqual(actual[label]["ordinary_tokens"], sum(counts.values()))

    def test_uniform_and_empty(self):
        result = P.measure([(0, s) for s in range(32)])
        self.assertIsNone(result["first_escape_token_index_zero_based"])
        self.assertEqual(result["before"]["p_one_b4_to_b0"], [.5] * 5)
        self.assertEqual(result["after"]["p_one_b4_to_b0"], [None] * 5)
        self.assertEqual(P.measure([(17, 31)])["before"]["ordinary_tokens"], 0)

    def test_incomplete_suffix_and_prefix_limit(self):
        self.assertEqual(P.scan_prefix(bytes([1])), ([], 0))
        self.assertEqual(P.scan_prefix(bytes([0xff, 0xff]), 1), ([(0, 31)], 6))

    def test_string_parser_oracle(self):
        tokens = [(q, (q * 3) % 32) for q in (0, 1, 16, 17, 18, 23, 0)]
        bits = "".join("0" * q + "1" + format(s, "05b") for q, s in tokens)
        padded = bits + "0" * (-len(bits) % 8)
        payload = int(padded, 2).to_bytes(len(padded) // 8, "big")
        self.assertEqual(P.scan_prefix(payload), (tokens, len(bits)))
        self.assertEqual(P.measure(P.scan_prefix(payload)[0]), P.measure(tokens))


if __name__ == "__main__":
    unittest.main()
