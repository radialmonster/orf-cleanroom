"""Fixed-pitch alternative literal motif phase, fit once then score."""
from collections import Counter
import hashlib
import json
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fixed_motif_phase_continuity as prior
from motif_interior_probe import motif_positions, independent_strips, SafeParser, SAMPLES

COHORTS={'discovery':('PA200010.ORF','PA210010.ORF'), 'repeat':('PA200011.ORF',)}
EXPECTED={'PA200010.ORF':(398,400,2,0), 'PA210010.ORF':(398,400,400,2712),
          'PA200011.ORF':(242,142,0,0)}
WINDOWS=((800,1000),(1000,1200),(1200,1600))
PITCH=31332


def select_and_score(position_windows,original,pitch=PITCH,origin=40,windows=WINDOWS):
    counts=[]
    for positions in position_windows:
        counts.append(Counter((pos-origin)%pitch for pos in positions))
    options={phase:n for phase,n in counts[0].items() if phase!=original and n>0}
    chosen=None
    if options:
        best=max(options.values())
        winners=sorted(k for k,v in options.items() if v==best)
        phase=winners[0]
        chosen={'phase':phase,'fit_matches':best,'tie_count':len(winners),
                'phase_difference':phase-original}
    results=[]
    for (a,b),positions,cell in zip(windows,position_windows,counts):
        tiles={(pos-origin)//pitch for pos in positions}
        results.append({'indices':[a,b], 'motif_starts':len(positions),
                        'tiles_with_motif':len(tiles),
                        'original_phase_matches':cell.get(original,0),
                        'selected_phase_matches':None if chosen is None else cell.get(chosen['phase'],0)})
    recovery=None if chosen is None else all(r['selected_phase_matches']==r['indices'][1]-r['indices'][0] for r in results)
    return {'selected':chosen,'windows':results,'full_phase_recovery':recovery}


def analyze(payload,phase,expected,width,height):
    if width!=5220 or height!=3912:
        raise ValueError('unexpected_geometry')
    base=prior.analyze(payload,phase,expected[:2],width,height)
    counts=tuple(w['present'] for w in base['windows'])
    if counts!=tuple(expected):
        raise ValueError('prior_coverage_mismatch')
    position_windows=[]
    for a,b in WINDOWS:
        lo=40+a*PITCH
        end=40+b*PITCH
        if end+47 > len(payload)*8:
            raise ValueError('incomplete_window')
        positions=motif_positions(payload,lo,end+47)
        position_windows.append([pos for pos in positions if pos<end])
    result=select_and_score(position_windows,phase,pitch=PITCH,windows=WINDOWS)
    result.update(original_phase=phase,pitch=PITCH,prior_fixed_counts=list(counts))
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
            if geo['strip_count']!=1:
                raise ValueError('not_single_strip')
            row.update(status='ok',width=geo['width'],height=geo['height'],
                       result=analyze(payload,prior.PHASES[name],EXPECTED[name],geo['width'],geo['height']))
        except (OSError,ValueError,IndexError,KeyError,TypeError) as exc:
            row.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'cohort':args.cohort,'samples':rows}))
    return int(any(r['status']!='ok' for r in rows))


if __name__=='__main__':
    sys.exit(main())
