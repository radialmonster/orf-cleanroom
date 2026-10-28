"""Frozen cross-file KT table transfer on precomputed aggregate reports.

Descriptive held-out candidate-field losses; not causal or physical inference.
"""
import argparse,hashlib,json,os,sys
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from token_lag3_heldout_probe import losses
IDS={"1993":"0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8","5283":"bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b","1995":"8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f","6343":"ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7"}

def validate_table(table,expected):
 for order in (0,2,3):
  rows=table[str(order)]
  if len(rows)!=2**order or any(len(row)!=2 or any(type(x) is not int or x<0 for x in row) for row in rows):raise ValueError("invalid counts")
  if sum(map(sum,rows))!=expected:raise ValueError("count/selection mismatch")
 for i,row in enumerate(table["2"]):
  if row!=[sum(table["3"][2*i+j][v] for j in (0,1)) for v in (0,1)]:raise ValueError("nested context mismatch")
 if table["0"][0]!=[sum(row[v] for row in table["2"]) for v in (0,1)]:raise ValueError("nested context mismatch")

def summarize(reports):
 data={str(r["pixls_id"]):r for r in reports}
 if len(data)!=len(reports) or not {"1993","5283"}.issubset(data) or len(data) not in (2,4):raise ValueError("fixed cohort required")
 if len(data)==4 and set(data)!={"1993","5283","1995","6343"}:raise ValueError("fixed cohort required")
 bands={r["test_band"] for r in reports}
 if len(bands)!=1 or bands.pop()!=(1 if len(data)==2 else 2):raise ValueError("fixed test band required")
 output={"trainers":["1993","5283"],"targets":list(data),"cells":[]}
 for target,t in data.items():
  if t["sha256"]!=IDS[target] or t["prefix_shortfall"] or t["requested_tokens"]!=t["returned_tokens"] or t["requested_tokens"]!=(t["test_band"]+1)*262144:raise ValueError("identity or extent mismatch")
  for field in ("q_positive","suffix_b0"):
   f=t["result"]["fields"][field];validate_table(f["train"],125*t["result"]["train_selection"]["retained_blocks"]);validate_table(f["test"],125*t["result"]["test_selection"]["retained_blocks"])
  for trainer in ("1993","5283"):
   tr=data[trainer];cell={"trainer":trainer,"trainer_sha256":tr["sha256"],"target":target,"target_sha256":t["sha256"],"train_band":0,"test_band":t["test_band"],"fields":{}}
   for field in ("q_positive","suffix_b0"):
    a=tr["result"]["fields"][field]["train"];b=t["result"]["fields"][field]["test"];local=t["result"]["fields"][field]["train"];cross=losses(a,b);base=losses(local,b)
    diff={}
    for order in ("0","2","3"):
     x=cross[order]["logloss"];y=base[order]["logloss"];diff[order]=None if x is None or y is None else x-y
    x=cross["gain_order2_minus_order3"];y=base["gain_order2_minus_order3"];cell["fields"][field]={"training_tables":a,"target_tables":b,"recipient_training_tables":local,"transfer_scores":cross,"recipient_scores":base,"transfer_minus_recipient_loss":diff,"transfer_minus_recipient_gain":None if x is None or y is None else x-y}
   output["cells"].append(cell)
 return output

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("report",nargs="+",help="precomputed aggregate reports");args=ap.parse_args()
 try:
  reports=[];report_hashes={}
  for path in args.report:
   raw=Path(path).read_bytes();r=json.loads(raw);reports.append(r);report_hashes[str(r["pixls_id"])]=hashlib.sha256(raw).hexdigest()
  result=summarize(reports);result["report_sha256"]=report_hashes;result["source_sha256"]={name:hashlib.sha256((Path(__file__).resolve().parent/name).read_bytes()).hexdigest() for name in ("token_lag3_transfer_probe.py","token_lag3_heldout_probe.py")}
  print(json.dumps(result,indent=2,allow_nan=False));return 0
 except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
  print("aggregate failed: "+type(exc).__name__,file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
