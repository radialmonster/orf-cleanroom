"""Bounded matched-anchor candidate skip comparison for #30.

Descriptive token parsing only; neither escape semantics nor physical alignment
is established. All horizons end at the baseline prefix endpoint.
"""
from bisect import bisect_right
from fractions import Fraction

def scan(buf,start,end,count):
 pos=start;out=[]
 while len(out)<count:
  p=pos
  while p<end and not (buf[p//8]>>(7-p%8)&1):p+=1
  if p+6>end:return None
  suffix=0
  for i in range(p+1,p+6):suffix=(suffix<<1)|((buf[i//8]>>(7-i%8))&1)
  out.append((p-pos,suffix,pos,p+6));pos=p+6
 return out

def measure(buf,limit,horizon=24):
 rows=scan(buf,0,len(buf)*8,limit)
 if rows is None:raise ValueError('prefix shortfall')
 boundary=rows[-1][3];by_suffix=[[] for _ in range(32)]
 # Precompute both complete control horizons once; require end before each escape.
 for i,(q,s,start,end) in enumerate(rows):
  if q:continue
  a=scan(buf,end,boundary,horizon);b=scan(buf,end+12,boundary,horizon)
  if a is not None and b is not None:
   by_suffix[s].append((max(a[-1][3],b[-1][3]),i, sum(v[0]==0 for v in a), sum(v[0]==0 for v in b)))
 # Sort by completion; each prefix maximum retains latest eligible ordinal.
 indexes=[]
 for bucket in by_suffix:
  bucket.sort(key=lambda x:(x[0],x[1]));best=[];index=-1;choice=None
  for end,i,a,b in bucket:
   if i>index:index=i;choice=(i,a,b)
   best.append(choice)
  indexes.append(([v[0] for v in bucket],best))
 out={'requested_tokens':limit,'parsed_tokens':len(rows),'endpoint_bits':boundary,'skip_bits':12,'horizon_tokens':horizon,'escape0_q0':0,'escape12_q0':0,'control0_q0':0,'control12_q0':0,'anchors':0,'matched':0,'no_match':0,'short_horizon':0,'positive':0,'ties':0,'negative':0,'sum_difference':Fraction(),'controls':{}}
 for q,s,start,end in rows:
  if q<17:continue
  out['anchors']+=1;keys,best=indexes[s];ix=bisect_right(keys,start)-1
  if ix<0:out['no_match']+=1;continue
  ci,a,b=best[ix];x=scan(buf,end,boundary,horizon);y=scan(buf,end+12,boundary,horizon)
  if x is None or y is None:out['short_horizon']+=1;continue
  delta=Fraction(sum(v[0]==0 for v in y)-sum(v[0]==0 for v in x)-b+a,horizon)
  out['matched']+=1;out['sum_difference']+=delta;out['controls'][ci]=out['controls'].get(ci,0)+1
  out['escape0_q0']+=sum(v[0]==0 for v in x);out['escape12_q0']+=sum(v[0]==0 for v in y);out['control0_q0']+=a;out['control12_q0']+=b
  out['positive' if delta>0 else 'negative' if delta<0 else 'ties']+=1
 uses=out.pop('controls');out['q0_denominator']=out['matched']*horizon;out['unique_controls']=len(uses);out['reused_control_pairs']=sum(v-1 for v in uses.values());out['mean_difference']=out['sum_difference']/out['matched'] if out['matched'] else None;return out


def main():
 import argparse, hashlib, json, os, re, sys
 sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 from orf_tokens import locate_data
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--sample',nargs=3,required=True,metavar=('PUBLIC_NAME','SHA256','FILE'))
 ap.add_argument('--tokens',type=int,required=True,choices=(262144,524288))
 args=ap.parse_args();name,digest,path=args.sample
 if not name or any(c in name for c in '/\\') or not re.fullmatch('[0-9a-f]{64}',digest):ap.error('invalid public identity or SHA-256')
 try:
  with open(path,'rb') as f:data=f.read()
  if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('hash mismatch')
  width,height,payload=locate_data(data)
  result=measure(payload,args.tokens)
  for key in ('sum_difference','mean_difference'):
   x=result[key];result[key]=None if x is None else {'numerator':x.numerator,'denominator':x.denominator}
  print(json.dumps({'name':name,'sha256':digest,'width':width,'height':height,'payload_bytes':len(payload),'result':result},indent=2,allow_nan=False))
  return 0
 except (OSError,ValueError,IndexError,TypeError) as exc:
  print('measurement failed: '+type(exc).__name__,file=sys.stderr);return 1

if __name__=='__main__':
 import sys
 sys.exit(main())
