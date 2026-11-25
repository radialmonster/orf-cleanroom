#!/usr/bin/env python3
"""Synthetic literal equality and group-column controls for #951."""
import os
import struct
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import row_group_border_inventory as p
from test_makernote_prefix_audit import fixture


class Tests(unittest.TestCase):
    def note(self,value):
        return {'status':'ok','paths':{'2040':{'status':'ok','tags':{'0612':value}}}}

    def test_scalar_equality_and_mismatch(self):
        group={'parsed_heads':7,'columns':{'2':5,'3':2}}
        self.assertEqual(p.compare(self.note({'status':'ok','values':[2]}),group)['unequal'],2)
        self.assertEqual(p.compare(self.note({'status':'ok','values':[0]}),group)['equal'],0)

    def test_unknown_absent_vector_no_heads(self):
        self.assertEqual(p.compare({'status':'unknown'},{} )['status'],'unknown_metadata')
        self.assertEqual(p.compare(self.note({'status':'absent'}),{})['status'],'absent')
        self.assertEqual(p.compare(self.note({'status':'ok','values':[1,2]}),{})['status'],'not_scalar')
        self.assertEqual(p.compare(self.note({'status':'ok','values':[0]}),{'parsed_heads':0})['status'],'no_parsed_heads')

    def test_known_group_columns_and_no_chain(self):
        for column in (1,3,8):
            width=40
            row='100000'*column+'10000000'*6+'100000'*(width-column-6)
            result=p.groups('0'*39+'1'+row*12,width,40)
            self.assertGreater(result['selected_heads'],5)
            self.assertEqual(set(result['columns']),{str(column)})
        self.assertEqual(p.groups('10'*100,40,0)['selected_heads'],0)

    def test_requested_literal_path_and_default_unchanged(self):
        data=fixture()
        struct.pack_into('<H',data,362,0x0612)
        result=p.metadata(data,[],p.TAGS)
        self.assertEqual(result['paths']['2040']['tags']['0612']['values'],[14,0])
        self.assertEqual(p.metadata(fixture(),[])['paths']['2040']['tags']['0653']['values'],[6])


if __name__=='__main__': unittest.main()
