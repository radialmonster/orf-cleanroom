"""Fixed lattice-adjacent motif interiors and independent six-bit budget check."""
from collections import Counter
import hashlib
import json
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from motif_interior_probe import SAMPLES, SafeParser, independent_strips, interior

PHASES = {'PA210010.ORF':147, 'PA200010.ORF':41, 'PA200011.ORF':43}
COHORTS = {'discovery':('PA210010.ORF','PA200010.ORF'), 'repeat':('PA200011.ORF',)}
CONFIGS = (('literal_k4',4,False),('literal_k5',5,False),
           ('capped_k4',4,True),('capped_k5',5,True))


def bit(payload,pos):
    return bool(payload[pos//8] & (128 >> (pos%8)))


def motif(payload,start):
    return all(bit(payload,start+8*i) and not bit(payload,start+8*i+1)
               and not bit(payload,start+8*i+2) for i in range(6))


def analyze(payload,width,phase,first=400,count=400):
    pitch=6*width+12
    start=40+phase+first*pitch
    end=40+(first+count)*pitch
    if count<2 or width<7 or phase<0 or phase>=pitch or pitch-48 != 6*(width-6):
        raise ValueError('invalid_geometry')
    if len(payload)*8<end:
        raise ValueError('incomplete_window')
    positions=[start+j*pitch for j in range(count)]
    present=[pos+48<=end and motif(payload,pos) for pos in positions]
    summaries={name:{'exact_endpoint':0,'endpoint_and_target_words':0,
                      'completed_escapes':0,'reasons':Counter()} for name,_,_ in CONFIGS}
    joint=Counter(); joint_endpoint=Counter(); predicate=Counter(); agreement=Counter()
    edges=0
    for j in range(count-1):
        if not (present[j] and present[j+1]):
            continue
        edges+=1
        a,b=positions[j]+48,positions[j+1]
        fixed=all(bit(payload,a+6*k) for k in range(width-6))
        predicate['true' if fixed else 'false']+=1
        mask=''
        endpoint_mask=''
        for name,k,capped in CONFIGS:
            r=interior(payload,a,b,k,capped)
            success=r['endpoint'] and r['words']==width-6
            mask += str(int(success))
            endpoint_mask += str(int(r['endpoint']))
            cell=summaries[name]
            cell['exact_endpoint']+=int(r['endpoint'])
            cell['endpoint_and_target_words']+=int(success)
            cell['completed_escapes']+=r['escapes']
            cell['reasons'][r['reason']]+=1
        joint[mask]+=1
        joint_endpoint[endpoint_mask]+=1
        agreement['both_agree' if (mask[1]=='1')==fixed and (mask[3]=='1')==fixed else 'disagree']+=1
    return {'status':'ok' if edges else 'no_available_edges', 'phase':phase,'pitch':pitch,
            'window':[40+first*pitch,end], 'predicted_anchors':count,
            'present_anchors':sum(present), 'missing_anchors':count-sum(present),
            'possible_edges':count-1, 'available_edges':edges,'unavailable_edges':count-1-edges,
            'target_words':width-6,'predicate':dict(predicate),'predicate_agreement':dict(agreement),
            'joint_order':[x[0] for x in CONFIGS], 'joint_success_masks':dict(joint),
            'joint_endpoint_masks':dict(joint_endpoint),
            'grammars':summaries}


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
            if geo['width']!=5220:
                raise ValueError('unexpected_width')
            row.update(status='ok',width=geo['width'],height=geo['height'],
                       result=analyze(payload,geo['width'],PHASES[name]))
        except (OSError,ValueError,IndexError,KeyError,TypeError) as exc:
            row.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'cohort':args.cohort,'samples':rows}))
    return int(any(r['status']!='ok' for r in rows))


if __name__=='__main__':
    sys.exit(main())
