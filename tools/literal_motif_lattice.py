"""Literal fixed-pitch motif lattices on two bounded windows, no token parsing."""
from collections import Counter
import hashlib
import json
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from motif_interior_probe import motif_positions, independent_strips, SafeParser

SAMPLES = {
 'PA210010.ORF':'d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e',
 'PA200010.ORF':'b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4',
 'PA200011.ORF':'a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3',
 'PA200012.ORF':'c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7',
}
COHORTS = {'discovery':('PA210010.ORF','PA200010.ORF'),
           'repeat':('PA200011.ORF','PA200012.ORF')}


def possible(lo,hi,pitch,phase,origin=40):
    first=lo+(origin+phase-lo)%pitch
    return max(0,1+(hi-48-first)//pitch)


def evaluate(positions1,positions2,window1,window2,pitches,origin=40):
    """Exact lattice coverage; exclude empty lattices rather than treat as full."""
    full1=full2=both=0
    best=None
    for pitch in pitches:
        counts1=Counter((x-origin)%pitch for x in positions1)
        counts2=Counter((x-origin)%pitch for x in positions2)
        f1={f for f,n in counts1.items() if n==possible(*window1,pitch,f,origin) and n>0}
        f2={f for f,n in counts2.items() if n==possible(*window2,pitch,f,origin) and n>0}
        full1+=len(f1); full2+=len(f2); both+=len(f1 & f2)
        for phase,matched in counts1.items():
            total=possible(*window1,pitch,phase,origin)
            if total<=0:
                raise ValueError('motif_outside_window')
            if (best is None or matched*best['possible'] > best['matched']*total or
                (matched*best['possible'] == best['matched']*total and
                 (matched,-pitch,-phase) > (best['matched'],-best['pitch'],-best['phase']))):
                best={'pitch':pitch,'phase':phase,'matched':matched,'possible':total}
    later=None
    if best is not None:
        pitch,phase=best['pitch'],best['phase']
        later={'pitch':pitch,'phase':phase,
               'matched':sum((x-origin)%pitch==phase for x in positions2),
               'possible':possible(*window2,pitch,phase,origin)}
    return {'motifs_first':len(positions1),'motifs_second':len(positions2),
            'full_first':full1,'full_second':full2,'full_both_same_lattice':both,
            'best_first':best,'same_lattice_second':later}


def measure(payload,width):
    if width!=5220:
        raise ValueError('unexpected_width')
    pitch=6*width+12
    tolerance=max(64,pitch//100)
    windows=((40,40+400*pitch),(40+400*pitch,40+800*pitch))
    if len(payload)*8<windows[1][1]:
        raise ValueError('incomplete_window')
    positions=[motif_positions(payload,*w) for w in windows]
    result=evaluate(*positions,*windows,range(pitch-tolerance,pitch+tolerance+1))
    result.update(windows=[list(w) for w in windows],pitch_range=[pitch-tolerance,pitch+tolerance])
    return result


def main():
    p=SafeParser(description=__doc__)
    p.add_argument('--cohort',choices=tuple(COHORTS),default='discovery')
    p.add_argument('--sample',nargs=2,action='append',required=True,metavar=('NAME','PATH'))
    args=p.parse_args()
    if tuple(n for n,_ in args.sample)!=COHORTS[args.cohort]:
        p.error('fixed cohort order required')
    rows=[]
    for name,path in args.sample:
        row={'name':name,'sha256':SAMPLES[name]}
        try:
            with open(path,'rb') as f:
                data=f.read(128*1024*1024+1)
            if len(data)>128*1024*1024 or hashlib.sha256(data).hexdigest()!=SAMPLES[name]:
                raise ValueError('size_or_hash')
            geo,payload=independent_strips(data)
            row.update(status='ok',width=geo['width'],height=geo['height'],result=measure(payload,geo['width']))
        except (OSError,ValueError,IndexError,KeyError,TypeError) as exc:
            row.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'cohort':args.cohort,'samples':rows}))
    return int(any(r['status']!='ok' for r in rows))


if __name__=='__main__':
    sys.exit(main())
