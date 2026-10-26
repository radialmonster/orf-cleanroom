"""Deterministic synthetic checks for value_map_probe; never opens target data."""

import contextlib
import io
import itertools
import json
import os
import struct
import sys
import tempfile
import unittest
from fractions import Fraction
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # also under python -I
import value_map_probe as probe


def oracle(xs):
    """Build exact rational bridges explicitly, independently of integer A/V."""
    n = len(xs)
    mean = Fraction(sum(xs), n)
    bridges = [sum(Fraction(x) - mean for x in xs[:k]) for k in range(1, n + 1)]
    energy = sum(b * b for b in bridges) / n
    variance = sum((Fraction(x) - mean) ** 2 for x in xs) / n
    return energy, Fraction(n + 1, 6) * variance


def exact(serialized):
    if serialized is None:
        return None
    value = Fraction(serialized["numerator"], serialized["denominator"])
    if serialized["approx"] != float(value):
        raise AssertionError("incorrect approximate display value")
    return value


def encoded_tokens(tokens):
    bits = "".join("0" * q + "1" + format(s, "05b") for q, s in tokens)
    bits += "0" * (-len(bits) % 8)
    return int(bits, 2).to_bytes(len(bits) // 8, "big")


def synthetic_tiff(payload):
    """Minimal original TIFF 6.0 container; only artificial token bytes."""
    tags = [(0x100, 128), (0x101, 2), (0x102, 12), (0x103, 1),
            (0x111, 8 + 2 + 6 * 12 + 4), (0x117, len(payload))]
    return (b"II" + struct.pack("<HIH", 42, 8, len(tags))
            + b"".join(struct.pack("<HHII", tag, 4, 1, value) for tag, value in tags)
            + struct.pack("<I", 0) + payload)


class BridgeTests(unittest.TestCase):
    def test_fixed_integer_terms(self):
        self.assertEqual(probe.bridge_energy_terms([0, 1]), (2, 1, 1))
        self.assertEqual(probe.bridge_energy_terms([-1, 0, 2]), (3, 41, 14))
        self.assertEqual(probe.bridge_energy_terms([7]), (1, 0, 0))
        for constant in (-10 ** 90, 0, 7, 10 ** 90):
            self.assertEqual(probe.bridge_energy_terms([constant] * 9), (9, 0, 0))

    def test_invalid_inputs_and_nonmutation(self):
        for obj in (None, 1, "123", {1: 2}, {1, 2}, iter([1]), range(3)):
            with self.assertRaises(TypeError):
                probe.bridge_energy_terms(obj)
        for obj in ([], ()):
            with self.assertRaises(ValueError):
                probe.bridge_energy_terms(obj)
        class IntSubclass(int):
            pass
        class ListSubclass(list):
            pass
        for obj in ([True], [False], [1.0], [Fraction(1)], [IntSubclass(1)], ListSubclass([1])):
            with self.assertRaises(TypeError):
                probe.bridge_energy_terms(obj)
        xs = [-10 ** 100, 3, 10 ** 99, -8]
        before = xs[:]
        result = probe.bridge_energy_terms(xs)
        self.assertEqual(xs, before)
        self.assertTrue(all(type(x) is int for x in result))
        self.assertEqual(result, probe.bridge_energy_terms(tuple(xs)))
        self.assertEqual(probe.energies(*result), oracle(xs))

    def test_exhaustive_labeled_permutation_null(self):
        total = 0
        for xs in ([0, 1], [-1, 0, 2], [-2, -2, 1, 3], [0, 0, 0, 1], [6, 6, 6]):
            energies = []
            for perm in itertools.permutations(xs):
                n, a, v = probe.bridge_energy_terms(perm)
                energy, null = oracle(perm)
                self.assertEqual(probe.energies(n, a, v), (energy, null))
                self.assertEqual(v, probe.bridge_energy_terms(xs)[2])
                energies.append(energy)
            self.assertEqual(sum(energies) / len(energies), oracle(xs)[1])
            total += len(energies)
        self.assertEqual(total, 62)

    def test_exhaustive_small_domain_properties(self):
        count = 0
        for n in range(1, 6):
            for xs in itertools.product((-2, 0, 3), repeat=n):
                _, a, v = probe.bridge_energy_terms(xs)
                self.assertEqual(probe.energies(n, a, v), oracle(xs))
                self.assertEqual(probe.bridge_energy_terms(tuple(reversed(xs))), (n, a, v))
                self.assertEqual(probe.bridge_energy_terms([x + 19 for x in xs]), (n, a, v))
                for scale in (-7, 2):
                    self.assertEqual(probe.bridge_energy_terms([scale * x for x in xs]),
                                     (n, a * scale ** 2, v * scale ** 2))
                    self.assertEqual(probe.ratio(n, a * scale ** 2, v * scale ** 2), probe.ratio(n, a, v))
                if n == 2 and v:
                    self.assertEqual(probe.ratio(n, a, v), 1)
                count += 1
        self.assertEqual(count, 363)

    def test_opposite_ordering_controls(self):
        for n in (2, 4, 8, 64, 128):
            for xs, expected_e, expected_r in (
                    ([-1, 1] * (n // 2), Fraction(1, 2), Fraction(3, n + 1)),
                    ([-1] * (n // 2) + [1] * (n // 2), Fraction(n * n + 2, 12),
                     Fraction(n * n + 2, 2 * (n + 1)))):
                _, a, v = probe.bridge_energy_terms(xs)
                self.assertEqual(oracle(xs)[0], expected_e)
                self.assertEqual(probe.energies(n, a, v)[0], expected_e)
                self.assertEqual(probe.ratio(n, a, v), expected_r)


class AggregateTests(unittest.TestCase):
    def test_all_suffix_mappings(self):
        signed_digit = [0, 1, 2, 3, -8, -7, -6, -5, 4, 5, 6, 7, -4, -3, -2, -1,
                        8, 9, 10, 11, 0, 1, 2, 3, 12, 13, 14, 15, 4, 5, 6, 7]
        low3 = [0, 1, 2, 3, -4, -3, -2, -1] * 4
        for name, table in (("signed_digit", signed_digit), ("signed_low3", low3),
                            ("unsigned_suffix", list(range(32)))):
            self.assertEqual([probe.map_suffix(s, name) for s in range(32)], table)
        with self.assertRaises(ValueError):
            probe.map_suffix(0, "unplanned")

    def test_escape_omissions_absolute_parity_and_zero_variance(self):
        qs = [0] * (5 * 128 + 7)
        for index in (0, 255, 300, 641):
            qs[index] = 17
        ss = [0 if j % 2 == 0 else (j // 2) % 32 for j in range(len(qs))]
        ss[512:640] = [4] * 128
        report = probe.token_aggregates(qs, ss)
        self.assertEqual(report["omissions"], {
            "parsed_tokens": 647, "complete_blocks": 5, "retained_blocks": 2,
            "escape_omitted_blocks": 3, "parsed_escapes": 4,
            "escapes_in_incomplete_tail": 1, "incomplete_tail_tokens": 7,
            "escape_omitted_tokens": 384, "total_omitted_tokens": 391})
        self.assertEqual(len(report["cells"]), 6)
        for cell in report["cells"]:
            self.assertEqual([b["block_index"] for b in cell["blocks"]], [3, 4])
            self.assertEqual(cell["zero_variance_blocks"], 1)
            self.assertEqual(cell["pool"]["zero_variance_lanes"], 1 if cell["lane_count"] == 1 else 3)
            self.assertEqual(cell["blocks"][1]["R"], None)
            self.assertEqual(cell["block_ratios"]["defined_blocks"], 1)
            energy_total, null_total = Fraction(0), Fraction(0)
            for block in cell["blocks"]:
                block_e, block_n = Fraction(0), Fraction(0)
                for lane in block["lanes"]:
                    parity = lane["absolute_parity"]
                    indices = [j for j in range(block["block_index"] * 128, (block["block_index"] + 1) * 128)
                               if parity is None or j % 2 == parity]
                    xs = [probe.map_suffix(ss[j], cell["mapping"]) for j in indices]
                    e, null = oracle(xs)
                    self.assertEqual(Fraction(lane["A"], len(xs) ** 3), e)
                    block_e += e
                    block_n += null
                self.assertEqual(exact(block["sum_E"]), block_e)
                self.assertEqual(exact(block["sum_N"]), block_n)
                self.assertEqual(exact(block["R"]), block_e / block_n if block_n else None)
                energy_total += block_e
                null_total += block_n
            self.assertEqual(exact(cell["pool"]["R_pool"]), energy_total / null_total)
            self.assertEqual(exact(cell["pool"]["mean_E"]), energy_total / (2 * cell["lane_count"]))
            self.assertEqual(exact(cell["pool"]["mean_N"]), null_total / (2 * cell["lane_count"]))
            if cell["lane_count"] == 2:
                self.assertEqual([p["absolute_parity"] for p in cell["parity_pools"]], [0, 1])
                self.assertIsNone(cell["parity_pools"][0]["R_pool"])
                self.assertEqual(exact(cell["parity_pools"][1]["R_pool"]), energy_total / null_total)

    def test_escape_boundaries_and_unary_not_assembled(self):
        ss = [j % 32 for j in range(384)]
        baseline = probe.token_aggregates([0] * 384, ss)
        self.assertEqual(baseline, probe.token_aggregates([16] * 384, ss))
        for index, omitted in ((127, 0), (128, 1), (383, 2)):
            qs = [0] * 384
            qs[index] = 99
            result = probe.token_aggregates(qs, ss)
            self.assertEqual(result["omissions"]["escape_omitted_blocks"], 1)
            self.assertEqual([b["block_index"] for b in result["cells"][0]["blocks"]],
                             [j for j in range(3) if j != omitted])

    def test_empty_and_zero_variance_cells(self):
        for qs, ss in (([], []), ([0] * 7, [5] * 7), ([17] + [0] * 127, [5] * 128)):
            for cell in probe.token_aggregates(qs, ss)["cells"]:
                self.assertEqual(cell["blocks"], [])
                self.assertEqual(cell["pool"]["lane_count"], 0)
                for name in ("mean_E", "mean_N", "R_pool"):
                    self.assertIsNone(cell["pool"][name])
                self.assertIsNone(cell["block_ratios"]["distribution"])
        for cell in probe.token_aggregates([0] * 128, [3] * 128)["cells"]:
            self.assertEqual(cell["pool"]["zero_variance_lanes"], cell["lane_count"])
            self.assertEqual(cell["zero_variance_blocks"], 1)
            self.assertEqual(exact(cell["pool"]["sum_E"]), 0)
            self.assertEqual(exact(cell["pool"]["sum_N"]), 0)
            self.assertIsNone(cell["pool"]["R_pool"])
            self.assertEqual(cell["block_ratios"]["fraction_denominator"], 0)

    def test_variance_weighted_pooling(self):
        sequences = ([-1, 1, -1, 1], [-3, -3, 3, 3], [7] * 4)
        terms = [probe.bridge_energy_terms(xs)[1:] for xs in sequences]
        result = probe.pooled(4, terms)
        energies = [oracle(xs) for xs in sequences]
        expected = sum(x[0] for x in energies) / sum(x[1] for x in energies)
        unweighted = sum(e / n for e, n in energies if n) / 2
        self.assertEqual(expected, Fraction(42, 25))
        self.assertEqual(unweighted, Fraction(6, 5))
        self.assertEqual(exact(result["R_pool"]), expected)
        self.assertNotEqual(expected, unweighted)
        self.assertEqual(result["zero_variance_lanes"], 1)

    def test_exact_threshold_quantiles_and_empty(self):
        delta = Fraction(1, 10 ** 50)
        low, equal, high = Fraction(1, 2) - delta, Fraction(1, 2), Fraction(1, 2) + delta
        result = probe.ratio_summary([high, Fraction(9, 10), equal, low])
        self.assertEqual(result["at_most_half_count"], 2)
        self.assertEqual(result["fraction_denominator"], 4)
        self.assertEqual(exact(result["at_most_half_fraction"]), Fraction(1, 2))
        for key, expected in (("min", low), ("Q25", low), ("median", equal),
                              ("Q75", high), ("max", Fraction(9, 10))):
            self.assertEqual(exact(result["distribution"][key]), expected)
        # Exact threshold equality also agrees with the frozen integer test.
        self.assertEqual(probe.ratio(3, 1, 1), Fraction(1, 2))
        self.assertEqual(12 * 1, 3 * (3 + 1) * 1)
        empty = probe.ratio_summary([])
        self.assertIsNone(empty["distribution"])
        self.assertIsNone(empty["at_most_half_fraction"])
        for count in (1, 2, 3, 5, 9):
            result = probe.ratio_summary([Fraction(j) for j in range(count)])
            for name, p in (("Q25", Fraction(1, 4)), ("median", Fraction(1, 2)), ("Q75", Fraction(3, 4))):
                rank = -(-(p.numerator * count) // p.denominator)
                self.assertEqual(exact(result["distribution"][name]), rank - 1)

    def test_invalid_token_arrays(self):
        for qs, ss in (([0], []), ([-1], [0]), ([False], [0]), ([0], [32]), ([0], [True]),
                       ([0] * (probe.MAX_TOKENS + 1), [0] * (probe.MAX_TOKENS + 1))):
            with self.assertRaises(probe.ProbeError):
                probe.token_aggregates(qs, ss)


class RunnerTests(unittest.TestCase):
    def test_original_parser_synthetic_prefixes_and_overrun(self):
        tokens = [(0, 0), (2, 31), (17, 7), (100, 3), (1, 16)]
        payload = encoded_tokens(tokens)
        for count in range(1, len(tokens) + 1):
            qs, ss, bits = probe.guarded_parse(payload, count)
            self.assertEqual(list(zip(qs, ss)), tokens[:count])
            self.assertEqual(bits, sum(q + 6 for q, s in tokens[:count]))
        with self.assertRaises(probe.ProbeError):
            probe.guarded_parse(b"\x01", 1)  # no complete token; suffix would be in padding
        for count in (0, -1, probe.MAX_TOKENS + 1, True, 1.0):
            with self.assertRaises(probe.ProbeError):
                probe.guarded_parse(b"", count)

    def test_synthetic_container_measurement_provenance_and_no_paths(self):
        payload = encoded_tokens([(0, j % 32) for j in range(256)])
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "PRIVATE_LOCAL_NAME.ORF")
            with open(path, "wb") as stream:
                stream.write(synthetic_tiff(payload))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = probe.main(["--phase", "discovery", "--measured-by", "synthetic-user",
                                     "--sample", "1993", "SYNTHETIC_TEST_ONLY.ORF", path, "--max-tokens", "256"])
            self.assertEqual(status, 0)
            text = output.getvalue()
            self.assertNotIn(directory, text)
            self.assertNotIn("PRIVATE_LOCAL_NAME", text)
            result = json.loads(text)
            self.assertEqual(result["measured_by"], "synthetic-user")
            self.assertEqual(set(result["provenance"]["source_sha256"]),
                             {"value_map_probe.py", "orf_tokens.py", "orf_signature.py"})
            sample = result["samples"][0]
            self.assertEqual(sample["measured_signature"]["file"], "SYNTHETIC_TEST_ONLY.ORF")
            self.assertEqual(sample["returned_tokens"], 256)
            self.assertEqual(sample["consumed_bits"], 1536)
            self.assertEqual(len(sample["cells"]), 6)
            self.assertEqual(sample["sha256"], probe.file_hash(path))
            with open(path, "wb") as stream:
                stream.write(synthetic_tiff(payload)[:-1])
            # The signature validator rejects the truncated strip before the
            # measurement-specific bounds check can run.
            with self.assertRaisesRegex(ValueError, "strip extent"):
                probe.measure(1993, "SYNTHETIC_TEST_ONLY.ORF", path, 256)

    def test_fail_closed_and_diagnostics_hide_paths(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = probe.main(["--phase", "validation", "--measured-by", "synthetic-user",
                                 "--sample", "1998", "PUBLIC.ORF", "/private/nonexistent/sample.ORF"])
        self.assertEqual(status, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn("/private", stderr.getvalue())
        self.assertIn("no results emitted", stderr.getvalue())
        with mock.patch.object(probe.orf_tokens, "parse", return_value=([0], [0], [], 9)):
            with self.assertRaises(probe.ProbeError):
                probe.guarded_parse(b"\xff", 1)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            probe.main(["--max-tokens", "/private/not-an-integer"])
        self.assertNotIn("/private", stderr.getvalue())

    def test_cli_rejects_unfrozen_samples_and_settings(self):
        base = ["--phase", "discovery", "--measured-by", "synthetic-user"]
        cases = [base + ["--sample", "1998", "PUBLIC.ORF", "/unused"],
                 base + ["--sample", "1993", "/private/PUBLIC.ORF", "/unused"],
                 base + ["--sample", "1993", "PUBLIC.ORF", "/unused", "--max-tokens", "262145"],
                 base + ["--sample", "1993", "PUBLIC.ORF", "/unused"] * 2,
                 ["--self-test", "--phase", "discovery"]]
        for args in cases:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                probe.main(args)
            self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
