"""Synthetic exact support and mixture identity tests."""
import sys,unittest,json,io,contextlib
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import b4_q_mixture_probe as p

def rows():return [[[0]*16,[0]*16] for _ in range(17)]
def samples():
 result=[]
 for ident,sha in p.IDS.items():
  fields={}
  for name,width in (('low3',8),('low4',16)):
   strata=[]
   for q in range(17):
    hist=[[0]*width for _ in range(2)]
    if q==0:hist[0][0]=hist[1][0]=131072
    strata.append({'q':q,'b4_rows_value_columns':hist})
   fields[name]={'strata':strata}
  result.append({'pixls_id':ident,'sha256':sha,'requested_tokens':262144,'returned_tokens':262144,'token_shortfall':0,'statistics':{'ordinary_tokens':262144,'escape_tokens_omitted':0,'q_stratified_fields':fields}})
 return result
class TestMixture(unittest.TestCase):
 def test_simpson_reversal_and_fixed_support(self):
  r=rows();r[0][0][0]=10;r[0][1][1]=90;r[1][0][10]=90;r[1][1][11]=10
  for q in range(2,9):r[q][0][0]=r[q][1][0]=1
  out=p.decompose(r)
  self.assertEqual((out['pooled'],out['within'],out['composition'],out['outside']),('-700/107','100/107','-800/107','0'))
 def test_outside_remainder_and_unequal_totals(self):
  r=rows()
  for q in range(9):r[q][0][0]=1;r[q][1][1]=2
  r[9][0][3]=7;r[10][1][8]=4
  out=p.decompose(r)
  from fractions import Fraction
  self.assertNotEqual(out['outside'],'0');self.assertEqual(Fraction(out['pooled']),sum(Fraction(out[k]) for k in ('within','composition','outside')))
 def test_missing_and_empty(self):
  r=rows();out=p.decompose(r);self.assertEqual(out['totals'],[0,0]);self.assertEqual(out['missing_support'],list(range(9)));self.assertIsNone(out['pooled'])
  for q in range(8):r[q][0][0]=r[q][1][0]=1
  self.assertEqual(p.decompose(r)['missing_support'],[8]);self.assertIsNone(p.decompose(r)['within'])
 def test_identity_counts_and_cli(self):
  data=samples();out=p.summarize(data);self.assertEqual(out['support_q'],list(range(9)));self.assertEqual(out['samples']['241']['low4']['missing_support'],list(range(1,9)))
  data[0]['sha256']='0'*64
  with self.assertRaises(ValueError):p.summarize(data)
  data=samples();data[0]['statistics']['ordinary_tokens']-=1
  with self.assertRaises(ValueError):p.summarize(data)
  data=samples();low=data[0]['statistics']['q_stratified_fields']['low3']['strata'][0]['b4_rows_value_columns'][0];low[0]-=1;low[1]+=1
  with self.assertRaises(ValueError):p.summarize(data)
  raw=json.dumps({'samples':samples(),'failures':[]}).encode();original=Path.read_bytes
  def read(path):return raw if str(path)=='synthetic' else original(path)
  with mock.patch.object(Path,'read_bytes',read),mock.patch.object(sys,'argv',['probe','synthetic']),contextlib.redirect_stdout(io.StringIO()) as stream:
   self.assertEqual(p.main(),0);result=json.loads(stream.getvalue());self.assertEqual(len(result['input_sha256']),64);self.assertEqual(len(result['source_sha256']),64)
if __name__=='__main__':unittest.main()
