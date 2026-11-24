#!/usr/bin/env python3
"""Generated metadata and literal-prefix controls; no camera pixels."""
import os
import struct
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import makernote_prefix_audit as p


def fixture(om=False,big=False):
    data=bytearray(1800)
    e='>' if big else '<'
    def directory(at,entries):
        struct.pack_into(e+'H',data,at,len(entries))
        for i,row in enumerate(entries):
            struct.pack_into(e+'HHII',data,at+2+12*i,*row)
    data[:8]=(b'MMOR' if big else b'IIRO')+struct.pack(e+'I',8)
    directory(8,[(0x8769,4,1,64)])
    directory(64,[(0x927c,7,1500,200)])
    header=b'OM SYSTEM\0\0\0' if om else b'OLYMPUS\0'
    data[200:200+len(header)+4]=header+(b'MM' if big else b'II')+b'\x04\0'
    directory(200+len(header)+4,[(0x2020,13,1,96),(0x2040,13,1,160),(0x2050,13,1,240)])
    directory(296,[(0x0101,4,1,1000),(0x0102,4,1,100)])
    directory(360,[(0x0611,3,2,0),(0x0653,4,1,6)])
    struct.pack_into(e+'2H',data,370,14,0)
    directory(440,[(0x1800,3,1,0)])
    struct.pack_into(e+'H',data,450,3584)
    return data


class Tests(unittest.TestCase):
    def test_header_and_endian_pairs(self):
        for om in (False,True):
            for big in (False,True):
                result=p.metadata(fixture(om,big),[])
                self.assertEqual(result['paths']['2040']['tags']['0611']['values'],[14,0])
                self.assertEqual(result['paths']['2040']['tags']['0653']['values'],[6])
                self.assertEqual(result['paths']['2050']['tags']['1800']['values'],[3584])

    def test_unknown_header_is_not_absence(self):
        data=fixture()
        data[200]=0
        self.assertEqual(p.metadata(data,[])['reason'],'unsupported_leading_header')

    def test_actual_tag_absence(self):
        result=p.metadata(fixture(),[])
        self.assertEqual(result['paths']['2040']['tags']['0620']['status'],'absent')

    def test_raw_strip_read_exclusion(self):
        with self.assertRaisesRegex(ValueError,'metadata_overlap'):
            p.metadata(fixture(),[(64,100)])

    def test_preview_directory_exclusion(self):
        data=fixture()
        struct.pack_into('<I',data,212+2+12+8,1000)
        self.assertEqual(p.metadata(data,[])['paths']['2040']['reason'],'metadata_overlap')

    def test_indirect_short_values(self):
        reader=p.Reader(b'\0'*16+b'\x01\0\x02\0\x03\0','little')
        self.assertEqual(reader.value({7:(3,3,4)},7)['status'],'ok')
        data=bytearray(32)
        struct.pack_into('<I',data,4,16)
        struct.pack_into('<3H',data,16,1,2,3)
        self.assertEqual(p.Reader(data,'little').value({7:(3,3,4)},7)['values'],[1,2,3])

    def test_prefix_lengths_and_all_zero(self):
        for zeros in (0,1,39,47,71):
            bits='0'*zeros+'1'
            bits+='0'*(-len(bits)%8)
            payload=int(bits,2).to_bytes(len(bits)//8,'big')
            self.assertEqual(p.startup_zeros(payload),zeros)
        self.assertIsNone(p.startup_zeros(b'\0'*16))


if __name__=='__main__':
    unittest.main()
