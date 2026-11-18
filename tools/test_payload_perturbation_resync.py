#!/usr/bin/env python3
"""Unit tests for payload_perturbation_resync.py (#300)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import payload_perturbation_resync as P


class TestPayloadPerturbationResync(unittest.TestCase):
    def test_self_test_runs(self):
        P.self_test()

    def test_forward_coord(self):
        self.assertEqual(P.forward_coord(100, 50, "flip"), 100)
        self.assertEqual(P.forward_coord(100, 50, "insert"), 101)
        self.assertEqual(P.forward_coord(100, 50, "delete"), 99)
        with self.assertRaises(ValueError):
            P.forward_coord(50, 50, "flip")

    def test_perturb_bits(self):
        bits = "00101100"
        self.assertEqual(P.perturb_bits(bits, 2, "flip"), "00001100")
        self.assertEqual(P.perturb_bits(bits, 2, "delete"), "0001100")
        self.assertEqual(P.perturb_bits(bits, 2, "insert"), "000101100")

    def test_parse_tokens_fixed5(self):
        bits = "0000100010"
        tokens, tail = P.parse_tokens(bits, grammar="fixed5")
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0], (0, 5, 0, 1, False))
        self.assertEqual(tokens[1], (5, 10, 0, 2, False))
        self.assertEqual(tail, 0)

    def test_parse_tokens_rice5(self):
        # q=0: '1' + 5 bits '00011' -> value 3
        # q=2: '001' + 5 bits '00001' -> value (2<<5) | 1 = 65
        bits = "100011" + "00100001"
        tokens, tail = P.parse_tokens(bits, grammar="orf_rice5")
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0], (0, 6, 0, 3, False))
        self.assertEqual(tokens[1], (6, 14, 2, 65, False))
        self.assertEqual(tail, 0)


if __name__ == "__main__":
    unittest.main()
