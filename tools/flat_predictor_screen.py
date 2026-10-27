#!/usr/bin/env python3
"""Bounded candidate predictor screens for #31, based on @mtakemoto's flat tests.

Candidate raster, channel parity, numeric value and black-level domains are
assumptions, not an established codec or physical pixel mapping. k=4 also
has near-site counts; white q>=6 startup exceptions exist. The 5.7..6.3
bits/site subset was added after the original search and is descriptive.
The 254 dark target is an assumed metadata anchor, not established per-channel
calibration. Capture conditions are owner declarations. Missing-stop cross
skip is reported as failure rather than the historical malformed-input path.
All arrays remain in memory; output is aggregate candidate statistics only.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import os
import random
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens

ROWS=16
START=4
LIMIT=100000


def search_configs():
    rules=[('fixed',k,0,0) for k in range(9)]
    rules += [('jls',0,a,c) for a in (4,64) for c in (1,4)]
    rules += [('prev',k,0,c) for k in (0,2,4) for c in (1,4)]
    rules += [('act',k,0,1) for k in (0,2,4)]
    return list(itertools.product(('W','N','avg','planar','med'),('zz+','zz-','sl'),(1,0),(0,1),(0,2048),rules))


def cross_configs():
    return list(itertools.product(('zz+','zz-','sl'),(0,1),(0,2048),(0,1),('W','N','avg','planar','med'),('L','LD','U')))


def predictor(kind,a,b,d):
    if kind=='W': return a
    if kind=='N': return b
    if kind=='avg': return (a+b)>>1
    if kind=='planar': return a+b-d
    return min(a,b) if d>=max(a,b) else max(a,b) if d<=min(a,b) else a+b-d


def signed(u,mapping):
    if mapping=='zz+': return -(u+1)//2 if u&1 else u//2
    if mapping=='zz-': return (u+1)//2 if u&1 else -(u//2)
    return -(u//2) if u&1 else u//2


def candidate(bits,w,cfg,cross=False):
    if cross:
        mapping,skip,p0,gclass,pred,other=cfg
        stop=1; rule=('fixed',5,0,0)
    else:
        pred,mapping,stop,skip,p0,rule=cfg
    mode,kp,ainit,nctx=rule
    pos=0; stopc=str(stop)
    if skip:
        j=bits.find(stopc)
        # Historical cross test advanced from -1 on a missing stop; report
        # this malformed input as a failure instead of treating it as valid.
        if j<0: return None,'missing_stop'
        pos=j+6
    nc=4 if nctx==4 else 1
    accum=[ainit]*nc; count=[1]*nc; last=[0]*nc
    rows=[[0]*w for _ in range(ROWS)]
    for r in range(ROWS):
        row=rows[r]; up=rows[r-2] if r>=2 else None
        for c in range(w):
            ctx=((r&1)*2+(c&1)) if nc==4 else 0
            same = not cross or ((r+c)&1)==gclass or c<3 or (other=='U' and r<1)
            if same:
                if r<2 and c<2: base=p0
                elif r<2: base=row[c-2]
                elif c<2: base=up[c]
                else: base=predictor(pred,row[c-2],up[c],up[c-2])
            elif other=='L': base=row[c-1]
            elif other=='LD': base=row[c-1]+row[c-2]-row[c-3]
            else: base=rows[r-1][c]
            if mode=='fixed': k=kp
            elif mode=='jls':
                k=0
                while (count[ctx]<<k)<accum[ctx] and k<16: k+=1
            elif mode=='prev': k=max(kp,abs(last[ctx]).bit_length())
            else:
                activity=(abs(row[c-2]-up[c-2])+abs(up[c]-up[c-2])+abs(up[c+2]-up[c])) if r>=2 and 2<=c<w-2 else 0
                k=max(kp,activity.bit_length())
            k=min(k,16)
            j=bits.find(stopc,pos)
            if j<0: return None,'missing_stop'
            if j-pos>40: return None,'long_unary'
            if j+1+k>len(bits): return None,'incomplete_word'
            u=((j-pos)<<k)|(int(bits[j+1:j+1+k],2) if k else 0)
            pos=j+1+k; error=signed(u,mapping); value=base+error
            if abs(value)>LIMIT: return None,'range'
            row[c]=value; last[ctx]=error
            if mode=='jls':
                accum[ctx]+=abs(error);count[ctx]+=1
                if count[ctx]>=64: accum[ctx]>>=1;count[ctx]>>=1
    sites=[]
    for sr in (0,1):
        for sc in (0,1):
            vals=[rows[r][c] for r in range(START+sr,ROWS,2) for c in range(sc,w,2)]
            mean=sum(vals)/len(vals);sd=(sum((v-mean)**2 for v in vals)/len(vals))**0.5
            sites.append((round(mean,1 if cross else 2),round(sd,2)))
    return {'sites':sites,'bits_per_site':round(pos/(ROWS*w),4),'consumed_bits':pos},None


def bits_from_file(path,digest,n,shuffle=False):
    with open(path,'rb') as f: data=f.read()
    actual=hashlib.sha256(data).hexdigest()
    if actual!=digest: raise ValueError('hash mismatch')
    w,h,payload=orf_tokens.locate_data(data)
    if w<4 or len(payload)<n: raise ValueError('input too short')
    buf=bytearray(payload[:n])
    if shuffle: random.Random(20261022).shuffle(buf)
    return w,bin(int.from_bytes(buf,'big'))[2:].zfill(len(buf)*8)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dark',required=True);ap.add_argument('--dark-sha256',required=True)
    ap.add_argument('--white');ap.add_argument('--white-sha256')
    ap.add_argument('--shuffle',action='store_true')
    a=ap.parse_args()
    if bool(a.white)!=bool(a.white_sha256): ap.error('white and white-sha256 required together')
    if a.white and a.shuffle: ap.error('cross test uses unshuffled inputs')
    try:
        w,bits=bits_from_file(a.dark,a.dark_sha256,300000,a.shuffle)
        results=[]
        for cfg in search_configs():
            result,error=candidate(bits,w,cfg)
            if result is not None:
                result['pass']=all(abs(m-254)<=64 and sd<=32 for m,sd in result['sites'])
                result['in_posthoc_bpp_range']=5.7<=result['bits_per_site']<=6.3
            results.append({'config':cfg,'result':result,'failure':error})
        done=[r['result'] for r in results if r['result'] is not None]
        filtered=[r for r in results if r['result'] is not None and r['result']['in_posthoc_bpp_range']]
        filtered.sort(key=lambda r: max(abs(m-254)/64+sd/32 for m,sd in r['result']['sites']))
        output={'dark_sha256':a.dark_sha256,'width':w,'shuffle':a.shuffle,
                'search_summary':{'requested':len(results),'completed':len(done),
                                  'failed':len(results)-len(done),
                                  'failure_counts':dict(Counter(r['failure'] for r in results if r['failure'])),
                                  'passed':sum(r['pass'] for r in done),
                                  'posthoc_bpp_range_completed':sum(r['in_posthoc_bpp_range'] for r in done)},
                'posthoc_bpp_range_closest':filtered[:15],
                'search':results}
        if a.white:
            ww,white=bits_from_file(a.white,a.white_sha256,200000)
            if ww!=w: raise ValueError('width mismatch')
            dark=bits[:200000*8]
            cross=[]
            for cfg in cross_configs():
                d,de=candidate(dark,w,cfg,True);v,ve=candidate(white,w,cfg,True)
                cross.append({'config':cfg,'dark':d,'white':v,'dark_failure':de,'white_failure':ve,
                    'dark_pass':d is not None and all(abs(m-254)<=64 and sd<=32 for m,sd in d['sites']),
                    'white_pass':v is not None and all(sd<=2 for m,sd in v['sites'])})
            output['white_sha256']=a.white_sha256;output['cross']=cross
            output['cross_summary']={'requested':len(cross),
                                     'dark_completed':sum(r['dark'] is not None for r in cross),
                                     'white_completed':sum(r['white'] is not None for r in cross),
                                     'dark_failures':dict(Counter(r['dark_failure'] for r in cross if r['dark_failure'])),
                                     'white_failures':dict(Counter(r['white_failure'] for r in cross if r['white_failure'])),
                                     'dark_passed':sum(r['dark_pass'] for r in cross),
                                     'white_passed':sum(r['white_pass'] for r in cross),
                                     'both_passed':sum(r['dark_pass'] and r['white_pass'] for r in cross)}
        print(json.dumps(output,allow_nan=False))
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError) as e:
        print(json.dumps({'error':type(e).__name__}));return 1


if __name__=='__main__': sys.exit(main())
