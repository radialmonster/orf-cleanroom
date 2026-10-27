import itertools
import contextlib
import io
import json
from unittest import mock
import os
import random
import sys
import unittest
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import code_family_screen as reference
import token_framing_probe as framing
import whole_family_null as tool


class WholeFamilyTests(unittest.TestCase):
    def test_all_byte_strings_and_offsets(self):
        for a in range(256):
            buf=bytes([a]); bits=format(a,'08b')
            for family,k in tool.FAMILIES:
                for pos in range(9):
                    self.assertEqual(tool.next_end(buf,pos,family,k),reference.next_end(bits,pos,family,k),(bits,pos,family,k))
                self.assertEqual(tool.count(buf,family,k),reference.count_family(bits,family,k,len(bits))[1])

    def test_long_unary_and_truncation(self):
        for bits in ('0'*47+'1'+'0'*32,'0'*130+'1'+'0'*6,'1'*64,'0'*64,
                     '00101011'*8,'00110011'*8):
            bits += '0' * (-len(bits)%8)
            buf=int(bits,2).to_bytes(len(bits)//8,'big')
            for family,k in tool.FAMILIES:
                self.assertEqual(tool.count(buf,family,k),reference.count_family(bits,family,k,len(bits))[1])

    def test_delta_exact_fit_and_one_short(self):
        self.assertEqual(tool.next_end(bytes([0b00000100]),4,'elias_delta',0),8)
        self.assertIsNone(tool.next_end(bytes([0b00000010]),5,'elias_delta',0))

    def test_fibonacci_cross_byte(self):
        self.assertEqual(tool.next_end(bytes([1,128]),0,'fibonacci',0),9)
        self.assertIsNone(tool.next_end(bytes([1]),0,'fibonacci',0))

    def test_cli_snapshot_and_zero_count(self):
        out=io.StringIO()
        with mock.patch('builtins.open',mock.mock_open(read_data=b'container')), \
             mock.patch.object(tool.orf_tokens,'locate_data',return_value=(1,1,b'\x00')), \
             contextlib.redirect_stdout(out):
            self.assertEqual(tool.main(['input']),0)
        r=json.loads(out.getvalue())
        self.assertEqual(r['sha256'],__import__('hashlib').sha256(b'container').hexdigest())
        self.assertEqual(r['models']['real']['elias_delta_k0']['count'],0)
        self.assertEqual(r['models']['real']['elias_delta_k0']['residual_bits'],8)

    def test_null_draw_order(self):
        for n in (0,1,7,33):
            for p in (0,.13,.5,1):
                self.assertEqual(bytes(tool.bernoulli(n,p,20261021)),framing.bernoulli_bytes(n,p,random.Random(20261021)))


if __name__=='__main__': unittest.main()
