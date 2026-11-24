#!/usr/bin/env python3
"""Independent generated-location controls; no sample-derived images."""
import os
import struct
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_locator_independent as p


def jpeg():
    return (b'\xff\xd8\xff\xc0\x00\x0b\x08\x04\xb0\x06\x40\x01\x01\x11\0'
            b'\xff\xda\0\x08\x01\x01\0\0\x3f\0\x31\xff\0\x32\xff\xd0\x33\xff\xd9')


def container(base=128, settings=80, relative=320, outer='little', inner='little'):
    image = jpeg()
    data = bytearray(base+relative+len(image)+128)
    def directory(at, entries, order):
        e = '<' if order == 'little' else '>'
        struct.pack_into(e+'H', data, at, len(entries))
        for i, (tag, typ, count, value) in enumerate(entries):
            struct.pack_into(e+'HHII', data, at+2+12*i, tag, typ, count, value)
    data[:4] = b'IIRO' if outer == 'little' else b'MMOR'
    data[4:8] = (8).to_bytes(4, outer)
    directory(8, [(0x8769, 4, 1, 64)], outer)
    directory(64, [(0x927c, 7, len(data)-base, base)], outer)
    data[base:base+12] = b'OLYMPUS\0' + (b'II' if inner == 'little' else b'MM') + b'\x03\0'
    directory(base+12, [(0x2020, 13, 1, settings)], inner)
    directory(base+settings, [(0x0101, 4, 1, relative), (0x0102, 4, 1, len(image))], inner)
    data[base+relative:base+relative+len(image)] = image
    return data


class Tests(unittest.TestCase):
    def test_all_endian_pairs_and_changing_origins(self):
        for outer in ('little', 'big'):
            for inner in ('little', 'big'):
                data = container(256, 96, 400, outer, inner)
                self.assertEqual(p.candidate(data), dict(status='ok', offset=656,
                    length=len(jpeg()), width=1600, height=1200))

    def test_larger_jpeg_does_not_select_candidate(self):
        data = container()
        image = bytearray(jpeg())
        image[7:11] = b'\x09\x60\x0c\x80'
        data.extend(image)
        self.assertEqual(p.candidate(data)['offset'], 448)

    def test_absolute_instead_of_relative_preview_is_not_rescued(self):
        data = container()
        struct.pack_into('<I', data, 128+80+10, 448)
        with self.assertRaises(ValueError):
            p.candidate(data)

    def test_incorrect_directory_base_is_not_rescued(self):
        data = container()
        struct.pack_into('<I', data, 128+12+10, 208)
        with self.assertRaises(ValueError):
            p.candidate(data)

    def test_displaced_header_is_unsupported(self):
        data = container()
        data[128:136] = b'xxxxxxxx'
        data[128+240:128+248] = b'OLYMPUS\0'
        with self.assertRaisesRegex(ValueError, 'unsupported_maker_header'):
            p.candidate(data)

    def test_eoi_must_equal_declared_end(self):
        with self.assertRaisesRegex(ValueError, 'jpeg_endpoint'):
            p.jpeg_geometry(jpeg()+b'\0')
        with self.assertRaises(ValueError):
            p.jpeg_geometry(jpeg()[:-2])

    def test_envelope_and_metadata_overlap(self):
        data = container()
        struct.pack_into('<I', data, 128+80+10, len(data))
        with self.assertRaisesRegex(ValueError, 'outside_maker'):
            p.candidate(data)
        data = container()
        struct.pack_into('<I', data, 128+80+10, 80)
        with self.assertRaisesRegex(ValueError, 'preview_metadata_overlap'):
            p.candidate(data)

    def test_ifd_duplicate_and_out_of_bounds(self):
        view = p.View(b'\x01\0'+b'\0'*12, 'little')
        with self.assertRaisesRegex(ValueError, 'bounds'):
            view.directory(0)
        data = container()
        struct.pack_into('<H', data, 128+80+14, 0x0101)
        with self.assertRaisesRegex(ValueError, 'duplicate_tag'):
            p.candidate(data)


if __name__ == '__main__':
    unittest.main()
