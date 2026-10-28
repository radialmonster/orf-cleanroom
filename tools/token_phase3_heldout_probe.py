"""Fixed absolute-index phase3 and lag3 held-out candidate-token models.

Phase is token index modulo 3, not established physical framing.
"""
import argparse,hashlib,json,math,os,random,struct,sys
from pathlib import Path
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff,size_class
from suffix_joint_probe import scan_prefix
BAND=262144

def select(tokens,offset):
 blocks=[];omitted=0;full=len(tokens)//128
 for i in range(full):
  block=tokens[i*128:(i+1)*128]
  if any(q>=17 for q,s in block):omitted+=1
  else:blocks.append((offset+i*128,block))
 tail=tokens[full*128:]
 return blocks,{"complete_blocks":full,"retained_blocks":len(blocks),"escape_omitted_blocks":omitted,"escape_omitted_tokens":128*omitted,"retained_tokens":128*len(blocks),"tail_tokens":len(tail),"parsed_escapes":sum(q>=17 for q,s in tokens),"tail_escapes":sum(q>=17 for q,s in tail)}

def tables(blocks,field,rotation):
 out={"pooled_lag3":[[0,0] for _ in range(2)],"phase_only":[[0,0] for _ in range(3)],"phase_lag3":[[0,0] for _ in range(6)]}
 for offset,block in blocks:
  bits=[int(q>0) if field=="q_positive" else s&1 for q,s in block]
  for i in range(3,len(bits)):
   phase=(offset+i+rotation)%3;lag=bits[i-3];value=bits[i];out["pooled_lag3"][lag][value]+=1;out["phase_only"][phase][value]+=1;out["phase_lag3"][2*phase+lag][value]+=1
 return out

def losses(train,test):
 out={}
 for name in ("pooled_lag3","phase_only","phase_lag3"):
  a=train[name];b=test[name];n=sum(map(sum,a));m=sum(map(sum,b));unseen=sum(sum(y) for x,y in zip(a,b) if not sum(x))
  value=None if not n or not m else -sum(count*math.log2((a[i][v]+.5)/(sum(a[i])+1)) for i,row in enumerate(b) for v,count in enumerate(row) if count)/m
  out[name]={"train_total":n,"test_total":m,"unseen_test":unseen,"logloss":value}
 return out

def shuffle(blocks,seed):
 rng=random.Random(seed);out=[]
 for offset,row in blocks:
  row=list(row);rng.shuffle(row);out.append((offset,row))
 return out

def measure(tokens,test_band):
 if test_band not in (1,2):raise ValueError("test band")
 train,ts=select(tokens[:BAND],0);test,vs=select(tokens[test_band*BAND:(test_band+1)*BAND],test_band*BAND);out={"train_token_range":[0,BAND],"test_token_range":[test_band*BAND,(test_band+1)*BAND],"train_selection":ts,"test_selection":vs,"fields":{}}
 for field in ("q_positive","suffix_b0"):
  def evaluate(a,b):
   t=tables(a,field,0);rot={}
   for rotation in (0,1,2):
    x=tables(b,field,rotation);sc=losses(t,x);pool=sc["pooled_lag3"]["logloss"];phase=sc["phase_only"]["logloss"];joint=sc["phase_lag3"]["logloss"];rot[str(rotation)]={"test":x,"scores":sc,"pool_minus_phase_lag3":None if pool is None or joint is None else pool-joint,"phase_only_minus_phase_lag3":None if phase is None or joint is None else phase-joint}
   return {"train":t,"rotations":rot}
  observed=evaluate(train,test);observed["nulls"]=[evaluate(shuffle(train,20261021+i),shuffle(test,20361021+i)) for i in range(16)];out["fields"][field]=observed
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
  r=report(sid,name,data,a.test_band);names=("token_phase3_heldout_probe.py","suffix_joint_probe.py","orf_signature.py");sources={x:hashlib.sha256((Path(__file__).resolve().parent/x).read_bytes()).hexdigest() for x in names}
  print(json.dumps({"source_sha256":sources,"python_version":sys.version.split()[0],"band_tokens":BAND,"block_tokens":128,"permutations":16,"train_seed":20261021,"test_seed":20361021,"sample":r},indent=2,allow_nan=False));return 1 if r["prefix_shortfall"] else 0
 except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as exc:
  print("measurement failed: "+type(exc).__name__,file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
