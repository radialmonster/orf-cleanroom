from pathlib import Path
import random,sys
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parent))
import escape_matched_control_probe as m
def words(bits,start,end,n):
 out=[];pos=start
 for _ in range(n):
  at=bits.find("1",pos,end)
  if at<0 or at+6>end:return None
  out.append((at-pos,int(bits[at+1:at+6],2),pos,at+6));pos=at+6
 return out
def oracle(buf,limit,h):
 bits="".join(f"{x:08b}" for x in buf); rows=words(bits,0,len(bits),limit)
 if rows is None:raise ValueError
 end=rows[-1][3];out=dict(requested_tokens=limit,parsed_tokens=len(rows),endpoint_bits=end,skip_bits=12,horizon_tokens=h,escape0_q0=0,escape12_q0=0,control0_q0=0,control12_q0=0,anchors=0,matched=0,no_match=0,short_horizon=0,positive=0,ties=0,negative=0,sum_difference=Fraction(),controls={})
 for q,s,start,stop in rows:
  if q<17:continue
  out["anchors"]+=1;eligible=[]
  for i,(cq,cs,cstart,cend) in enumerate(rows):
   if cq or cs!=s or cstart>=start:continue
   a=words(bits,cend,end,h);b=words(bits,cend+12,end,h)
   if a and b and max(a[-1][3],b[-1][3])<=start:eligible.append((i,a,b))
  if not eligible:out["no_match"]+=1;continue
  i,a,b=eligible[-1];x=words(bits,stop,end,h);y=words(bits,stop+12,end,h)
  if x is None or y is None:out["short_horizon"]+=1;continue
  z=lambda seq:sum(v[0]==0 for v in seq)
  delta=Fraction(z(y)-z(x)-z(b)+z(a),h);out["matched"]+=1;out["sum_difference"]+=delta
  out["escape0_q0"]+=z(x);out["escape12_q0"]+=z(y);out["control0_q0"]+=z(a);out["control12_q0"]+=z(b);out["controls"][i]=out["controls"].get(i,0)+1;out["positive" if delta>0 else "negative" if delta<0 else "ties"]+=1
 uses=out.pop("controls");out["q0_denominator"]=out["matched"]*h;out["unique_controls"]=len(uses);out["reused_control_pairs"]=sum(v-1 for v in uses.values());out["mean_difference"]=out["sum_difference"]/out["matched"] if out["matched"] else None
 return out
rng=random.Random(301)
matched_cases=0;signs=set();reused=0;short=0;h24_matched=0
for n in range(400):
 seq=[(17 if rng.randrange(5)==0 else rng.randrange(3),rng.randrange(3)) for _ in range(70)]
 bits="".join("0"*q+"1"+f"{s:05b}" for q,s in seq);bits+= "0"*((-len(bits))%8);data=int(bits,2).to_bytes(len(bits)//8,"big")
 for h in (1,3,8,24):
  actual=m.measure(data,70,h);assert actual==oracle(data,70,h),(n,h)
  assert actual==m.measure(data+bytes([255])*64,70,h), (n,h,"prefix clipping")
  h24_matched+=bool(actual["matched"]) if h==24 else 0
  matched_cases+=bool(actual["matched"]);reused+=bool(actual["reused_control_pairs"]);short+=bool(actual["short_horizon"]);signs.update(k for k in ("positive","negative","ties") if actual[k])
print("PASS 1600 comparisons; h24_matched ",h24_matched,"matched_cases",matched_cases,"reused_cases",reused,"short_cases",short,"signs",sorted(signs))
assert h24_matched and matched_cases and reused and short and len(signs)==3
