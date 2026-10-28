"""Synthetic-only literal brute oracle for context matched-control selection."""
from pathlib import Path
import random,sys
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parent))
import escape_context_match_probe as prod
import escape_matched_control_probe as oldprobe

def parse(bits,start,end,n):
 out=[];pos=start
 for _ in range(n):
  p=bits.find("1",pos,end)
  if p<0 or p+6>end:return None
  out.append((p-pos,int(bits[p+1:p+6],2),pos,p+6));pos=p+6
 return out
def cl(q):return 0 if q==0 else 1 if q<17 else 2
def brute(data,limit,h):
 bits="".join(f"{x:08b}" for x in data);rows=parse(bits,0,len(bits),limit)
 if rows is None:raise ValueError
 end=rows[-1][3];out={"requested_tokens":limit,"parsed_tokens":limit,"endpoint_bits":end,"skip_bits":12,"horizon_tokens":h,"anchors":0,"original_eligible":0,"no_previous":0,"no_suffix_control":0,"no_context_control":0,"short_horizon":0,"paired":0,"escape0_q0":0,"escape12_q0":0,"controls":{}}
 for key in ("suffix","context"):out["controls"][key]={"control0_q0":0,"control12_q0":0,"values":[],"uses":{}}
 for i,(q,s,start,stop) in enumerate(rows):
  if q<17:continue
  out["anchors"]+=1
  candidates=[]
  for j,(cq,cs,cstart,cend) in enumerate(rows[:i]):
   if cq or cs!=s:continue
   a=parse(bits,cend,end,h);b=parse(bits,cend+12,end,h)
   if a is not None and b is not None and max(a[-1][3],b[-1][3])<=start:candidates.append((j,a,b))
  if not candidates:out["no_suffix_control"]+=1;continue
  a=parse(bits,stop,end,h);b=parse(bits,stop+12,end,h)
  if a is None or b is None:out["short_horizon"]+=1;continue
  out["original_eligible"]+=1
  if not i:out["no_previous"]+=1;continue
  strict=[x for x in candidates if x[0]>0 and cl(rows[x[0]-1][0])==cl(rows[i-1][0])]
  if not strict:out["no_context_control"]+=1;continue
  z=lambda x:sum(q==0 for q,s,a,b in x);ea=z(a);eb=z(b);out["paired"]+=1;out["escape0_q0"]+=ea;out["escape12_q0"]+=eb
  for name,(j,x,y) in (("suffix",candidates[-1]),("context",strict[-1])):
   c=out["controls"][name];ca=z(x);cb=z(y);c["control0_q0"]+=ca;c["control12_q0"]+=cb;c["values"].append(Fraction(eb-ea-cb+ca,h));c["uses"][j]=c["uses"].get(j,0)+1
 out["q0_denominator"]=out["paired"]*h
 for c in out["controls"].values():
  vs=c.pop("values");uses=c.pop("uses");c["positive"]=sum(v>0 for v in vs);c["negative"]=sum(v<0 for v in vs);c["zero"]=sum(v==0 for v in vs);c["unique_controls"]=len(uses);c["reused_control_pairs"]=sum(v-1 for v in uses.values());m=sum(vs,Fraction())/len(vs) if vs else None;c["mean_difference"]=None if m is None else {"numerator":m.numerator,"denominator":m.denominator}
 a=out["controls"]["suffix"]["mean_difference"];b=out["controls"]["context"]["mean_difference"]
 delta=None if a is None or b is None else Fraction(b["numerator"],b["denominator"])-Fraction(a["numerator"],a["denominator"])
 out["context_minus_suffix"]=None if delta is None else {"numerator":delta.numerator,"denominator":delta.denominator}
 return out

rng=random.Random(30030);matched=0;different=0
for i in range(400):
 seq=[(rng.choice([0,0,0,1,2,17,18]),rng.randrange(3)) for _ in range(80)];bits="".join("0"*q+"1"+f"{s:05b}" for q,s in seq);bits+="0"*((-len(bits))%8);data=int(bits,2).to_bytes(len(bits)//8,"big")
 for h in (1,3,8,24):
  actual=prod.measure(data,80,h);assert actual==brute(data,80,h),(i,h);assert actual["original_eligible"]==oldprobe.measure(data,80,h)["matched"];assert actual["anchors"]==actual["no_suffix_control"]+actual["short_horizon"]+actual["no_previous"]+actual["no_context_control"]+actual["paired"];assert actual["original_eligible"]==actual["no_previous"]+actual["no_context_control"]+actual["paired"];assert actual==prod.measure(data+bytes([255])*32,80,h);matched+=bool(actual["paired"]);different+=actual["controls"]["suffix"]["mean_difference"]!=actual["controls"]["context"]["mean_difference"]
print("PASS 1600 literal brute cases; matched",matched,"different means",different)
