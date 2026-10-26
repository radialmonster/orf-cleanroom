"""Synthetic checks for active-area CLI result completeness (lead #11)."""
import contextlib
import io
import os
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_active_area as a


def synthetic_tiff():
    data = b"II" + struct.pack("<HIH", 42, 8, 2)
    for tag, value in ((0x100, 10), (0x101, 8)):
        data += struct.pack("<HHII", tag, 4, 1, value)
    return data + struct.pack("<I", 0)


class MainTests(unittest.TestCase):
    def test_success(self):
        with patch("builtins.open", return_value=io.BytesIO(synthetic_tiff())):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(a.main(["good.ORF"]), 0)
        self.assertIn("payload 10x8", output.getvalue())

    def test_mixed_success_failure_retains_output_and_failure_status(self):
        def open_input(path, mode):
            if path == "missing.ORF":
                raise FileNotFoundError("missing fixture")
            return io.BytesIO(b"bad" if path == "bad.ORF" else synthetic_tiff())

        with patch("builtins.open", side_effect=open_input):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with contextlib.redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(a.main(["missing.ORF", "good.ORF", "bad.ORF"]), 1)
        self.assertIn("payload 10x8", output.getvalue())
        self.assertIn("missing fixture", errors.getvalue())
        self.assertIn("not a TIFF-structured file", errors.getvalue())

    def test_nonnumeric_dimension_keeps_later_input(self):
        for entry, tag in ((0, 0x100), (1, 0x101)):
            bad = bytearray(synthetic_tiff())
            struct.pack_into('<HHI4s', bad, 10 + entry * 12, tag, 2, 2, b'A\0\0\0')
            def open_input(path, mode):
                return io.BytesIO(bytes(bad) if path == 'bad.ORF' else synthetic_tiff())
            out, err = io.StringIO(), io.StringIO()
            with self.subTest(tag=tag), patch('builtins.open', side_effect=open_input), \
                 contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(a.main(['bad.ORF', 'good.ORF']), 1)
                self.assertIn('good.ORF payload 10x8', out.getvalue())
                self.assertIn('bad.ORF:', err.getvalue())

    def test_cli_propagates_status(self):
        with patch.object(sys, "argv", ["orf_active_area.py", "bad.ORF"]):
            with patch.object(a, "main", return_value=1):
                self.assertEqual(a.main_cli(), 1)


if __name__ == "__main__":
    unittest.main()
