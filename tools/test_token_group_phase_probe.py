#!/usr/bin/env python3
"""Original synthetic arithmetic/selection/CLI tests for group-phase diagnostic."""
import contextlib
from fractions import Fraction
import io
import json
import math
import os
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_group_phase_probe as probe


def fixture(tokens, endian="<"):
    bits = "".join("0" * q + "1" + format(s, "05b") for q, s in tokens)
    bits += "0" * (-len(bits) % 8)
    payload = int(bits, 2).to_bytes(len(bits) // 8, "big") if bits else b""
    entries = [(256, 100), (257, 100), (259, 1), (273, 74), (279, len(payload))]
    order = b"II" if endian == "<" else b"MM"
    header = order + struct.pack(endian + "HIH", 42, 8, len(entries))
    for tag, value in entries:
        header += struct.pack(endian + "HHII", tag, 4, 1, value)
    return header + struct.pack(endian + "I", 0) + payload


class GroupPhaseTests(unittest.TestCase):
    def test_identity_rejected_before_any_measurement(self):
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
            conversion = patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(simulated=simulated, case=samples[-1][0][:4]), patch.object(probe, 'report') as measured, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(args)
                self.assertEqual(caught.exception.code, 2)
                measured.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_valid_public_identity_spelling_is_preserved(self):
        name = 'OM - Élite "camera" (4:3).ORF'
        def echo(sid, public=None, path=None, *args):
            return {'pixls_id': sid, 'pixls_name': public, 'prefix_complete': True, 'prefix_shortfall': 0}
        args = ['--sample', '01', name, 'unused']
        out = io.StringIO()
        with patch.object(probe, 'report', side_effect=echo), contextlib.redirect_stdout(out):
            status = probe.main(args)
        self.assertEqual(status, 0)
        sample = json.loads(out.getvalue())['samples'][0]
        self.assertEqual((sample['pixls_id'], sample['pixls_name']), ('01', name))


    def test_fraction_oracle_every_phase(self):
        blocks = [[(i * 7 + b * 11) % 13 for i in range(probe.BLOCK)] for b in range(2)]
        for g in probe.GROUPS:
            m = (probe.BLOCK - g + 1) // g
            for p in range(g):
                groups = [block[p + g * j:p + g * (j + 1)] for block in blocks for j in range(m)]
                means = [Fraction(sum(xs), g) for xs in groups]
                grand = sum(means) / len(means)
                bss = g * sum((v - grand) ** 2 for v in means)
                wss = sum(sum((Fraction(v) - mu) ** 2 for v in xs) for xs, mu in zip(groups, means))
                msb = bss / (len(groups) - 1)
                msw = wss / (len(groups) * (g - 1))
                icc = (msb - msw) / (msb + (g - 1) * msw)
                actual = probe.phase_cell(blocks, g, p)
                self.assertAlmostEqual(actual["between_ss"], float(bss), places=10)
                self.assertAlmostEqual(actual["within_ss"], float(wss), places=10)
                self.assertAlmostEqual(actual["icc1"], float(icc), places=12)
                self.assertEqual(actual["group_count"], len(groups))
                self.assertEqual(actual["selected_tokens"], len(groups) * g)

    def test_phase_locked_and_negative_controls(self):
        block = [float((i // 3) % 2) for i in range(probe.BLOCK)]
        aligned = probe.phase_cell([block], 3, 0)
        self.assertEqual(aligned["icc1"], 1)
        self.assertLess(probe.phase_cell([block], 3, 1)["icc1"], 0)
        self.assertLess(probe.phase_cell([block], 3, 2)["icc1"], 0)
        balanced = [float(i % 3) for i in range(probe.BLOCK)]
        for p in range(3):
            self.assertEqual(probe.phase_cell([balanced], 3, p)["icc1"], -0.5)

    def test_six_token_aligned_control(self):
        block = [float((i // 6) % 2) for i in range(probe.BLOCK)]
        self.assertEqual(probe.phase_cell([block], 6, 0)["icc1"], 1)
        for phase in range(1, 6):
            self.assertLess(probe.phase_cell([block], 6, phase)["icc1"], 1)

    def test_nonconstant_shuffles_preserve_each_block(self):
        blocks = [[float((i * 7) % 17) for i in range(probe.BLOCK)],
                  [float(100 + (i * 3) % 13) for i in range(probe.BLOCK)]]
        saved = [list(b) for b in blocks]
        snapshots = []
        original = probe.phase_tables
        def inspect(candidate):
            snapshots.append([list(b) for b in candidate])
            return original(candidate)
        with patch.object(probe, "phase_tables", side_effect=inspect):
            probe.measure(blocks)
        self.assertEqual(blocks, saved)
        self.assertEqual(len(snapshots), probe.REPLICATES + 1)
        self.assertTrue(any(b != saved for b in snapshots[1:]))
        for rep in snapshots[1:]:
            for actual, expected in zip(rep, saved):
                self.assertEqual(sorted(actual), sorted(expected))

    def test_undefined_and_validation(self):
        for blocks in ([], [[4.0] * probe.BLOCK], [[math.log2(3)] * probe.BLOCK]):
            self.assertTrue(all(c["icc1"] is None for c in probe.phase_tables(blocks)))
        with self.assertRaises(ValueError):
            probe.phase_cell([[1]], 3, 0)
        with self.assertRaises(ValueError):
            probe.phase_cell([[math.nan] * probe.BLOCK], 3, 0)
        with self.assertRaises(ValueError):
            probe.phase_cell([], 3, 3)

    def test_translation_and_scale(self):
        original = [[float(i % 17) for i in range(probe.BLOCK)]]
        changed = [[9 + 4 * x for x in original[0]]]
        for a, b in zip(probe.phase_tables(original), probe.phase_tables(changed)):
            self.assertAlmostEqual(a["icc1"], b["icc1"], places=12)
            self.assertAlmostEqual(a["within_ss"] * 16, b["within_ss"], places=9)
            self.assertAlmostEqual(a["between_ss"] * 16, b["between_ss"], places=9)

    def test_omissions_tail_and_proxy(self):
        tokens = [(0, 0)] * (3 * probe.BLOCK + 1)
        tokens[probe.BLOCK] = (17, 0)
        tokens[2 * probe.BLOCK] = (1, 31)
        tokens[-1] = (18, 0)
        blocks, counts = probe.select_blocks(tokens)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[1][0], 6)
        self.assertEqual(counts["escape_omitted_blocks"], 1)
        self.assertEqual(counts["escape_omitted_original_block_indices"], [1])
        self.assertEqual(counts["parsed_escapes"], 2)
        self.assertEqual(counts["tail_escapes"], 1)
        self.assertEqual(counts["tail_tokens"], 1)
        self.assertEqual(counts["retained_tokens"] + counts["escape_omitted_tokens"] + counts["tail_tokens"], len(tokens))

    def test_permutation_determinism_and_preserved_block_drift(self):
        blocks = [[0.0] * probe.BLOCK, [1.0] * probe.BLOCK]
        result = probe.measure(blocks)
        self.assertEqual(result, probe.measure(blocks))
        self.assertTrue(all(c["icc1"] == 1 for c in result["observed"]))
        self.assertTrue(all(c["icc1"] == 1 for rep in result["permutations"] for c in rep))
        self.assertEqual([c["max_minus_min_icc1"] for c in result["phase_spreads"]], [0, 0])

    def call_cli(self, samples, inputs, limit=252):
        original = open
        def read(path, *args, **kwargs):
            if path in inputs:
                return io.BytesIO(inputs[path])
            if path == "missing":
                raise FileNotFoundError("secret local owner path")
            return original(path, *args, **kwargs)
        args = [v for sample in samples for v in ("--sample", *sample)]
        output = io.StringIO()
        with patch("builtins.open", read), patch.object(probe, "LIMIT", limit), contextlib.redirect_stdout(output):
            code = probe.main(args)
        return code, json.loads(output.getvalue())

    def test_real_main_complete_both_byte_orders(self):
        for endian in ("<", ">"):
            code, result = self.call_cli([("1", "public", "input")], {"input": fixture([(0, 0)] * 252, endian)})
            self.assertEqual(code, 0)
            self.assertEqual(result["failures"], [])
            sample = result["samples"][0]
            self.assertTrue(sample["prefix_complete"])
            self.assertEqual(sample["bits_consumed"], 1512)
            self.assertEqual(sample["selection"]["retained_blocks"], 2)

    def test_real_main_short_empty_mixed_and_sanitized(self):
        inputs = {"full": fixture([(0, 0)] * 252), "short": fixture([(0, 0)] * 126),
                  "empty": fixture([]), "truncated": fixture([]) + b"\x01"}
        # Positive payload with a late stop and no complete suffix.
        raw = bytearray(inputs["truncated"])
        struct.pack_into("<I", raw, 66, 1)
        inputs["truncated"] = bytes(raw)
        for bad in ("short", "empty", "truncated", "missing"):
            code, result = self.call_cli([("1", "good", "full"), ("2", "bad", bad)], inputs)
            self.assertEqual(code, 1)
            self.assertEqual(result["samples"][0]["returned_tokens"], 252)
            self.assertEqual(len(result["failures"]), 1)
            self.assertNotIn("secret", json.dumps(result))
            if bad in ("short", "truncated"):
                self.assertFalse(result["samples"][1]["prefix_complete"])
                self.assertEqual(result["failures"][0]["error"], "IncompletePrefix")

    def test_id_validation_precedes_reads(self):
        for sid in ("0", "-1", "x", "\u0661"):
            with patch("builtins.open", side_effect=AssertionError("read before validation")), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    probe.main(["--sample", sid, "public", "input"])
                self.assertEqual(raised.exception.code, 2)
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                probe.main(["--sample", "1", "a", "x", "--sample", "01", "b", "y"])


if __name__ == "__main__":
    unittest.main()
