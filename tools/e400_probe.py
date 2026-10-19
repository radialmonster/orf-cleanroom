#!/usr/bin/env python3
"""
import sys as _s
if any(a in ('-h','--help') for a in _s.argv[1:]):
    print(__doc__); _s.exit(0)E-400 low-nibble probe: words with a nonzero low nibble vs the mean of same-colour neighbours.
Usage: python -I tools/e400_probe.py E400_FILE   (numbers to stdout only)"""
import sys,os,collections
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(HERE,'..','decoder'))
import orf_decode as od
path=sys.argv[1]  # the E-400 packed-16 file (raw.pixls.us id 2151)
p=od.Payload(path);w,h=p.sig['payload_w'],p.sig['payload_h'];rb=od.row_bytes('packed-16',w)
bad=[]
with open(path,'rb') as f:
    for y in range(h):
        r=od.unpack_row('packed-16','le',p.read(f,y*rb,rb),w)[0]
        for x,v in enumerate(r):
            if v&15: bad.append((y,x,v))
print(len(bad))
print('low nibble hist',sorted(collections.Counter(v&15 for y,x,v in bad).items()))
print('value hist (top)',collections.Counter(v>>4 for y,x,v in bad).most_common(8))
ys=collections.Counter(y for y,x,v in bad);xs=collections.Counter(x for y,x,v in bad)
print('distinct rows',len(ys),'top rows',ys.most_common(5));print('distinct cols',len(xs),'top cols',xs.most_common(5))
print('y range',min(ys),max(ys),'x range',min(xs),max(xs),'w,h',w,h)
print('x parity',collections.Counter(x&1 for y,x,v in bad),'y parity',collections.Counter(y&1 for y,x,v in bad))
print('x%2.. mod 3',collections.Counter(x%3 for y,x,v in bad))
print('first 12',bad[:12])
# sum of high-12 of bad vs overall max
print('--- neighbour-mean test')
# keep needed rows
need=set()
for y,x,v in bad:
    for dy in (-2,0,2): need.add(y+dy)
rows={}
with open(path,'rb') as f:
    for y in sorted(need):
        if 0<=y<h: rows[y]=od.unpack_row('packed-16','le',p.read(f,y*rb,rb),w)[0]
def nb(y,x,kind):
    try:
        g=lambda dy,dx: rows[y+dy][x+dx]
        if kind=='H2': v=[g(0,-2),g(0,2)]
        elif kind=='V2': v=[g(-2,0),g(2,0)]
        elif kind=='4': v=[g(0,-2),g(0,2),g(-2,0),g(2,0)]
        elif kind=='8': v=[g(dy,dx) for dy in(-2,0,2) for dx in (-2,0,2) if dy or dx]
        elif kind=='D4': v=[g(-2,-2),g(-2,2),g(2,-2),g(2,2)]
        else: return None
        return v
    except (KeyError,IndexError): return None
for kind in ('H2','V2','4','D4','8'):
    ex=fl=tot=0;near=0
    for y,x,v in bad:
        n=nb(y,x,kind)
        if not n or y+2 not in rows or y-2<0: continue
        tot+=1;s=sum(n)
        if s%len(n)==0 and s//len(n)==v: ex+=1
        if s//len(n)==v: fl+=1
        if abs(s/len(n)-v)<=32: near+=1
    print(kind,'bad words tested',tot,'exact mean',ex,'floor-mean',fl,'within 32 (2 12-bit steps)',near)
# control: nibble-zero words with random positions
import random
r=random.Random(3);ctrl=[]
while len(ctrl)<793:
    y=r.randrange(4,h-4);x=r.randrange(4,w-4)
    ctrl.append((y,x))
with open(path,'rb') as f:
    for y in set(c[0] for c in ctrl)|set(c[0]+d for c in ctrl for d in(-2,2)):
        if y not in rows: rows[y]=od.unpack_row('packed-16','le',p.read(f,y*rb,rb),w)[0]
for kind in ('H2','V2','4','D4','8'):
    ex=near=tot=0
    for y,x in ctrl:
        n=nb(y,x,kind);v=rows[y][x]
        tot+=1;s=sum(n)
        if s//len(n)==v: ex+=1
        if abs(s/len(n)-v)<=32: near+=1
    print('control',kind,tot,'floor-mean match',ex,'within 32',near)
