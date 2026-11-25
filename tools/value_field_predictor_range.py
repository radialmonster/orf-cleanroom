"""Exact unwrapped 12-bit range necessity for a fixed candidate residual field."""
from array import array
from fractions import Fraction
import hashlib
import json
import os
import random
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_field_q_accounting as old
import value_field_partner_null as pins

MISSING = -128


def make_grid(suffix, q, width, start=20, end=600, edge=20):
    if width <= 2*edge or len(suffix) < end*width+1 or len(q) != len(suffix):
        raise ValueError('insufficient_support')
    grid = array('b')
    support = [0,0]
    omitted = total = 0
    for row in range(start,end):
        for col in range(edge,width-edge):
            i = row*width+col
            a,b = suffix[i],suffix[i+1]
            if a < 0 or b < 0:
                grid.append(MISSING)
                omitted += 1
                continue
            x = (a>>2)&1
            val = (a&3) + (1-2*x)*(8*((b>>4)&1)-4*(1-((b>>3)&1))) - 12*x
            grid.append(val)
            support[int(q[i+1]>0)] += 1
            total += val
    return grid, {'eligible': sum(support), 'omitted_escape': omitted,
                  'partner_q_support': support, 'field_sum': total,
                  'field_mean': str(Fraction(total,sum(support))) if sum(support) else None}


def shuffled(grid, rows, cols, seed):
    out = array('b', grid)
    rng = random.Random(seed)
    for row in range(rows):
        base = row*cols
        for parity in (0,1):
            ix = [i for i in range(base+parity,base+cols,2) if out[i] != MISSING]
            values = [out[i] for i in ix]
            rng.shuffle(values)
            for i,v in zip(ix,values):
                out[i] = v
    return out


def ranges(grid, rows, cols, direction):
    if len(grid) != rows*cols or direction not in ('H','V'):
        raise ValueError('invalid_grid')
    stats = {'total_chains': 0, 'complete_chains': 0, 'unknown_chains': 0,
             'over_4095': 0, 'max_complete_span': None}
    def add(indices):
        val = low = high = 0
        missing = False
        for i in indices:
            d = grid[i]
            if d == MISSING:
                missing = True
            else:
                val += d
                low = min(low,val)
                high = max(high,val)
        stats['total_chains'] += 1
        if missing:
            stats['unknown_chains'] += 1
        else:
            span = high-low
            stats['complete_chains'] += 1
            stats['over_4095'] += int(span > 4095)
            if stats['max_complete_span'] is None or span > stats['max_complete_span']:
                stats['max_complete_span'] = span
    if direction == 'H':
        for r in range(rows):
            for parity in (0,1):
                add(range(r*cols+parity,(r+1)*cols,2))
    else:
        for c in range(cols):
            for parity in (0,1):
                add(range(parity*cols+c,rows*cols,2*cols))
    stats['decision'] = ('rejected' if stats['over_4095'] else
                         'unknown' if stats['unknown_chains'] or not stats['complete_chains'] else
                         'not_rejected')
    return stats


def analyze(grid, rows, cols):
    result = {}
    for label, data in (('real',grid), ('shuffle_1',shuffled(grid,rows,cols,1)),
                        ('shuffle_2',shuffled(grid,rows,cols,2))):
        result[label] = {d: ranges(data,rows,cols,d) for d in ('H','V')}
    return result


def main():
    p = old.SafeParser(description=__doc__)
    p.add_argument('--cohort',choices=tuple(pins.COHORTS),default='discovery')
    p.add_argument('--sample',nargs=2,action='append',required=True,metavar=('NAME','PATH'))
    args=p.parse_args()
    if tuple(n for n,_ in args.sample) != pins.COHORTS[args.cohort]:
        p.error('fixed cohort order required')
    rows=[]
    for name,path in args.sample:
        group,digest=pins.SAMPLES[name]
        row={'name':name,'sha256':digest,'group':group}
        try:
            with open(path,'rb') as f:
                data=f.read(128*1024*1024+1)
            if len(data)>128*1024*1024 or hashlib.sha256(data).hexdigest()!=digest:
                raise ValueError('size_or_hash')
            geo,payload=old.independent_strips(data)
            width=geo['width']
            if width != (5220 if args.cohort=='discovery' else 4640):
                raise ValueError('unexpected_width')
            suffix,q=old.parse(payload,601*width)
            grid,support=make_grid(suffix,q,width)
            row.update(status='ok',width=width,height=geo['height'],support=support,
                       outcomes=analyze(grid,580,width-40))
        except (OSError,ValueError,IndexError,KeyError,TypeError) as exc:
            row.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'cohort':args.cohort,'nominal_rows':[20,600], 'samples':rows}))
    return int(any(r['status']!='ok' for r in rows))


if __name__=='__main__':
    sys.exit(main())
