"""Synthetic declarations and phase replay checks."""
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
import v0_declared_geometry as probe


def fixture(endian='<'):
    data = bytearray(1000)
    struct.pack_into(endian + '2sHI', data, 0, b'II' if endian == '<' else b'MM', 42, 8)
    entries = [(256, 3, 1, 16), (257, 3, 1, 16), (273, 4, 1, 400),
               (279, 4, 1, 512), (274, 3, 1, 6), (50829, 3, 4, 200)]
    struct.pack_into(endian + 'H', data, 8, len(entries))
    for i, (tag, typ, count, value) in enumerate(entries):
        pos = 10 + i * 12
        struct.pack_into(endian + 'HHI', data, pos, tag, typ, count)
        struct.pack_into(endian + ('H' if typ == 3 and count == 1 else 'I'), data, pos + 8, value)
    struct.pack_into(endian + '4H', data, 200, 1, 2, 15, 14)
    return bytes(data)


class Tests(unittest.TestCase):
    def test_endian_shapes(self):
        for endian in ('<', '>'):
            result = probe.measure(fixture(endian), ('16', '16', 'packed-16'))
            self.assertEqual(result['raw_tags']['274']['values'], [6])
            self.assertEqual(result['raw_tags']['50829']['values'], [1, 2, 15, 14])
            self.assertEqual(result['ifd0_tags']['50706']['status'], 'absent')

    def test_bad_shape_and_bounds(self):
        data = bytearray(fixture())
        struct.pack_into('<I', data, 10 + 5*12 + 4, 3)
        result = probe.measure(bytes(data), ('16', '16', 'packed-16'))
        self.assertEqual(result['raw_tags']['50829']['status'], 'unsupported_shape')
        struct.pack_into('<I', data, 10 + 5*12 + 4, 4)
        struct.pack_into('<I', data, 10 + 5*12 + 8, 999)
        result = probe.measure(bytes(data), ('16', '16', 'packed-16'))
        self.assertEqual(result['raw_tags']['50829']['status'], 'out_of_bounds')
        struct.pack_into('<I', data, 10 + 5*12 + 8, 400)
        result = probe.measure(bytes(data), ('16', '16', 'packed-16'))
        self.assertEqual(result['raw_tags']['50829']['status'], 'strip_overlap')
        self.assertNotIn('values', result['raw_tags']['50829'])

    def test_rational_and_zero_denominator(self):
        data = bytearray(fixture())
        struct.pack_into('<HHII', data, 10 + 5*12, 50718, 5, 2, 200)
        struct.pack_into('<4I', data, 200, 1, 2, 3, 4)
        tag = probe.measure(bytes(data), ('16', '16', 'packed-16'))['raw_tags']['50718']
        self.assertEqual(tag['values'], [[1, 2], [3, 4]])
        struct.pack_into('<I', data, 204, 0)
        tag = probe.measure(bytes(data), ('16', '16', 'packed-16'))['raw_tags']['50718']
        self.assertEqual(tag['status'], 'zero_denominator')

    def test_ifd_inside_strip_unknown(self):
        data = bytearray(fixture())
        struct.pack_into('<I', data, 10 + 2*12 + 8, 8)
        with self.assertRaisesRegex(ValueError, 'ifd_strip_overlap'):
            probe.measure(bytes(data), ('16', '16', 'packed-16'))

    def test_phase_replay(self):
        ids = probe.DISCOVERY + probe.EXTENSION
        data = fixture()
        digest = hashlib.sha256(data).hexdigest()
        identities = {sid: ('public', digest, '16', '16', 'packed-16') for sid in ids}
        opened, frozen = [], [None]
        def fake_open(path, mode='r', **kwargs):
            opened.append(path)
            return io.StringIO(frozen[0]) if path == 'frozen' else io.BytesIO(data)
        def argv(phase):
            a = ['probe', '--phase', phase]
            if phase == 'verification':
                a += ['--frozen', 'frozen']
            for sid in ids if phase == 'verification' else probe.DISCOVERY:
                a += ['--sample', sid, sid]
            return a
        with mock.patch.object(probe, 'roster', return_value=identities), mock.patch.object(probe, 'open', fake_open, create=True):
            out = io.StringIO()
            with mock.patch.object(sys, 'argv', argv('discovery')), contextlib.redirect_stdout(out):
                self.assertEqual(probe.main(), 0)
            saved = json.loads(out.getvalue())
            frozen[0] = json.dumps(saved)
            with mock.patch.object(sys, 'argv', argv('verification')), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main(), 0)
            saved['samples'][0]['width'] += 1
            frozen[0] = json.dumps(saved)
            opened.clear()
            with mock.patch.object(sys, 'argv', argv('verification')):
                with self.assertRaisesRegex(SystemExit, 'discovery_mismatch'):
                    probe.main()
            self.assertNotIn(probe.EXTENSION[0], opened)


if __name__ == '__main__':
    unittest.main()
