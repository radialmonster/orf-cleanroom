"""Synthetic conditional-information and fixed-block controls."""
import os,sys,unittest,math,random,struct,io,json,contextlib
from unittest import mock
from collections import Counter
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import token_lag3_conditional_probe as p

class ConditionalTests(unittest.TestCase):
 def test_uniform_constant_xor(self):
  uniform=[[[1,1],[1,1]] for _ in range(4)];x=p.scores(uniform);self.assertEqual(x["pairs"],16);self.assertEqual(x["contexts"],[4]*4);self.assertEqual(x["conditional_mi"],0);self.assertEqual(x["unconditional_mi"],0)
  constant=[[[0,0],[0,0]] for _ in range(4)];constant[0][0][0]=9;self.assertEqual(p.scores(constant)["conditional_mi"],0)
  xor=[[[0,0],[0,0]] for _ in range(4)]
  for z in range(4):
   for y in range(2):xor[z][y^(z%2)][y]=1
  y=p.scores(xor);self.assertAlmostEqual(y["conditional_mi"],1);self.assertAlmostEqual(y["unconditional_mi"],0)
  self.assertIsNone(p.scores([[[0,0],[0,0]] for _ in range(4)])["conditional_mi"])
 def test_first_order_markov_conditional_zero(self):
  table=[[[0,0],[0,0]] for _ in range(4)]
  for a in range(2):
   for b in range(2):
    for c in range(2):
     for d in range(2):table[2*c+b][d][a]+=(3 if a==b else 1)*(3 if b==c else 1)*(3 if c==d else 1)
  scores=p.scores(table);self.assertEqual(scores["pairs"],128);self.assertAlmostEqual(scores["conditional_mi"],0,places=12);self.assertGreater(scores["unconditional_mi"],0)
 def test_independent_entropy_identity(self):
  rng=random.Random(293);table=[[[rng.randrange(6) for _ in range(2)] for _ in range(2)] for _ in range(4)];n=sum(v for z in table for row in z for v in row)
  def h(values):return -sum(v/n*math.log2(v/n) for v in values if v)
  hz=h([sum(map(sum,z)) for z in table]);hxz=h([sum(z[x]) for z in table for x in range(2)]);hyz=h([sum(z[x][y] for x in range(2)) for z in table for y in range(2)]);hxyz=h([v for z in table for row in z for v in row]);self.assertAlmostEqual(p.scores(table)["conditional_mi"],hxz+hyz-hz-hxyz,places=12)
 def test_pairs_omissions_and_manual_permutations(self):
  a=[(i%3,(i*7)%32) for i in range(128)];bad=[(17,0)]*128;b=[(i%2,i%32) for i in range(128)];r=p.measure(a+bad+b);self.assertEqual(r["selection"]["retained_blocks"],2);self.assertEqual(r["selection"]["escape_omitted_blocks"],1)
  for rep in range(-1,16):
   blocks=[a[:],b[:]]
   if rep>=0:
    rng=random.Random(20261021+rep)
    for block in blocks:
     for i in range(127,0,-1):
      j=rng.randrange(i+1);block[i],block[j]=block[j],block[i]
   for field in ("q_positive","suffix_b0"):
    f=(lambda t:int(t[0]>0)) if field=="q_positive" else (lambda t:t[1]%2);c=Counter((2*f(row[i-1])+f(row[i-2]),f(row[i]),f(row[i-3])) for row in blocks for i in range(3,128));cell=r["fields"][field] if rep<0 else r["fields"][field]["nulls"][rep];table=cell["joint_counts"]
    self.assertEqual(sum(c.values()),250);self.assertEqual(c,Counter({(z,x,y):table[z][x][y] for z in range(4) for x in range(2) for y in range(2) if table[z][x][y]}))
 def test_short_prefix_selection(self):
  r=p.measure([(0,0)]*128+[(0,1)]*7);self.assertEqual(r["selection"]["tail_tokens"],7);self.assertEqual(r["fields"]["q_positive"]["scores"]["pairs"],125)
 def test_tiff_cli_success_and_shortfall(self):
  bits=("1"+"00101")*256;payload=int(bits,2).to_bytes(len(bits)//8,"big");tags=((256,25),(257,1),(273,62),(279,len(payload)))
  data=b"II"+struct.pack("<HIH",42,8,len(tags))+b"".join(struct.pack("<HHII",t,4,1,v) for t,v in tags)+struct.pack("<I",0)+payload
  a=p.report("1","public",data,256);self.assertEqual((a["returned_tokens"],a["bits_consumed"],a["prefix_shortfall"]),(256,1536,0));self.assertEqual(a["result"]["fields"]["suffix_b0"]["scores"]["pairs"],250)
  original=open
  def fake(path,*args,**kwargs):return io.BytesIO(data) if path=="synthetic" else original(path,*args,**kwargs)
  real_report=p.report
  def small(sid,name,raw,limit):return real_report(sid,name,raw,256 if limit==262144 else 384)
  with mock.patch("builtins.open",side_effect=fake),mock.patch.object(p,"report",side_effect=small):
   for arg,status in (("262144",0),("524288",1)):
    out=io.StringIO()
    with mock.patch.object(sys,"argv",["probe","--sample","1","public","synthetic","--tokens",arg]),contextlib.redirect_stdout(out):self.assertEqual(p.main(),status)
    doc=json.loads(out.getvalue());self.assertIn("token_lag3_conditional_probe.py",doc["source_sha256"]);self.assertEqual(doc["sample"]["prefix_shortfall"],0 if status==0 else 128)
if __name__=="__main__":unittest.main()
