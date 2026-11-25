"""Generated zero-run and capped candidate boundary checks."""
from bisect import bisect_left
from unittest import TestCase,main,mock
import os,sys
import random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import motif_escape_support as p

def pack(bits):
    bits+='0'*(-len(bits)%8)
    return bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8))

class Tests(TestCase):
    def test_independent_random_run_census(self):
        rng=random.Random(197)
        for _ in range(100):
            bits=''.join(str(rng.randrange(2)) for _ in range(300))
            bits=bits[:100]+'1'+'0'*12+'1'+bits[114:]
            expected=[]
            for i in range(1,len(bits)-1):
                if bits[i]=='0' and bits[i-1]=='1':
                    j=i
                    while j<len(bits) and bits[j]=='0':j+=1
                    if j<len(bits) and j-i>=12:expected.append((i,j))
            self.assertEqual(p.runs(bits,0),expected)
            lo,hi=40,250
            self.assertEqual(p.supported(expected,[x for x,y in expected],lo,hi),[x for x,y in expected if lo<x and y<hi])

    def test_flanks_and_maximality(self):
        bits='1'+'0'*12+'1'+'0'*11+'1'+'0'*13+'1'
        runs=p.runs(bits,0); self.assertEqual(runs,[(1,13),(26,39)])
        starts=[x for x,y in runs]
        self.assertEqual(p.supported(runs,starts,0,len(bits)),[1,26])
        self.assertEqual(p.supported(runs,starts,1,len(bits)),[26])
        self.assertEqual(p.supported(runs,starts,0,13),[])
        self.assertEqual(p.runs('0'*12+'1',0),[])
        self.assertEqual(p.runs('1'+'0'*12,0),[])

    def test_run_not_aligned_does_not_imply_escape(self):
        bits='1'+'0'*12+'1'*12
        rs=p.runs(bits,0);self.assertEqual(rs,[(1,13)])
        marks=[];p.interior(pack(bits),0,len(bits),5,True,marks)
        self.assertEqual(marks,[])

    def test_aligned_escape_differs_and_truncation_not_counted(self):
        bits='1'*6+'0'*12+'1'*12
        self.assertEqual(p.runs(bits,0),[(6,18)])
        marks=[];cap=p.interior(pack(bits),0,len(bits),5,True,marks)
        literal=p.interior(pack(bits),0,len(bits),5,False)
        self.assertEqual(marks,[6]);self.assertEqual(cap['escapes'],1)
        self.assertNotEqual((cap['endpoint'],cap['words']), (literal['endpoint'],literal['words']))
        marks=[];x='0'*12+'1'*11
        result=p.interior(pack(x),0,len(x),5,True,marks)
        self.assertEqual(result['reason'],'escape_overrun');self.assertEqual(marks,[])

    def test_no_support_skips_both_parsers(self):
        pitch=6*5240+12;end=40+400*pitch
        payload=bytes((end+7)//8);motifs=[100,100+pitch]
        with mock.patch.object(p,'motif_positions',return_value=motifs),mock.patch.object(p,'runs',return_value=[]),mock.patch.object(p,'interior') as reader:
            result=p.measure(payload,5240)
        self.assertEqual(result['eligible_edges'],1)
        self.assertEqual(result['run_bearing_edges'],0)
        self.assertEqual(result['status'],'no_run_bearing_edge')
        reader.assert_not_called()

if __name__=='__main__':main()
