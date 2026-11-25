"""Fixed common-support candidate donor sign tables, not physical row evidence."""
import argparse
from array import array
import hashlib
import json
import math
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import orf_tokens
from strip_start_audit import independent_strips

PINS={
 '1993':('Olympus - E-M1MarkII - 16bit (4:3).ORF','0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8',5240),
 '5283':('OM System - OM-1 - 16bit (4:3).ORF','bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b',5220),
 '6343':('OM System - OM-5 - 16bit (4:3).ORF','ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7',5240)}
COHORTS={'discovery':('1993','5283'),'repeat':('6343',)}
WINDOWS=((0,262144),(1048576,1310720))
PARITIES=((0,0),(0,1),(1,0),(1,1))


def table_stat(table):
    a,b=table[0];c,d=table[1]
    det=a*d-b*c
    den=(a+b)*(c+d)*(a+c)*(b+d)
    return {'table':table,'determinant':det,
            'correlation':det/math.sqrt(den) if den else None,
            'sign':('positive' if det>0 else 'negative' if det<0 else 'zero') if den else 'undefined'}


def pattern(stats,width):
    signs=[stats[str(lag)]['sign'] for lag in (width,2*width-2,2*width,2*width+2)]
    if 'undefined' in signs:return 'undefined'
    return 'match' if signs==['negative','positive','negative','positive'] else 'no_match'


def band(q,s,width,start,end):
    lags=(width-2,width,width+2,2*width-2,2*width,2*width+2)
    if width<5 or start<0 or end>len(q) or len(q)!=len(s):raise ValueError('invalid_window')
    records={str(r)+str(c):{'candidate':0,'geometry_omitted':0,'q_omitted':0,'retained':0,
                             'tables':{str(l):[[0,0],[0,0]] for l in lags}} for r,c in PARITIES}
    for t in range(start+2*width+2,end):
        col=t%width; key=str((t//width)%2)+str(col%2); out=records[key]
        out['candidate']+=1
        if col<2 or col>=width-2:
            out['geometry_omitted']+=1; continue
        if q[t]>=17 or any(q[t-l]>=17 for l in lags):
            out['q_omitted']+=1; continue
        out['retained']+=1
        target=(s[t]>>2)&1
        for lag in lags:
            donor=(s[t-lag]>>2)&1
            out['tables'][str(lag)][donor][target]+=1
    pooled={str(l):[[0,0],[0,0]] for l in lags}
    for row in records.values():
        for lag in lags:
            table=row['tables'][str(lag)]
            for i in (0,1):
                for j in (0,1):pooled[str(lag)][i][j]+=table[i][j]
        row['tables']={k:table_stat(v) for k,v in row['tables'].items()}
        row['pattern']=pattern(row['tables'],width)
    total={k:sum(r[k] for r in records.values()) for k in ('candidate','geometry_omitted','q_omitted','retained')}
    total['tables']={k:table_stat(v) for k,v in pooled.items()}
    total['pattern']=pattern(total['tables'],width)
    return {'window':[start,end],'lags':list(lags),'parities':records,'pooled':total,
            'matched_parities':sum(r['pattern']=='match' for r in records.values()),
            'undefined_parities':sum(r['pattern']=='undefined' for r in records.values())}


def analyze(payload,width):
    q=array('I');s=array('B')
    _,endbit=orf_tokens.scan(payload,WINDOWS[-1][1],0,0,None,q,s,2**32-1)
    if len(q)<WINDOWS[-1][1]:raise ValueError('incomplete_windows')
    ends=[sum(x+6 for x in q[:a]) for a,b in WINDOWS]
    result=[]
    for (a,b),startbit in zip(WINDOWS,ends):
        out=band(q,s,width,a,b)
        out.update(start_bit=startbit,end_bit=startbit+sum(x+6 for x in q[a:b]))
        result.append(out)
    if result[-1]['end_bit']!=endbit:raise ValueError('cursor_mismatch')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cohort',choices=tuple(COHORTS),default='discovery')
    p.add_argument('--sample',nargs=2,action='append',required=True,metavar=('ID','PATH'))
    args=p.parse_args()
    if tuple(i for i,_ in args.sample)!=COHORTS[args.cohort]:p.error('fixed cohort order required')
    rows=[]
    for ident,path in args.sample:
        name,pin,width=PINS[ident]; row={'id':ident,'name':name,'sha256':pin}
        try:
            with open(path,'rb') as f:data=f.read(128*1024*1024+1)
            if len(data)>128*1024*1024 or hashlib.sha256(data).hexdigest()!=pin:raise ValueError('size_or_hash')
            geo,payload=independent_strips(data)
            if geo['strip_count']!=1 or geo['width']!=width:raise ValueError('unexpected_geometry')
            row.update(status='ok',width=width,height=geo['height'],results=analyze(payload,width))
        except (OSError,ValueError,IndexError,KeyError,TypeError,OverflowError) as exc:
            row.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'cohort':args.cohort,'samples':rows},allow_nan=False))
    return int(any(r['status']!='ok' for r in rows))


if __name__=='__main__':sys.exit(main())
