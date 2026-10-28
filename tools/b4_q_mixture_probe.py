"""Exact descriptive b4 pooled-mean decomposition at fixed q=0..8 support.

Input is q-stratified aggregate JSON; no sample files are read. This symmetric
split is not a causal adjustment or an equal-q mean.
"""
import argparse,hashlib,json
from fractions import Fraction
from pathlib import Path

IDS={"241":"540edabdd9d4e6ef8602f56443730cc3133d714dc4d3d2c607e2f0aa6be5cbcd","1079":"db8a564def35efaadf72cf74de92fa3959b2ab44bee4e0ec7876305830c59765","4126":"ce03e936cb2e8131343e7045a3249f78477bd2ae944e121ace72058b89fef509","6343":"ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7"}
SUPPORT=tuple(range(9))

def decompose(rows):
 counts=[[sum(row) for row in pair] for pair in rows]
 sums=[[sum(i*n for i,n in enumerate(row)) for row in pair] for pair in rows]
 totals=[sum(c[b] for c in counts) for b in (0,1)]
 missing=[q for q in SUPPORT if not all(counts[q])]
 if not all(totals) or missing:
  return {"totals":totals,"missing_support":missing,"pooled":None,"within":None,"composition":None,"outside":None}
 pooled=Fraction(sum(x[1] for x in sums),totals[1])-Fraction(sum(x[0] for x in sums),totals[0]);within=Fraction();composition=Fraction();outside=Fraction()
 for q in range(17):
  if q in SUPPORT:
   p0,p1=(Fraction(counts[q][b],totals[b]) for b in (0,1));m0,m1=(Fraction(sums[q][b],counts[q][b]) for b in (0,1))
   within+=(p1+p0)*(m1-m0)/2;composition+=(m1+m0)*(p1-p0)/2
  else:outside+=Fraction(sums[q][1],totals[1])-Fraction(sums[q][0],totals[0])
 assert within+composition+outside==pooled
 return {"totals":totals,"missing_support":missing,"pooled":str(pooled),"within":str(within),"composition":str(composition),"outside":str(outside)}

def summarize(samples):
 if len(samples)!=4 or {str(s['pixls_id']) for s in samples}!=set(IDS):raise ValueError('fixed four IDs required')
 extents={s['requested_tokens'] for s in samples}
 if len(extents)!=1 or next(iter(extents)) not in (262144,524288):raise ValueError('fixed extent required')
 out={'requested_tokens':next(iter(extents)),'support_q':list(SUPPORT),'direction':'mean_b4_1_minus_b4_0','samples':{}}
 for s in samples:
  if s['sha256']!=IDS[str(s['pixls_id'])]:raise ValueError('identity hash mismatch')
  if s['token_shortfall'] or s['returned_tokens']!=s['requested_tokens']:raise ValueError('incomplete input')
  fields={};group_counts=[];histograms={}
  for field,width in (('low3',8),('low4',16)):
   strata=s['statistics']['q_stratified_fields'][field]['strata']
   if len(strata)!=17:raise ValueError('expected q strata')
   rows=[]
   for q,row in enumerate(strata):
    hist=row['b4_rows_value_columns']
    if row['q']!=q or len(hist)!=2 or any(len(x)!=width for x in hist) or any(type(v) is not int or v<0 for x in hist for v in x):raise ValueError('invalid histogram')
    rows.append(hist)
   histograms[field]=rows;group_counts.append([[sum(x) for x in pair] for pair in rows]);fields[field]=decompose(rows)
  if group_counts[0]!=group_counts[1]:raise ValueError('field counts differ')
  if any(histograms['low3'][q][b][v]!=histograms['low4'][q][b][v]+histograms['low4'][q][b][v+8] for q in range(17) for b in (0,1) for v in range(8)):raise ValueError('field histograms disagree')
  ordinary=sum(sum(pair) for pair in group_counts[0]);stats=s['statistics']
  if ordinary!=stats['ordinary_tokens'] or ordinary+stats['escape_tokens_omitted']!=s['returned_tokens']:raise ValueError('token counts disagree')
  out['samples'][str(s['pixls_id'])]=fields
 return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report');a=p.parse_args()
 try:
  raw=Path(a.report).read_bytes();report=json.loads(raw)
  if report.get('failures'):raise ValueError('input failures')
  result=summarize(report['samples']);print(json.dumps({'input_sha256':hashlib.sha256(raw).hexdigest(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'result':result},indent=2,allow_nan=False));return 0
 except (OSError,ValueError,TypeError,KeyError,IndexError):
  print('aggregate failed: invalid input');return 1
if __name__=='__main__':raise SystemExit(main())
