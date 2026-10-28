"""Synthetic phase model, rotations, hole and finite loss tests."""
import os,sys,unittest,math,random,struct,io,json,contextlib
from unittest import mock
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import token_phase3_heldout_probe as p

class PhaseTests(unittest.TestCase):
 def test_planted_phase_transition_and_rotations(self):
  p.BAND=256;tokens=[]
  for base in range(0,512,128):
   bits=[0,1,0]
   for i in range(3,128):bits.append(bits[i-3]^int((base+i)%3==1))
   tokens.extend([(x,x) for x in bits])
  r=p.measure(tokens,1)["fields"]["q_positive"];rot=r["rotations"]
  self.assertGreater(rot["0"]["pool_minus_phase_lag3"],0);self.assertGreater(rot["0"]["phase_only_minus_phase_lag3"],0)
  self.assertLess(rot["0"]["scores"]["phase_lag3"]["logloss"],rot["1"]["scores"]["phase_lag3"]["logloss"]);self.assertLess(rot["0"]["scores"]["phase_lag3"]["logloss"],rot["2"]["scores"]["phase_lag3"]["logloss"])
 def test_absolute_phase_holes_and_offset(self):
  blocks,sel=p.select([(17,0)]*128+[(0,1)]*128,262144);self.assertEqual(sel["escape_omitted_blocks"],1);self.assertEqual(blocks[0][0],262272);x=p.tables(blocks,"suffix_b0",0);self.assertEqual([sum(z) for z in x["phase_only"]],[42,42,41])
 def test_uniform_ties_and_empty(self):
  train={"pooled_lag3":[[3,3] for _ in range(2)],"phase_only":[[2,2] for _ in range(3)],"phase_lag3":[[1,1] for _ in range(6)]};test={k:[row[:] for row in v] for k,v in train.items()};scores=p.losses(train,test);self.assertTrue(all(scores[k]["logloss"]==1 for k in scores))
  empty={k:[[0,0] for _ in v] for k,v in train.items()};self.assertTrue(all(p.losses(empty,test)[k]["logloss"] is None for k in scores))
 def test_manual_counts_loss_and_shuffle(self):
  blocks=[(256,[(i%3,(i*7)%32) for i in range(128)])];r=p.tables(blocks,"q_positive",1);manual=[[0,0] for _ in range(6)]
  for i in range(3,128):
   bit=lambda j:int(blocks[0][1][j][0]>0);manual[2*((256+i+1)%3)+bit(i-3)][bit(i)]+=1
  self.assertEqual(r["phase_lag3"],manual)
  s=p.losses(r,r)["phase_lag3"];terms=[]
  for a in r["phase_lag3"]:
   for v,count in enumerate(a):terms.extend([-math.log2((count+.5)/(sum(a)+1))]*count)
  self.assertAlmostEqual(s["logloss"],sum(terms)/len(terms),places=12)
  for rep in range(16):
   values=blocks[0][1][:];rng=random.Random(20261021+rep)
   for i in range(127,0,-1):j=rng.randrange(i+1);values[i],values[j]=values[j],values[i]
   self.assertEqual(p.shuffle(blocks,20261021+rep),[(256,values)])
 def test_tiff_band2_gap_and_cli(self):
  p.BAND=256;bits=("1"+"00101")*256+("01"+"00110")*256+("001"+"00111")*256;payload=int(bits,2).to_bytes(len(bits)//8,"big");tags=((256,25),(257,1),(273,62),(279,len(payload)))
  data=b"II"+struct.pack("<HIH",42,8,len(tags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in tags)+struct.pack("<I",0)+payload
  result=p.report("1","public",data,2);self.assertEqual((result["requested_tokens"],result["returned_tokens"],result["bits_consumed"]),(768,768,5376));b=result["result"]["fields"]["suffix_b0"];self.assertEqual(sum(r[1] for r in b["train"]["phase_only"]),250);self.assertEqual(sum(r[1] for r in b["rotations"]["0"]["test"]["phase_only"]),250)
  tokens=[(0,5)]*256+[(17,0)]*256+[(2,7)]*256;self.assertEqual(p.measure(tokens,2),result["result"])
  original=open
  def fake(path,*args,**kwargs):return io.BytesIO(data) if path=="synthetic" else original(path,*args,**kwargs)
  with mock.patch("builtins.open",side_effect=fake):
   out=io.StringIO()
   with mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--test-band","2"]),contextlib.redirect_stdout(out):self.assertEqual(p.main(),0)
   self.assertIn("token_phase3_heldout_probe.py",json.loads(out.getvalue())["source_sha256"])
   shorter=payload[:-100];shorttags=((256,25),(257,1),(273,62),(279,len(shorter)));short=b"II"+struct.pack("<HIH",42,8,len(shorttags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in shorttags)+struct.pack("<I",0)+shorter
   def fake_short(path,*args,**kwargs):return io.BytesIO(short) if path=="synthetic" else original(path,*args,**kwargs)
   out=io.StringIO()
   with mock.patch("builtins.open",side_effect=fake_short),mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--test-band","2"]),contextlib.redirect_stdout(out):self.assertEqual(p.main(),1)
   self.assertGreater(json.loads(out.getvalue())["sample"]["prefix_shortfall"],0)
 def test_no_eligible_and_all_band_offsets(self):
  p.BAND=256;tokens=[(17,0)]*256+[(0,1)]*512
  for band in (1,2):
   r=p.measure(tokens,band);self.assertEqual(r["train_selection"]["retained_blocks"],0)
   for field in r["fields"].values():
    for rotation in field["rotations"].values():self.assertTrue(all(v["logloss"] is None for v in rotation["scores"].values()))
  for offset in (0,256,512):
   blocks,_=p.select([(0,0)]*128,offset);t=p.tables(blocks,"q_positive",0);expected=[sum(1 for i in range(3,128) if (offset+i)%3==j) for j in range(3)];self.assertEqual([sum(x) for x in t["phase_only"]],expected)
if __name__=="__main__":unittest.main()
