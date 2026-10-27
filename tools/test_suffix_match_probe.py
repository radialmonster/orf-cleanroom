#!/usr/bin/env python3
"""Lead #31 suffix-match tests: synthetic bytes and exhaustive permutations only."""
import contextlib
import copy
from fractions import Fraction
import hashlib
import io
import itertools
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_match_probe as probe


def named_temp(mode="w+b", **kwargs):
    """A named temporary file that can be reopened by name while open, also on Windows."""
    @contextlib.contextmanager
    def manager():
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "sample"), mode, **kwargs) as stream:
                yield stream
    return manager()


def permutation_oracle(symbols, width, lag):
    """Independent direct enumeration: None is a fixed unavailable slot.

    No analytic histograms, probabilities, or pair-grouping helpers are used.
    Distinct arrangements have equal probability within a block even with ties.
    """
    choices = []
    for start in range(0, len(symbols), width):
        block = symbols[start:start + width]
        available = [x for x in block if x is not None]
        arrangements = []
        for perm in sorted(set(itertools.permutations(available))):
            iterator = iter(perm)
            arrangements.append(tuple(None if x is None else next(iterator) for x in block))
        choices.append(arrangements)
    matches, count = 0, 0
    for blocks in itertools.product(*choices):
        candidate = sum(blocks, ())
        matches += sum(candidate[i] is not None and candidate[i + lag] is not None
                       and candidate[i] == candidate[i + lag]
                       for i in range(max(0, len(candidate) - lag)))
        count += 1
    return Fraction(matches, count)


def token_lists(symbols):
    return ([17 if s is None else 0 for s in symbols],
            [0 if s is None else s for s in symbols])


def fraction(field):
    return None if field is None else Fraction(field["numerator"], field["denominator"])


def cohort():
    return {"design_id": probe.DESIGN_ID, "design_sha256": probe.DESIGN_SHA256,
            "phase": "replication", "samples": [
                {"id": 101, "name": "Fictional - alpha.ORF", "sha256": "a" * 64},
                {"id": 202, "name": "Fictional - beta.ORI", "sha256": "b" * 64}]}


def synthetic_tiff(payload=b"\x80", width=2, height=3, offset=None, length=None):
    # Original minimal little-endian TIFF container, not image/decoder output.
    base = 8 + 2 + 5 * 12 + 4
    tags = ((0x100, width), (0x101, height), (0x103, 1),
            (0x111, base if offset is None else offset),
            (0x117, len(payload) if length is None else length))
    return (b"II" + struct.pack("<HIH", 42, 8, len(tags))
            + b"".join(struct.pack("<HHII", tag, 4, 1, value) for tag, value in tags)
            + struct.pack("<I", 0) + payload)


class HistogramTests(unittest.TestCase):
    def test_contract_and_no_mutation(self):
        q, s = [0, 16, 17, 1000], [0, 31, 31, 2]
        original = (q[:], s[:])
        h = probe.suffix_histogram(q, s)
        self.assertIs(type(h), tuple)
        self.assertEqual((len(h), sum(h), h[0], h[31]), (32, 2, 1, 1))
        self.assertTrue(all(type(x) is int for x in h))
        self.assertEqual((q, s), original)
        self.assertEqual(probe.suffix_histogram((), []), (0,) * 32)

    def test_types_lengths_and_all_ranges(self):
        class ListSubclass(list):
            pass
        class TupleSubclass(tuple):
            pass
        for bad in (None, "", iter([]), ListSubclass(), TupleSubclass()):
            for q, s in ((bad, []), ([], bad)):
                with self.assertRaises(TypeError):
                    probe.suffix_histogram(q, s)
        for q, s in (([True], [0]), ([0], [False]), ([1.0], [0]), ([0], ["1"])):
            with self.assertRaises(TypeError):
                probe.suffix_histogram(q, s)
        for q, s in (([0], []), ([-1], [0]), ([0], [-1]), ([0], [32]),
                     ([17], [32]), ([99], [-1])):
            with self.assertRaises(ValueError):
                probe.suffix_histogram(q, s)


