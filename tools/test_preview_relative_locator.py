#!/usr/bin/env python3
"""Synthetic MakerNote-relative locator checks."""
import os
import contextlib
import hashlib
import io
import json
import struct
import sys
import unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_relative_locator as probe
from test_preview_scalar_correspondence import fixture, ifd


def make_candidate(extra=0):
    data = bytearray(fixture(extra=extra))
    struct.pack_into('<I', data, 64 + 2 + 4, len(data) - 120)
    # Move the ImageProcessing IFD to avoid overlapping CameraSettings.
    struct.pack_into('<I', data, 120 + 12 + 2 + 12 + 8, 140)
    image_length = len(data) - 400
    blob = bytearray(data[120:])
    ifd(blob, 64, [(0x0101, 4, 1, 280), (0x0102, 4, 1, image_length)])
    ifd(blob, 140, [])
    data[120:] = blob
    return bytes(data)


class Tests(unittest.TestCase):
    def test_relative_candidate_and_match(self):
        data = make_candidate()
        result = probe.discover(data)
        self.assertEqual(result['relative_matches'], [0x0101])
        self.assertTrue(result['length_0102_matches'])
        self.assertEqual(probe.check(data, [0x0101])['candidates'][0]['status'], 'match')

    def test_missing_and_bad_extent_unknown(self):
        data = bytearray(make_candidate())
        self.assertEqual(probe.check(bytes(data), [0x0103])['candidates'][0]['reason'], 'missing_or_wrong_type')
        struct.pack_into('<I', data, 120 + 64 + 2 + 8, 99999)
        row = probe.check(bytes(data), [0x0101])['candidates'][0]
        self.assertEqual((row['status'], row['reason']), ('contradiction', 'outside_envelope'))

    def test_bad_marker_unknown(self):
        data = bytearray(make_candidate())
        struct.pack_into('<I', data, 120 + 64 + 2 + 12 + 8, len(data) - 401)
        row = probe.check(bytes(data), [0x0101])['candidates'][0]
        self.assertEqual((row['status'], row['reason']), ('contradiction', 'different_extent'))
        self.assertEqual(row['marker_status'], 'unknown')

    def test_trailing_end_and_frozen_length_gate(self):
        data = bytearray(make_candidate())
        data.extend(b'xx')
        struct.pack_into('<I', data, 64 + 2 + 4, len(data) - 120)
        struct.pack_into('<I', data, 120 + 64 + 2 + 12 + 8, len(data) - 400)
        result = probe.check(bytes(data), [0x0101])['candidates'][0]
        self.assertEqual((result['status'], result['reason']), ('contradiction', 'endpoint_mismatch'))
        rows = [dict(status='ok', length_0102_matches=True, relative_matches=[0x0101]) for _ in range(4)]
        self.assertEqual(probe.candidates(rows), [0x0101])
        rows[2]['length_0102_matches'] = False
        self.assertIsNone(probe.candidates(rows))

    def test_different_valid_extent_contradicts(self):
        data = bytearray(make_candidate())
        other = bytearray(data[400:])
        other[7:9] = (900).to_bytes(2, 'big')
        other[9:11] = (900).to_bytes(2, 'big')
        offset = len(data)
        data.extend(other)
        struct.pack_into('<I', data, 64 + 2 + 4, len(data) - 120)
        struct.pack_into('<I', data, 120 + 64 + 2 + 8, offset - 120)
        self.assertEqual(probe.check(bytes(data), [0x0101])['candidates'][0]['status'], 'contradiction')

    def test_frozen_mismatch_prevents_holdout_reads(self):
        ids = probe.DISCOVERY + probe.EXTENSION
        contents = {sid: make_candidate(extra=i) for i, sid in enumerate(ids)}
        samples = {sid: ('name' + sid, hashlib.sha256(contents[sid]).hexdigest()) for sid in ids}
        opened, frozen = [], [None]

        def fake_open(path, mode='r', **kwargs):
            opened.append(path)
            return io.StringIO(frozen[0]) if path == 'frozen' else io.BytesIO(contents[path])

        def args(phase):
            argv = ['probe', '--phase', phase]
            if phase == 'verification':
                argv += ['--frozen', 'frozen']
            for sid in (ids if phase == 'verification' else ids[:4]):
                argv += ['--sample', sid, sid]
            return argv

        with mock.patch.object(probe, 'SAMPLES', samples), mock.patch.object(probe, 'open', fake_open, create=True):
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', args('discovery')), contextlib.redirect_stdout(out):
                self.assertEqual(probe.main(), 0)
            previous = json.loads(out.getvalue())
            previous['samples'][0]['scanner_start'] += 1
            frozen[0] = json.dumps(previous)
            opened.clear()
            with mock.patch.object(sys, 'argv', args('verification')):
                with self.assertRaisesRegex(ValueError, 'discovery_mismatch'):
                    probe.main()
            self.assertNotIn('6343', opened)
            self.assertNotIn('5283', opened)


if __name__ == '__main__':
    unittest.main()
