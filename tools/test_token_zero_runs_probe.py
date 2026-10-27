#!/usr/bin/env python3
"""Synthetic tests for complete runs, censoring, escapes and exact moments."""
import itertools
import contextlib
import io
import json
import os
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from token_zero_runs_probe import measure, scan_window
from suffix_joint_probe import scan_prefix
import token_zero_runs_probe as probe


def tokens(bits):
    return [(0, 4 * int(bit)) for bit in bits]


def synthetic_tiff(payload):
    """An in-memory, single-strip TIFF; no sample or fixture files written."""
    entries = [(0x100, 8), (0x101, 8), (0x103, 1),
               (0x111, 74), (0x117, len(payload))]
    return (b"II" + struct.pack("<HIH", 42, 8, len(entries))
            + b"".join(struct.pack("<HHII", tag, 4, 1, value)
                       for tag, value in entries)
            + struct.pack("<I", 0) + payload)


class CliTests(unittest.TestCase):
    def test_id_conversion_failure_is_an_argument_error(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        for sample_id, simulated in [('42', True), ('9' * (limit + 1), False)]:
            if not simulated and not limit:
                continue
            out, err = io.StringIO(), io.StringIO()
            convert = patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated), patch.object(sys, 'argv', ['probe', '--sample', sample_id, 'a.ORF', 'unused']), \
                 patch.object(probe, 'report') as report, convert, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as raised:
                    probe.main()
                self.assertEqual(raised.exception.code, 2)
                report.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private detail', err.getvalue())
                self.assertIn('sample IDs', err.getvalue())

    def test_invalid_public_names_fail_before_any_report(self):
        for name in ('', 'private/path.ORF', 'private\\path.ORF', 'bad\nname.ORF', 'bad\x00name'):
            argv = [probe.__file__, '--sample', '1', 'valid.ORF', 'first', '--sample', '2', name, 'second']
            out, err = io.StringIO(), io.StringIO()
            fake = {'start_shortfall': 0, 'token_shortfall': 0}
            with self.subTest(name=name), patch.object(sys, 'argv', argv), \
                    patch.object(probe, 'report', return_value=fake) as report, \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as raised:
                    probe.main()
                self.assertEqual(raised.exception.code, 2)
                report.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_printable_public_name_is_preserved(self):
        name = 'Olympus - Modèle "test" (4:3).ORF'
        argv = [probe.__file__, '--sample', '1', name, 'synthetic']
        out = io.StringIO()
        def fake_report(sample_id, public_name, path, start, count):
            return {'pixls_name': public_name, 'start_shortfall': 0, 'token_shortfall': 0}
        with patch.object(sys, 'argv', argv), patch.object(probe, 'report', side_effect=fake_report), \
                contextlib.redirect_stdout(out):
            self.assertEqual(probe.main(), 0)
        self.assertEqual(json.loads(out.getvalue())['samples'][0]['pixls_name'], name)
    def test_numeric_id_aliases_are_rejected_before_measurement(self):
        argv = [probe.__file__, '--sample', '1', 'a.ORF', 'first',
                '--sample', '01', 'b.ORF', 'second']
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', argv), patch.object(probe, 'report', return_value={'start_shortfall': 0, 'token_shortfall': 0}) as report, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as raised:
                probe.main()
        self.assertEqual(raised.exception.code, 2)
        report.assert_not_called()
        self.assertEqual(out.getvalue(), '')

    def test_single_leading_zero_id_preserves_existing_output(self):
        status, result = self.run_cli([('01', 'complete.orf')])
        self.assertEqual(status, 0)
        self.assertEqual(result['samples'][0]['pixls_id'], '01')

    def run_cli(self, samples, start=0, count=4):
        # Each token is q=0 plus five suffix bits. Full input has b2=1001;
        # short input has b2=10 followed by four zero pad bits (not a token).
        fixtures = {"complete.orf": synthetic_tiff(bytes([0x92, 0x08, 0x24])),
                    "short.orf": synthetic_tiff(bytes([0x92, 0x00]))}
        real_open = open

        def read_input(path, *args, **kwargs):
            if path in fixtures:
                self.assertEqual(args, ("rb",))
                return io.BytesIO(fixtures[path])
            if path == "missing.orf":
                raise FileNotFoundError("private fixture diagnostic")
            return real_open(path, *args, **kwargs)

        argv = [probe.__file__, "--start-token", str(start), "--tokens", str(count)]
        for sample_id, path in samples:
            argv.extend(["--sample", sample_id, "synthetic", path])
        output = io.StringIO()
        with patch.object(sys, "argv", argv), patch("builtins.open", side_effect=read_input):
            with contextlib.redirect_stdout(output):
                status = probe.main()
        text = output.getvalue()
        self.assertNotIn("private fixture diagnostic", text)
        return status, json.loads(text)

    def test_complete_window_exit_zero(self):
        status, result = self.run_cli([("1", "complete.orf")])
        self.assertEqual(status, 0)
        sample = result["samples"][0]
        self.assertEqual(sample["returned_tokens"], 4)
        self.assertEqual(sample["bits_consumed"], 24)
        self.assertEqual(sample["statistics"]["histogram"], [{"length": 2, "count": 1}])
        self.assertEqual(result["failures"], [])

    def test_count_shortfall_exit_one_preserves_aggregates(self):
        status, result = self.run_cli([("1", "complete.orf")], count=5)
        self.assertEqual(status, 1)
        sample = result["samples"][0]
        self.assertEqual(sample["start_shortfall"], 0)
        self.assertEqual(sample["token_shortfall"], 1)
        self.assertEqual(sample["prefix_shortfall"], 1)
        self.assertEqual(sample["returned_tokens"], 4)
        self.assertEqual(sample["statistics"]["sum_run_lengths"], 2)
        self.assertEqual(result["failures"], [])

    def test_start_shortfall_exit_one(self):
        status, result = self.run_cli([("1", "complete.orf")], start=5, count=1)
        self.assertEqual(status, 1)
        sample = result["samples"][0]
        self.assertEqual(sample["start_shortfall"], 1)
        self.assertEqual(sample["skipped_tokens"], 4)
        self.assertEqual(sample["token_shortfall"], 1)
        self.assertEqual(sample["returned_tokens"], 0)
        self.assertEqual(sample["statistics"]["histogram"], [])

    def test_reached_start_but_short_window_exit_one(self):
        status, result = self.run_cli([("1", "complete.orf")], start=2, count=3)
        self.assertEqual(status, 1)
        sample = result["samples"][0]
        self.assertEqual(sample["start_shortfall"], 0)
        self.assertEqual(sample["returned_tokens"], 2)
        self.assertEqual(sample["token_shortfall"], 1)

    def test_mixed_complete_shortfall_and_exception(self):
        status, result = self.run_cli([("1", "complete.orf"), ("2", "short.orf"),
                                       ("3", "missing.orf")])
        self.assertEqual(status, 1)
        self.assertEqual([s["pixls_id"] for s in result["samples"]], ["1", "2"])
        self.assertEqual([s["returned_tokens"] for s in result["samples"]], [4, 2])
        self.assertEqual([s["token_shortfall"] for s in result["samples"]], [0, 2])
        self.assertEqual(result["samples"][0]["statistics"]["sum_run_lengths"], 2)
        self.assertEqual(result["failures"], [{"pixls_id": "3", "error": "FileNotFoundError"}])

    def test_mixed_complete_and_shortfall_exit_one(self):
        status, result = self.run_cli([("1", "complete.orf"), ("2", "short.orf")])
        self.assertEqual(status, 1)
        self.assertEqual(len(result["samples"]), 2)
        self.assertEqual(result["failures"], [])


