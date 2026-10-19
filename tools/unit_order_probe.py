#!/usr/bin/env python3
"""
import sys as _s
if any(a in ('-h','--help') for a in _s.argv[1:]):
    print(__doc__); _s.exit(0)Pixel order inside a packed-12 / 12.8 unit. Usage: python -I tools/unit_order_probe.py THRESHOLD SAMPLE_DIR"""
# Measure fixed in advance: within-unit lag-1 roughness W = mean|x[2k]-x[2k+1]| and cross-unit A = mean|x[2k+1]-x[2k+2]|
# for the decoder's order and for the order with each pair swapped; ratio A/W. If the stored order is spatial,
# A/W ~ 1 (both are distance-1 neighbours); if wrong, A spans distance 3 so A/W > 1.
import sys,os
THR=int(sys.argv[1])
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(HERE,'..','decoder'))
import orf_decode as od
d=sys.argv[2]  # directory of CC0 samples
for fn in sorted(os.listdir(d)):
    path=os.path.join(d,fn)
    p=od.Payload(path); sc=p.sig['size_class']
    if sc not in('packed-12','packed-12.8'): continue
    w,h=p.sig['payload_w'],p.sig['payload_h'];rb=od.row_bytes(sc,w)
    with open(path,'rb') as f:
        order,_=od.detect_order(f,p,sc,w,h,rb)
        res={}
        for sw in (0,1):
            W=A=nW=nA=0
            for y in range(h//2-150,h//2+150) if h>400 else range(h):
                # stored row index: for IIRS the rows are interleaved, use stored order within a field (lag-1 within a row only)
                r=od.unpack_row(sc,order,p.read(f,y*rb,rb),w)[0]
                if sw:
                    r=list(r); r[0::2],r[1::2]=r[1::2],r[0::2]
                else: r=list(r)
                # edge-rich units only: |x[i+2]-x[i-2]| (same-colour, 4 columns) in the top 10% of its row's mid-section
                for i in range(2,len(r)-3,2):
                    g=abs(r[i+2]-r[i-2])+abs(r[i+3]-r[i-1])
                    if g>THR:
                        W+=abs(r[i]-r[i+1]); nW+=1; A+=abs(r[i+1]-r[i+2]); nA+=1
            res[sw]=(W/nW,A/nA)
    print('%-8s %-11s %-14s emitted(first,second): W=%.1f A=%.1f A/W=%.3f | swapped: W=%.1f A=%.1f A/W=%.3f'%(fn.split(' - ')[1],sc,order,res[0][0],res[0][1],res[0][1]/res[0][0],res[1][0],res[1][1],res[1][1]/res[1][0]))
