#!/usr/bin/env python3
"""Decompose candidate q lag covariance by original token-index parity (V2 G0).

Uses the #86 candidate q+stop+5 parse from payload bit zero, retains every token
including escapes, and caps q at 8. Groups use source-token index modulo 2,
without filtering or compaction. Integer pair moments feed exact rational within
and between covariance numerators; both are divided by the same pooled Pearson
denominator. Correlations are undefined for no pairs or zero pooled variance.
The between-component share of lag-2 minus lag-1 correlation is reported only
when that difference is positive. It is descriptive, not a physical row, CFA,
causal, predictor or codec claim. A short requested prefix exits nonzero.
"""
import argparse
from array import array
from fractions import Fraction
import hashlib
import json
import math
import os
import struct
import sys

sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import orf_tokens


def serial_fraction(x):
    return {'numerator': x.numerator, 'denominator': x.denominator}


def moments(xs,lag):
    """Per-source-parity exact pair moments (n, sx, sy, sxx, syy, sxy)."""
    out=[[0,0,0,0,0,0] for _ in range(2)]
    for i in range(len(xs)-lag):
        x,y=xs[i],xs[i+lag]
        m=out[i%2]
        m[0]+=1; m[1]+=x; m[2]+=y; m[3]+=x*x; m[4]+=y*y; m[5]+=x*y
    return out


def decompose(xs,lag):
    groups=moments(xs,lag)
    n,sx,sy,sxx,syy,sxy=(sum(g[i] for g in groups) for i in range(6))
    output={'lag':lag,'groups':[dict(zip(('n','sx','sy','sxx','syy','sxy'),g)) for g in groups],
            'within_numerator':None,'between_numerator':None,'r':None,'within':None,'between':None}
    if not n:
        return output
    total=Fraction(sxy)-Fraction(sx*sy,n)
    within=sum((Fraction(g[5])-Fraction(g[1]*g[2],g[0]) for g in groups if g[0]),Fraction())
    between=total-within
    output['within_numerator']=serial_fraction(within)
    output['between_numerator']=serial_fraction(between)
    vx=Fraction(sxx)-Fraction(sx*sx,n)
    vy=Fraction(syy)-Fraction(sy*sy,n)
    if vx<=0 or vy<=0:
        return output
    denom=math.sqrt(float(vx*vy))
    output.update(r=float(total)/denom,within=float(within)/denom,between=float(between)/denom)
    return output


def summarize(xs):
    lags=[decompose(xs,1),decompose(xs,2)]
    delta=share=None
    if all(x['r'] is not None for x in lags):
        delta=lags[1]['r']-lags[0]['r']
        if delta>0:
            share=(lags[1]['between']-lags[0]['between'])/delta
    return {'lags':lags,'delta_r':delta,'between_delta_share':share,
            'at_least_half':share>=0.5 if share is not None else None}


def measure(path,limit):
    with open(path,'rb') as f: data=f.read()
    digest=hashlib.sha256(data).hexdigest()
    w,h,payload=orf_tokens.locate_data(data)
    del data
    if w<=0 or h<=0 or not payload: raise ValueError('invalid payload')
    q=array('B'); suffix=array('B')
    _,end=orf_tokens.scan(payload,limit,0,0,None,q,suffix,8)
    if len(q)!=limit: raise ValueError('requested token prefix incomplete')
    result=summarize(q)
    result.update(sha256=digest,width=w,height=h,requested_tokens=limit,
                  tokens=len(q),consumed_bits=end,first_q_capped=q[0])
    return result


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('file'); ap.add_argument('--tokens',type=int,default=1000000)
    a=ap.parse_args(argv)
    if a.tokens<3: ap.error('--tokens must be at least 3')
    try:
        result=measure(a.file,a.tokens)
        print(json.dumps(result,indent=2));return 0
    except (OSError,ValueError,TypeError,IndexError,KeyError,struct.error) as exc:
        print(json.dumps({'error':type(exc).__name__}));return 1

if __name__=='__main__': sys.exit(main())