class RunTests(unittest.TestCase):
    def test_hand_moments(self):
        result = measure(tokens("10010001"))
        self.assertEqual(result["histogram"], [{"length": 2, "count": 1}, {"length": 3, "count": 1}])
        self.assertEqual(result["sum_run_lengths"], 5)
        self.assertEqual(result["sum_squared_run_lengths"], 13)
        self.assertEqual(result["population_mean"], 2.5)
        self.assertEqual(result["population_variance"], 0.25)
        self.assertEqual(result["fitted_positive_geometric_variance"], 3.75)

    def test_censoring(self):
        r = measure(tokens("001001000"))
        self.assertEqual(r["leading_censored_zeros"], 2)
        self.assertEqual(r["trailing_censored_zeros"], 3)
        self.assertEqual(r["sum_run_lengths"], 2)
        self.assertEqual(r["zero_tokens"], 7)

    def test_empty_degenerate(self):
        for bits in ("", "111", "000", "001", "100"):
            r = measure(tokens(bits))
            self.assertEqual(r["complete_positive_runs"], 0)
            self.assertIsNone(r["population_mean"])
            self.assertIsNone(r["population_variance"])
        r = measure(tokens("000"))
        self.assertEqual(r["all_zero_segment_zeros"], 3)
        self.assertEqual(r["leading_censored_zeros"], 0)
        self.assertEqual(r["trailing_censored_zeros"], 0)
        self.assertIsNone(measure(tokens("10101"))["variance_ratio"])

    def test_escape_splits(self):
        r = measure(tokens("10") + [(17, 0), (18, 4)] + tokens("01"))
        self.assertEqual(r["complete_positive_runs"], 0)
        self.assertEqual(r["segments"], 2)
        self.assertEqual(r["omitted_escape_tokens"], 2)
        self.assertEqual(r["trailing_censored_zeros"], 1)
        self.assertEqual(r["leading_censored_zeros"], 1)
        self.assertEqual(measure([(17, 0)])["segments"], 0)

    def test_scanner_end_boundary(self):
        # A late stop without all five suffix bits must contribute no token.
        self.assertEqual(scan_prefix(bytes([1])), ([], 0))
        self.assertEqual(scan_prefix(bytes([0x81])), ([(0, 0)], 6))
        self.assertEqual(measure(scan_prefix(bytes([1]))[0])["retained_tokens"], 0)

    def test_exhaustive_string_oracle(self):
        # Independent oracle: trim at first/last one and split on ones.
        for length in range(10):
            for bits in itertools.product("01", repeat=length):
                text = "".join(bits)
                runs = ([len(s) for s in text[text.find("1"):text.rfind("1")+1].split("1") if s]
                        if "1" in text else [])
                r = measure(tokens(text))
                self.assertEqual(r["complete_positive_runs"], len(runs))
                self.assertEqual(r["sum_run_lengths"], sum(runs))
                self.assertEqual(r["sum_squared_run_lengths"], sum(x*x for x in runs))

    def test_windows_against_independent_encoder(self):
        expected = [(q, (3*q + i) % 32) for i, q in enumerate((0, 1, 17, 7, 96, 2, 18, 0))]
        encoded = ["0"*q + "1" + format(s, "05b") for q, s in expected]
        text = "".join(encoded)
        padded = text + "0"*((-len(text)) % 8)
        payload = int(padded, 2).to_bytes(len(padded)//8, "big")
        for start in range(len(expected)+3):
            for count in (1, 3, 20):
                window, meta = scan_window(payload, start, count)
                end_index = min(start+count, len(expected))
                skipped = min(start, len(expected))
                self.assertEqual(window, expected[start:start+count])
                self.assertEqual(meta["bits_consumed"], sum(map(len, encoded[:end_index])))
                self.assertEqual(meta["window_start_bit"], sum(map(len, encoded[:skipped])))
                self.assertEqual(meta["skipped_tokens"], skipped)
                self.assertEqual(meta["skipped_escape_tokens"], sum(q >= 17 for q, _ in expected[:skipped]))
                self.assertEqual(meta["start_shortfall"], start-skipped)
                self.assertEqual(meta["window_bits_consumed"], sum(map(len, encoded[skipped:end_index])))
        window, meta = scan_window(payload)
        self.assertEqual((window, meta["bits_consumed"]), scan_prefix(payload))

    def test_window_boundaries_are_censored_independently(self):
        # The full run has length five. A window containing its middle cannot
        # inherit either external bounding one, and must not count that run.
        text = "1000001"
        encoded = "".join("1" + format(s, "05b") for _, s in tokens(text))
        payload = int(encoded + "0"*((-len(encoded)) % 8), 2).to_bytes((len(encoded)+7)//8, "big")
        r = measure(scan_window(payload, 2, 3)[0])
        self.assertEqual(r["complete_positive_runs"], 0)
        self.assertEqual(r["all_zero_segment_zeros"], 3)
        self.assertEqual(measure(scan_window(payload, 0, 4)[0])["trailing_censored_zeros"], 3)
        self.assertEqual(measure(scan_window(payload, 3, 4)[0])["leading_censored_zeros"], 3)

    def test_window_truncation_and_validation(self):
        for payload in (b"", bytes([1]), bytes(20), bytes([0x81])):
            baseline, end = scan_prefix(payload)
            for start in (0, 1, 2):
                got, meta = scan_window(payload, start, 3)
                self.assertEqual(got, baseline[start:])
                self.assertEqual(meta["bits_consumed"], end)
        for start, count in ((-1, 1), (0, 0), (0, -1)):
            with self.assertRaises(ValueError):
                scan_window(b"", start, count)


if __name__ == "__main__":
    unittest.main()
