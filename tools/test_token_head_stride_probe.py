#!/usr/bin/env python3
"""Synthetic head/stride and globally disjoint split checks; no sample data."""
import contextlib
import io
import json
import math
import os
import struct
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_head_stride_probe as P


class Tests(unittest.TestCase):
    def test_public_identity_before_measurement(self):
        def args(pairs):
            return sum((["--sample", sid, name, "0" * 64, "5", "unused"] for sid, name in pairs), []) + ["--radius", "0", "--head", "1"]
        for pairs in ([('1', 'ok'), ('01', 'ok')], [('0', 'ok')], [('\u0661', 'ok')],
                      [('-1', 'ok')], [('1', 'ok'), ('2', '')],
                      [('1', 'ok'), ('2', 'private/name')], [('1', 'ok'), ('2', 'private\\name')],
                      [('1', 'ok'), ('2', 'private\nname')]):
            with self.subTest(pairs=pairs):
                output, error = io.StringIO(), io.StringIO()
                with mock.patch.object(P, 'measure') as measure, contextlib.redirect_stdout(output), \
                        contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    P.main(args(pairs))
                self.assertEqual(raised.exception.code, 2)
                measure.assert_not_called()
                self.assertEqual(output.getvalue(), '')
                self.assertNotIn('private', error.getvalue())
        with mock.patch.object(P, 'int', side_effect=ValueError('private detail'), create=True), \
                mock.patch.object(P, 'measure') as measure, contextlib.redirect_stderr(io.StringIO()) as error, \
                self.assertRaises(SystemExit) as raised:
            P.main(args([('1', 'ok')]))
        self.assertEqual(raised.exception.code, 2)
        self.assertNotIn('private detail', error.getvalue())
        measure.assert_not_called()
        output = io.StringIO()
        with mock.patch.object(P, 'measure', return_value={'complete': True, 'token_shortfall': 0}), \
                contextlib.redirect_stdout(output):
            self.assertEqual(P.main(args([('01', 'Camera "é" (4:3), +.ORF')])), 0)
        self.assertEqual((json.loads(output.getvalue())['samples'][0]['pixls_id'],
                          json.loads(output.getvalue())['samples'][0]['pixls_name']),
                         ('01', 'Camera "é" (4:3), +.ORF'))

    def test_every_cell_and_brute_force(self):
        qs = P.B.array.array("B", [(i*7+i//3)%41 for i in range(300)])
        report = P.diagnostic(qs, [7, 9, 8], [1, 3], 5)
        self.assertEqual(len(report["cells"]), 6)
        self.assertEqual(report["training_latest_end_token_exclusive"], 45)
        self.assertEqual(report["test_start_candidate_row"], 7)
        self.assertEqual(report["test_earliest_start_token"], 49)
        for cell in report["cells"]:
            stride, head = cell["stride"], cell["head"]
            for split, first in [("train", 0), ("test", 7)]:
                expected = []
                for row in range(first, first+5):
                    values = list(qs[row*stride:(row+1)*stride])
                    expected.append(sum(values[:head])/head-sum(values[head:])/(stride-head))
                mean = sum(expected)/5
                var = sum((x-mean)**2 for x in expected)/4
                exact = [sum(qs[r*stride:r*stride+head])*(stride-head)-sum(qs[r*stride+head:(r+1)*stride])*head for r in range(first, first+5)]
                self.assertEqual(cell[split]["sum_contrast_numerator"], sum(exact))
                self.assertEqual(cell[split]["sum_squared_contrast_numerator"], sum(x*x for x in exact))
                self.assertEqual(cell[split]["sum_head_q_capped40"], sum(qs[r*stride+j] for r in range(first, first+5) for j in range(head)))
                self.assertEqual(cell[split]["sum_rest_q_capped40"], sum(qs[r*stride+j] for r in range(first, first+5) for j in range(head,stride)))
                self.assertAlmostEqual(cell[split]["mean_head_minus_rest"], mean)
                self.assertAlmostEqual(cell[split]["signed_mean_over_se"], mean/math.sqrt(var/5))
        for selection in report["selections"]:
            cells = [c for c in report["cells"] if c["head"] == selection["head"]]
            best = sorted(cells, key=lambda c: (-c["train"]["signed_mean_over_se"], c["stride"]))[0]
            self.assertEqual(selection["selected_stride"], best["stride"])
            self.assertEqual(selection["selected_test"], best["test"])

    def test_ties_signed_and_test_never_selects(self):
        def fake(qs, stride, start, rows, head):
            return dict(complete=True, score_defined=True,
                        signed_mean_over_se=(-2 if start == 0 else stride))
        with mock.patch.object(P.B, "profile", side_effect=fake):
            out = P.diagnostic([], [9, 7, 8], [1], 5)
        pick = out["selections"][0]
        self.assertEqual(pick["selected_stride"], 7)
        self.assertEqual(pick["tied_strides"], [7, 8, 9])
        self.assertEqual(pick["selected_test"]["signed_mean_over_se"], 7)

    def test_global_nonoverlap_and_shortfall(self):
        for strides in ([3, 100], [5224, 5256], [5456, 5488]):
            out = P.diagnostic(P.B.array.array("B"), strides, [1], 150)
            self.assertGreaterEqual(out["test_earliest_start_token"], out["training_latest_end_token_exclusive"])
            self.assertFalse(out["complete"])
            self.assertIsNone(out["selections"][0]["selected_stride"])
        # Constant nonzero contrasts have undefined SE and cannot win.
        out = P.diagnostic(P.B.array.array("B", [1, 0]*20), [2], [1], 5)
        self.assertTrue(out["complete"])
        self.assertIsNone(out["selections"][0]["selected_stride"])

    def test_cli_failure_retention_and_incomplete_exit(self):
        sink = io.StringIO()
        args = ["--sample", "1", "public one", "0"*64, "5", "missing-private-path", "--radius", "0", "--head", "1"]
        with contextlib.redirect_stdout(sink):
            code = P.main(args)
        self.assertEqual(code, 1)
        self.assertNotIn("missing-private-path", sink.getvalue())
        self.assertEqual(json.loads(sink.getvalue())["samples"][0]["error"], "FileNotFoundError")
        sink = io.StringIO()
        with mock.patch.object(P, "measure", return_value=dict(complete=False, token_shortfall=1)), contextlib.redirect_stdout(sink):
            self.assertEqual(P.main(args), 1)
        self.assertFalse(json.loads(sink.getvalue())["samples"][0]["ok"])

    def test_actual_measure_main_complete_shortfall_and_hash_gate(self):
        def sample(count):
            bits = "".join("0"*(i%4)+"100000" for i in range(count))
            bits += "0"*(-len(bits)%8)
            payload = bytes(int(bits[i:i+8], 2) for i in range(0,len(bits),8))
            entries = [(256,5), (257,5), (259,1), (273,74), (279,len(payload))]
            header = struct.pack("<2sHIH", b"II", 0x5352, 8, len(entries))
            tags = b"".join(struct.pack("<HHII", tag, 4, 1, value) for tag,value in entries)
            return header + tags + struct.pack("<I",0) + payload
        full, short = sample(40), sample(12)
        blobs = {"full":full, "short":short}
        def opening(path, mode):
            self.assertEqual(mode,"rb")
            return io.BytesIO(blobs[path])
        args = []
        for sid, name in [("1","full"),("2","short")]:
            args += ["--sample",sid,"public "+name,P.hashlib.sha256(blobs[name]).hexdigest(),"4",name]
        args += ["--rows","2","--head","1","--radius","1"]
        sink = io.StringIO()
        with mock.patch("builtins.open",side_effect=opening), contextlib.redirect_stdout(sink):
            self.assertEqual(P.main(args),1)
        full_result, short_result = json.loads(sink.getvalue())["samples"]
        self.assertTrue(full_result["ok"])
        self.assertEqual(full_result["parsed_tokens"],30)
        self.assertEqual(full_result["token_shortfall"],0)
        self.assertFalse(short_result["ok"])
        self.assertEqual(short_result["parsed_tokens"],12)
        self.assertEqual(short_result["token_shortfall"],18)
        self.assertTrue(all(c["train"]["complete"] for c in short_result["cells"]))
        self.assertTrue(all(not c["test"]["complete"] for c in short_result["cells"]))
        with mock.patch("builtins.open",return_value=io.BytesIO(full)), mock.patch.object(P.B,"Tiff",side_effect=AssertionError("must not parse")):
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                P.measure("unused","0"*64,4,1,[1],2)

    def test_geometry_and_duplicate_ids(self):
        for strides, heads, rows in [([], [1], 3), ([2], [2], 3), ([2], [0], 3), ([2], [1], 1)]:
            with self.assertRaises(ValueError):
                P.diagnostic([], strides, heads, rows)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            P.main(["--sample", "1", "name", "0"*64, "5", "unused"]*2)
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