class ExactMeanTests(unittest.TestCase):
    def check_fixture(self, symbols, width):
        q, s = token_lists(symbols)
        result = probe.analyze_tokens(q, s, width, requested=len(symbols))
        self.assertEqual([r["label"] for r in result["lags"]], list(probe.LABELS))
        for row in result["lags"]:
            lag = row["lag"]
            if lag <= 0:
                self.assertEqual(row["reason"], "invalid_lag")
                self.assertTrue(all(row[k] is None for k in probe.METRICS))
                continue
            expected = permutation_oracle(symbols, width, lag)
            observed = sum(symbols[i] is not None and symbols[i + lag] is not None
                           and symbols[i] == symbols[i + lag]
                           for i in range(max(0, len(symbols) - lag)))
            pairs = sum(symbols[i] is not None and symbols[i + lag] is not None
                        for i in range(max(0, len(symbols) - lag)))
            self.assertEqual((row["P"], row["M"], fraction(row["E"])),
                             (pairs, observed, expected), (symbols, width, row["label"]))
            self.assertEqual(fraction(row["observed_rate"]), Fraction(observed, pairs) if pairs else None)
            self.assertEqual(fraction(row["expected_rate"]), expected / pairs if pairs else None)
            self.assertEqual(fraction(row["difference"]), (observed - expected) / pairs if pairs else None)
            self.assertEqual(fraction(row["ratio"]), observed / expected if expected else None)

    def test_exhaustive_two_blocks_ternary_every_named_lag(self):
        for width in (1, 2, 3):
            for symbols in itertools.product((None, 0, 1), repeat=2 * width):
                self.check_fixture(symbols, width)

    def test_three_blocks_and_suffix_31(self):
        for symbols, width in (([31, None, 0, None, None, None, 31, 0, 31], 3),
                               ([0, 1, None, None, 1, 0], 2),
                               ([None, 31, None], 1),
                               ([31] * 9, 3), ([None] * 9, 3)):
            self.check_fixture(symbols, width)

    def test_same_histograms_different_masks_change_expectation(self):
        a = [0, 1, None, 0, 1, None]
        b = [0, None, 1, 0, 1, None]
        qa, sa = token_lists(a)
        qb, sb = token_lists(b)
        for start in (0, 3):
            self.assertEqual(probe.suffix_histogram(qa[start:start + 3], sa[start:start + 3]),
                             probe.suffix_histogram(qb[start:start + 3], sb[start:start + 3]))
        self.assertNotEqual(probe.lag_counts(qa, sa, 3, 1)[2],
                            probe.lag_counts(qb, sb, 3, 1)[2])
        self.check_fixture(a, 3)
        self.check_fixture(b, 3)

    def test_aliases_boundaries_and_zero_denominators(self):
        result = probe.analyze_tokens([0, 0], [0, 1], 1, requested=2)
        rows = result["lags"]
        self.assertEqual((rows[4]["lag"], rows[4]["reason"]), (-1, "invalid_lag"))
        self.assertEqual((rows[7]["lag"], rows[7]["reason"]), (0, "invalid_lag"))
        self.assertEqual(rows[5]["alias_of"], "1")
        self.assertEqual(rows[6]["alias_of"], "3")
        self.assertEqual(rows[0]["P"], 1)
        self.assertEqual(fraction(rows[0]["E"]), 0)
        self.assertIsNone(rows[0]["ratio"])
        self.assertEqual(fraction(rows[0]["difference"]), 0)
        self.assertEqual(rows[1]["P"], 0)  # lag == N
        self.assertEqual(fraction(rows[1]["E"]), 0)
        self.assertTrue(all(rows[1][k] is None for k in
                            ("observed_rate", "expected_rate", "difference", "ratio")))
        for bad in (0, -1, True, 1.0):
            with self.assertRaises(probe.InputError):
                probe.lag_counts([0], [0], 1, bad)

    def test_discard_and_count_validation(self):
        result = probe.analyze_tokens([0, 0, 0, 17, 17], [0] * 5, 2, requested=5)
        self.assertEqual((result["tokens_retained"], result["tokens_discarded"],
                          result["blocks"], result["escapes_parsed"], result["escapes_retained"]),
                         (4, 1, 2, 2, 1))
        self.assertEqual(result["lags"][0]["P"], 2)
        for width, requested in ((0, 5), (True, 5), (2, True), (6, 5), (2, 4), (2, 6)):
            with self.assertRaises(probe.InputError):
                probe.analyze_tokens([0] * 5, [0] * 5, width, requested)
        with self.assertRaises(probe.InputError):
            probe.lag_counts([0], [0], 2, 1)