print('--- unmatched analysis')
import itertools
um=[];sub=collections.Counter();res=[]
for y,x,v in bad:
    n=nb(y,x,'4')
    if not n or y-2<0 or y+2 not in rows: continue
    if sum(n)//4==v: continue
    um.append((y,x,v,n))
    found=[]
    for k in (2,3):
        for c in itertools.combinations(range(4),k):
            if sum(n[i] for i in c)==v*k: found.append((k,c))
    sub[bool(found)]+=1
    res.append((v-sum(n)/4)/16)
print('unmatched',len(um),'explained by exact mean of some 2- or 3-subset of {L,R,U,D}:',sub)
res.sort();print('residual v-mean4 in 12-bit units: min,q1,med,q3,max',res[0],res[len(res)//4],res[len(res)//2],res[3*len(res)//4],res[-1])
print('abs residual <=1 (12-bit unit):',sum(abs(r)<=1 for r in res),'<=4:',sum(abs(r)<=4 for r in res),'of',len(res))
print('sample unmatched',[(y,x,v>>4,[a>>4 for a in n]) for y,x,v,n in um[:8]])
print('--- other families on the unmatched')
need2=set()
for y,x,v,n in um:
    for dy in range(-3,4): need2.add(y+dy)
with open(path,'rb') as f:
    for y in need2:
        if 0<=y<h and y not in rows: rows[y]=od.unpack_row('packed-16','le',p.read(f,y*rb,rb),w)[0]
fam={'diag1':[(-1,-1),(-1,1),(1,-1),(1,1)],'axial1':[(-1,0),(1,0),(0,-1),(0,1)],
 'ring1':[(a,b) for a in(-1,0,1) for b in(-1,0,1) if a or b],
 'axial2':[(-2,0),(2,0),(0,-2),(0,2)],'diag1+axial2':[(-1,-1),(-1,1),(1,-1),(1,1),(-2,0),(2,0),(0,-2),(0,2)],
 'axial2+diag2':[(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(-2,2),(2,-2),(2,2)],
 'H2+H1(row)':[(0,-2),(0,2),(0,-1),(0,1)],'axial1+axial2':[(-1,0),(1,0),(0,-1),(0,1),(-2,0),(2,0),(0,-2),(0,2)],
 'H4':[(0,-2),(0,2),(0,-4),(0,4)]}
for nm,offs in fam.items():
    ok=0;okfl=0;tot=0
    for y,x,v,n in um:
        try: vals=[rows[y+dy][x+dx] for dy,dx in offs]
        except (KeyError,IndexError): continue
        tot+=1;s=sum(vals)
        if s//len(vals)==v: ok+=1
    print(nm,tot,ok)
print('--- parity vs family; residual')
fm=collections.Counter();res1=[]
for y,x,v in bad:
    if not(2<=y<h-2 and 2<=x<w-2): res1.append(('edge',y,x,v));continue
    r=lambda dy,dx: rows[y+dy][x+dx] if (y+dy) in rows else None
    for yy in (y-2,y-1,y+1,y+2):
        pass
for y,x,v,n in um: pass
# re-evaluate each bad word with both families, needs rows y-2..y+2 loaded
with open(path,'rb') as f:
    for y,x,v in bad:
        for dy in range(-2,3):
            if 0<=y+dy<h and y+dy not in rows: rows[y+dy]=od.unpack_row('packed-16','le',p.read(f,y*rb+dy*rb,rb),w)[0]
for y,x,v in bad:
    if not(2<=y<h-2 and 2<=x<w-2): res1.append(('edge',y,x,v));continue
    a=sum(rows[y+dy][x+dx] for dy,dx in((-2,0),(2,0),(0,-2),(0,2)))//4==v
    b=sum(rows[y+dy][x+dx] for dy,dx in((-1,-1),(-1,1),(1,-1),(1,1)))//4==v
    fm[(y&1,x&1,'axial2' if a else '',  'diag1' if b else '')]+=1
    if not(a or b): res1.append(('none',y,x,v&15,v>>4))
for k,c in sorted(fm.items()): print(k,c)
print(res1)
