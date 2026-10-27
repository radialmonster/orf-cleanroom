"""Synthetic geometry/arithmetic controls for preview_pair_screen; no images."""
import io
import contextlib
import json
import math
import os
import runpy
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_pair_screen as p


def reference(a, b):
    # Independent unnormalized Pearson formula on original synthetic values.
    n = len(a)
    numerator = n * sum(x * y for x, y in zip(a, b)) - sum(a) * sum(b)
    denominator = math.sqrt((n * sum(x * x for x in a) - sum(a) ** 2) *
                            (n * sum(y * y for y in b) - sum(b) ** 2))
    return numerator / denominator


class ScreenTests(unittest.TestCase):
    def test_all_unreadable_reports_empty_summary_and_private_safe_error(self):
        out, err = io.StringIO(), io.StringIO()
        with patch('builtins.open', side_effect=FileNotFoundError('private path')), \
                patch.object(sys, 'argv', ['preview_pair_screen', 'private-one.ORF', 'private-two.ORF']), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(p.main(), 1)
        lines = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(len(lines), 1)
        self.assertEqual((lines[0]['summary']['samples'], lines[0]['summary']['pairs']), (0, 0))
        self.assertEqual(err.getvalue().splitlines(), ['input 1: FileNotFoundError', 'input 2: FileNotFoundError'])
        self.assertNotIn('private', out.getvalue() + err.getvalue())

    def test_valid_sample_cli_succeeds(self):
        out = io.StringIO()
        with patch('builtins.open', return_value=io.BytesIO(b'synthetic')), \
                patch.object(p.jpeg_dc, 'find_preview', return_value=(9216, 0, 1, 96, 96)), \
                patch.object(p.jpeg_dc, 'decode', return_value=(12, 12, list(range(144)))), \
                patch.object(sys, 'argv', ['preview_pair_screen', 'valid.ORF']), \
                contextlib.redirect_stdout(out):
            self.assertEqual(p.main(), 0)
        lines = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(lines[0]['sample']['status'], 'ok')
        self.assertEqual(lines[-1]['summary']['samples'], 1)

    def test_cli_reports_unreadable_and_unsupported_but_keeps_valid(self):
        inputs = {'bad.ORF': b'bad', 'good.ORF': b'good'}
        def opening(path, mode):
            if path not in inputs:
                raise FileNotFoundError('private path')
            return io.BytesIO(inputs[path])
        def preview(data):
            return None if data == b'bad' else (9216, 0, 1, 96, 96)
        out, err = io.StringIO(), io.StringIO()
        args = ['preview_pair_screen', 'missing.ORF', 'bad.ORF', 'good.ORF']
        with patch('builtins.open', side_effect=opening), \
                patch.object(p.jpeg_dc, 'find_preview', side_effect=preview), \
                patch.object(p.jpeg_dc, 'decode', return_value=(12, 12, list(range(144)))), \
                patch.object(sys, 'argv', args), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(p.main(), 1)
        lines = [json.loads(line) for line in out.getvalue().splitlines()]
        samples = {line['sample']['name']: line['sample']['status'] for line in lines if 'sample' in line}
        self.assertEqual(samples, {'bad.ORF': 'unsupported', 'good.ORF': 'ok'})
        self.assertEqual(lines[-1]['summary']['samples'], 2)
        self.assertIn('input 1: FileNotFoundError', err.getvalue())
        self.assertNotIn('private path', err.getvalue())

    def test_all_unsupported_is_failure_and_low_information_is_not(self):
        for preview, dc, expected in ((None, [], 1), ((9216, 0, 1, 96, 96), [0] * 144, 0)):
            out = io.StringIO()
            with self.subTest(expected=expected), patch('builtins.open', return_value=io.BytesIO(b'synthetic')), \
                    patch.object(p.jpeg_dc, 'find_preview', return_value=preview), \
                    patch.object(p.jpeg_dc, 'decode', return_value=(12, 12, dc)), \
                    patch.object(sys, 'argv', ['preview_pair_screen', 'sample.ORF']), \
                    contextlib.redirect_stdout(out):
                self.assertEqual(p.main(), expected)
            self.assertEqual(json.loads(out.getvalue().splitlines()[0])['sample']['status'],
                             'unsupported' if expected else 'low_information')

    def test_entrypoint_returns_failure_status(self):
        script = os.path.join(os.path.dirname(__file__), 'preview_pair_screen.py')
        with patch.object(sys, 'argv', [script, 'missing.ORF']), \
                patch('builtins.open', side_effect=FileNotFoundError('private path')), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                runpy.run_path(script, run_name='__main__')
        self.assertEqual(raised.exception.code, 1)

    def test_entrypoint_status_for_supported_and_unsupported(self):
        script = os.path.join(os.path.dirname(__file__), 'preview_pair_screen.py')
        for preview, dc, expected in ((None, [], 1),
                ((9216, 0, 1, 96, 96), list(range(144)), 0),
                ((9216, 0, 1, 96, 96), [0] * 144, 0)):
            with self.subTest(expected=expected, dc=dc[:2]), \
                    patch.object(sys, 'argv', [script, 'sample.ORF']), \
                    patch('builtins.open', return_value=io.BytesIO(b'synthetic')), \
                    patch.object(p.jpeg_dc, 'find_preview', return_value=preview), \
                    patch.object(p.jpeg_dc, 'decode', return_value=(12, 12, dc)), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    runpy.run_path(script, run_name='__main__')
                self.assertEqual(raised.exception.code, expected)

    def test_direct_measure_still_raises_for_unreadable_file(self):
        with patch('builtins.open', side_effect=FileNotFoundError('private path')):
            with self.assertRaises(FileNotFoundError):
                p.measure(['missing.ORF'])

    def test_bad_jpeg_sampling_does_not_abort_remaining_files(self):
        scan = b"\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x3f\x00"
        dc = list(range(144))
        original_decode = p.jpeg_dc.decode
        for sampling in (0x01, 0x10):
            frame = (b"\xff\xc0\x00\x11\x08\x00\x60\x00\x60\x03" +
                     bytes([1, sampling, 0, 2, sampling, 0, 3, sampling, 0]))
            inputs = {"bad.ORF": b"\xff\xd8" + frame + scan, "good.ORF": b"good synthetic input"}
            def decode(data, offset):
                return original_decode(data, offset) if data == inputs["bad.ORF"] else (12, 12, dc)
            with self.subTest(sampling=sampling), \
                    patch("builtins.open", side_effect=lambda path, mode: io.BytesIO(inputs[path])), \
                    patch.object(p.jpeg_dc, "find_preview", return_value=(9216, 0, 1, 96, 96)), \
                    patch.object(p.jpeg_dc, "decode", side_effect=decode):
                rows = p.measure(["bad.ORF", "good.ORF"])
                by_name = {record["name"]: (record, fp) for record, fp in rows}
                self.assertEqual((by_name["bad.ORF"][0]["status"], by_name["bad.ORF"][0]["error"]),
                                 ("unsupported", "ZeroDivisionError"))
                self.assertIsNone(by_name["bad.ORF"][1])
                self.assertEqual(by_name["good.ORF"][0]["status"], "ok")
                self.assertIsNotNone(by_name["good.ORF"][1])

    def test_malformed_scan_does_not_abort_remaining_files(self):
        # A SOF component absent from SOS raises StopIteration in jpeg_dc.decode
        # (reported in #347). Keep this per-file failure out of pair scores.
        inputs = {"bad.ORF": b"bad synthetic input", "good.ORF": b"good synthetic input"}
        dc = list(range(144))
        with patch("builtins.open", side_effect=lambda path, mode: io.BytesIO(inputs[path])), \
                patch.object(p.jpeg_dc, "find_preview", return_value=(9216, 0, 1, 96, 96)), \
                patch.object(p.jpeg_dc, "decode", side_effect=[StopIteration(), (12, 12, dc)]):
            rows = p.measure(["bad.ORF", "good.ORF"])
        by_name = {record["name"]: (record, fp) for record, fp in rows}
        bad, bad_fp = by_name["bad.ORF"]
        good, good_fp = by_name["good.ORF"]
        self.assertEqual((bad["status"], bad["error"], bad_fp),
                         ("unsupported", "StopIteration", None))
        self.assertEqual(good["status"], "ok")
        self.assertIsNotNone(good_fp)

    def test_affine_and_inverse(self):
        a = [((i * 37) % 151) - 75 for i in range(144)]
        fa, _ = p.fingerprint(12, 12, a, 96, 96)
        for b, expected in [([3*x + 100 for x in a], 1), ([-x for x in a], -1)]:
            fb, _ = p.fingerprint(12, 12, b, 96, 96)
            self.assertAlmostEqual(p.correlation(fa, fb), expected, places=13)
            self.assertAlmostEqual(p.correlation(fa, fb), reference(a, b), places=13)

    def test_independent_structure(self):
        # Orthogonal horizontal and vertical ramps are unrelated controls,
        # not sampled pictures or a claim about unrelated public captures.
        a = [x * 10 for y in range(12) for x in range(12)]
        b = [y * 10 for y in range(12) for x in range(12)]
        fa, _ = p.fingerprint(12, 12, a, 96, 96)
        fb, _ = p.fingerprint(12, 12, b, 96, 96)
        self.assertAlmostEqual(p.correlation(fa, fb), 0, places=13)
        self.assertAlmostEqual(p.correlation(fa, fb), reference(a, b), places=13)

    def test_flat_rejection(self):
        self.assertEqual(p.fingerprint(12, 12, [999]*144, 96, 96), (None, 0.0))
        self.assertIsNone(p.fingerprint(12, 12, [i % 2 for i in range(144)], 96, 96)[0])

    def test_partial_blocks_excluded(self):
        a = [x + 12*y for y in range(12) for x in range(12)]
        padded = []
        for y in range(13):
            padded.extend(a[y*12:(y+1)*12] + [999999] if y < 12 else [999999]*13)
        fa, sa = p.fingerprint(12, 12, a, 96, 96)
        fb, sb = p.fingerprint(13, 13, padded, 103, 103)
        self.assertEqual((fa, sa), (fb, sb))

    def test_disjoint_bin_means(self):
        # 24x24 replicates each 12x12 grid cell as a constant 2x2 tile.
        a = [i for i in range(144)]
        b = [a[(y//2)*12 + x//2] for y in range(24) for x in range(24)]
        self.assertEqual(p.fingerprint(12, 12, a, 96, 96),
                         p.fingerprint(24, 24, b, 192, 192))

    def test_invalid_geometry(self):
        with self.assertRaises(ValueError):
            p.fingerprint(12, 12, [], 96, 96)
        with self.assertRaises(ValueError):
            p.fingerprint(11, 12, [0]*132, 88, 96)


if __name__ == "__main__":
    unittest.main()
