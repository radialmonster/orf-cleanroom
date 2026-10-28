#!/usr/bin/env python3
"""Bounded prefix/whole candidate Rice projections for #106; aggregates only.

The finite-prefix ones density uses complete bytes before the token endpoint.
No extra escape skip; q is capped at 8 for pair-centered lag correlations.
As in the historical CLI, the null is undefined when density is 0 or 1.
A whole candidate parse is not a decoded raster, codec or causal ISO test.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import math
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_tokens import locate_data
from token_tail_distribution_probe import scan_tokens

PREFIX = 1500000


def ratio(n,d):
    if not d: return None
    f=Fraction(n,d)
    return {'numerator':f.numerator,'denominator':f.denominator}


def finish(payload,w,h,count,end,escapes,moments):
    bits=8*(end//8)
    ones=sum(b.bit_count() if hasattr(int,'bit_count') else bin(b).count('1') for b in payload[:end//8])
    total=len(payload)*8; sites=w*h
    real=ratio(total*count,end*sites)
    null=ratio(total*ones,sites*(5*ones+bits)) if 0 < ones < bits else None
    density=ones/bits if bits else None
    real_printed=float(format(total/(end/count)/sites,'.4f')) if count and end else None
    null_printed=(float(format(total/(6+(1-density)/density)/sites,'.4f'))
                  if density is not None and 0<density<1 else None)
    lags={}
    for lag,values in moments.items():
        n,sx,sy,sxx,syy,sxy=values
        vx=n*sxx-sx*sx;vy=n*syy-sy*sy
        covariance=n*sxy-sx*sy
        lags[str(lag)]={'n':n,'sx':sx,'sy':sy,'sxx':sxx,'syy':syy,'sxy':sxy,
                        'pearson':covariance/math.sqrt(vx*vy) if vx>0 and vy>0 else None}
    return {'tokens':count,'endpoint_bits':end,'residual_bits':total-end,'escapes':escapes,
            'complete_byte_bits':bits,'ones':ones,'real_projection':real,'null_projection':null,
            'real_printed':real_printed,'null_printed':null_printed,
            'lags':lags}


def measure(payload,w,h,prefix=PREFIX):
    if w<=0 or h<=0 or type(prefix) is not int or prefix<=0:
        raise ValueError('positive geometry and prefix required')
    moments={1:[0]*6,2:[0]*6};history=[]; count=end=esc=0; pre=None
    # No array of per-token values is retained; each lag uses integer moments.
    for q,_,endpoint in scan_tokens(payload,1<<62):
        value=min(q,8)
        for lag,m in moments.items():
            if len(history)>=lag:
                x=history[-lag];m[0]+=1;m[1]+=x;m[2]+=value;m[3]+=x*x;m[4]+=value*value;m[5]+=x*value
        history.append(value)
        if len(history)>2: history.pop(0)
        count+=1;end=endpoint;esc+=q>=17
        if count==prefix:
            pre=finish(payload,w,h,count,end,esc,moments)
    whole=finish(payload,w,h,count,end,esc,moments)
    return {'prefix_requested':prefix,'prefix_status':'complete' if pre else 'shortfall',
            'prefix':pre,'whole':whole}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sample',nargs=3,required=True,metavar=('PUBLIC_NAME','SHA256','PATH'))
    args=ap.parse_args(argv);name,sha,path=args.sample
    if not name or any(c in name for c in '/\\') or not re.fullmatch('[0-9a-f]{64}',sha):
        ap.error('invalid public identity or SHA-256')
    try:
        with open(path,'rb') as f: data=f.read()
        if hashlib.sha256(data).hexdigest()!=sha: raise ValueError('hash mismatch')
        w,h,payload=locate_data(data)
        result=measure(payload,w,h)
        print(json.dumps({'name':name,'sha256':sha,'width':w,'height':h,
                          'payload_bytes':len(payload),'result':result},indent=2,allow_nan=False))
        return 0 if result['prefix_status']=='complete' else 1
    except (OSError,ValueError,TypeError,IndexError) as e:
        print('measurement failed: '+type(e).__name__,file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
