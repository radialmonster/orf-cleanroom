"""Held-out fixed KT order-2 versus order-3 candidate-token comparison.

Disjoint candidate-token bands and within-block controls are descriptive.
"""
import argparse,hashlib,json,math,os,random,struct,sys
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff,size_class
from suffix_joint_probe import scan_prefix
from token_lag_probe import select_blocks
BAND=262144

def tables(blocks,field):
 result={str(order):[[0,0] for _ in range(1<<order)] for order in (0,2,3)}
 for block in blocks:
  bits=[int(q>0) if field=="q_positive" else s&1 for q,s in block]
  for i in range(3,len(bits)):
   for order in (0,2,3):
    ctx=0
    for lag in range(1,order+1):ctx=2*ctx+bits[i-lag]
    result[str(order)][ctx][bits[i]]+=1
 return result

def losses(train,test):
 out={}
 for order in (0,2,3):
  a=train[str(order)];b=test[str(order)];ntrain=sum(sum(row) for row in a);ntest=sum(sum(row) for row in b);unseen=sum(sum(y) for x,y in zip(a,b) if not sum(x))
  loss=None if not ntrain or not ntest else -sum(count*math.log2((a[i][v]+0.5)/(sum(a[i])+1)) for i,row in enumerate(b) for v,count in enumerate(row) if count)/ntest
  out[str(order)]={"train_total":ntrain,"test_total":ntest,"unseen_test":unseen,"logloss":loss}
 out["gain_order2_minus_order3"]=None if out["2"]["logloss"] is None or out["3"]["logloss"] is None else out["2"]["logloss"]-out["3"]["logloss"]
 return out

def permute(blocks,seed):
 rng=random.Random(seed);result=[]
 for block in blocks:
  a=list(block);rng.shuffle(a);result.append(a)
 return result

def measure(tokens,test_band):
 if test_band not in (1,2):raise ValueError("test band must be 1 or 2")
 train,train_sel=select_blocks(tokens[:BAND]);test,test_sel=select_blocks(tokens[test_band*BAND:(test_band+1)*BAND]);out={"train_token_range":[0,BAND],"test_token_range":[test_band*BAND,(test_band+1)*BAND],"train_selection":train_sel,"test_selection":test_sel,"fields":{}}
 for field in ("q_positive","suffix_b0"):
  tr=tables(train,field);te=tables(test,field);nulls=[]
  for rep in range(16):
   a=tables(permute(train,20261021+rep),field);b=tables(permute(test,20361021+rep),field);nulls.append({"train":a,"test":b,"scores":losses(a,b)})
  out["fields"][field]={"train":tr,"test":te,"scores":losses(tr,te),"nulls":nulls}
 return out

def report(sid,name,data,test_band):
 d=max(Tiff(data).all_ifds(),key=lambda v:sum(v.get(0x117) or []));offs,lens=d[0x111],d[0x117]
 if len(offs)!=1 or len(lens)!=1:raise ValueError("single strip required")
 off,n=offs[0],lens[0];w,h=d[0x100][0],d[0x101][0]
 if off<0 or n<=0 or off+n>len(data) or w<=0 or h<=0 or size_class(n,w,h)!="variable":raise ValueError("invalid payload")
 requested=(test_band+1)*BAND;tokens,end=scan_prefix(data[off:off+n],requested)
 return {"pixls_id":sid,"pixls_name":name,"sha256":hashlib.sha256(data).hexdigest(),"payload_w":w,"payload_h":h,"payload_bytes":n,"test_band":test_band,"requested_tokens":requested,"returned_tokens":len(tokens),"prefix_shortfall":requested-len(tokens),"bits_consumed":end,"result":measure(tokens,test_band)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--sample",nargs=3,required=True,metavar=("ID","PUBLIC_NAME","FILE"));p.add_argument("--test-band",type=int,choices=(1,2),required=True);a=p.parse_args();sid,name,path=a.sample
 if not sid.isascii() or not sid.isdecimal() or int(sid)<1 or not name or not name.isprintable() or any(c in name for c in "/\\"):p.error("invalid public identity")
 try:
  with open(path,"rb") as f:data=f.read()
  r=report(sid,name,data,a.test_band);names=("token_lag3_heldout_probe.py","token_lag_probe.py","suffix_joint_probe.py","orf_signature.py");sources={x:hashlib.sha256((Path(__file__).resolve().parent/x).read_bytes()).hexdigest() for x in names}
  print(json.dumps({"source_sha256":sources,"python_version":sys.version.split()[0],"band_tokens":BAND,"block_tokens":128,"permutations":16,"train_seed":20261021,"test_seed":20361021,"sample":r},indent=2,allow_nan=False));return 1 if r["prefix_shortfall"] else 0
 except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as exc:
  print("measurement failed: "+type(exc).__name__,file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