class ParseTests(unittest.TestCase):
    def test_actual_synthetic_parser_boundaries(self):
        self.assertEqual(probe.checked_parse(b"\x80", 1, 1), ([0], [0], 6))
        for payload, reason in ((b"\x00", "token_count_mismatch"),
                                (b"\x01", "token_count_mismatch")):
            with self.assertRaisesRegex(probe.InputError, reason):
                probe.checked_parse(payload, 1, 1)

    def test_inconsistent_parser_outputs(self):
        for output, reason in ((([0], [0], [], 7), "invalid_consumed_bits"),
                               (([0], [0], [], True), "invalid_consumed_bits"),
                               (([0], [], [], 6), "invalid_tokens"),
                               (([True], [0], [], 6), "invalid_tokens"),
                               (([17], [32], [], 23), "invalid_tokens"),
                               (([0, 0], [0, 0], [], 12), "token_count_mismatch")):
            with mock.patch.object(probe.orf_tokens, "parse", return_value=output):
                with self.assertRaisesRegex(probe.InputError, reason):
                    probe.checked_parse(b"\x80", 1, 1)

    def test_layout_bounds_and_dimensions(self):
        # Start from a valid signature: signature() now rejects invalid strip
        # extents before check_layout() can examine those negative controls.
        data = synthetic_tiff()
        with named_temp() as stream:
            stream.write(data)
            stream.flush()
            sig = probe.orf_signature.signature(stream.name)
        for kwargs, changes, reason in (({"offset": 1000}, {}, "invalid_payload_bounds"),
                                        ({"length": 0}, {}, "invalid_payload_bounds"),
                                        ({"width": 0}, {"payload_w": 0}, "invalid_dimensions")):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(probe.InputError, reason):
                probe.check_layout(synthetic_tiff(**kwargs), dict(sig, **changes))
        probe.check_layout(data, sig)
        for change, reason in (({"size_class": "packed-12"}, "unsupported_size_class"),
                               ({"payload_offset": 2}, "signature_layout_mismatch"),
                               ({"payload_w": True}, "invalid_dimensions")):
            with self.assertRaisesRegex(probe.InputError, reason):
                probe.check_layout(data, dict(sig, **change))
        with mock.patch.object(probe.orf_signature, "Tiff") as tiff:
            tiff.return_value.all_ifds.return_value = [{0x111: [2, 3], 0x117: [1, 1]}]
            with self.assertRaisesRegex(probe.InputError, "unsupported_strips"):
                probe.check_layout(data, sig)


