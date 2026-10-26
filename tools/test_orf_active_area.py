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
import orf_signature


def synthetic_tiff():
    data = b"II" + struct.pack("<HIH", 42, 8, 2)
    for tag, value in ((0x100, 10), (0x101, 8)):
        data += struct.pack("<HHII", tag, 4, 1, value)
    return data + struct.pack("<I", 0)


class MainTests(unittest.TestCase):
    def test_payload_geometry_uses_largest_strip_ifd(self):
        for route in ('sub', 'next'):
            data = bytearray(512)
            struct.pack_into('<2sHIH', data, 0, b'II', 0x5352, 8, 5 if route == 'sub' else 4)
            entries = [(0x100, 10), (0x101, 8), (0x111, 300), (0x117, 4)]
            if route == 'sub':
                entries.append((0x14a, 96))
            for i, (tag, value) in enumerate(entries):
                struct.pack_into('<HHII', data, 10 + i * 12, tag, 4, 1, value)
            if route == 'next':
                struct.pack_into('<I', data, 10 + 4 * 12, 96)
            struct.pack_into('<H', data, 96, 4)
            for i, (tag, value) in enumerate(((0x100, 40), (0x101, 30), (0x111, 320), (0x117, 64))):
                struct.pack_into('<HHII', data, 98 + i * 12, tag, 4, 1, value)
            with self.subTest(route=route), patch('builtins.open', side_effect=lambda *args, **kwargs: io.BytesIO(data)):
                self.assertEqual((orf_signature.signature('fixture')['payload_w'],
                                  orf_signature.signature('fixture')['payload_h']), (40, 30))
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(a.main(['fixture.ORF']), 0)
                self.assertIn('payload 40x30', output.getvalue())
                image = {0x0614: (4, 1, b'', 8), 0x0615: (4, 1, b'', 6)}
                with patch.object(a, 'maker_note', return_value=b'synthetic'), \
                     patch.object(a, 'olympus_tags', return_value={'image_processing': image}), \
                     contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(a.main(['fixture.ORF']), 0)
                self.assertIn('payload 40x30  active 8x6  border 32x24', output.getvalue())

    def test_success(self):
        with patch("builtins.open", return_value=io.BytesIO(synthetic_tiff())):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(a.main(["good.ORF"]), 0)
        self.assertIn("primary 10x8", output.getvalue())

    def test_no_strip_active_geometry_does_not_claim_payload_border(self):
        image = {0x0614: (4, 1, b'', 8), 0x0615: (4, 1, b'', 6)}
        with patch('builtins.open', return_value=io.BytesIO(synthetic_tiff())), \
             patch.object(a, 'maker_note', return_value=b'synthetic'), \
             patch.object(a, 'olympus_tags', return_value={'image_processing': image}), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(a.main(['fixture.ORF']), 0)
        self.assertIn('primary 10x8  active 8x6  border unavailable', output.getvalue())

    def test_mixed_success_failure_retains_output_and_failure_status(self):
        def open_input(path, mode):
            if path == "missing.ORF":
                raise FileNotFoundError("missing fixture")
            return io.BytesIO(b"bad" if path == "bad.ORF" else synthetic_tiff())

        with patch("builtins.open", side_effect=open_input):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with contextlib.redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(a.main(["missing.ORF", "good.ORF", "bad.ORF"]), 1)
        self.assertIn("primary 10x8", output.getvalue())
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
                self.assertIn('good.ORF primary 10x8', out.getvalue())
                self.assertIn('bad.ORF:', err.getvalue())

    def test_cli_propagates_status(self):
        with patch.object(sys, "argv", ["orf_active_area.py", "bad.ORF"]):
            with patch.object(a, "main", return_value=1):
                self.assertEqual(a.main_cli(), 1)


if __name__ == "__main__":
    unittest.main()
