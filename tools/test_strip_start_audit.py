#!/usr/bin/env python3
"""Original synthetic checks for the V2 G4 declared-strip audit (no camera data)."""
import argparse
from contextlib import redirect_stdout
import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strip_start_audit as probe


def fixture(order='little', layout='root', split=False, ambiguous=False, zeros=47):
    """Build small TIFF-shaped bytes with separately known directory positions."""
    data = bytearray(768)

    def put(at, value, width):
        data[at:at + width] = value.to_bytes(width, order)

    data[:2] = b'II' if order == 'little' else b'MM'
    put(2, 0x4f52, 2)
    put(4, 8, 4)
    raw_ifd = {'root': 8, 'next': 128, 'sub': 256}[layout]
    payload = bytes(zeros // 8) + bytes([1 << (7 - zeros % 8)]) + bytes(range(1, 25))
    offsets = [512, 640] if split else [512]
    counts = [12, len(payload) - 12] if split else [len(payload)]

    def directory(at, width, height, starts, lengths, next_ifd=0, sub=None):
        tags = [(0x100, 4, [width]), (0x101, 4, [height]),
                (0x102, 3, [16]), (0x103, 3, [1]),
                (0x111, 4, starts), (0x117, 4, lengths)]
        if sub is not None:
            tags.append((0x14a, 4, [sub]))
        put(at, len(tags), 2)
        for i, (tag, kind, values) in enumerate(tags):
            entry = at + 2 + 12 * i
            put(entry, tag, 2)
            put(entry + 2, kind, 2)
            put(entry + 4, len(values), 4)
            step = 2 if kind == 3 else 4
            if len(values) * step <= 4:
                value_at = entry + 8
            else:
                value_at = 344 if tag == 0x111 else 360
                put(entry + 8, value_at, 4)
            for j, value in enumerate(values):
                put(value_at + step * j, value, step)
        put(at + 2 + 12 * len(tags), next_ifd, 4)

    if layout != 'root':
        preview_count = len(payload) if ambiguous else 8
        directory(8, 2, 2, [448], [preview_count],
                  next_ifd=128 if layout == 'next' else 0,
                  sub=256 if layout == 'sub' else None)
        data[448:448 + preview_count] = b'\xff' * preview_count
    directory(raw_ifd, 4, 4, offsets, counts)
    cursor = 0
    for start, count in zip(offsets, counts):
        data[start:start + count] = payload[cursor:cursor + count]
        cursor += count
    return bytes(data), payload, raw_ifd


class StripStartTests(unittest.TestCase):
    def test_startup_count_matches_literal_bits(self):
        for zero_bytes in range(9):
            for value in range(1, 256):
                buf = bytes(zero_bytes) + bytes([value])
                bits = ''.join(format(b, '08b') for b in buf)
                self.assertEqual(probe.startup_zeros(buf), bits.index('1'))
        self.assertIsNone(probe.startup_zeros(b'\0' * 9))

    def test_known_extents_both_orders_and_directory_paths(self):
        for order in ('little', 'big'):
            for layout in ('root', 'next', 'sub'):
                for zeros in (39, 47):
                    with self.subTest(order=order, layout=layout, zeros=zeros):
                        data, expected, selected = fixture(order, layout, zeros=zeros)
                        record, payload = probe.independent_strips(data)
                        self.assertEqual(payload, expected)
                        self.assertEqual(record['selected_ifd'], selected)
                        self.assertEqual(record['strip_offsets'], [512])
                        self.assertEqual(record['strip_byte_counts'], [len(expected)])
                        self.assertEqual(record['strip_offsets_entry'], selected + 50)
                        self.assertEqual(record['strip_counts_entry'], selected + 62)
                        self.assertEqual(record['bytes_after_last_physical_strip'], 768 - 512 - len(expected))
                        compared = probe.compare_snapshot(data)
                        self.assertEqual(compared['initial_zero_bits'], zeros)
                        self.assertTrue(all(compared['agreements'].values()))

    def test_discontiguous_strips_exclude_gap(self):
        for order in ('little', 'big'):
            data, expected, _ = fixture(order, 'sub', split=True)
            record, payload = probe.independent_strips(data)
            self.assertEqual(payload, expected)
            self.assertEqual(record['strip_offsets'], [512, 640])
            self.assertEqual(record['strip_byte_counts'], [12, len(expected) - 12])
            compared = probe.compare_snapshot(data)
            self.assertTrue(all(compared['agreements'].values()))
            self.assertEqual(compared['geometry_summary']['forward_gaps'], 1)

    def test_shifted_existing_extraction_is_detected(self):
        data, expected, _ = fixture()
        for wrong in (expected[1:], b'\0' + expected):
            with patch.object(probe, 'locate_data', return_value=(4, 4, wrong)):
                self.assertFalse(probe.compare_snapshot(data)['agreements']['full_payload_bytes'])

    def test_wrong_ifd_extraction_is_detected(self):
        data, _, _ = fixture(layout='sub')
        with patch.object(probe, 'locate_data', return_value=(2, 2, data[448:456])):
            checks = probe.compare_snapshot(data)['agreements']
            self.assertFalse(checks['full_payload_bytes'])
            self.assertFalse(checks['locator_dimensions'])

    def test_ambiguous_selection_is_unknown(self):
        data, _, _ = fixture(layout='next', ambiguous=True)
        with self.assertRaisesRegex(probe.ContainerError, 'ambiguous_largest_ifd'):
            probe.independent_strips(data)

    def test_truncated_directory_is_unknown(self):
        data, _, _ = fixture()
        with self.assertRaises(probe.ContainerError):
            probe.independent_strips(data[:25])

    def test_truncated_strip_is_unknown(self):
        data, _, _ = fixture()
        with self.assertRaisesRegex(probe.ContainerError, 'strip_outside_file'):
            probe.independent_strips(data[:520])

    def test_hash_gate_precedes_parsing(self):
        data, _, _ = fixture()
        with patch.object(probe.Path, 'read_bytes', return_value=data):
            with self.assertRaisesRegex(probe.ContainerError, 'hash_mismatch'):
                probe.measure('unused', '0' * 64)

    def test_cli_retains_unknown_inputs(self):
        with patch.object(probe, 'measure', side_effect=probe.ContainerError('hash_mismatch')):
            out = io.StringIO()
            with redirect_stdout(out):
                code = probe.main(['--sample', '1', 'public.ORF', '0' * 64, 'unused'])
            self.assertEqual(code, 1)
            self.assertIn('"status": "unknown"', out.getvalue())
            self.assertNotIn('unused', out.getvalue())


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    unittest.main(argv=[sys.argv[0]])
