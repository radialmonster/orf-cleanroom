"""Fixed row-centered nominal 128x128 block sums for lead #31.

This proxy is not the unavailable private rectangle-bound measure, nor proof of
physical image rows, a predictor, or calibrated significance.
"""
import argparse,hashlib,json,os,random,struct,sys
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff,size_class
from suffix_joint_probe import scan_prefix
from token_loop_probe import map_value,shuffled_rows,shuffled_global

BLOCK=128
MAPPINGS=("u","signed_digit","signed_low3")

def centered_energy(values,w,rows):
 if w<BLOCK or rows<BLOCK or len(values)!=w*rows:raise ValueError("incomplete nominal grid")
 nr=rows//BLOCK;nc=w//BLOCK;total=0
 for br in range(nr):
  rowstart=br*BLOCK;row_sums=[sum(values[r*w:(r+1)*w]) for r in range(rowstart,rowstart+BLOCK)]
  baseline=BLOCK*sum(row_sums)
  for bc in range(nc):
   column=bc*BLOCK;block_sum=sum(sum(values[r*w+column:r*w+column+BLOCK]) for r in range(rowstart,rowstart+BLOCK))
   numerator=w*block_sum-baseline;total+=numerator*numerator
 return {"squared_centered_numerator_sum":total,"blocks":nr*nc,"block_rows":nr,"block_columns":nc,"excluded_rows":rows%BLOCK,"excluded_columns":w%BLOCK}

def measure(tokens,w,rows,sid):
 if len(tokens)!=w*rows:raise ValueError("incomplete prefix")
 out={"rows":rows,"width":w,"tokens":len(tokens),"escape_count":sum(q>=17 for q,s in tokens),"mappings":{}}
 for index,name in enumerate(MAPPINGS):
  values=[map_value(q,s,name) for q,s in tokens];entry={"real":centered_energy(values,w,rows),"nulls":{},"real_over_mean_null":{}}
  for mode in ("within-row","global"):
   runs=[]
   for rep in range(4):
    seed=20261021+1000*int(sid)+10*index+rep;rng=random.Random(seed)
    shuffled=shuffled_rows(values,w,rows,rng) if mode=="within-row" else shuffled_global(values,rng)
    runs.append({"seed":seed,"energy":centered_energy(shuffled,w,rows)})
   denom=sum(r["energy"]["squared_centered_numerator_sum"] for r in runs)
   entry["nulls"][mode]=runs;entry["real_over_mean_null"][mode]=str(Fraction(4*entry["real"]["squared_centered_numerator_sum"],denom)) if denom else None
  out["mappings"][name]=entry
 return out

def report(sid,name,data,rows):
 d=max(Tiff(data).all_ifds(),key=lambda v:sum(v.get(0x117) or []));offs,lens=d[0x111],d[0x117]
 if len(offs)!=1 or len(lens)!=1:raise ValueError("single strip required")
 off,n=offs[0],lens[0];w,h=d[0x100][0],d[0x101][0]
 if off<0 or n<=0 or off+n>len(data) or w<BLOCK or h<=0 or size_class(n,w,h)!="variable":raise ValueError("invalid payload")
 tokens,end=scan_prefix(data[off:off+n],w*rows)
 if len(tokens)!=w*rows:raise ValueError("incomplete prefix")
 return {"pixls_id":sid,"pixls_name":name,"sha256":hashlib.sha256(data).hexdigest(),"payload_w":w,"payload_h":h,"payload_bytes":n,"bits_consumed":end,"result":measure(tokens,w,rows,sid)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--sample",nargs=3,required=True,metavar=("ID","PUBLIC_NAME","FILE"));p.add_argument("--rows",type=int,choices=(300,600),required=True);a=p.parse_args();sid,name,path=a.sample
 if not sid.isascii() or not sid.isdecimal() or int(sid)<1 or not name or not name.isprintable() or any(c in name for c in "/\\"):p.error("invalid public identity")
 try:
  data=Path(path).read_bytes();result=report(sid,name,data,a.rows)
  names=("token_planar_control_probe.py","token_loop_probe.py","suffix_joint_probe.py","orf_signature.py");sources={x:hashlib.sha256((Path(__file__).resolve().parent/x).read_bytes()).hexdigest() for x in names}
  print(json.dumps({"source_sha256":sources,"sample":result},allow_nan=False));return 0
 except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error):
  print("measurement failed: input, locator, signature or parser error",file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
