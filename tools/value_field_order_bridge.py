"""Order-sensitive centered H bridges under fixed block shuffles (#31)."""
import hashlib
import json
import math
import os
import random
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_field_predictor_range as old


def bridge(values):
    """Integer bridge centered over all n prefix positions."""
    n = len(values)
    total = sum(values)
    running = 0
    z = []
    for j,v in enumerate(values,1):
        running += v
        z.append(n*running-j*total)
    center = sum(z)
    return [n*x-center for x in z]


def shuffled_blocks(values, rng):
    count = len(values)//32
    order = list(range(count))
    rng.shuffle(order)
    out = []
    for i in order:
        out.extend(values[32*i:32*i+32])
    out.extend(values[count*32:])
    return out


def correlation_greater(a, b):
    """Exact order for defined signed correlations from integer moments."""
    x, y = a['cross'], b['cross']
    if (x > 0) != (y > 0) or (x < 0) != (y < 0):
        return (x > 0) - (x < 0) > (y > 0) - (y < 0)
    if x == 0:
        return False
    lhs = x*x*b['energy_x']*b['energy_y']
    rhs = y*y*a['energy_x']*a['energy_y']
    return lhs > rhs if x > 0 else lhs < rhs

def analyze(grid, rows, cols):
    if len(grid) != rows*cols or rows < 3 or cols < 2 or cols%2:
        raise ValueError('invalid_grid')
    rngs = (random.Random(1),random.Random(2))
    names = ('real','shuffle_1','shuffle_2')
    totals = {k: {'cross':0,'energy_x':0,'energy_y':0,
                   'complete_pairs':0,'skipped_pairs':0,'paired_values':0} for k in names}
    previous = [None,None]
    for r in range(rows):
        current = []
        for parity in (0,1):
            chain = list(grid[r*cols+parity:(r+1)*cols:2])
            if old.MISSING in chain:
                current.append(None)
            else:
                current.append([bridge(chain), *(bridge(shuffled_blocks(chain,rng)) for rng in rngs)])
        if r >= 2:
            prior = previous[r%2]
            for parity in (0,1):
                if prior[parity] is None or current[parity] is None:
                    for t in totals.values():
                        t['skipped_pairs'] += 1
                    continue
                for name, left, right in zip(names,prior[parity],current[parity]):
                    t = totals[name]
                    t['complete_pairs'] += 1
                    t['paired_values'] += len(left)
                    t['cross'] += sum(a*b for a,b in zip(left,right))
                    t['energy_x'] += sum(a*a for a in left)
                    t['energy_y'] += sum(b*b for b in right)
        previous[r%2] = current
    for t in totals.values():
        if not t['complete_pairs']:
            t.update(status='no_pairs',r=None)
        elif not t['energy_x'] or not t['energy_y']:
            t.update(status='zero_energy',r=None)
        else:
            t.update(status='ok',r=t['cross']/math.sqrt(t['energy_x']*t['energy_y']))
    if all(t['status']=='ok' for t in totals.values()):
        differences=[totals['real']['r']-totals[k]['r'] for k in names[1:]]
        decision={'status':'defined','real_minus_controls':differences,
                  'strict_above_both':all(correlation_greater(totals['real'],totals[k]) for k in names[1:])}
    else:
        decision={'status':'undefined','real_minus_controls':None,'strict_above_both':None}
    return {'lanes':totals,'decision':decision}


def main():
    p=old.old.SafeParser(description=__doc__)
    p.add_argument('--cohort',choices=tuple(old.pins.COHORTS),default='discovery')
    p.add_argument('--sample',nargs=2,action='append',required=True,metavar=('NAME','PATH'))
    args=p.parse_args()
    if tuple(n for n,_ in args.sample)!=old.pins.COHORTS[args.cohort]:
        p.error('fixed cohort order required')
    rows=[]
    for name,path in args.sample:
        group,digest=old.pins.SAMPLES[name]
        row={'name':name,'sha256':digest,'group':group}
        try:
            with open(path,'rb') as f:
                data=f.read(128*1024*1024+1)
            if len(data)>128*1024*1024 or hashlib.sha256(data).hexdigest()!=digest:
                raise ValueError('size_or_hash')
            geo,payload=old.old.independent_strips(data)
            width=geo['width']
            if width!=(5220 if args.cohort=='discovery' else 4640):
                raise ValueError('unexpected_width')
            suffix,q=old.old.parse(payload,601*width)
            grid,support=old.make_grid(suffix,q,width)
            row.update(status='ok',width=width,height=geo['height'],support=support,
                       result=analyze(grid,580,width-40))
        except (OSError,ValueError,IndexError,KeyError,TypeError) as exc:
            row.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'cohort':args.cohort,'nominal_rows':[20,600],'block_size':32,'samples':rows},allow_nan=False))
    return int(any(r['status']!='ok' for r in rows))


if __name__=='__main__':
    sys.exit(main())
