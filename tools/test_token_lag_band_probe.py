"""Synthetic band boundaries, exclusions, ranks and legacy control parity."""
import os,sys,unittest,random,math,struct,io,json,contextlib
from collections import Counter
from unittest import mock
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import token_lag_band_probe as p
import token_lag_probe as legacy

class BandTests(unittest.TestCase):
 def test_disjoint_blocks_and_legacy_measure(self):
  p.BAND=256
  tokens=[(0,(i*7)%32) for i in range(768)];tokens[128]=(17,0)
  out=p.summarize(tokens,[0,1,2]);self.assertEqual([x["start_token"] for x in out],[0,256,512])
  self.assertEqual([x["selection"]["retained_blocks"] for x in out],[1,2,2]);self.assertEqual(out[0]["selection"]["escape_omitted_blocks"],1)
  for i,x in enumerate(out):
   blocks,_=legacy.select_blocks(tokens[i*256:(i+1)*256]);self.assertEqual(x["lags"],legacy.measure(blocks))
   self.assertEqual([v["pairs"] for v in x["lags"]],[(128-lag)*len(blocks) for lag in range(1,6)])
 def test_zero_pairs_and_ties(self):
  p.BAND=256
  empty=p.summarize([(17,0)]*256,[0])[0];self.assertTrue(all(v is None for v in empty["rankings"].values()))
  const=p.summarize([(0,0)]*256,[0])[0];self.assertEqual(const["rankings"]["q_positive_observed"]["maximum_lags"],[1,2,3,4,5]);self.assertEqual(const["rankings"]["q_positive_excess"]["maximum_lags"],[1,2,3,4,5])
 def test_shortfall(self):
  p.BAND=256
  x=p.summarize([(0,1)]*300,[1])[0];self.assertEqual((x["tokens_returned"],x["shortfall"],x["selection"]["tail_tokens"]),(44,212,44))
 def test_literal_counts_mi_and_permutation(self):
  p.BAND=128;tokens=[(i%3,(i*7)%32) for i in range(128)];observed=p.summarize(tokens,[0])[0]
  for perm in range(-1,16):
   data=tokens[:]
   if perm>=0:
    rng=random.Random(20261021+perm)
    for i in range(len(data)-1,0,-1):
     j=rng.randrange(i+1);data[i],data[j]=data[j],data[i]
   for lag,cell in enumerate(observed["lags"],1):
    for field in ("q_positive","low3"):
     get=(lambda t:int(t[0]>0)) if field=="q_positive" else (lambda t:t[1]%8)
     pairs=Counter((get(data[i]),get(data[i+lag])) for i in range(128-lag));n=sum(pairs.values());left=Counter();right=Counter()
     for (a,b),count in pairs.items():left[a]+=count;right[b]+=count
     mi=sum(c/n*math.log2(c*n/(left[a]*right[b])) for (a,b),c in pairs.items())
     if perm<0:
      table=cell[field+"_counts"];self.assertEqual(pairs,Counter({(a,b):v for a,row in enumerate(table) for b,v in enumerate(row) if v}));self.assertAlmostEqual(cell[field+"_mi_bits"],mi,places=12)
     else:self.assertAlmostEqual(cell[field+"_permuted_mi_bits"][perm],mi,places=12)
 def test_complete_nonzero_band_report(self):
  p.BAND=256
  bits=("1"+"00101")*256+("01"+"01001")*256;payload=int(bits,2).to_bytes(len(bits)//8,"big")
  tags=((256,25),(257,1),(273,62),(279,len(payload)))
  data=b"II"+struct.pack("<HIH",42,8,len(tags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in tags)+struct.pack("<I",0)+payload
  r=p.report("1","public",data,[1]);band=r["bands"][0]
  self.assertEqual((r["requested_tokens"],r["returned_tokens"],r["bits_consumed"]),(512,512,3328))
  self.assertEqual((band["start_bit"],band["end_bit"],band["tokens_returned"]),(1536,3328,256))
  for cell in band["lags"]:
   self.assertEqual(cell["q_positive_counts"][1][1],cell["pairs"]);self.assertEqual(cell["low3_counts"][1][1],cell["pairs"])
 def test_report_cli_tiff_and_legacy(self):
  p.BAND=256;legacy.LIMIT=256
  bits=("1"+"00101")*256;payload=int(bits,2).to_bytes(len(bits)//8,"big")
  def fixture(payload):
   tags=((256,25),(257,1),(273,62),(279,len(payload)))
   return b"II"+struct.pack("<HIH",42,8,len(tags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in tags)+struct.pack("<I",0)+payload
  data=fixture(payload);full=p.report("1","public",data,[0]);self.assertEqual(full["bits_consumed"],1536);self.assertEqual((full["bands"][0]["start_bit"],full["bands"][0]["end_bit"]),(0,1536))
  original=open
  def fake(path,*args,**kwargs):return io.BytesIO(data) if path=="synthetic" else original(path,*args,**kwargs)
  with mock.patch("builtins.open",side_effect=fake):
   old=legacy.report("1","public","synthetic");self.assertEqual(full["bands"][0]["selection"],old["selection"]);self.assertEqual(full["bands"][0]["lags"],old["lags"])
   for bands,status in ((["0"],0),(["0","1"],1)):
    out=io.StringIO()
    with mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--bands"]+bands),contextlib.redirect_stdout(out):
     self.assertEqual(p.main(),status)
    doc=json.loads(out.getvalue());self.assertIn("token_lag_band_probe.py",doc["source_sha256"]);self.assertEqual(doc["sample"]["prefix_shortfall"],0 if status==0 else 256)
if __name__=="__main__":unittest.main()
