"""Synthetic checks for fixed-support nominal-row energy."""
import sys,unittest,random,struct,io,json,contextlib
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import token_row_dpcm_probe as probe

class TestEnergy(unittest.TestCase):
 def test_hand_counts_and_common_support(self):
  values=list(range(20));got=probe.energies(values,4)
  self.assertEqual(set(got),{"3","4","5","7","8","9"})
  for lag,item in got.items():
   self.assertEqual(item,{"pairs":11,"squared_error_sum":11*int(lag)**2})
 def test_periodic_and_decoy(self):
  values=[i%4 for i in range(24)];got=probe.energies(values,4)
  self.assertEqual(got["4"]["squared_error_sum"],0)
  self.assertGreater(got["3"]["squared_error_sum"],0)
  self.assertGreater(got["5"]["squared_error_sum"],0)
 def test_mapping_and_seed_controls(self):
  tokens=[(i%3,i%32) for i in range(24)];out=probe.measure(tokens,4,6,"1993")
  self.assertEqual(out["target_start"],9);self.assertEqual(out["target_end"],24)
  for name,item in out["mappings"].items():
   values=[probe.map_value(q,s,name) for q,s in tokens]
   self.assertEqual(item["real"],probe.energies(values,4))
   for mode,runs in item["nulls"].items():
    self.assertEqual(len(runs),4)
    self.assertEqual([r["seed"] for r in runs],list(range(runs[0]["seed"],runs[0]["seed"]+4)))
    for r in runs:
     self.assertTrue(all(e["pairs"]==15 for e in r["energies"].values()))
 def test_reject_short(self):
  with self.assertRaises(ValueError):probe.measure([(0,0)]*11,4,3,"1993")
 def test_half_offsets_even_odd_and_default(self):
  for w in (6,7):
   values=list(range(w*4));n=len(values)-(2*w+1);h=w//2
   got=probe.energies(values,w,"half")
   self.assertEqual(set(got),{str(h-1),str(h),str(h+1)})
   for lag,item in got.items():self.assertEqual(item,{"pairs":n,"squared_error_sum":n*int(lag)**2})
   self.assertEqual(probe.energies(values,w),probe.energies(values,w,"row"))
  with self.assertRaises(ValueError):probe.energies(list(range(12)),3,"half")
 def test_half_zero_null_and_fixed_support(self):
  out=probe.measure([(0,7)]*28,7,4,"1","half")
  self.assertEqual((out["target_start"],out["target_end"]),(15,28))
  for cell in out["mappings"].values():
   self.assertEqual(set(cell["real"]),{"2","3","4"})
   self.assertTrue(all(x["pairs"]==13 for x in cell["real"].values()))
   for ratios in cell["real_over_mean_null"].values():self.assertTrue(all(x is None for x in ratios.values()))
 def test_zero_null_and_escape_retention(self):
  out=probe.measure([(17,0)]*24,4,6,"1")
  self.assertEqual(out["escape_count"],24)
  for item in out["mappings"].values():
   for ratios in item["real_over_mean_null"].values():self.assertTrue(all(value is None for value in ratios.values()))
 def test_independent_shuffle_and_energy(self):
  tokens=[(i%3,(i*7)%32) for i in range(24)];out=probe.measure(tokens,4,6,"1")
  values=[32*q+s for q,s in tokens]
  for mode in ("within-row","global"):
   for rep,entry in enumerate(out["mappings"]["u"]["nulls"][mode]):
    rng=random.Random(20262021+rep);v=values[:]
    ranges=[(i,i+4) for i in range(0,24,4)] if mode=="within-row" else [(0,24)]
    for lo,hi in ranges:
     for i in range(hi-1,lo,-1):
      j=lo+rng.randrange(i-lo+1);v[i],v[j]=v[j],v[i]
    for lag in (3,4,5,7,8,9):
     expected=sum((v[i]-v[i-lag])**2 for i in range(9,24))
     self.assertEqual(entry["energies"][str(lag)]["squared_error_sum"],expected)
 def test_tiff_cli_and_shortfall(self):
  bits="100101"*1200;payload=int(bits,2).to_bytes(len(bits)//8,"big")
  def tiff(raw):
   tags=((256,4),(257,100),(273,62),(279,len(raw)))
   return b"II"+struct.pack("<HIH",42,8,len(tags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in tags)+struct.pack("<I",0)+raw
  original=Path.read_bytes
  for data,expected in ((tiff(payload),0),(tiff(payload[:-1]),1)):
   def read(path):return data if str(path)=="synthetic" else original(path)
   with mock.patch.object(Path,"read_bytes",read),mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--rows","300"]),contextlib.redirect_stdout(io.StringIO()) as out,contextlib.redirect_stderr(io.StringIO()):
    self.assertEqual(probe.main(),expected)
    if not expected:
     result=json.loads(out.getvalue());self.assertEqual(result["sample"]["result"]["tokens"],1200);self.assertIn("token_row_dpcm_probe.py",result["source_sha256"])
  def read(path):return tiff(payload) if str(path)=="synthetic" else original(path)
  with mock.patch.object(Path,"read_bytes",read),mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--rows","300","--offset-family","half"]),contextlib.redirect_stdout(io.StringIO()) as out:
   self.assertEqual(probe.main(),0);result=json.loads(out.getvalue());self.assertEqual(result["offset_family"],"half");self.assertEqual(set(result["sample"]["result"]["mappings"]["u"]["real"]),{"1","2","3"})

if __name__=="__main__":unittest.main()
