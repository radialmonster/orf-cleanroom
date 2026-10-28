"""Hand controls for row-centered fixed planar aggregates."""
import sys,unittest,random,struct,io,json,contextlib
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import token_planar_control_probe as p

class TestPlanar(unittest.TestCase):
 def test_excluded_column_contributes_to_row_mean(self):
  values=([0]*128+[1])*129;got=p.centered_energy(values,129,129)
  self.assertEqual(got,{"squared_centered_numerator_sum":(128*128)**2,"blocks":1,"block_rows":1,"block_columns":1,"excluded_rows":1,"excluded_columns":1})
 def test_constant_rows_and_row_shift_invariance(self):
  values=[r for r in range(128) for c in range(256)]
  self.assertEqual(p.centered_energy(values,256,128)["squared_centered_numerator_sum"],0)
  base=[(c%11) for r in range(128) for c in range(257)]
  shifted=[v+i//257 for i,v in enumerate(base)]
  self.assertEqual(p.centered_energy(base,257,128),p.centered_energy(shifted,257,128))
 def test_multiple_blocks_square_before_sum(self):
  values=([1]*128+[0]*129)*256;got=p.centered_energy(values,257,256)
  n1=128*128*(257-128);n2=-128*128*128
  self.assertEqual(got["blocks"],4)
  self.assertEqual(got["squared_centered_numerator_sum"],2*(n1*n1+n2*n2))
  self.assertNotEqual(got["squared_centered_numerator_sum"],(2*(n1+n2))**2)
 def test_zero_null_and_escape_accounting(self):
  out=p.measure([(17,0)]*(128*128),128,128,"1")
  self.assertEqual(out["escape_count"],128*128)
  for cell in out["mappings"].values():
   self.assertTrue(all(x is None for x in cell["real_over_mean_null"].values()))
 def test_shuffle_independent(self):
  tokens=[(0,i%32) for i in range(129*128)];out=p.measure(tokens,129,128,"1");values=[s for q,s in tokens]
  for mode in ("within-row","global"):
   for rep,entry in enumerate(out["mappings"]["u"]["nulls"][mode]):
    a=values[:];rng=random.Random(20262021+rep)
    spans=[(i,i+129) for i in range(0,len(a),129)] if mode=="within-row" else [(0,len(a))]
    for lo,hi in spans:
     for i in range(hi-1,lo,-1):
      j=lo+rng.randrange(i-lo+1);a[i],a[j]=a[j],a[i]
    numerator=sum(129*sum(a[r*129:r*129+128])-128*sum(a[r*129:r*129+129]) for r in range(128))
    self.assertEqual(entry["energy"]["squared_centered_numerator_sum"],numerator*numerator)
 def test_short(self):
  with self.assertRaises(ValueError):p.centered_energy([0]*100,128,128)
 def test_tiff_cli_and_shortfall(self):
  bits="100101"*(128*300);payload=int(bits,2).to_bytes(len(bits)//8,"big")
  def tiff(raw):
   tags=((256,128),(257,100),(273,62),(279,len(raw)))
   return b"II"+struct.pack("<HIH",42,8,len(tags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in tags)+struct.pack("<I",0)+raw
  original=Path.read_bytes
  for data,expected in ((tiff(payload),0),(tiff(payload[:-1]),1)):
   def read(path):return data if str(path)=="synthetic" else original(path)
   with mock.patch.object(Path,"read_bytes",read),mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--rows","300"]),contextlib.redirect_stdout(io.StringIO()) as out,contextlib.redirect_stderr(io.StringIO()):
    self.assertEqual(p.main(),expected)
    if not expected:
     result=json.loads(out.getvalue());self.assertEqual(result["sample"]["result"]["tokens"],128*300);self.assertIn("token_planar_control_probe.py",result["source_sha256"])
if __name__=="__main__":unittest.main()
