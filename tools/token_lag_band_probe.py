"""Fixed token-index band extension of #29 item 6.

Candidate blocks are not physical rows; repeated within-block permutations
are descriptive controls, not calibrated stationarity or significance tests.
Rank ties use exact equality of computed Python floating-point values.
"""
import argparse,hashlib,json,itertools,os,struct,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff,size_class
from pathlib import Path
from suffix_joint_probe import scan_prefix
from token_lag_probe import select_blocks,measure
BAND=262144

def summarize(tokens,bands):
 out=[]
 for band in bands:
  start=band*BAND;stop=start+BAND;segment=tokens[start:stop];blocks,selection=select_blocks(segment);cells=measure(blocks)
  start_bit=sum(q+6 for q,_ in itertools.islice(tokens,min(start,len(tokens)))) if start<=len(tokens) else None
  end_bit=None if start_bit is None else start_bit+sum(q+6 for q,_ in segment)
  ranks={}
  for field in ("q_positive","low3"):
   for variant in ("observed","excess"):
    values=[(c[field+"_mi_bits"] if variant=="observed" else None if c[field+"_mi_bits"] is None or c[field+"_permuted_mean_bits"] is None else c[field+"_mi_bits"]-c[field+"_permuted_mean_bits"]) for c in cells]
    if any(v is None for v in values):ranks[field+"_"+variant]=None
    else:
     mx=max(values);ranks[field+"_"+variant]={"lag3_is_max":values[2]==mx,"maximum_lags":[i+1 for i,v in enumerate(values) if v==mx],"values":values}
  out.append({"band":band,"start_token":start,"end_token_exclusive":stop,"start_bit":start_bit,"end_bit":end_bit,"tokens_returned":len(segment),"shortfall":BAND-len(segment),"selection":selection,"lags":cells,"rankings":ranks})
 return out

def report(sample_id,name,data,bands):
 best=max(Tiff(data).all_ifds(),key=lambda d:sum(d.get(0x117) or []));offsets,lengths=best[0x111],best[0x117]
 if len(offsets)!=1 or len(lengths)!=1:raise ValueError("single strip required")
 off,count=offsets[0],lengths[0];w,h=best[0x100][0],best[0x101][0]
 if off<0 or count<=0 or off+count>len(data) or w<=0 or h<=0 or size_class(count,w,h)!="variable":raise ValueError("invalid variable-size input")
 requested=(max(bands)+1)*BAND;tokens,end=scan_prefix(data[off:off+count],requested)
 return {"pixls_id":sample_id,"pixls_name":name,"sha256":hashlib.sha256(data).hexdigest(),"payload_w":w,"payload_h":h,"payload_bytes":count,"requested_tokens":requested,"returned_tokens":len(tokens),"bits_consumed":end,"prefix_shortfall":requested-len(tokens),"bands":summarize(tokens,bands)}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--sample",nargs=3,required=True,metavar=("ID","PUBLIC_NAME","FILE"));ap.add_argument("--bands",nargs="+",type=int,choices=range(5),required=True);args=ap.parse_args();sid,name,path=args.sample
 if not sid.isascii() or not sid.isdecimal() or int(sid)<1 or not name or not name.isprintable() or any(c in name for c in "/\\") or len(set(args.bands))!=len(args.bands):ap.error("invalid identity or duplicate bands")
 try:
  with open(path,"rb") as f:data=f.read()
  result=report(sid,name,data,args.bands);sources={name:hashlib.sha256((Path(__file__).resolve().parent/name).read_bytes()).hexdigest() for name in ("token_lag_band_probe.py","token_lag_probe.py","suffix_joint_probe.py","orf_signature.py")}
  print(json.dumps({"source_sha256":sources,"python_version":sys.version.split()[0],"band_tokens":BAND,"block_tokens":128,"lags":[1,2,3,4,5],"replicates":16,"seed":20261021,"sample":result},indent=2,allow_nan=False));return 1 if result["prefix_shortfall"] else 0
 except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as exc:
  print("measurement failed: "+type(exc).__name__,file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
