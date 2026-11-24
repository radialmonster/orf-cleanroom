#!/usr/bin/env python3
"""Original legacy directory fixtures, not camera pixel expectations."""
import os
import struct
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from legacy_maker_directory import directory


def fixture(version=1,big=False,parent=False):
    data=bytearray(512)
    e='>' if big else '<'
    data[:8]=(b'MMOR' if big else b'IIRO')+struct.pack(e+'I',8)
    def ifd(at,rows):
        struct.pack_into(e+'H',data,at,len(rows))
        for i,row in enumerate(rows): struct.pack_into(e+'HHII',data,at+2+12*i,*row)
    ifd(8,[(0x8769,4,1,64)])
    ifd(64,[(0x927c,7,128,200)])
    data[200:208]=b'OLYMP\0'+bytes([version,0])
    ifd(208,[(0x2040 if parent else 0x0100,13,1,80)])
    return data


class Tests(unittest.TestCase):
    def test_versions_orders_and_literal_absence(self):
        for version in (1,2):
            for big in (False,True):
                r=directory(fixture(version,big),[])
                self.assertEqual(r['entries'],1)
                self.assertEqual(r['directory_end'],26)
                self.assertEqual(r['paths']['2040'],'absent_top_entry')
                self.assertEqual(r['next_ifd'],0)

    def test_present_is_not_absent_or_traversed(self):
        self.assertEqual(directory(fixture(parent=True),[])['paths']['2040'],'present_uninterpreted')

    def test_unknown_header_stays_unknown(self):
        self.assertEqual(directory(fixture(3),[])['status'],'unknown')

    def test_truncated_directory_and_raw_overlap(self):
        data=fixture()
        struct.pack_into('<H',data,208,100)
        with self.assertRaisesRegex(ValueError,'bounds'): directory(data,[])
        with self.assertRaisesRegex(ValueError,'metadata_overlap'): directory(fixture(),[(200,300)])


if __name__=='__main__': unittest.main()
