#!/usr/bin/env python3
"""Unit tests for payload_stride_landscape_probe.py (#296)."""
import array
import collections
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import payload_stride_landscape_probe as P


class TestPayloadStrideLandscapeProbe(unittest.TestCase):
    def test_self_test_runs(self):
        P.self_test()

    def test_constant_tokens_zero_elevation(self):
        q_const = array.array("B", [3] * 1000)
        scores = P.compute_stride_scores_for_band(q_const, s_min=50, s_max=60, head=10, min_rows=5)
        for s, entry in scores.items():
            self.assertEqual(entry["elevation"], 0.0)
            self.assertEqual(entry["z"], 0.0)

    def test_find_band_winner_boundary(self):
        scores = {
            50: {"z": 10.5, "elevation": 2.0, "rows": 20},
            51: {"z": 5.0, "elevation": 1.0, "rows": 20},
            52: {"z": 2.0, "elevation": 0.5, "rows": 20},
        }
        res = P.find_band_winner(scores, s_min=50, s_max=52)
        self.assertEqual(res["best_stride"], 50)
        self.assertTrue(res["range_boundary"])

        scores_mid = {
            50: {"z": 2.0, "elevation": 0.5, "rows": 20},
            51: {"z": 10.5, "elevation": 2.0, "rows": 20},
            52: {"z": 3.0, "elevation": 0.6, "rows": 20},
        }
        res_mid = P.find_band_winner(scores_mid, s_min=50, s_max=52)
        self.assertEqual(res_mid["best_stride"], 51)
        self.assertFalse(res_mid["range_boundary"])

    def test_shuffle_token_blocks_multiset(self):
        rng = random.Random(999)
        tokens = array.array("B", [random.randint(0, 15) for _ in range(500)])
        shuffled = P.shuffle_token_blocks(tokens, block_size=64, rng=rng)
        self.assertEqual(collections.Counter(tokens), collections.Counter(shuffled))
        self.assertNotEqual(tokens.tolist(), shuffled.tolist())

    def test_invalid_parameters_raise(self):
        with self.assertRaises(ValueError):
            P.analyze_landscape(b"\x00" * 100, nominal_w=0)
        with self.assertRaises(ValueError):
            P.analyze_landscape(b"\x00" * 100, nominal_w=50, s_min=60, s_max=50)


if __name__ == "__main__":
    unittest.main()
