"""Synthetic checks for local candidate suffix-balance windows."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_balance_windows as probe
from suffix_joint_probe import scan_prefix


class BalanceWindows(unittest.TestCase):
    def test_uniform_and_escape_index(self):
        tokens = [(0, s) for s in range(32)] + [(17, 31), (0, 0)]
        result = probe.measure(tokens, 0, 33)
        self.assertEqual(result["joint_h_rows_l_columns"], [[1] * 8 for _ in range(4)])
        self.assertEqual(result["escape_tokens"], 1)
        self.assertEqual(result["one_counts"], {"b0": 16, "b1": 16})
        self.assertEqual(result["one_proportions_exact"], {"b0": "1/2", "b1": "1/2"})
        self.assertEqual(result["plugin_mi_bits"], 0.0)
        self.assertTrue(result["tolerance_pass"])
        self.assertEqual(probe.measure(tokens, 33, 1)["retained_tokens"], 1)

    def test_known_dependence_and_boundaries(self):
        result = probe.measure([(0, 0)] * 10 + [(0, 15)] * 10, 0, 20)
        self.assertTrue(math.isclose(result["plugin_mi_bits"], 1.0))
        self.assertFalse(result["tolerance_pass"])
        at_limit = probe.measure([(0, 0)] * 9 + [(0, 3)] * 11, 0, 20)
        self.assertEqual(at_limit["one_proportions_exact"]["b0"], "11/20")
        self.assertTrue(at_limit["tolerance_pass"])
        self.assertFalse(probe.measure([(0, 0)] * 8 + [(0, 3)] * 12, 0, 20)["tolerance_pass"])

    def test_empty_short_and_design(self):
        for result in (probe.measure([(17, 0)], 0, 1), probe.measure([(0, 0)], 0, 2)):
            self.assertIsNone(result["tolerance_pass"])
            self.assertIsNone(result["plugin_mi_bits"])
            self.assertEqual(result["one_proportions_exact"], {"b0": None, "b1": None})
        self.assertEqual(probe.windows("discovery")[-1], (3 * probe.WINDOW, probe.WINDOW))
        self.assertEqual(probe.windows("verification")[-1], (4 * probe.WINDOW, 2 * probe.WINDOW))

    def test_synthetic_bitstream(self):
        values = [(0, 3), (17, 29), (2, 10)]
        bits = "".join("0" * q + "1" + format(s, "05b") for q, s in values)
        payload = int(bits + "0" * (-len(bits) % 8), 2).to_bytes((len(bits) + 7) // 8, "big")
        parsed, end = scan_prefix(payload, len(values))
        self.assertEqual((parsed, end), (values, len(bits)))
        result = probe.measure(parsed, 1, 2)
        self.assertEqual((result["escape_tokens"], result["retained_tokens"]), (1, 1))
        self.assertEqual(result["joint_h_rows_l_columns"][1][2], 1)


if __name__ == "__main__":
    unittest.main()
