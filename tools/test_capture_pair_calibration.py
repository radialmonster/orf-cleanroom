"""Synthetic tests for capture_pair_calibration; no camera files."""
import io
import hashlib
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_pair_calibration as c


def m(name, dto, hires=False):
    return {"base": c.base_name(name), "ori": name.lower().endswith(".ori"), "hires": hires,
            "dto": dto, "time": datetime.strptime(dto, "%Y:%m:%d %H:%M:%S")}


def h(letter):
    return letter * 64


class Tests(unittest.TestCase):
    def test_base_name(self):
        self.assertEqual(c.base_name("dir/P1012824_01.ORF"), "P1012824_01")
        self.assertEqual(c.base_name("P1012824.ORI"), "P1012824")

    def test_numbered_stems_do_not_alias(self):
        dto = "2025:01:01 10:00:00"
        high = m("IMG_0001.ORF", dto, hires=True)
        self.assertEqual(c.classify(high, m("IMG_0002.ORI", dto), 600), "B")
        self.assertEqual(c.classify(high, m("IMG_0001.ORI", dto), 600), "P")
        self.assertEqual(c.classify(m("IMG_0001_01.ORF", dto, hires=True),
                                    m("IMG_0001.ORI", dto), 600), "B")

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
            h("a"): m("P1.ORF", "2025:01:01 10:00:00", hires=True),
            h("b"): m("P1.ORI", "2025:01:01 10:00:00"),
            h("c"): m("P2.ORF", "2025:01:01 10:05:00"),
            h("d"): m("P3.ORF", "2025:01:02 10:00:00"),
        }
        recs = [{"pair": [h("a"), h("b")], "r": 0.999}, {"pair": [h("a"), h("c")], "r": 0.5},
                {"pair": [h("b"), h("c")], "r": 0.4}, {"pair": [h("a"), h("d")], "r": 0.1},
                {"pair": [h("b"), h("d")], "r": None}, {"pair": [h("c"), h("d")], "r": 0.0}]
        days, split_of, scores, excluded = c.analyse(recs, meta, 600)
        self.assertEqual(split_of, {"2025:01:01": "cal", "2025:01:02": "val"})
        self.assertEqual(scores[("cal", "P")], [0.999])
        self.assertEqual(sorted(scores[("cal", "H")]), [0.4, 0.5])
        self.assertEqual(sorted(scores[("all", "E")]), [0.0, 0.1])
        self.assertNotIn(("val", "E"), scores)
        self.assertEqual(excluded, {"E": 1})
        out = io.StringIO()
        c.report(days, split_of, scores, excluded, 0.98, out=out)
        self.assertIn("calibration: unsupported", out.getvalue())

    def test_invalid_dates_are_missing_metadata(self):
        for dto in ("0000:00:00 00:00:00", "2025:02:30 10:00:00", "bad", "2025:1:01 10:00:00"):
            with self.subTest(dto=dto), patch("builtins.open", return_value=io.BytesIO(b"file")), \
                    patch.object(c, "date_time_original", return_value=dto), \
                    patch.object(c, "signature", return_value={"payload_w": 5000, "sha256": hashlib.sha256(b"file").hexdigest()}):
                _, result = c.file_meta("sample.ORF")
                self.assertIsNone(result["dto"])
                self.assertIsNone(result["time"])
                good = m("P2.ORF", "2025:01:01 10:00:00")
                _, _, scores, excluded = c.analyse([{"pair": [h("e"), h("f")], "r": 0.9}],
                                                    {h("e"): result, h("f"): good}, 600)
                self.assertEqual(scores, {})
                self.assertEqual(excluded, {"no_metadata": 1})
        with patch("builtins.open", return_value=io.BytesIO(b"file")), \
                patch.object(c, "date_time_original", return_value="2025:01:01 10:00:00"), \
                patch.object(c, "signature", return_value={"payload_w": 5000, "sha256": hashlib.sha256(b"file").hexdigest()}):
            _, result = c.file_meta("sample.ORF")
            self.assertEqual(result["dto"], "2025:01:01 10:00:00")
            self.assertEqual(result["time"], datetime(2025, 1, 1, 10))

    def test_changed_file_cannot_relabel_original_snapshot(self):
        with patch("builtins.open", return_value=io.BytesIO(b"original")), \
                patch.object(c, "date_time_original", return_value="2025:01:01 10:00:00"), \
                patch.object(c, "signature", return_value={"payload_w": 8000,
                    "sha256": hashlib.sha256(b"changed").hexdigest()}):
            with self.assertRaisesRegex(ValueError, "changed"):
                c.file_meta("P1.ORF")

    def test_screen_rejects_duplicate_self_and_malformed_pairs(self):
        a, b = h("a"), h("b")
        single = {"pair": [a, b], "r": 0.5}
        for pair in ([a, b], [b, a]):
            for value in (0.5, 0.6, None):
                with self.subTest(pair=pair, value=value):
                    with self.assertRaisesRegex(ValueError, "duplicate"):
                        c.analyse([single, {"pair": pair, "r": value}], {}, 600)
        for pair in ([a, a], [a], [a, b, h("c")], "bad", [a, None], [a, "bad"]):
            with self.subTest(pair=pair):
                with self.assertRaises(ValueError):
                    c.analyse([{"pair": pair, "r": 0.5}], {}, 600)

    def test_invalid_screen_fails_before_report(self):
        records = [{"pair": [h("a"), h("b")], "r": 0.5}] * 2
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(c, "load_screen", return_value=records), \
                patch("sys.stdout", stdout), patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit) as raised:
                c.main(["--screen", "synthetic"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("duplicate unordered pair", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")

    def test_duplicate_screen_keys_rejected_in_both_encodings(self):
        a, b, d = h("a"), h("b"), h("d")
        pair = '["%s","%s"]' % (a, b)
        other = '["%s","%s"]' % (a, d)
        for line in ('{"pair":%s,"pair":%s,"r":0.5}' % (pair, other),
                     '{"pair":%s,"r":2,"r":0.5}' % pair):
            for encoding in ("utf-8", "utf-16"):
                with self.subTest(line=line, encoding=encoding):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with patch("builtins.open", return_value=io.BytesIO(line.encode(encoding))), \
                            patch("sys.stdout", stdout), patch("sys.stderr", stderr), \
                            patch.object(c, "report") as report:
                        with self.assertRaises(SystemExit) as raised:
                            c.main(["--screen", "private-screen"])
                    self.assertEqual(raised.exception.code, 2)
                    report.assert_not_called()
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertNotIn("private-screen", stderr.getvalue())

    def test_normal_screen_json_encodings(self):
        text = '{"summary":{"samples":2}}\n{"pair":["%s","%s"],"r":0.5}\n' % (h("a"), h("b"))
        for encoding in ("utf-8", "utf-16"):
            with self.subTest(encoding=encoding), \
                    patch("builtins.open", return_value=io.BytesIO(text.encode(encoding))):
                self.assertEqual(c.load_screen("synthetic"), [{"summary": {"samples": 2}},
                                                              {"pair": [h("a"), h("b")], "r": 0.5}])

    def test_nonobject_screen_lines_fail_before_report(self):
        for line in ("null", "2", "[]", '"text"'):
            with self.subTest(line=line), \
                    patch("builtins.open", return_value=io.BytesIO(line.encode("utf-8"))), \
                    patch.object(c, "report") as report, \
                    patch("sys.stdout", io.StringIO()), patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    c.main(["--screen", "synthetic"])
                self.assertEqual(raised.exception.code, 2)
                report.assert_not_called()

    def test_repeated_pairs_cannot_claim_support(self):
        a, b, d = h("a"), h("b"), h("d")
        meta = {a: m("P1.ORF", "2025:01:01 10:00:00", hires=True),
                b: m("P1.ORI", "2025:01:01 10:00:00"),
                d: m("P2.ORF", "2025:01:01 10:05:00")}
        records = [{"pair": [a, b], "r": 0.99}] * 10 + [{"pair": [a, d], "r": 0.2}] * 10
        with self.assertRaisesRegex(ValueError, "duplicate"):
            c.analyse(records, meta, 600)

    def test_screen_rejects_invalid_correlations_even_without_metadata(self):
        for value in (float("nan"), float("inf"), -float("inf"), -1.01, 1.01, "0.5", True):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "correlation"):
                    c.analyse([{"pair": [h("a"), h("b")], "r": value}], {}, 600)
        with self.assertRaisesRegex(ValueError, "correlation"):
            c.analyse([{"pair": [h("a"), h("b")]}], {}, 600)
        for value in (-1.0, 0.0, 1.0, None):
            with self.subTest(value=value):
                self.assertEqual(c.analyse([{"pair": [h("a"), h("b")], "r": value}], {}, 600)[3],
                                 {"no_metadata": 1})

    def test_calibration_support_and_auc_counts(self):
        scores = {(split, kind): values for split in ("cal", "val")
                  for kind, values in (("P", [0.9] * 10), ("H", [0.1] * 10), ("E", [0.2] * 3))}
        out = io.StringIO()
        c.report([], {}, scores, {}, 0.5, out=out)
        text = out.getvalue()
        self.assertIn("AUC P (n=10) vs H (n=10) 1.0000, P (n=10) vs E (n=3) 1.0000", text)
        self.assertIn("calibrated t* 0.900000000", text)
        self.assertIn("validation: supported", text)
        self.assertIn("H 0/10", text)
        self.assertIn("scene unknown", text)

    def test_small_cal_or_validation_class_is_unsupported(self):
        for split in ("cal", "val"):
            for kind in ("P", "H"):
                scores = {(s, k): [0.9 if k == "P" else 0.1] * 10
                          for s in ("cal", "val") for k in ("P", "H")}
                scores[(split, kind)].pop()
                out = io.StringIO()
                c.report([], {}, scores, {}, 0.5, out=out)
                self.assertIn(("calibration" if split == "cal" else "validation") + ": unsupported", out.getvalue())
                if split == "cal":
                    self.assertNotIn("calibrated t*", out.getvalue())


if __name__ == "__main__":
    unittest.main()
