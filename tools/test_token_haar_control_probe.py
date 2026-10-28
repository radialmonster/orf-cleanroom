"""Synthetic fixed-support Haar control tests."""
import sys,unittest,random,struct,io,json,contextlib
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import token_haar_control_probe as p

class TestHaar(unittest.TestCase):
 def test_planted_directions_and_identity(self):
  for values,expected in (([1,0,1,0],(4,0,0)),([1,1,0,0],(0,4,0)),([1,0,0,1],(0,0,4))):
   result=p.haar_energy(values,2,2);self.assertEqual(tuple(result[k] for k in ("H","V","D")),expected)
  rng=random.Random(31)
  for _ in range(200):
   a=[rng.randrange(-20,21) for i in range(4)];r=p.haar_energy(a,2,2)
   self.assertEqual(sum(r[k] for k in ("H","V","D")),4*sum(x*x for x in a)-sum(a)**2)
 def test_edges_and_zero_null(self):
  r=p.measure([(0,7)]*15,3,5,"1")
  for cell in r["mappings"].values():
   self.assertEqual((cell["real"]["blocks"],cell["real"]["excluded_rows"],cell["real"]["excluded_columns"]),(2,1,1))
   for ratios in cell["real_over_mean_null"].values():self.assertTrue(all(x is None for x in ratios.values()))
 def test_independent_shuffle_and_energy(self):
  tokens=[(0,i%32) for i in range(24)];r=p.measure(tokens,4,6,"1");values=[s for q,s in tokens]
  for mode in ("within-row","global"):
   for rep,e in enumerate(r["mappings"]["u"]["nulls"][mode]):
    v=values[:];rng=random.Random(20262021+rep);spans=[(i,i+4) for i in range(0,24,4)] if mode=="within-row" else [(0,24)]
    for lo,hi in spans:
     for i in range(hi-1,lo,-1):j=lo+rng.randrange(i-lo+1);v[i],v[j]=v[j],v[i]
    sums=[0,0,0]
    for row in range(0,6,2):
     for col in range(0,4,2):
      a,b,c,d=(v[row*4+col],v[row*4+col+1],v[(row+1)*4+col],v[(row+1)*4+col+1])
      for i,x in enumerate((a-b+c-d,a+b-c-d,a-b-c+d)):sums[i]+=x*x
    self.assertEqual(tuple(e["energy"][k] for k in ("H","V","D")),tuple(sums))
 def test_tiff_cli_and_shortfall(self):
  bits="100101"*1200;payload=int(bits,2).to_bytes(len(bits)//8,"big")
  def tiff(raw):
   tags=((256,4),(257,100),(273,62),(279,len(raw)))
   return b"II"+struct.pack("<HIH",42,8,len(tags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in tags)+struct.pack("<I",0)+raw
  original=Path.read_bytes
  for data,expected in ((tiff(payload),0),(tiff(payload[:-1]),1)):
   def read(path):return data if str(path)=="synthetic" else original(path)
   with mock.patch.object(Path,"read_bytes",read),mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--rows","300"]),contextlib.redirect_stdout(io.StringIO()) as out,contextlib.redirect_stderr(io.StringIO()):
    self.assertEqual(p.main(),expected)
    if not expected:self.assertIn("token_haar_control_probe.py",json.loads(out.getvalue())["source_sha256"])
if __name__=="__main__":unittest.main()
