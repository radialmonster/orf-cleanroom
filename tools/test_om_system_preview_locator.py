#!/usr/bin/env python3
"""Known-location synthetic controls for the fixed OM SYSTEM locator."""
import contextlib
import hashlib
import io
import json
import os
import struct
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import om_system_preview_locator as probe


def ifd(data, at, entries):
    struct.pack_into('<H', data, at, len(entries))
    for i, row in enumerate(entries):
        struct.pack_into('<HHII', data, at + 2 + 12*i, *row)
    struct.pack_into('<I', data, at + 2 + 12*len(entries), 0)


def jpeg(width=1600, height=1200):
    sof = bytes([8]) + struct.pack('>HH', height, width) + b'\x01\x01\x11\x00'
    return (b'\xff\xd8\xff\xc0' + struct.pack('>H', len(sof)+2) + sof
            + b'\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\x22\xff\xd9')


def fixture(base=120, settings=64, relative=300):
    image = jpeg()
    size = relative + len(image) + 256
    data = bytearray(base + size)
    data[:8] = b'IIRO' + struct.pack('<I', 8)
    ifd(data, 8, [(0x8769, 4, 1, 64)])
    ifd(data, 64, [(0x927c, 7, size, base)])
    data[base:base+16] = probe.HEADER
    ifd(data, base+16, [(0x2020, 13, 1, settings)])
    ifd(data, base+settings, [(0x0101, 4, 1, relative), (0x0102, 4, 1, len(image))])
    data[base+relative:base+relative+len(image)] = image
    return data


class Tests(unittest.TestCase):
    def test_known_location_across_bases_and_directory_offsets(self):
        for base, settings in ((120, 64), (256, 96)):
            with self.subTest(base=base):
                data = fixture(base, settings)
                row = probe.measure(data)
                self.assertEqual(row['candidate']['offset'], base+300)
                self.assertEqual(row['candidate']['settings_relative'], settings)
                self.assertEqual(row['relation'], 'match')
                self.assertEqual(row['previous']['reason'], 'nonleading_header')

    def test_candidate_does_not_call_scanner(self):
        with mock.patch.object(probe.jpeg_dc, 'find_preview', side_effect=AssertionError('scanner')):
            self.assertEqual(probe.candidate(fixture())['offset'], 420)

    def test_larger_decoy_does_not_change_metadata_interval(self):
        data = fixture()
        data.extend(jpeg(3200, 2400))
        row = probe.measure(data)
        self.assertEqual(row['candidate']['offset'], 420)
        self.assertEqual(row['relation'], 'mismatch')

    def test_wrong_absolute_preview_base_is_not_rescued(self):
        data = fixture()
        struct.pack_into('<I', data, 120+64+2+8, 420)
        row = probe.measure(data)
        self.assertEqual(row['candidate']['reason'], 'missing_soi')
        self.assertEqual(row['scanner']['status'], 'ok')

    def test_wrong_settings_base_is_unknown(self):
        data = fixture()
        struct.pack_into('<I', data, 120+16+2+8, 184)
        self.assertEqual(probe.measure(data)['candidate']['reason'], 'missing_scalar')

    def test_header_must_lead_and_match_entire_fixed_header(self):
        for offset in (0, 14):
            data = fixture()
            data[120+offset] ^= 1
            data[120+200:120+216] = probe.HEADER
            self.assertEqual(probe.measure(data)['candidate']['reason'], 'unsupported_leading_header')

    def test_declared_endpoint_and_envelope(self):
        data = fixture()
        length_at = 120+64+2+12+8
        struct.pack_into('<I', data, length_at, len(jpeg())+1)
        self.assertEqual(probe.measure(data)['candidate']['reason'], 'endpoint_mismatch')
        struct.pack_into('<I', data, length_at, len(data))
        self.assertEqual(probe.measure(data)['candidate']['reason'], 'outside_envelope')

    def test_metadata_overlap_is_unresolved(self):
        data = fixture()
        struct.pack_into('<I', data, 120+64+2+8, 64)
        self.assertEqual(probe.measure(data)['candidate']['reason'], 'jpeg_metadata_overlap')

    def test_candidate_precedes_scanner(self):
        calls = []
        candidate, scanner = probe.candidate, probe.scanner
        def first(data):
            calls.append('candidate')
            return candidate(data)
        def second(data):
            calls.append('scanner')
            return scanner(data)
        with mock.patch.object(probe, 'candidate', first), mock.patch.object(probe, 'scanner', second):
            self.assertEqual(probe.measure(fixture())['relation'], 'match')
        self.assertEqual(calls, ['candidate', 'scanner'])

    def test_changed_discovery_blocks_reserved_reads(self):
        content = bytes(fixture())
        samples = {sid: ('sample '+sid, hashlib.sha256(content).hexdigest()) for sid in probe.SAMPLES}
        opened, frozen = [], [None]
        def read(path, mode='r', **kwargs):
            opened.append(path)
            return io.StringIO(frozen[0]) if path == 'frozen' else io.BytesIO(content)
        def argv(phase):
            result = ['probe', '--phase', phase]
            if phase == 'verification':
                result += ['--frozen', 'frozen']
            for sid in probe.DISCOVERY + (probe.EXTENSION if phase == 'verification' else []):
                result += ['--sample', sid, sid]
            return result
        with mock.patch.object(probe, 'SAMPLES', samples), mock.patch.object(probe, 'open', read, create=True):
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', argv('discovery')), contextlib.redirect_stdout(out):
                self.assertEqual(probe.main(), 0)
            report = json.loads(out.getvalue())
            report['samples'][0]['candidate']['offset'] += 1
            frozen[0] = json.dumps(report)
            opened.clear()
            with mock.patch.object(sys, 'argv', argv('verification')):
                with self.assertRaisesRegex(ValueError, 'discovery_mismatch'):
                    probe.main()
            self.assertFalse(set(probe.EXTENSION).intersection(opened))


if __name__ == '__main__':
    unittest.main()
