"""Synthetic checks for jpeg_dc marker parsing and arithmetic (no sample files)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jpeg_dc as j  # noqa: E402


def sof0(width, height):
    # marker + length + precision + height + width + 3 components
    seg = bytes([8, height >> 8, height & 255, width >> 8, width & 255, 3,
                 1, 0x22, 0, 2, 0x11, 1, 3, 0x11, 1])
    return b"\xff\xc0" + bytes([0, len(seg) + 2]) + seg


class JpegTests(unittest.TestCase):
    def test_extend(self):
        self.assertEqual(j.extend(0b101, 3), 5)
        self.assertEqual(j.extend(0b001, 3), -6)
        self.assertEqual(j.extend(0b1111, 4), 15)
        self.assertEqual(j.extend(0b0000, 4), -15)

    def test_huffman(self):
        table = j.build_huffman([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [7, 8])
        self.assertEqual(table[(1, 0)], 7)
        self.assertEqual(table[(2, 2)], 8)

    def test_find_preview(self):
        data = b"\xff\xd8" + sof0(3200, 2400) + b"\xff\xda\x00\x02" + b"\xff\xd9"
        best = j.find_preview(data)
        self.assertIsNotNone(best)
        self.assertEqual(best[0], 3200 * 2400)
        self.assertEqual((best[3], best[4]), (3200, 2400))

    def test_thumbnail_ignored(self):
        thumb = b"\xff\xd8" + sof0(160, 120) + b"\xff\xda\x00\x02" + b"\xff\xd9"
        full = b"\xff\xd8" + sof0(3200, 2400) + b"\xff\xda\x00\x02" + b"\xff\xd9"
        best = j.find_preview(thumb + full)
        self.assertEqual((best[3], best[4]), (3200, 2400))

    def test_frame_without_scan_does_not_hide_valid_preview(self):
        incomplete = b"\xff\xd8" + sof0(4000, 3000) + b"\xff\xd9"
        valid = b"\xff\xd8" + sof0(3200, 2400) + b"\xff\xda\x00\x02" + b"\xff\xd9"
        best = j.find_preview(incomplete + valid)
        self.assertEqual((best[1], best[3], best[4]), (len(incomplete), 3200, 2400))

    def test_eoi_inside_app_segment_does_not_end_preview(self):
        app = b"\xff\xe1\x00\x06\xff\xd9xx"
        data = b"\xff\xd8" + app + sof0(3200, 2400) + b"\xff\xda\x00\x02" + b"\xff\xd9"
        self.assertEqual(j.find_preview(data)[2], len(data))

    def test_missing_first_scan_component_is_rejected(self):
        scan = b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00"
        with self.assertRaisesRegex(ValueError, "first scan"):
            j.decode(b"\xff\xd8" + sof0(16, 8) + scan, 0)

    def test_single_component_sampling_factors_do_not_expand_mcus(self):
        segment = bytes([8, 0, 8, 0, 24, 1, 1, 0x22, 0])
        frame = b"\xff\xc0" + bytes([0, len(segment) + 2]) + segment
        # One one-bit DC category 0 and one one-bit AC end-of-block code.
        counts = bytes([1] + [0] * 15)
        tables = b"\x00" + counts + b"\x00" + b"\x10" + counts + b"\x00"
        dht = b"\xff\xc4" + (len(tables) + 2).to_bytes(2, "big") + tables
        scan = b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00"
        data = b"\xff\xd8" + frame + dht + scan + b"\x00\xff\xd9"
        self.assertEqual(j.decode(data, 0), (3, 1, [0, 0, 0]))


if __name__ == "__main__":
    unittest.main()
