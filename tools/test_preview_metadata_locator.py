#!/usr/bin/env python3
"""Synthetic metadata-first locator and scanner-order controls."""
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
import preview_metadata_locator as probe
from test_preview_relative_locator import make_candidate


class Tests(unittest.TestCase):
    def test_generated_container_agrees(self):
        result = probe.measure(make_candidate())
        self.assertEqual(result['candidate']['status'], 'ok')
        self.assertEqual(result['relation'], 'match')

    def test_nonleading_header_is_unknown(self):
        data = bytearray(make_candidate())
        data[120:128] = b'xxxxxxxx'
        result = probe.measure(bytes(data))
        self.assertEqual(result['candidate']['reason'], 'nonleading_header')
        self.assertEqual(result['scanner']['status'], 'ok')
        self.assertEqual(result['relation'], 'unknown')

    def test_derived_jpeg_overlap_directory_unknown(self):
        data = bytearray(make_candidate())
        struct.pack_into('<I', data, 120 + 64 + 2 + 8, 64)
        result = probe.measure(bytes(data))
        self.assertEqual(result['candidate']['reason'], 'jpeg_metadata_overlap')
        self.assertEqual(result['scanner']['status'], 'ok')

    def test_outside_envelope_contradiction(self):
        data = bytearray(make_candidate())
        struct.pack_into('<I', data, 120 + 64 + 2 + 8, 99999)
        result = probe.measure(bytes(data))
        self.assertEqual(result['candidate']['status'], 'contradiction')
        self.assertEqual(result['scanner']['status'], 'ok')

    def test_in_bounds_non_jpeg_contradiction(self):
        data = bytearray(make_candidate())
        struct.pack_into('<I', data, 120 + 64 + 2 + 8, 279)
        result = probe.measure(bytes(data))
        self.assertEqual(result['candidate']['status'], 'contradiction')
        self.assertEqual(result['candidate']['reason'], 'missing_soi')
        self.assertEqual(result['scanner']['status'], 'ok')

    def test_candidate_checked_before_scanner(self):
        events = []
        candidate = probe.candidate
        scanner = probe.jpeg_dc.find_preview
        def candidate_first(data):
            events.append('candidate')
            return candidate(data)
        def scanner_second(data):
            events.append('scanner')
            return scanner(data)
        with mock.patch.object(probe, 'candidate', candidate_first), mock.patch.object(probe.jpeg_dc, 'find_preview', scanner_second):
            self.assertEqual(probe.measure(make_candidate())['relation'], 'match')
        self.assertEqual(events, ['candidate', 'scanner', 'scanner'])

    def test_frozen_gate_blocks_extensions(self):
        ids = probe.DISCOVERY + probe.EXTENSION
        contents = {sid: make_candidate(extra=i) for i, sid in enumerate(ids)}
        samples = {sid: ('name' + sid, hashlib.sha256(contents[sid]).hexdigest()) for sid in ids}
        opened, frozen = [], [None]
        def fake_open(path, mode='r', **kwargs):
            opened.append(path)
            return io.StringIO(frozen[0]) if path == 'frozen' else io.BytesIO(contents[path])
        def argv(phase):
            result = ['probe', '--phase', phase]
            if phase == 'verification':
                result += ['--frozen', 'frozen']
            for sid in (ids if phase == 'verification' else ids[:4]):
                result += ['--sample', sid, sid]
            return result
        with mock.patch.object(probe, 'SAMPLES', samples), mock.patch.object(probe, 'open', fake_open, create=True):
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', argv('discovery')), contextlib.redirect_stdout(out):
                self.assertEqual(probe.main(), 0)
            previous = json.loads(out.getvalue())
            previous['samples'][0]['candidate']['offset'] += 1
            frozen[0] = json.dumps(previous)
            opened.clear()
            with mock.patch.object(sys, 'argv', argv('verification')):
                with self.assertRaisesRegex(ValueError, 'discovery_mismatch'):
                    probe.main()
            self.assertNotIn('1051', opened)
            self.assertNotIn('3588', opened)


if __name__ == '__main__':
    unittest.main()
