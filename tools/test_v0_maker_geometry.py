#!/usr/bin/env python3
"""Original literal-geometry controls, including unknown versus absent."""
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
import v0_maker_geometry as p


def directory(data, at, entries):
    struct.pack_into('<H', data, at, len(entries))
    for i, item in enumerate(entries):
        struct.pack_into('<HHII', data, at+2+12*i, *item)


def fixture():
    data = bytearray(1600)
    data[:8] = b'IIRO'+struct.pack('<I', 8)
    directory(data, 8, [(0x8769, 4, 1, 64)])
    directory(data, 64, [(0xa002, 4, 1, 640), (0xa003, 3, 1, 480), (0x927c, 7, 1400, 200)])
    data[200:212] = b'OLYMPUS\0II\x03\0'
    directory(data, 212, [(0x2020, 13, 1, 64), (0x2040, 13, 1, 128)])
    directory(data, 264, [(0x0101, 4, 1, 900), (0x0102, 4, 1, 100)])
    directory(data, 328, [(0x0614, 3, 1, 640), (0x0615, 4, 1, 480), (0x0637, 3, 4, 200)])
    struct.pack_into('<4H', data, 400, 1, 640, 2, 481)
    return data


class Tests(unittest.TestCase):
    def fields(self, data):
        view = p.GuardedView(data, 'little')
        root, _ = view.directory(8)
        exif, _ = view.directory(view.scalar(root, 0x8769))
        return p.maker_fields(data, view, exif)

    def test_inline_and_indirect_literal_values(self):
        result = self.fields(fixture())
        self.assertEqual(result['tags']['1556']['values'], [640])
        self.assertEqual(result['tags']['1557']['values'], [480])
        self.assertEqual(result['tags']['1591']['values'], [1, 640, 2, 481])

    def test_missing_is_distinct_from_wrong_shape_and_zero(self):
        data = fixture()
        directory(data, 328, [(0x0614, 4, 1, 0), (0x0637, 4, 1, 7)])
        tags = self.fields(data)['tags']
        self.assertEqual(tags['1556']['values'], [0])
        self.assertEqual(tags['1557']['status'], 'absent')
        self.assertEqual(tags['1591']['status'], 'unsupported_shape')

    def test_unsupported_header_is_not_absence(self):
        data = fixture()
        data[200] = 0
        with self.assertRaisesRegex(ValueError, 'unsupported_leading_header'):
            self.fields(data)

    def test_preview_guard_blocks_directory(self):
        data = fixture()
        struct.pack_into('<I', data, 212+2+12+8, 900)
        with self.assertRaisesRegex(ValueError, 'forbidden_metadata_read'):
            self.fields(data)

    def test_preview_guard_blocks_indirect_value(self):
        data = fixture()
        struct.pack_into('<I', data, 328+2+24+8, 900)
        self.assertEqual(self.fields(data)['tags']['1591']['reason'], 'forbidden_metadata_read')

    def test_strip_guard_blocks_reads(self):
        view = p.GuardedView(fixture(), 'little', [(64, 100)])
        with self.assertRaisesRegex(ValueError, 'forbidden_metadata_read'):
            view.directory(64)

    def test_big_endian_inline_short(self):
        data = b'\0\x01'+struct.pack('>HHI', 0x0614, 3, 1)+b'\x02\x80\0\0'+b'\0'*4
        view = p.GuardedView(data, 'big')
        tags, _ = view.directory(0)
        self.assertEqual(p.literal(view, tags, 0x0614, 1)['values'], [640])

    def test_replay_blocks_reserved_inputs(self):
        content = bytes(fixture())
        digest = hashlib.sha256(content).hexdigest()
        roster = {sid: ('public', digest, '640', '480', 'packed-12') for sid in p.DISCOVERY+p.EXTENSION}
        opened, saved = [], [None]
        def read(path, mode='r', **kwargs):
            opened.append(path)
            return io.StringIO(saved[0]) if path == 'frozen' else io.BytesIO(content)
        def args(phase):
            out = ['probe', '--phase', phase]+(['--frozen', 'frozen'] if phase == 'verification' else [])
            for sid in p.DISCOVERY+(p.EXTENSION if phase == 'verification' else []):
                out += ['--sample', sid, sid]
            return out
        with mock.patch.object(p.baseline, 'roster', return_value=roster), mock.patch.object(p, 'open', read, create=True), mock.patch.object(p, 'measure', return_value={'status': 'ok'}):
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', args('discovery')), contextlib.redirect_stdout(out):
                self.assertEqual(p.main(), 0)
            report = json.loads(out.getvalue())
            report['samples'][0]['status'] = 'changed'
            saved[0] = json.dumps(report)
            opened.clear()
            with mock.patch.object(sys, 'argv', args('verification')):
                with self.assertRaisesRegex(ValueError, 'discovery_mismatch'):
                    p.main()
            self.assertFalse(set(p.EXTENSION).intersection(opened))


if __name__ == '__main__':
    unittest.main()
