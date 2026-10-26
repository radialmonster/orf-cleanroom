"""Synthetic complete-word boundary checks for packed-12 candidate analysis."""
import contextlib
import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_v0_unpack as probe


class CandidateTests(unittest.TestCase):
    def test_exact_row_incomplete_words_are_explicitly_unavailable(self):
        for length, pixels, width in ((30, 20, 4), (45, 30, 2), (45, 30, 4)):
            with self.subTest(length=length, width=width):
                with self.assertRaises(probe.IncompleteWord):
                    probe.candidates("packed-12")["w%d-12-lsb" % width](bytes(length), pixels)

    def test_longer_row_supplies_complete_word_for_prefix(self):
        row = bytes(range(48))
        for width in (2, 4):
            with self.subTest(width=width):
                needed = (45 + width - 1) // width * width
                got = probe.candidates("packed-12")["w%d-12-lsb" % width](row, 30)
                self.assertEqual(got, probe.pairs12(probe.swapped(row[:needed], width), 0, 30, "lsb"))
                self.assertEqual(len(got), 30)

    def test_analyse_skips_unavailable_candidates(self):
        data = bytes((i * 31 + 9) % 256 for i in range(45 * 8))
        signature = dict(size_class="packed-12", payload_w=30, payload_h=8,
                         payload_bytes=len(data), payload_offset=0, file="synthetic",
                         sha256="synthetic", model="synthetic")
        output = io.StringIO()
        with patch.object(probe.orf_signature, "signature", return_value=signature), \
                patch("builtins.open", return_value=io.BytesIO(data)), \
                contextlib.redirect_stdout(output):
            probe.analyse("synthetic", 3, 1, 30)
        self.assertIn("w2-12-lsb skipped: complete 2-byte word unavailable", output.getvalue())
        self.assertIn("w4-12-lsb skipped: complete 4-byte word unavailable", output.getvalue())
        self.assertIn("chosen:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
