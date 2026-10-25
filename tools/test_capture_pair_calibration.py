"""Synthetic tests for capture_pair_calibration; no camera files."""
import io
import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_pair_calibration as c


def m(name, dto, hires=False):
    return {"base": c.base_name(name), "ori": name.lower().endswith(".ori"), "hires": hires,
            "dto": dto, "time": datetime.strptime(dto, "%Y:%m:%d %H:%M:%S")}


class Tests(unittest.TestCase):
    def test_base_name(self):
        self.assertEqual(c.base_name("dir/P1012824_01.ORF"), "P1012824")
        self.assertEqual(c.base_name("P1012824.ORI"), "P1012824")

    def test_classes(self):
        hr = m("P1.ORF", "2025:01:01 10:00:00", hires=True)
        ori = m("P1.ORI", "2025:01:01 10:00:00")
        burst = m("P2.ORF", "2025:01:01 10:00:00")
        near = m("P3.ORF", "2025:01:01 10:10:00")
        far = m("P4.ORF", "2025:01:01 10:10:01")
        other = m("P5.ORF", "2025:01:02 10:00:00")
        self.assertEqual(c.classify(hr, ori, 600), "P")
        self.assertEqual(c.classify(ori, hr, 600), "P")
        self.assertEqual(c.classify(burst, ori, 600), "B")
        self.assertEqual(c.classify(hr, near, 600), "H")
        self.assertEqual(c.classify(hr, far, 600), "S")
        self.assertEqual(c.classify(hr, other, 600), "E")
        # Same name and second but no High Res member is not a companion.
        self.assertEqual(c.classify(m("P1.ORF", ori["dto"]), ori, 600), "B")

    def test_auc(self):
        self.assertEqual(c.auc([3, 4], [1, 2]), 1.0)
        self.assertEqual(c.auc([1], [1]), 0.5)
        self.assertEqual(c.auc([1, 2], [3, 4]), 0.0)
        self.assertAlmostEqual(c.auc([2, 4], [1, 3]), 0.75)
        self.assertIsNone(c.auc([], [1]))

    def test_calibrate_prefers_highest_on_ties(self):
        j, th = c.calibrate([0.9, 0.95], [0.1, 0.2])
        self.assertEqual((j, th), (1.0, 0.9))

    def test_split_and_report(self):
        meta = {
            "a": m("P1.ORF", "2025:01:01 10:00:00", hires=True),
            "b": m("P1.ORI", "2025:01:01 10:00:00"),
            "c": m("P2.ORF", "2025:01:01 10:05:00"),
            "d": m("P3.ORF", "2025:01:02 10:00:00"),
        }
        recs = [{"pair": ["a", "b"], "r": 0.999}, {"pair": ["a", "c"], "r": 0.5},
                {"pair": ["b", "c"], "r": 0.4}, {"pair": ["a", "d"], "r": 0.1},
                {"pair": ["b", "d"], "r": None}, {"pair": ["c", "d"], "r": 0.0}]
        days, split_of, scores, excluded = c.analyse(recs, meta, 600)
        self.assertEqual(split_of, {"2025:01:01": "cal", "2025:01:02": "val"})
        self.assertEqual(scores[("cal", "P")], [0.999])
        self.assertEqual(sorted(scores[("cal", "H")]), [0.4, 0.5])
        self.assertEqual(sorted(scores[("all", "E")]), [0.0, 0.1])
        self.assertNotIn(("val", "E"), scores)
        self.assertEqual(excluded, {"E": 1})
        out = io.StringIO()
        c.report(days, split_of, scores, excluded, 0.98, out=out)
        self.assertIn("calibrated t* 0.999000000", out.getvalue())


if __name__ == "__main__":
    unittest.main()
