"""Candidate stop-1/five-bit word-start byte phases and frozen rotations (#11)."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import orf_tokens
from strip_start_audit import independent_strips

PINS={
 '1993':('Olympus - E-M1MarkII - 16bit (4:3).ORF','0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8'),
 '1997':('Olympus - E-M1MarkII - 16bit (4:3).ORI','89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a'),
 '1998':('Olympus - E-M1MarkII - 16bit (4:3).ORF','4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71')}
COHORTS={'discovery':('1993','1997'),'repeat':('1998',)}
WINDOWS=((0,262144),(1048576,1310720))
SHIFTS=(257,4093,16381)


def category(q):
    return q if q<3 else 3 if q<=7 else 4 if q<=16 else 5


def mutual(table):
    n=sum(map(sum,table))
    if not n:return None
    columns=[sum(row[k] for row in table) for k in range(len(table[0]))]
    return sum((v/n)*math.log2(v*n/(sum(row)*columns[k]))
               for row in table for k,v in enumerate(row) if v)


def joint(phases,qs,ss,shift):
    n=len(qs)
    tables={'q':[[0]*6 for _ in range(8)],'b4':[[0]*2 for _ in range(8)],'b2':[[0]*2 for _ in range(8)]}
    for i,(q,s) in enumerate(zip(qs,ss)):
        phase=phases[(i+shift)%n]
        tables['q'][phase][category(q)] += 1
        if q<17:
            tables['b4'][phase][(s>>4)&1]+=1
            tables['b2'][phase][(s>>2)&1]+=1
    return tables


def choose(table,index):
    candidates=[]
    for phase,row in enumerate(table):
        total=sum(row)
        if total:candidates.append((Fraction(row[index],total),phase))
    if not candidates:return None
    low=min(x for x,_ in candidates); high=max(x for x,_ in candidates)
    if low==high:return None
    return {'high':min(p for x,p in candidates if x==high),
            'low':min(p for x,p in candidates if x==low)}


def rates(table,index,chosen):
    if chosen is None:return None
    out={}
    for key in ('high','low'):
        phase=chosen[key]; row=table[phase]; den=sum(row)
        out[key]={'phase':phase,'numerator':row[index],'denominator':den}
    a,b=out['high'],out['low']
    out['signed_difference']=(str(Fraction(a['numerator'],a['denominator'])-Fraction(b['numerator'],b['denominator']))
                              if a['denominator'] and b['denominator'] else None)
    return out


def window(qs,ss,start_bit):
    phases=[]; pos=start_bit
    for q in qs:
        phases.append(pos%8); pos+=q+6
    tables={str(s):joint(phases,qs,ss,s) for s in (0,)+SHIFTS}
    for s,group in tables.items():
        assert sum(map(sum,group['q']))==len(qs)
        assert all(sum(map(sum,group[k]))==sum(q<17 for q in qs) for k in ('b4','b2'))
    return {'start_bit':start_bit,'end_bit':pos,'sum_q_plus_6':pos-start_bit,
            'occupancy':[phases.count(i) for i in range(8)], 'tables':tables,
            'mutual_information':{s:{k:mutual(t) for k,t in group.items()} for s,group in tables.items()}}


def analyze(payload):
    qs=[]; ss=[]
    _,end=orf_tokens.scan(payload,WINDOWS[-1][1],0,0,None,qs,ss,1<<62)
    if len(qs)<WINDOWS[-1][1]:raise ValueError('incomplete_windows')
    starts=[sum(q+6 for q in qs[:a]) for a,b in WINDOWS]
    records=[window(qs[a:b],ss[a:b],start) for (a,b),start in zip(WINDOWS,starts)]
    if records[-1]['end_bit']!=end:raise ValueError('cursor_mismatch')
    contrasts={}
    for field,index in (('q',0),('b4',1),('b2',1)):
        selected=choose(records[0]['tables']['0'][field],index)
        first=rates(records[0]['tables']['0'][field],index,selected)
        later=rates(records[1]['tables']['0'][field],index,selected)
        mis=[r['mutual_information'] for r in records]
        defined=all(m['0'][field] is not None and all(m[str(s)][field] is not None for s in SHIFTS) for m in mis)
        contrasts[field]={'selected':selected,'first':first,'later':later,
                          'direction_retained':None if later is None or later['signed_difference'] is None else Fraction(later['signed_difference'])>0,
                          'real_mi_above_all_controls_both_windows':None if not defined else all(m['0'][field]>max(m[str(s)][field] for s in SHIFTS) for m in mis)}
    return {'windows':[list(x) for x in WINDOWS], 'records':records,'contrasts':contrasts}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cohort',choices=tuple(COHORTS),default='discovery')
    p.add_argument('--sample',nargs=2,action='append',required=True,metavar=('ID','PATH'))
    args=p.parse_args()
    if tuple(x for x,_ in args.sample)!=COHORTS[args.cohort]:p.error('fixed cohort order required')
    rows=[]
    for ident,path in args.sample:
        name,pin=PINS[ident]; row={'id':ident,'name':name,'sha256':pin}
        try:
            with open(path,'rb') as f:data=f.read(128*1024*1024+1)
            if len(data)>128*1024*1024 or hashlib.sha256(data).hexdigest()!=pin:raise ValueError('size_or_hash')
            geo,payload=independent_strips(data)
            if geo['strip_count']!=1 or (geo['width'],geo['height'])!=(5240,3912):raise ValueError('unexpected_geometry')
            row.update(status='ok',result=analyze(payload))
        except (OSError,ValueError,IndexError,KeyError,TypeError) as exc:
            row.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'cohort':args.cohort,'samples':rows},allow_nan=False))
    return int(any(r['status']!='ok' for r in rows))


if __name__=='__main__':sys.exit(main())
