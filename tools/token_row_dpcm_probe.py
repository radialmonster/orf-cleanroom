"""Fixed nominal-row DPCM energy and shuffle controls for lead #31.

Nominal W-token rows are an indexing convention, not established image rows.
The original private method and second-difference ratios cannot be reproduced.
"""
import argparse,hashlib,json,os,random,struct,sys
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff,size_class
from suffix_joint_probe import scan_prefix
from token_loop_probe import map_value,shuffled_rows,shuffled_global

MAPPINGS=("u","signed_digit","signed_low3")

def energies(values,w):
 """All six lags share targets [2W+1,N), hence equal pair counts."""
 if w<2 or len(values)<2*w+1:raise ValueError("insufficient nominal rows")
 start=2*w+1; n=len(values)-start
 return {str(lag):{"pairs":n,"squared_error_sum":sum((values[i]-values[i-lag])**2 for i in range(start,len(values)))} for lag in (w-1,w,w+1,2*w-1,2*w,2*w+1)}

def measure(tokens,w,rows,sid):
 if w<3 or rows<3 or len(tokens)!=w*rows:raise ValueError("incomplete selected rows")
 out={"rows":rows,"width":w,"tokens":len(tokens),"target_start":2*w+1,"target_end":len(tokens),"escape_count":sum(q>=17 for q,s in tokens),"mappings":{}}
 for index,name in enumerate(MAPPINGS):
  values=[map_value(q,s,name) for q,s in tokens]; item={"real":energies(values,w),"nulls":{}}
  for mode in ("within-row","global"):
   runs=[]
   for rep in range(4):
    seed=20261021+1000*int(sid)+10*index+rep;rng=random.Random(seed)
    shuffled=shuffled_rows(values,w,rows,rng) if mode=="within-row" else shuffled_global(values,rng)
    runs.append({"seed":seed,"energies":energies(shuffled,w)})
   item["nulls"][mode]=runs
  item["real_over_mean_null"]={}
  for mode,runs in item["nulls"].items():
   ratios={}
   for lag,cell in item["real"].items():
    denominator=sum(r["energies"][lag]["squared_error_sum"] for r in runs)
    ratios[lag]=str(Fraction(4*cell["squared_error_sum"],denominator)) if denominator else None
   item["real_over_mean_null"][mode]=ratios
  out["mappings"][name]=item
 return out

def report(sid,name,data,rows):
 d=max(Tiff(data).all_ifds(),key=lambda v:sum(v.get(0x117) or []));offs,lens=d[0x111],d[0x117]
 if len(offs)!=1 or len(lens)!=1:raise ValueError("single strip required")
 off,n=offs[0],lens[0];w,h=d[0x100][0],d[0x101][0]
 if off<0 or n<=0 or off+n>len(data) or w<3 or h<=0 or size_class(n,w,h)!="variable":raise ValueError("invalid payload")
 requested=w*rows;tokens,end=scan_prefix(data[off:off+n],requested)
 if len(tokens)!=requested:raise ValueError("incomplete prefix")
 return {"pixls_id":sid,"pixls_name":name,"sha256":hashlib.sha256(data).hexdigest(),"payload_w":w,"payload_h":h,"payload_bytes":n,"bits_consumed":end,"result":measure(tokens,w,rows,sid)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--sample",nargs=3,required=True,metavar=("ID","PUBLIC_NAME","FILE"));p.add_argument("--rows",type=int,choices=(300,600),required=True);a=p.parse_args();sid,name,path=a.sample
 if not sid.isascii() or not sid.isdecimal() or int(sid)<1 or not name or not name.isprintable() or any(c in name for c in "/\\"):p.error("invalid public identity")
 try:
  data=Path(path).read_bytes();result=report(sid,name,data,a.rows)
  names=("token_row_dpcm_probe.py","token_loop_probe.py","suffix_joint_probe.py","orf_signature.py");sources={x:hashlib.sha256((Path(__file__).resolve().parent/x).read_bytes()).hexdigest() for x in names}
  print(json.dumps({"source_sha256":sources,"sample":result},allow_nan=False));return 0
 except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error):
  print("measurement failed: input, locator, signature or parser error",file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
