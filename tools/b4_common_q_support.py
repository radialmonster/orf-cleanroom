#!/usr/bin/env python3
"""Equal-q b4 contrasts on common support from four aggregate reports.

Input is aggregate JSON from token_b4_gate_probe.py --q-stratified; it never
reads sample files. Uniform weights over the observed support are descriptive,
not a causal adjustment, significance test or physical codec-state claim.
"""
import argparse
from fractions import Fraction
import json


def summarize(samples):
    if len(samples)!=4 or len({str(s['pixls_id']) for s in samples})!=4:
        raise ValueError('exactly four distinct samples required')
    extents={s['requested_tokens'] for s in samples}
    if len(extents)!=1:raise ValueError('requested extents differ')
    tables={}
    for sample in samples:
        if sample['token_shortfall'] or sample['returned_tokens']!=sample['requested_tokens']:
            raise ValueError('incomplete input')
        ident=str(sample['pixls_id']);tables[ident]={}
        for field,width in (('low3',8),('low4',16)):
            strata=sample['statistics']['q_stratified_fields'][field]['strata']
            if len(strata)!=17:raise ValueError('expected 17 q strata')
            tables[ident][field]=[]
            for q,row in enumerate(strata):
                hist=row['b4_rows_value_columns']
                if row['q']!=q or len(hist)!=2 or any(len(x)!=width for x in hist):
                    raise ValueError('invalid histogram shape')
                if any(type(v) is not int or v<0 for x in hist for v in x):
                    raise ValueError('invalid histogram count')
                counts=[sum(x) for x in hist]
                totals=[sum(i*n for i,n in enumerate(x)) for x in hist]
                tables[ident][field].append((counts,totals))
    # Both low3 and low4 encode the same q/b4 token counts; reject inconsistent input.
    for ident in tables:
        for q in range(17):
            if tables[ident]['low3'][q][0]!=tables[ident]['low4'][q][0]:
                raise ValueError('field counts disagree')
    support=[q for q in range(17) if all(all(tables[i]['low4'][q][0]) for i in tables)]
    out={'requested_tokens':next(iter(extents)),'support_q':support,
         'excluded_q':[q for q in range(17) if q not in support], 'support_strata':len(support),
         'counts_by_q':{str(q):{i:tables[i]['low4'][q][0] for i in tables} for q in range(17)},
         'exclusion_missing_groups':{str(q):{i:[b for b,n in enumerate(tables[i]['low4'][q][0]) if not n]
                                             for i in tables if not all(tables[i]['low4'][q][0])}
                                     for q in range(17) if q not in support},
         'contrast_direction':'mean_b4_1_minus_b4_0','samples':{}}
    for ident in tables:
        result={}
        local_support=[q for q in range(17) if all(tables[ident]['low4'][q][0])]
        for field in ('low3','low4'):
            values=[]
            for q in support:
                counts,totals=tables[ident][field][q]
                values.append(Fraction(totals[1],counts[1])-Fraction(totals[0],counts[0]))
            mean=sum(values,Fraction())/len(values) if values else None
            local_values=[]
            for q in local_support:
                counts,totals=tables[ident][field][q]
                local_values.append(Fraction(totals[1],counts[1])-Fraction(totals[0],counts[0]))
            local_mean=sum(local_values,Fraction())/len(local_values) if local_values else None
            result[field]={'mean':None if mean is None else {'numerator':mean.numerator,'denominator':mean.denominator},
                           'strata':{str(q):{'numerator':v.numerator,'denominator':v.denominator}
                                     for q,v in zip(support,values)},
                           'local_support_q':local_support,
                           'local_excluded_q':[q for q in range(17) if q not in local_support],
                           'local_equal_weight_mean':None if local_mean is None else
                               {'numerator':local_mean.numerator,'denominator':local_mean.denominator},
                           'positive':sum(x>0 for x in values),'zero':sum(x==0 for x in values),
                           'negative':sum(x<0 for x in values),'excluded_strata':17-len(support)}
        out['samples'][ident]=result
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('report',help='aggregate q-stratified JSON report')
    args=p.parse_args()
    try:
        with open(args.report,encoding='utf-8-sig') as f: report=json.load(f)
        if report.get('failures'):raise ValueError('input contains failures')
        print(json.dumps(summarize(report['samples']),indent=2,allow_nan=False))
    except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
        p.exit(1,'aggregate failed: '+type(exc).__name__+'\n')


if __name__=='__main__':main()
