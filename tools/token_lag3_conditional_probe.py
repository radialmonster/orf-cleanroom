"""Fixed binary lag-3 conditional association with within-block controls.

Candidate tokens/blocks are not established physical rows or codec states.
"""
import argparse,hashlib,json,math,os,random,struct,sys
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff,size_class
from suffix_joint_probe import scan_prefix,mutual_information
from token_lag_probe import select_blocks

def counts(blocks):
 out={field:[[[0]*2 for _ in range(2)] for _ in range(4)] for field in ("q_positive","suffix_b0")}
 for block in blocks:
  for i in range(3,len(block)):
   for field in out:
    f=(lambda t:int(t[0]>0)) if field=="q_positive" else (lambda t:t[1]&1)
    x=f(block[i]);y=f(block[i-3]);z=2*f(block[i-1])+f(block[i-2]);out[field][z][x][y]+=1
 return out

def scores(table):
 n=sum(v for z in table for row in z for v in row)
 if not n:return {"pairs":0,"contexts":[0]*4,"unconditional_mi":None,"conditional_mi":None}
 marginal=[[sum(table[z][x][y] for z in range(4)) for y in range(2)] for x in range(2)]
 cmi=0.0;contexts=[]
 for z in table:
  nz=sum(map(sum,z));contexts.append(nz)
  if not nz:continue
  xx=[sum(row) for row in z];yy=[sum(z[x][y] for x in range(2)) for y in range(2)]
  for x in range(2):
   for y in range(2):
    v=z[x][y]
    if v:cmi+=v/n*math.log2(v*nz/(xx[x]*yy[y]))
 return {"pairs":n,"contexts":contexts,"unconditional_mi":mutual_information(marginal),"conditional_mi":cmi}

def measure(tokens):
 blocks,selection=select_blocks(tokens);observed=counts(blocks);nulls=[]
 for rep in range(16):
  rng=random.Random(20261021+rep);permuted=[]
  for block in blocks:
   a=list(block);rng.shuffle(a);permuted.append(a)
  nulls.append(counts(permuted))
 fields={}
 for field,table in observed.items():
  fields[field]={"joint_counts":table,"scores":scores(table),"nulls":[{"joint_counts":r[field],"scores":scores(r[field])} for r in nulls]}
 return {"selection":selection,"fields":fields}

def report(sid,name,data,limit):
 d=max(Tiff(data).all_ifds(),key=lambda v:sum(v.get(0x117) or []));offs,lens=d[0x111],d[0x117]
 if len(offs)!=1 or len(lens)!=1:raise ValueError("single strip required")
 off,n=offs[0],lens[0];w,h=d[0x100][0],d[0x101][0]
 if off<0 or n<=0 or off+n>len(data) or w<=0 or h<=0 or size_class(n,w,h)!="variable":raise ValueError("invalid payload")
 tokens,end=scan_prefix(data[off:off+n],limit)
 return {"pixls_id":sid,"pixls_name":name,"sha256":hashlib.sha256(data).hexdigest(),"payload_w":w,"payload_h":h,"payload_bytes":n,"requested_tokens":limit,"returned_tokens":len(tokens),"prefix_shortfall":limit-len(tokens),"bits_consumed":end,"result":measure(tokens)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--sample",nargs=3,required=True,metavar=("ID","PUBLIC_NAME","FILE"));p.add_argument("--tokens",type=int,choices=(262144,524288),required=True);a=p.parse_args();sid,name,path=a.sample
 if not sid.isascii() or not sid.isdecimal() or int(sid)<1 or not name or not name.isprintable() or any(c in name for c in "/\\"):p.error("invalid public identity")
 try:
  with open(path,"rb") as f:data=f.read()
  r=report(sid,name,data,a.tokens);names=("token_lag3_conditional_probe.py","token_lag_probe.py","suffix_joint_probe.py","orf_signature.py");sources={x:hashlib.sha256((Path(__file__).resolve().parent/x).read_bytes()).hexdigest() for x in names}
  print(json.dumps({"source_sha256":sources,"python_version":sys.version.split()[0],"block_tokens":128,"permutations":16,"seed":20261021,"sample":r},indent=2,allow_nan=False));return 1 if r["prefix_shortfall"] else 0
 except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as exc:
  print("measurement failed: "+type(exc).__name__,file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