class CohortAndRunnerTests(unittest.TestCase):
    def test_duplicate_content_hash_is_rejected(self):
        c = cohort()
        c['samples'][1]['sha256'] = c['samples'][0]['sha256']
        with self.assertRaises(probe.InputError):
            probe.validate_cohort(c)

    def test_duplicate_identity_json_key_rejected_before_measurement(self):
        c = cohort()
        source = json.dumps(c)
        variants = (source.replace('"id": 101', '"id": 999, "id": 101'),
                    source.replace('"sha256": "' + 'a' * 64 + '"',
                                   '"sha256": "' + 'c' * 64 + '", "sha256": "' + 'a' * 64 + '"'))
        for text in variants:
            with self.subTest(text=text), named_temp(mode='w', encoding='utf-8') as stream:
                stream.write(text)
                stream.flush()
                with mock.patch.object(probe, 'measure_sample', return_value={'status': 'ok'}) as measure, \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    status = probe.main(['--cohort', stream.name, '--measured-by', '@fictional',
                                         '--sample', '101', '/private/a', '--sample', '202', '/private/b'])
                self.assertEqual(status, 1)
                measure.assert_not_called()
                self.assertEqual(json.loads(output.getvalue())['reason'], 'invalid_cohort_input')
                self.assertNotIn('private', output.getvalue())

    def test_shared_public_name_preserves_distinct_ordered_records(self):
        c = cohort()
        c["samples"][1]["name"] = c["samples"][0]["name"]
        self.assertIs(probe.validate_cohort(c), c)
        self.assertEqual([s["id"] for s in c["samples"]], [101, 202])
        self.assertNotEqual(c["samples"][0]["sha256"], c["samples"][1]["sha256"])
        with named_temp(mode="w", encoding="utf-8") as stream:
            json.dump(c, stream)
            stream.flush()
            with mock.patch.object(probe, "measure_sample", side_effect=[
                    dict(s, status="ok", lags=[]) for s in c["samples"]]):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    status = probe.main(["--cohort", stream.name, "--measured-by", "@fictional",
                                         "--sample", "202", "/private/b", "--sample", "101", "/private/a"])
        self.assertEqual(status, 0)
        samples = json.loads(output.getvalue())["samples"]
        self.assertEqual([(s["id"], s["name"], s["sha256"]) for s in samples],
                         [(s["id"], s["name"], s["sha256"]) for s in c["samples"]])

    def test_malformed_cli_emits_only_stable_sanitized_json(self):
        arguments = (["--sample", "101", "/private/fictional.ORF", "/private/extra.ORF"],
                     ["--sample", "/private/incomplete.ORF"])
        expected = {"metric_version": probe.DESIGN_ID, "status": "failed",
                    "reason": "invalid_cli_arguments", "samples": []}
        script = os.path.join(os.path.dirname(__file__), "suffix_match_probe.py")
        for argv in arguments:
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(probe.main(argv), 2)
            self.assertEqual(json.loads(stdout.getvalue()), expected)
            self.assertEqual(stderr.getvalue(), "")
            self.assertNotIn("private", stdout.getvalue() + stderr.getvalue())
            process = subprocess.run([sys.executable, "-I", script] + argv,
                                     capture_output=True, text=True, check=False)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(json.loads(process.stdout), expected)
            self.assertEqual(process.stderr, "")
            self.assertNotIn("private", process.stdout + process.stderr)

    def test_explicit_help_retains_success(self):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as caught:
                    probe.main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn("--cohort", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_cohort_and_replication_are_generic(self):
        c = cohort()
        self.assertIs(probe.validate_cohort(c), c)
        for phase in ("discovery", "validation", "replication"):
            probe.validate_cohort(dict(c, phase=phase))
        for path in ("lead31-suffix-matches-v1-discovery.json", "lead31-suffix-matches-v1-validation.json"):
            with open(os.path.join(os.path.dirname(__file__), "cohorts", path), encoding="utf-8") as stream:
                probe.validate_cohort(json.load(stream))
        changes = [{"phase": "later"}, {"design_id": "other"}, {"design_sha256": "c" * 64},
                   {"samples": []}, {"samples": tuple(c["samples"])}]
        for change in changes:
            with self.assertRaises(probe.InputError):
                probe.validate_cohort(dict(c, **change))
        for key, value in (("id", True), ("id", -1), ("name", "../private.ORF"),
                           ("name", "secret\n.ORF"), ("name", ""), ("sha256", "x" * 64)):
            bad = copy.deepcopy(c)
            bad["samples"][0][key] = value
            with self.assertRaises(probe.InputError):
                probe.validate_cohort(bad)
        bad = copy.deepcopy(c)
        bad["samples"][1] = dict(bad["samples"][0])
        with self.assertRaisesRegex(probe.InputError, "duplicate_sample_id"):
            probe.validate_cohort(bad)

    def test_mapping_coverage(self):
        c = cohort()
        self.assertEqual(probe.validate_mapping(c, [("202", "/b"), ("101", "/a")]),
                         {101: "/a", 202: "/b"})
        for mappings in ([], [("101", "/a")], [("101", "/a"), ("101", "/b")],
                         [("101", "/a"), ("303", "/b")], [("bad", "/a")],
                         [(True, "/a")], [(101.0, "/a")]):
            with self.assertRaises(probe.InputError):
                probe.validate_mapping(c, mappings)

    def test_sample_failures_never_emit_private_paths(self):
        result = probe.measure_sample(cohort()["samples"][0], "/private/nonexistent/orf")
        self.assertEqual(result["reason"], "input_io_error")
        self.assertEqual(len(result["lags"]), 10)
        self.assertNotIn("private", json.dumps(result))
        with named_temp() as stream:
            stream.write(synthetic_tiff())
            stream.flush()
            result = probe.measure_sample(cohort()["samples"][0], stream.name)
        self.assertEqual(result["reason"], "sample_hash_mismatch")
        self.assertTrue(all(row[k] is None for row in result["lags"] for k in probe.METRICS))

    def test_success_and_failure_preserved_in_cli_order(self):
        c = cohort()
        success = dict(c["samples"][0], status="ok", lags=probe.lag_rows(
            2, lambda lag: (0, 0, Fraction(0))))
        failure = dict(c["samples"][1], status="failed", reason="payload_overrun",
                       lags=probe.lag_rows(2, failure="payload_overrun"))
        with named_temp(mode="w", encoding="utf-8") as stream:
            json.dump(c, stream)
            stream.flush()
            with mock.patch.object(probe, "measure_sample", side_effect=[success, failure]) as measure:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    status = probe.main(["--cohort", stream.name, "--measured-by", "@fictional",
                                         "--sample", "202", "/private/b", "--sample", "101", "/private/a"])
            self.assertEqual(status, 1)
            data = json.loads(output.getvalue())
            self.assertEqual([s["id"] for s in data["samples"]], [101, 202])
            self.assertEqual([s["status"] for s in data["samples"]], ["ok", "failed"])
            self.assertEqual([call.args[1] for call in measure.call_args_list], ["/private/a", "/private/b"])
            self.assertNotIn("private", output.getvalue())
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(probe.main(["--cohort", stream.name, "--measured-by", "@fictional"]), 1)
            self.assertEqual(len(json.loads(output.getvalue())["samples"]), 2)

    def test_synthetic_sample_success_and_locate_crosscheck(self):
        data = synthetic_tiff()
        sample = dict(cohort()["samples"][0], sha256=hashlib.sha256(data).hexdigest())
        with named_temp() as stream:
            stream.write(data)
            stream.flush()
            with mock.patch.object(probe, "checked_parse", return_value=([0], [0], 6)):
                with mock.patch.object(probe, "analyze_tokens", return_value={"lags": []}):
                    result = probe.measure_sample(sample, stream.name)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["signature"]["file"], sample["name"])
            with mock.patch.object(probe.orf_tokens, "locate", return_value=(2, 3, b"")):
                result = probe.measure_sample(sample, stream.name)
            self.assertEqual(result["reason"], "locate_signature_mismatch")

    def test_unmocked_full_prefix_synthetic_container(self):
        # 100000 repeated: q=0, suffix=0. No real file/token/pixel input.
        data = synthetic_tiff(b"\x82\x08\x20" * 65536, width=4096, height=1)
        sample = dict(cohort()["samples"][0], sha256=hashlib.sha256(data).hexdigest())
        with named_temp() as stream:
            stream.write(data)
            stream.flush()
            result = probe.measure_sample(sample, stream.name)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["tokens_parsed"], probe.PREFIX)
        self.assertEqual((result["tokens_discarded"], result["blocks"], result["escapes_parsed"]),
                         (0, 64, 0))
        self.assertEqual(result["consumed_bits"], 6 * probe.PREFIX)
        for row in result["lags"]:
            pairs = probe.PREFIX - row["lag"]
            self.assertEqual((row["P"], row["M"], fraction(row["E"])), (pairs, pairs, pairs))
            self.assertEqual(fraction(row["ratio"]), 1)
        self.assertEqual(result["signature"]["file"], sample["name"])

    def test_invalid_cohort_cli_is_sanitized_json(self):
        with named_temp(mode="w", encoding="utf-8") as stream:
            stream.write("invalid JSON /private/fictional")
            stream.flush()
            with contextlib.redirect_stdout(io.StringIO()) as output:
                status = probe.main(["--cohort", stream.name, "--measured-by", "@fictional"])
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(output.getvalue())["reason"], "invalid_cohort_input")
        self.assertNotIn("private", output.getvalue())


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
    else:
        unittest.main()
