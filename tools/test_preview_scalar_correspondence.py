import importlib.util
import contextlib
import hashlib
import io
import json
import os
import struct
import sys
import unittest
from unittest import mock

path = os.path.join(os.path.dirname(__file__), 'preview_scalar_correspondence.py')
spec = importlib.util.spec_from_file_location('scalar', path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def ifd(data, offset, entries):
    struct.pack_into('<H', data, offset, len(entries))
    for i, entry in enumerate(entries):
        struct.pack_into('<HHII', data, offset + 2 + 12 * i, *entry)
    struct.pack_into('<I', data, offset + 2 + 12 * len(entries), 0)


def fixture(length_tag=0x1001, extra=0):
    data = bytearray(400)
    struct.pack_into('<2sHI', data, 0, b'II', 42, 8)
    ifd(data, 8, [(0x8769, 4, 1, 64), (0x3333, 4, 1, 400)])
    ifd(data, 64, [(0x927c, 7, 220, 120)])
    blob = bytearray(220)
    blob[:12] = b'OLYMPUS\0II\x03\x00'
    ifd(blob, 12, [(0x2020, 13, 1, 64), (0x2040, 13, 1, 100)])
    image = (b'\xff\xd8\xff\xc0\x00\x0b\x08\x03\xe8\x03\xe8\x01\x01\x11\x00'
             b'\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\x11' + b'\x11' * extra + b'\xff\xd9')
    ifd(blob, 64, [(length_tag, 4, 1, len(image)), (0x1002, 4, 1, 400)])
    ifd(blob, 100, [(0x1001, 3, 1, len(image))])
    data[120:340] = blob
    return bytes(data) + image


class Tests(unittest.TestCase):
    def test_paths_types_and_intersection(self):
        a = probe.measure(fixture())
        b = probe.measure(fixture(extra=1))
        self.assertEqual(a['matches']['ifd0']['offset'], [0x3333])
        self.assertEqual(a['matches']['camera_settings']['length'], [0x1001])
        self.assertEqual(a['matches']['image_processing']['length'], [])
        self.assertEqual(probe.intersection([a, b])['camera_settings'], [0x1001])
        c = probe.measure(fixture(0x1003, extra=1))
        self.assertEqual(probe.intersection([a, c])['camera_settings'], [])

    def test_missing_and_duplicate_paths_unknown(self):
        data = bytearray(fixture())
        struct.pack_into('<H', data, 120 + 12 + 2, 0x2021)
        row = probe.measure(bytes(data))
        self.assertEqual(row['matches']['camera_settings']['status'], 'unknown')
        self.assertEqual(row['matches']['ifd0']['status'], 'ok')
        data = bytearray(fixture())
        struct.pack_into('<H', data, 120 + 12 + 14, 0x2020)
        row = probe.measure(bytes(data))
        self.assertEqual(row['matches']['camera_settings']['status'], 'unknown')

    def test_four_varying_lengths_and_no_reselection(self):
        discovery = [probe.measure(fixture(extra=i)) for i in range(4)]
        frozen = probe.intersection(discovery)
        self.assertEqual(frozen['camera_settings'], [0x1001])
        extension = probe.measure(fixture(0x1003, extra=4))
        self.assertNotIn(0x1001, extension['matches']['camera_settings']['length'])
        self.assertEqual(frozen['camera_settings'], [0x1001])

    def test_child_alias_is_unknown_for_both(self):
        data = bytearray(fixture())
        struct.pack_into('<I', data, 120 + 12 + 2 + 12 + 8, 64)
        row = probe.measure(bytes(data))
        self.assertEqual(row['matches']['camera_settings']['status'], 'unknown')
        self.assertEqual(row['matches']['image_processing']['status'], 'unknown')

    def test_makernote_encloses_jpeg_and_child_outside(self):
        data = bytearray(fixture())
        struct.pack_into('<I', data, 64 + 2 + 4, len(data) - 120)
        row = probe.measure(bytes(data))
        self.assertEqual(row['maker_preview_relation'], 'contained')
        self.assertEqual(row['matches']['camera_settings']['status'], 'ok')
        self.assertEqual(row['matches']['image_processing']['status'], 'ok')
        self.assertEqual(row['matches']['camera_settings']['length'], [0x1001])

    def test_child_directory_inside_jpeg_unknown(self):
        data = bytearray(fixture())
        struct.pack_into('<I', data, 64 + 2 + 4, len(data) - 120)
        struct.pack_into('<I', data, 120 + 12 + 2 + 8, 280)
        row = probe.measure(bytes(data))
        self.assertEqual(row['maker_preview_relation'], 'contained')
        self.assertEqual(row['matches']['camera_settings']['reason'], 'ifd_preview_overlap')
        self.assertEqual(row['matches']['image_processing']['status'], 'ok')

    def test_signature_inside_jpeg_is_excluded(self):
        data = bytearray(fixture())
        data[-2:-2] = b'OLYMPUS\0'
        struct.pack_into('<I', data, 64 + 2 + 4, len(data) - 120)
        row = probe.measure(bytes(data))
        self.assertEqual(row['maker_preview_relation'], 'contained')
        self.assertEqual(row['matches']['camera_settings']['status'], 'ok')

    def test_header_split_across_preview_boundary_is_not_joined(self):
        data = bytearray(fixture() + b'PUS\0')
        struct.pack_into('<I', data, 64 + 2 + 4, len(data) - 120)
        data[120:128] = b'xxxxxxxx'
        data[396:400] = b'OLYM'
        row = probe.measure(bytes(data))
        self.assertEqual(row['matches']['camera_settings']['reason'], 'maker_header')

    def test_partial_envelope_overlap(self):
        data = bytearray(fixture())
        struct.pack_into('<I', data, 64 + 2 + 4, 290)
        row = probe.measure(bytes(data))
        self.assertEqual(row['maker_preview_relation'], 'partly_overlaps')
        self.assertEqual(row['matches']['camera_settings']['status'], 'ok')

    def test_changed_frozen_row_stops_before_extension_reads(self):
        ids = probe.DISCOVERY + probe.EXTENSION
        inputs = {sid: fixture(extra=i) for i, sid in enumerate(ids)}
        samples = {sid: ('name' + sid, hashlib.sha256(inputs[sid]).hexdigest()) for sid in ids}
        opened = []
        frozen_text = [None]

        def fake_open(path, mode='r', **kwargs):
            opened.append(path)
            if path == 'frozen':
                return io.StringIO(frozen_text[0])
            return io.BytesIO(inputs[path])

        def args(phase):
            result = ['probe', '--phase', phase]
            if phase == 'verification':
                result += ['--frozen', 'frozen']
            for sid in (ids if phase == 'verification' else ids[:4]):
                result += ['--sample', sid, sid]
            return result

        with mock.patch.object(probe, 'SAMPLES', samples), mock.patch.object(probe, 'open', fake_open, create=True):
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', args('discovery')), contextlib.redirect_stdout(out):
                self.assertEqual(probe.main(), 0)
            previous = json.loads(out.getvalue())
            previous['samples'][0]['preview_offset'] += 1
            frozen_text[0] = json.dumps(previous)
            opened.clear()
            with mock.patch.object(sys, 'argv', args('verification')):
                with self.assertRaisesRegex(ValueError, 'discovery_mismatch'):
                    probe.main()
            self.assertNotIn('1998', opened)
            self.assertNotIn('3801', opened)


if __name__ == '__main__':
    unittest.main()
