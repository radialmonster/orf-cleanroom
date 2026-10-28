"""Candidate escape context-matching sensitivity on the same eligible anchors.

Previous q classes are 0, 1..16 and >=17; token zero has no previous class.
No-control and short-horizon exclusions precede no-previous, so an index-zero
escape is counted as no-control and no_previous is necessarily zero.
This descriptive comparison does not establish physical escape syntax.
"""
from bisect import bisect_right
from fractions import Fraction
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from escape_matched_control_probe import scan

def qclass(q):
 return 0 if q==0 else 1 if q<17 else 2

def make_index(bucket):
 bucket.sort(key=lambda x:(x[0],x[1]));ends=[];best=[];choice=None
 for end,i,a,b in bucket:
  if choice is None or i>choice[0]:choice=(i,a,b)
  ends.append(end);best.append(choice)
 return ends,best

def lookup(index,deadline):
 ends,best=index;i=bisect_right(ends,deadline)-1
 return None if i<0 else best[i]

def measure(buf,limit,horizon=24):
 if type(limit) is not int or limit<1 or type(horizon) is not int or horizon<1:raise ValueError("positive limits required")
 rows=scan(buf,0,len(buf)*8,limit)
 if rows is None:raise ValueError("prefix shortfall")
 end=rows[-1][3];buckets=[[] for _ in range(32)];strict=[[[] for _ in range(3)] for _ in range(32)]
 for i,(q,s,start,stop) in enumerate(rows):
  if q!=0:continue
  a=scan(buf,stop,end,horizon);b=scan(buf,stop+12,end,horizon)
  if a is None or b is None:continue
  item=(max(a[-1][3],b[-1][3]),i,sum(x[0]==0 for x in a),sum(x[0]==0 for x in b));buckets[s].append(item)
  if i:strict[s][qclass(rows[i-1][0])].append(item)
 idx=[make_index(x) for x in buckets];sidx=[[make_index(x) for x in bucket] for bucket in strict]
 result={"requested_tokens":limit,"parsed_tokens":len(rows),"endpoint_bits":end,"skip_bits":12,"horizon_tokens":horizon,"anchors":0,"original_eligible":0,"no_previous":0,"no_suffix_control":0,"no_context_control":0,"short_horizon":0,"paired":0,"escape0_q0":0,"escape12_q0":0,"controls":{}}
 for name in ("suffix","context"):
  result["controls"][name]={"control0_q0":0,"control12_q0":0,"sum_difference":Fraction(),"positive":0,"zero":0,"negative":0,"uses":{}}
 for i,(q,s,start,stop) in enumerate(rows):
  if q<17:continue
  result["anchors"]+=1
  old=lookup(idx[s],start)
  if old is None:result["no_suffix_control"]+=1;continue
  a=scan(buf,stop,end,horizon);b=scan(buf,stop+12,end,horizon)
  if a is None or b is None:result["short_horizon"]+=1;continue
  result["original_eligible"]+=1
  if i==0:result["no_previous"]+=1;continue
  new=lookup(sidx[s][qclass(rows[i-1][0])],start)
  if new is None:result["no_context_control"]+=1;continue
  ea=sum(x[0]==0 for x in a);eb=sum(x[0]==0 for x in b);result["paired"]+=1;result["escape0_q0"]+=ea;result["escape12_q0"]+=eb
  for name,(ci,ca,cb) in (("suffix",old),("context",new)):
   c=result["controls"][name];delta=Fraction(eb-ea-cb+ca,horizon);c["control0_q0"]+=ca;c["control12_q0"]+=cb;c["sum_difference"]+=delta;c["positive" if delta>0 else "negative" if delta<0 else "zero"]+=1;c["uses"][ci]=c["uses"].get(ci,0)+1
 result["q0_denominator"]=result["paired"]*horizon
 for c in result["controls"].values():
  uses=c.pop("uses");c["unique_controls"]=len(uses);c["reused_control_pairs"]=sum(n-1 for n in uses.values());x=c.pop("sum_difference");mean=x/result["paired"] if result["paired"] else None;c["mean_difference"]=None if mean is None else {"numerator":mean.numerator,"denominator":mean.denominator}
 a=result["controls"]["suffix"]["mean_difference"];b=result["controls"]["context"]["mean_difference"]
 delta=None if a is None or b is None else Fraction(b["numerator"],b["denominator"])-Fraction(a["numerator"],a["denominator"])
 result["context_minus_suffix"]=None if delta is None else {"numerator":delta.numerator,"denominator":delta.denominator}
 return result


def main():
 import argparse,hashlib,json,os,re,sys
 sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
 from orf_tokens import locate_data
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--sample",nargs=3,required=True,metavar=("PUBLIC_NAME","SHA256","FILE"));ap.add_argument("--tokens",type=int,choices=(262144,524288),required=True);args=ap.parse_args();name,digest,path=args.sample
 if not name or any(c in name for c in "/\\") or not re.fullmatch("[0-9a-f]{64}",digest):ap.error("invalid public identity or SHA-256")
 try:
  with open(path,"rb") as f:data=f.read()
  if hashlib.sha256(data).hexdigest()!=digest:raise ValueError("hash mismatch")
  w,h,payload=locate_data(data);result=measure(payload,args.tokens);print(json.dumps({"name":name,"sha256":digest,"width":w,"height":h,"payload_bytes":len(payload),"result":result},indent=2,allow_nan=False));return 0
 except (OSError,ValueError,IndexError,TypeError) as exc:
  print("measurement failed: "+type(exc).__name__,file=sys.stderr);return 1

if __name__=="__main__":
 import sys
 sys.exit(main())
