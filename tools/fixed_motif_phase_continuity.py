"""Fixed-phase literal motif coverage over nominal indices, no token parse."""
import hashlib
import json
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fixed_motif_edge_budget import motif, PHASES, COHORTS
from motif_interior_probe import SAMPLES, SafeParser, independent_strips

EXPECTED = {'PA210010.ORF':(398,400), 'PA200010.ORF':(398,400),
            'PA200011.ORF':(242,142)}


def intervals(indices):
    if not indices:
        return []
    out=[]
    start=last=indices[0]
    for i in indices[1:]:
        if i!=last+1:
            out.append([start,last+1])
            start=i
        last=i
    out.append([start,last+1])
    return out


def summarize(states):
    present=[i for i,x in enumerate(states) if x=='present']
    absent=[i for i,x in enumerate(states) if x=='absent']
    outside=[i for i,x in enumerate(states) if x=='out_of_bounds']
    runs=intervals(present)
    longest=min(runs,key=lambda x:(-(x[1]-x[0]),x[0])) if runs else None
    return {'present':len(present),'absent':len(absent),'out_of_bounds':len(outside),
            'first_present':present[0] if present else None,
            'last_present':present[-1] if present else None,
            'present_run_count':len(runs),'longest_present_run':longest,
            'absent_ranges':intervals(absent),'first_absent':absent[0] if absent else None,
            'last_absent':absent[-1] if absent else None,
            'out_of_bounds_ranges':intervals(outside),
            'first_out_of_bounds':outside[0] if outside else None,
            'last_out_of_bounds':outside[-1] if outside else None}


def analyze(payload,phase,expected=None,width=5220,height=3912):
    if width!=5220 or height!=3912:
        raise ValueError('unexpected_geometry')
    pitch=6*width+12
    if not 0<=phase<pitch:
        raise ValueError('invalid_phase')
    nbits=len(payload)*8
    def state(j):
        pos=40+phase+j*pitch
        return 'out_of_bounds' if pos+48>nbits else 'present' if motif(payload,pos) else 'absent'
    states=[state(j) for j in range(800)]
    if expected is not None and (states[:400].count('present'),states[400:].count('present'))!=expected:
        raise ValueError('prior_coverage_mismatch')
    states.extend(state(j) for j in range(800,height))
    windows=[]
    for a,b in ((0,400),(400,800),(800,1200),(1200,height)):
        s=states[a:b]
        windows.append({'indices':[a,b],'present':s.count('present'),
                        'absent':s.count('absent'),'out_of_bounds':s.count('out_of_bounds')})
    first_extra=40+phase+height*pitch
    complete=max(0,1+(nbits-48-first_extra)//pitch)
    matched=sum(state(height+j)=='present' for j in range(complete))
    return {'phase':phase,'pitch':pitch,'payload_bits':nbits,'windows':windows,'nominal':summarize(states),
            'beyond_nominal':{'complete_starts':complete,'matched_starts':matched,
                              'eof_minus_first_expected_start_bits':nbits-first_extra}}


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
            if geo['strip_count'] != 1:
                raise ValueError('not_single_strip')
            row.update(status='ok',width=geo['width'],height=geo['height'],
                       result=analyze(payload,PHASES[name],EXPECTED[name],geo['width'],geo['height']))
        except (OSError,ValueError,IndexError,KeyError,TypeError) as exc:
            row.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'cohort':args.cohort,'samples':rows}))
    return int(any(r['status']!='ok' for r in rows))


if __name__=='__main__':
    sys.exit(main())
