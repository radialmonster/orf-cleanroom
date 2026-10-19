#!/usr/bin/env python3
"""Row-layout probe for V0 files (strip gaps, stored-row order). Usage: python -I tools/layout_probe.py FILE...
Prints numbers only; no file is written. Clean room: uses only decoder/orf_decode.py and the files."""
import sys as _s
if any(a in ('-h','--help') for a in _s.argv[1:]):
    print(__doc__); _s.exit(0)
# Measure fixed before looking: D(i,j) = sum|s_i-s_j| / mean-level, 400 centre columns, same column index.
# (1) stored-lag-1 D series: where are the discontinuities, vs strip gaps and h/2
# (2) hypotheses for image row order: N natural; F01 img[2k]=A_k,img[2k+1]=B_k ; F10 img[2k+1]=A_k,img[2k]=B_k
#     with A=stored[:n1], B=stored[n1:], n1 = split row found in (1). Score = mean D of image rows 2 apart
#     (same CFA colour) and 1 apart, over ~200 interior rows.
import sys,os,statistics
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(HERE,'..','decoder'))
import orf_decode as od
def D(a,b,c0,c1):
    s=0;t=0
    for x,y in zip(a[c0:c1],b[c0:c1]):
        s+=abs(x-y);t+=x+y
    return s/(t/2) if t else 0.0
def run(path):
    p=od.Payload(path); w,h,sc=p.sig['payload_w'],p.sig['payload_h'],p.sig['size_class']
    rb=od.row_bytes(sc,w); c0=(w-400)//2; c1=c0+400
    cnts=[c for o,c in p.strips]
    print('FILE',os.path.basename(path),sc,'%dx%d'%(w,h),'hdr',p.header,'payload',p.nbytes,'h*rb',h*rb,'(match %s)'%(p.nbytes==h*rb))
    print(' strips',len(cnts),'bytes/strip distinct',sorted(set(cnts))[:4],'rows/strip',sorted(set(round(c/rb,3) for c in cnts))[:4],
          'sum==payload',sum(cnts)==p.nbytes)
    gaps=[]
    for i in range(len(p.strips)-1):
        o,c=p.strips[i];n=p.strips[i+1][0]-(o+c)
        if n: gaps.append((i,n,(p.starts[i]+c)/rb))
    print(' gaps (strip idx, bytes, at stored row):',gaps,'| h/2=%.1f'%(h/2))
    cache={}
    with open(path,'rb') as f:
        order,_=od.detect_order(f,p,sc,w,h,rb)
        def row(y):
            if y not in cache: cache[y]=od.unpack_row(sc,order,p.read(f,y*rb,rb),w)[0][c0:c1]
            return cache[y]
        d1=[D(row(i),row(i+1),0,400) for i in range(h-1)]
        # discontinuities: d1 above 4x median of the +-6 neighbours
        peaks=[]
        for i in range(6,h-7):
            m=statistics.median(d1[i-6:i]+d1[i+1:i+7])
            if d1[i]>4*m and d1[i]>0.3: peaks.append((i+1,round(d1[i],2),round(m,3)))
        print(' discontinuities (stored row boundary, D, local median):',peaks[:8],'of',len(peaks))
        mid=[pk for pk in peaks if abs(pk[0]-h/2)<h*0.1]
        n1=mid[0][0] if mid else None
        lagmean=lambda L:sum(D(row(i),row(i+L),0,400) for i in range(10,h-10,max(1,(h-20)//200)))/len(range(10,h-10,max(1,(h-20)//200)))
        print(' stored lag D:',' '.join('%d:%.4f'%(L,lagmean(L)) for L in (1,2,3,4)))
        if n1 is None: print(' no split near h/2; natural order assumed'); return
        print(' split at stored row',n1,'; first part',n1,'rows second part',h-n1)
        def img_nat(i): return row(i)
        def f01(i): return row(i//2) if i%2==0 else row(n1+i//2)
        def f10(i): return row(n1+i//2) if i%2==0 else row(i//2)
        for nm,fn,ok in (('natural',img_nat,True),('F01 first part=even image rows',f01,n1-(h-n1) in (0,1)),('F10 first part=odd image rows',f10,(h-n1)-n1 in (0,1))):
            ids=range(20,h-20,max(1,(h-40)//200))
            d2=sum(D(fn(i),fn(i+2),0,400) for i in ids)/len(ids)
            d1_=sum(D(fn(i),fn(i+1),0,400) for i in ids)/len(ids)
            print('  %-34s counts-consistent=%s  D(2 apart)=%.4f  D(1 apart)=%.4f'%(nm,ok,d2,d1_))
        # row-wise argmin: for first-part rows, nearest stored row in second part
        import collections
        hist=collections.Counter()
        for i in range(20,n1-20,max(1,(n1-40)//40)):
            j=min((D(row(i),row(j),0,400),j) for j in range(n1,h))[1]
            hist[j-n1-i]+=1
        print(' nearest second-part row minus (n1+i):',hist.most_common(5))
        sh=[]
        for sft in range(-4,5):
            ks=range(10,min(n1,h-n1)-10,max(1,(min(n1,h-n1)-20)//150))
            sh.append((sft,round(sum(D(row(k),row(n1+k+sft),0,400) for k in ks)/len(ks),3)))
        print(' mean D(A_k, B_{k+s}) by s:',sh)
        # OB boundary in each part: first row whose mean level exceeds 3x mean of first 4 rows
        def lvl(y): r=row(y); return sum(r)/len(r)
        def ob(a,b):
            base=statistics.mean(lvl(y) for y in range(a,a+4))
            for y in range(a,b):
                if lvl(y)>2*base+20: return y-a
        print(' first bright row index within part A,B:',ob(0,n1),ob(n1,h),'levels top A/B rows:',round(lvl(0),1),round(lvl(n1),1))
for f in sys.argv[1:]: run(f)
