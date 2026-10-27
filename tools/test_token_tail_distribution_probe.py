#!/usr/bin/env python3
"""Independent synthetic controls for fixed candidate-tail distributions."""
import contextlib
import hashlib
import io
import json
import math
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_tail_distribution_probe as probe


def encode(tokens):
    bits = "".join("0" * q + "1" + format(s, "05b") for q, s in tokens)
    padded = bits + "0" * (-len(bits) % 8)
    return int(padded, 2).to_bytes(len(padded) // 8, "big"), len(bits)


class TailDistributionTests(unittest.TestCase):
    def test_public_identity_before_measurement(self):
        def args(pairs):
            return sum((["--sample", sid, name, "0" * 64, "unused"] for sid, name in pairs), []) + ["--stride", "8"]
        for pairs in ([('1', 'ok'), ('01', 'ok')], [('0', 'ok')], [('\u0661', 'ok')],
                      [('-1', 'ok')], [('1', 'ok'), ('2', '')],
                      [('1', 'ok'), ('2', 'private/name')], [('1', 'ok'), ('2', 'private\\name')],
                      [('1', 'ok'), ('2', 'private\nname')]):
            with self.subTest(pairs=pairs):
                output, error = io.StringIO(), io.StringIO()
                with mock.patch.object(probe, 'measure') as measure, contextlib.redirect_stdout(output), \
                        contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    probe.main(args(pairs))
                self.assertEqual(raised.exception.code, 2)
                measure.assert_not_called()
                self.assertEqual(output.getvalue(), '')
                self.assertNotIn('private', error.getvalue())
        with mock.patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True), \
                mock.patch.object(probe, 'measure') as measure, contextlib.redirect_stderr(io.StringIO()) as error, \
                self.assertRaises(SystemExit) as raised:
            probe.main(args([('1', 'ok')]))
        self.assertEqual(raised.exception.code, 2)
        self.assertNotIn('private detail', error.getvalue())
        measure.assert_not_called()
        output = io.StringIO()
        with mock.patch.object(probe, 'measure', return_value={'token_shortfall': 0}), \
                contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(args([('01', 'Camera "é" (4:3), +.ORF')])), 0)
        self.assertEqual((json.loads(output.getvalue())['samples'][0]['pixls_id'],
                          json.loads(output.getvalue())['samples'][0]['pixls_name']),
                         ('01', 'Camera "é" (4:3), +.ORF'))

    def test_parser_complete_and_truncated(self):
        tokens = [(q, (q * 3) % 32) for q in (0, 1, 7, 17, 96, 2)]
        payload, nbits = encode(tokens)
        parsed = list(probe.scan_tokens(payload, 100))
        self.assertEqual([(q, s) for q, s, _ in parsed], tokens)
        self.assertEqual(parsed[-1][2], nbits)
        self.assertEqual(list(probe.scan_tokens(bytes([1]), 100)), [])
        self.assertEqual(list(probe.scan_tokens(bytes([0x81]), 100)), [(0, 0, 6)])
        self.assertEqual(len(list(probe.scan_tokens(payload, 2))), 2)

    def test_planted_tail_and_exact_region_counts(self):
        row = [(0, 0)] * 6 + [(17, 31)] * 2
        payload, nbits = encode(row * 3)
        result = probe.distributions(payload, 6, 8, [0], 3)
        self.assertEqual((result["parsed_tokens"], result["consumed_bits"]), (24, nbits))
        band = result["bands"][0]
        regions = band["regions"]
        self.assertEqual(regions["first_width"]["q_counts"], {"0": 18})
        self.assertEqual(regions["tail"]["q_counts"], {"17": 6})
        self.assertEqual(regions["tail"]["escape_tokens"], 6)
        self.assertEqual(regions["tail"]["sum_q"], 102)
        for key in ("preceding", "middle"):
            self.assertEqual(regions[key]["tokens"], 6)
            self.assertEqual(band["tail_comparisons"][key]["q_total_variation"], 1)
            self.assertEqual(band["tail_comparisons"][key]["suffix_total_variation"], 1)

    def test_separated_bands_and_partial_row_exclusion(self):
        tokens = [(r, r) for r in range(5) for _ in range(8)] + [(17, 31)] * 3
        payload, _ = encode(tokens)
        result = probe.distributions(payload, 6, 8, [0, 3, 5], 2)
        self.assertEqual(result["parsed_tokens"], 43)
        self.assertEqual(result["token_shortfall"], 13)
        self.assertEqual([b["complete_rows"] for b in result["bands"]], [2, 2, 0])
        self.assertEqual(result["bands"][1]["regions"]["tail"]["q_counts"], {"3": 2, "4": 2})
        self.assertEqual(result["bands"][2]["regions"]["tail"]["tokens"], 0)
        self.assertIsNone(result["bands"][2]["tail_comparisons"]["middle"]["q_total_variation"])

    def test_brute_force_histograms_and_normalization(self):
        tokens = [(i % 23, (7 * i) % 32) for i in range(160)]
        payload, _ = encode(tokens)
        band = probe.distributions(payload, 6, 8, [2], 5)["bands"][0]
        for key, (lo, hi) in probe.regions(6, 8).items():
            expected = [tokens[r * 8 + p] for r in range(2, 7) for p in range(lo, hi)]
            qhist = {str(q): sum(a == q for a, _ in expected) for q in sorted({a for a, _ in expected})}
            shist = [sum(s == suffix for _, s in expected) for suffix in range(32)]
            self.assertEqual(band["regions"][key]["q_counts"], qhist)
            self.assertEqual(band["regions"][key]["suffix_counts_0_to_31"], shist)
        self.assertEqual(probe.total_variation({0: 2, 1: 2}, {0: 3, 1: 1}), 0.25)
        self.assertEqual(probe.total_variation({0: 1}, {0: 5}), 0)
        self.assertTrue(math.isclose(probe.entropy([2, 2]), 1))
        self.assertIsNone(probe.entropy([0, 0]))

    def test_hash_rejection_precedes_tiff_access(self):
        with mock.patch("builtins.open", mock.mock_open(read_data=b"sample")):
            with mock.patch.object(probe, "Tiff") as tiff:
                with self.assertRaises(ValueError):
                    probe.measure("unused", "0" * 64, 8, [0], 3)
                tiff.assert_not_called()

    def test_cli_sanitized_failure_and_duplicate_id(self):
        output = io.StringIO()
        with mock.patch.object(probe, "measure", side_effect=OSError("private-path")):
            with contextlib.redirect_stdout(output):
                code = probe.main(["--sample", "1", "PUBLIC", hashlib.sha256(b"x").hexdigest(),
                                   "private-path", "--stride", "8"])
        self.assertEqual(code, 1)
        self.assertNotIn("private-path", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["samples"],
                         [dict(pixls_id="1", pixls_name="PUBLIC", ok=False, error="OSError")])
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                probe.main(["--sample", "1", "A", "0" * 64, "a",
                            "--sample", "1", "B", "0" * 64, "b", "--stride", "8"])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
