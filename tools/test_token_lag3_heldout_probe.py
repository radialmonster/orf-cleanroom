"""Synthetic frozen-table, held-out and null controls."""
import os,sys,unittest,math,random,struct,io,json,contextlib
from unittest import mock
from collections import Counter
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import token_lag3_heldout_probe as p

class HeldoutTests(unittest.TestCase):
 def test_explicit_counts_kt_and_unseen(self):
  train={"0":[[3,1]],"2":[[3,1],[0,0],[0,0],[0,0]],"3":[[3,1]]+[[0,0] for _ in range(7)]};test={"0":[[1,1]],"2":[[1,0],[0,1],[0,0],[0,0]],"3":[[1,0],[0,1]]+[[0,0] for _ in range(6)]};r=p.losses(train,test);self.assertEqual(r["2"]["unseen_test"],1);self.assertAlmostEqual(r["2"]["logloss"],(-math.log2(3.5/5)-math.log2(.5))/2);self.assertEqual(r["gain_order2_minus_order3"],0)
  empty={"0":[[0,0]],"2":[[0,0] for _ in range(4)],"3":[[0,0] for _ in range(8)]};self.assertIsNone(p.losses(empty,test)["gain_order2_minus_order3"]);self.assertIsNone(p.losses(train,empty)["gain_order2_minus_order3"])
 def test_common_positions_and_manual_tables(self):
  blocks=[[(i%3,(i*5)%32) for i in range(128)],[(i%2,(i*7)%32) for i in range(128)]]
  for field in ("q_positive","suffix_b0"):
   tables=p.tables(blocks,field);get=(lambda x:int(x[0]>0)) if field=="q_positive" else (lambda x:x[1]%2)
   for order in (0,2,3):
    c=Counter()
    for b in blocks:
     for i in range(3,128):
      ctx=sum(get(b[i-k])*(1<<(order-k)) for k in range(1,order+1));c[ctx,get(b[i])]+=1
    assert sum(c.values())==250
    self.assertEqual(tables[str(order)],[[c[i,v] for v in range(2)] for i in range(1<<order)])
 def test_null_shuffle_seed_and_omission(self):
  p.BAND=256;rows=[[(i%3,i%32) for i in range(128)],[(17,0)]*128,[(i%2,(i*3)%32) for i in range(128)],[(i%4,(i*7)%32) for i in range(128)]];tokens=sum(rows,[]);r=p.measure(tokens,1);self.assertEqual((r["train_selection"]["retained_blocks"],r["test_selection"]["retained_blocks"]),(1,2))
  for rep in range(16):
   for field in ("q_positive","suffix_b0"):
    a=[rows[0][:]];b=[rows[2][:],rows[3][:]]
    for blocks,seed in ((a,20261021+rep),(b,20361021+rep)):
     rng=random.Random(seed)
     for block in blocks:
      for i in range(127,0,-1):j=rng.randrange(i+1);block[i],block[j]=block[j],block[i]
    n=r["fields"][field]["nulls"][rep];self.assertEqual(n["train"],p.tables(a,field));self.assertEqual(n["test"],p.tables(b,field))
 def test_planted_third_lag_positive_gain(self):
  seq=[int(c) for c in "00010111"*16];rows=[[(v,v) for v in seq] for _ in range(2)];train=p.tables(rows,"q_positive");test=p.tables(rows,"q_positive");scores=p.losses(train,test);self.assertGreater(scores["gain_order2_minus_order3"],0.5)
 def test_tiff_band2_and_cli_shortfall(self):
  p.BAND=256;bits=("1"+"00101")*256+("01"+"00110")*256+("001"+"00111")*256;payload=int(bits,2).to_bytes(len(bits)//8,"big");tags=((256,25),(257,1),(273,62),(279,len(payload)))
  data=b"II"+struct.pack("<HIH",42,8,len(tags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in tags)+struct.pack("<I",0)+payload
  r=p.report("1","public",data,2);self.assertEqual((r["requested_tokens"],r["returned_tokens"],r["bits_consumed"]),(768,768,5376));self.assertEqual(r["result"]["fields"]["q_positive"]["scores"]["0"]["test_total"],250);self.assertEqual(r["result"]["fields"]["suffix_b0"]["train"]["0"],[[0,250]]);self.assertEqual(r["result"]["fields"]["suffix_b0"]["test"]["0"],[[0,250]])
  original=open
  def fake(path,*args,**kwargs):return io.BytesIO(data) if path=="synthetic" else original(path,*args,**kwargs)
  with mock.patch("builtins.open",side_effect=fake):
   out=io.StringIO()
   with mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--test-band","2"]),contextlib.redirect_stdout(out):self.assertEqual(p.main(),0)
   self.assertIn("token_lag3_heldout_probe.py",json.loads(out.getvalue())["source_sha256"])
   shortpayload=payload[:-100];shorttags=((256,25),(257,1),(273,62),(279,len(shortpayload)));short=b"II"+struct.pack("<HIH",42,8,len(shorttags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in shorttags)+struct.pack("<I",0)+shortpayload;out=io.StringIO()
   def truncated(path,*args,**kwargs):return io.BytesIO(short) if path=="synthetic" else original(path,*args,**kwargs)
   with mock.patch("builtins.open",side_effect=truncated),mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--test-band","2"]),contextlib.redirect_stdout(out):self.assertEqual(p.main(),1)
   self.assertGreater(json.loads(out.getvalue())["sample"]["prefix_shortfall"],0)
 def test_independent_literal_test_loss(self):
  train={"0":[[7,3]],"2":[[5,1],[0,0],[2,2],[0,0]],"3":[[5,1],[0,0],[0,0],[0,0],[2,2],[0,0],[0,0],[0,0]]};test={"0":[[3,2]],"2":[[1,1],[1,0],[1,1],[0,0]],"3":[[1,1],[1,0],[0,0],[0,0],[1,1],[0,0],[0,0],[0,0]]};scores=p.losses(train,test)
  for order in (0,2,3):
   terms=[]
   for ctx,row in enumerate(test[str(order)]):
    for value,count in enumerate(row):
     prob=(train[str(order)][ctx][value]+.5)/(sum(train[str(order)][ctx])+1);terms.extend([-math.log2(prob)]*count)
   self.assertAlmostEqual(scores[str(order)]["logloss"],sum(terms)/len(terms),places=12)
 def test_band2_ignores_middle_band(self):
  p.BAND=256;a=[(i%3,i%32) for i in range(768)];b=a[:256]+[(17,0)]*256+a[512:];x=p.measure(a,2);y=p.measure(b,2);self.assertEqual(x,y);self.assertEqual(x["train_token_range"],[0,256]);self.assertEqual(x["test_token_range"],[512,768])
if __name__=="__main__":unittest.main()
