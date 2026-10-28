"""Synthetic fixed cross-file KT table transfer controls."""
import os,sys,unittest,copy,io,json,contextlib
from unittest import mock
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import token_lag3_transfer_probe as p

def tab(rows):
 order3=rows+[[0,0] for _ in range(8-len(rows))];order2=[[sum(order3[2*i+j][v] for j in (0,1)) for v in (0,1)] for i in range(4)];return {"0":[[sum(r[v] for r in order2) for v in (0,1)]],"2":order2,"3":order3}
def sample(sid,band,train,test):
 return {"pixls_id":sid,"sha256":p.IDS[sid],"test_band":band,"requested_tokens":(band+1)*262144,"returned_tokens":(band+1)*262144,"prefix_shortfall":0,"result":{"train_selection":{"retained_blocks":int(sum(train["0"][0])>0)},"test_selection":{"retained_blocks":int(sum(test["0"][0])>0)},"fields":{field:{"train":train,"test":test} for field in ("q_positive","suffix_b0")}}}

class TransferTests(unittest.TestCase):
 def test_diagonal_and_cross_tables(self):
  a=tab([[60,5],[5,55]]);b=tab([[5,60],[55,5]]);out=p.summarize([sample("1993",1,a,a),sample("5283",1,b,b)]);self.assertEqual(len(out["cells"]),4)
  for c in out["cells"]:
   for f in c["fields"].values():
    if c["trainer"]==c["target"]:self.assertEqual(f["transfer_minus_recipient_loss"],{"0":0.0,"2":0.0,"3":0.0});self.assertEqual(f["transfer_minus_recipient_gain"],0.0)
  cross=next(c for c in out["cells"] if c["trainer"]=="1993" and c["target"]=="5283")["fields"]["q_positive"];self.assertLess(cross["transfer_scores"]["gain_order2_minus_order3"],0);self.assertNotEqual(cross["transfer_minus_recipient_loss"]["3"],0)
 def test_unseen_empty(self):
  x=tab([]);y=tab([[60,5],[5,55]]);r=p.summarize([sample("1993",1,x,y),sample("5283",1,y,y)]);self.assertIsNone(r["cells"][0]["fields"]["q_positive"]["transfer_scores"]["0"]["logloss"]);self.assertEqual(r["cells"][2]["fields"]["q_positive"]["transfer_scores"]["0"]["unseen_test"],125)
 def test_four_targets_and_band_mismatch(self):
  t=tab([[60,5],[5,55]]);reports=[sample(x,2,t,t) for x in ("1993","5283","1995","6343")];self.assertEqual(len(p.summarize(reports)["cells"]),8);reports[0]["test_band"]=1
  with self.assertRaises(ValueError):p.summarize(reports)
 def test_invalid_identity_extent_and_nested_counts(self):
  t=tab([[60,5],[5,55]]);base=[sample("1993",1,t,t),sample("5283",1,t,t)]
  for change in ("hash","extent","shape","negative","total","nested"):
   values=copy.deepcopy(base);r=values[0]
   if change=="hash":r["sha256"]="0"*64
   if change=="extent":r["returned_tokens"]-=1
   if change=="shape":r["result"]["fields"]["q_positive"]["train"]["3"].pop()
   if change=="negative":r["result"]["fields"]["q_positive"]["train"]["3"][0][0]=-1
   if change=="total":r["result"]["fields"]["q_positive"]["train"]["3"][0][0]+=1
   if change=="nested":r["result"]["fields"]["q_positive"]["train"]["3"][0][0]-=1;r["result"]["fields"]["q_positive"]["train"]["3"][0][1]+=1
   with self.subTest(change=change),self.assertRaises(ValueError):p.summarize(values)
 def test_cli_report_hashes_and_source_provenance(self):
  t=tab([[60,5],[5,55]]);reports={"one":sample("1993",1,t,t),"two":sample("5283",1,t,t)};original=p.Path.read_bytes
  def fake(path):return json.dumps(reports[str(path)]).encode() if str(path) in reports else original(path)
  out=io.StringIO()
  with mock.patch.object(p.Path,"read_bytes",fake),mock.patch.object(sys,"argv",["probe","one","two"]),contextlib.redirect_stdout(out):self.assertEqual(p.main(),0)
  doc=json.loads(out.getvalue());self.assertEqual(set(doc["report_sha256"]),{"1993","5283"});self.assertEqual(set(doc["source_sha256"]),{"token_lag3_transfer_probe.py","token_lag3_heldout_probe.py"});self.assertEqual(len(doc["cells"]),4)
if __name__=="__main__":unittest.main()
