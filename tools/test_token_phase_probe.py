#!/usr/bin/env python3
"""Synthetic numerical checks for token_phase_probe.py (#30); no sample files."""
import contextlib
import io
import json
import struct
import itertools
import math
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_phase_probe as probe  # noqa: E402
from token_phase_probe import phase_statistics  # noqa: E402
from suffix_joint_probe import scan_prefix  # noqa: E402


class PhaseTests(unittest.TestCase):
    def test_balanced_controls(self):
        # Each phase gets each symbol exactly once, for every declared modulus.
        # Entropies are sums of float logs, so they are compared to 12 places, not exactly.
        period = 840  # lcm(2..8)
        tokens = [(0, suffix) for suffix in (0, 4, 16, 20) for _ in range(period)]
        for result in phase_statistics(tokens)["moduli"]:
            expected = period // result["modulus"]
            self.assertEqual(result["phase_by_symbol_00_01_10_11"],
                             [[expected] * 4 for _ in range(result["modulus"])])
            self.assertAlmostEqual(result["plugin_mi_bits"], 0, places=12)
            self.assertAlmostEqual(result["symbol_entropy_bits"], 2, places=12)
            self.assertAlmostEqual(result["conditional_symbol_entropy_bits"], 2, places=12)

    def test_planted_phase_lock(self):
        tokens = [(0, (0, 4, 16, 20)[i % 4]) for i in range(800)]
        results = {r["modulus"]: r for r in phase_statistics(tokens)["moduli"]}
        self.assertAlmostEqual(results[4]["plugin_mi_bits"], 2, places=12)
        self.assertAlmostEqual(results[2]["plugin_mi_bits"], 1, places=12)
        self.assertAlmostEqual(results[4]["conditional_symbol_entropy_bits"], 0, places=12)

    def test_escape_indices_not_compacted(self):
        result = phase_statistics([(0, 0), (17, 20), (0, 4), (0, 16)])
        self.assertEqual(result["escape_omitted_tokens"], 1)
        self.assertEqual(result["retained_tokens"], 3)
        self.assertEqual(result["moduli"][0]["phase_by_symbol_00_01_10_11"],
                         [[1, 1, 0, 0], [0, 0, 1, 0]])

    def test_entropy_identity_exhaustive(self):
        # A separate empirical entropy oracle builds joint labels and marginals.
        def oracle(values):
            return math.fsum(-(values.count(v) / len(values)) * math.log(values.count(v) / len(values)) / math.log(2) for v in set(values))
        for suffixes in itertools.product((0, 4, 16), repeat=5):
            results = phase_statistics([(0, s) for s in suffixes])
            for r in results["moduli"]:
                m = r["modulus"]
                symbols = [(s >> 4) * 2 + ((s >> 2) & 1) for s in suffixes]
                phases = [i % m for i in range(5)]
                expected = oracle(symbols) + oracle(phases) - oracle(list(zip(phases, symbols)))
                self.assertAlmostEqual(r["plugin_mi_bits"], expected, places=12)
                self.assertAlmostEqual(r["symbol_entropy_bits"] - r["conditional_symbol_entropy_bits"], expected, places=12)

    def test_degenerate_and_validation(self):
        for tokens in ([], [(17, 4), (96, 20)]):
            for r in phase_statistics(tokens)["moduli"]:
                self.assertIsNone(r["plugin_mi_bits"])
                self.assertIsNone(r["symbol_entropy_bits"])
                self.assertIsNone(r["conditional_symbol_entropy_bits"])
        for r in phase_statistics([(0, 20)] * 23)["moduli"]:
            self.assertEqual(r["plugin_mi_bits"], 0)
        for token in ((-1, 0), (True, 0), (0, 32), (0, -1), (0, False)):
            with self.assertRaises(ValueError):
                phase_statistics([token])

    def test_count_accounting(self):
        tokens = [(17 if i % 13 == 0 else i % 3, i % 32) for i in range(100)]
        original = list(tokens)
        result = phase_statistics(tokens)
        self.assertEqual(tokens, original)
        self.assertEqual(result["parsed_tokens"], 100)
        self.assertEqual(result["escape_omitted_tokens"], 8)
        for r in result["moduli"]:
            self.assertEqual(sum(r["phase_counts"]), 92)
            self.assertEqual(sum(r["symbol_counts"]), 92)
            self.assertEqual(sum(map(sum, r["phase_by_symbol_00_01_10_11"])), 92)

    def test_parser_roundtrip_and_truncation(self):
        expected = [(q, s) for q, s in zip((0, 17, 96, 1, 3), (0, 4, 16, 20, 31))]
        bits = "".join("0" * q + "1" + format(s, "05b") for q, s in expected)
        padded = bits + "0" * (-len(bits) % 8)
        payload = int(padded, 2).to_bytes(len(padded) // 8, "big")
        self.assertEqual(scan_prefix(payload), (expected, len(bits)))
        self.assertEqual(scan_prefix(bytes([0x81])), ([(0, 0)], 6))
        self.assertEqual(scan_prefix(bytes(20)), ([], 0))
        self.assertEqual(scan_prefix(bytes([1])), ([], 0))


class PhaseCliTests(unittest.TestCase):
    @staticmethod
    def tiff(payload):
        # Original minimal TIFF fixture, all numeric tags inline; no disk data.
        tags = [(0x100, 10), (0x101, 10), (0x103, 1),
                (0x111, 8 + 2 + 5 * 12 + 4), (0x117, len(payload))]
        header = b"II" + struct.pack("<HIH", 42, 8, len(tags))
        entries = b"".join(struct.pack("<HHII", tag, 4, 1, value)
                           for tag, value in tags)
        return header + entries + struct.pack("<I", 0) + payload

    def run_main(self, payloads):
        # Mock only sample reads, retaining actual source-hash reads and report.
        real_open = open
        argv = ["token_phase_probe.py"]
        for sample_id in payloads:
            argv += ["--sample", sample_id, "synthetic", "fixture-" + sample_id]

        def sample_open(path, mode="r", *args, **kwargs):
            for sample_id, payload in payloads.items():
                if path == "fixture-" + sample_id:
                    if payload is None:
                        raise OSError("private-path-must-not-appear")
                    return io.BytesIO(self.tiff(payload))
            return real_open(path, mode, *args, **kwargs)

        output = io.StringIO()
        with mock.patch.object(probe, "LIMIT", 4), \
                mock.patch.object(sys, "argv", argv), \
                mock.patch("builtins.open", side_effect=sample_open), \
                contextlib.redirect_stdout(output):
            status = probe.main()
        self.assertNotIn("private-path-must-not-appear", output.getvalue())
        return status, json.loads(output.getvalue())

    def test_complete_prefix(self):
        status, output = self.run_main({"1": bytes([255] * 3)})
        self.assertEqual(status, 0)
        sample = output["samples"][0]
        self.assertEqual(sample["requested_tokens"], 4)
        self.assertEqual(sample["prefix_shortfall"], 0)
        self.assertEqual(sample["statistics"]["parsed_tokens"], 4)
        self.assertEqual(sample["bits_consumed"], 24)
        self.assertEqual(output["failures"], [])

    def test_short_prefix_retains_statistics(self):
        status, output = self.run_main({"1": bytes([255])})
        self.assertEqual(status, 1)
        sample = output["samples"][0]
        self.assertEqual(sample["prefix_shortfall"], 3)
        self.assertEqual(sample["statistics"]["parsed_tokens"], 1)
        self.assertEqual(sample["statistics"]["retained_tokens"], 1)
        self.assertEqual(sample["bits_consumed"], 6)
        self.assertEqual(output["failures"], [])

    def test_no_complete_tokens(self):
        status, output = self.run_main({"1": bytes([0])})
        self.assertEqual(status, 1)
        sample = output["samples"][0]
        self.assertEqual(sample["prefix_shortfall"], 4)
        self.assertEqual(sample["statistics"]["parsed_tokens"], 0)
        self.assertEqual(sample["bits_consumed"], 0)
        self.assertTrue(all(r["plugin_mi_bits"] is None
                            for r in sample["statistics"]["moduli"]))

    def test_mixed_complete_and_short(self):
        status, output = self.run_main({"1": bytes([255] * 3), "2": bytes([255])})
        self.assertEqual(status, 1)
        self.assertEqual([s["prefix_shortfall"] for s in output["samples"]], [0, 3])
        self.assertEqual(output["failures"], [])

    def test_mixed_complete_and_exception(self):
        status, output = self.run_main({"1": bytes([255] * 3), "2": None})
        self.assertEqual(status, 1)
        self.assertEqual([s["pixls_id"] for s in output["samples"]], ["1"])
        self.assertEqual(output["failures"], [{"pixls_id": "2", "error": "OSError"}])


if __name__ == "__main__":
    unittest.main()
