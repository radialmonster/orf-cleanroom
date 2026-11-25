#!/usr/bin/env python3
"""Literal #951 group-column versus MakerNote-field comparison, not geometry.

The #950 bit-pattern/longest-chain rule is reused at a fixed 400-row limit.
Columns use its capped-prefix k=5 candidate parse and nominal payload width.
Only scalar IP 0x0612 is compared directly: no fitted offset or scale and no
claim that this tag is a physical border. Hash-gated public CC0 inputs only.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
import re
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from makernote_prefix_audit import metadata
from strip_start_audit import independent_strips

HEAD=re.compile(r'(?=(?:100[01]{5}){6})')
OCTETS=tuple(format(x,'08b') for x in range(256))
TAGS={0x2040:list(range(0x0611,0x0616))}


def groups(bits,width,marker):
    # Same selection algorithm as #950 e962724; not independent framing.
    pitch=6*width+12
    band=max(64,pitch//100)
    chains=[]
    current=[]
    for hit in HEAD.finditer(bits,marker,min(len(bits),marker+400*pitch)):
        at=hit.start()
        if current and at-current[-1]<band:
            continue
        if current and pitch-band<=at-current[-1]<=pitch+band:
            current.append(at)
        else:
            if len(current)>1: chains.append(current)
            current=[at]
    if len(current)>1: chains.append(current)
    heads=max(chains,key=len) if chains else []
    wanted=set(heads)
    columns=Counter()
    at,index=marker,0
    while heads and at<=heads[-1]:
        if at in wanted:
            columns[index%width]+=1
        stop=bits.find('1',at,min(at+12,len(bits)))
        end=at+24 if stop<0 else stop+6
        if end>len(bits): break
        at=end
        index+=1
    return dict(selected_heads=len(heads),parsed_heads=sum(columns.values()),
                unaligned_heads=len(heads)-sum(columns.values()),
                columns={str(k):v for k,v in sorted(columns.items())})


def compare(note,result):
    if note.get('status')!='ok': return {'status':'unknown_metadata'}
    path=note['paths'].get('2040',{})
    if path.get('status')!='ok': return {'status':path.get('status','unknown_path')}
    tag=path['tags']['0612']
    if tag.get('status')!='ok': return {'status':tag['status']}
    if len(tag['values'])!=1: return {'status':'not_scalar'}
    value=tag['values'][0]
    if not result['parsed_heads']: return {'status':'no_parsed_heads','literal_0612':value}
    equal=result['columns'].get(str(value),0)
    return dict(status='compared',literal_0612=value,equal=equal,
                unequal=result['parsed_heads']-equal)


def measure(data):
    g,payload=independent_strips(data)
    spans=[(a,a+n) for a,n in zip(g['strip_offsets'],g['strip_byte_counts'])]
    note=metadata(data,spans,TAGS)
    # Only the fixed search prefix is needed; keep the original literal marker.
    first=next((i for i,b in enumerate(payload) if b),None)
    if first is None: raise ValueError('no_literal_marker')
    marker=8*first+9-payload[first].bit_length()
    limit=(marker+400*(6*g['width']+12)+7)//8
    bits=''.join(OCTETS[b] for b in payload[:limit])
    result=groups(bits,g['width'],marker)
    return dict(width=g['width'],height=g['height'],marker_bits=marker,
                metadata=note,group=result,comparison=compare(note,result))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--records',required=True)
    p.add_argument('--sample',nargs=2,action='append',required=True,metavar=('NAME','FILE'))
    a=p.parse_args()
    with open(a.records,encoding='utf-8') as stream: records=json.load(stream)
    failed=False
    for name,path in a.sample:
        hits=[r for r in records if r['name']==name and r['licence']=='CC0']
        if len(hits)!=1: p.error('public identity missing or ambiguous')
        r=hits[0]
        out=dict(name=name,sha256=r['sha256'])
        try:
            with open(path,'rb') as stream: data=stream.read(160*1024*1024+1)
            if len(data)>160*1024*1024 or hashlib.sha256(data).hexdigest()!=r['sha256']:
                raise ValueError('size_or_hash')
            out.update(status='ok',**measure(data))
        except (OSError,ValueError,IndexError) as exc:
            failed=True
            out.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        print(json.dumps(out,sort_keys=True),flush=True)
    return int(failed)


if __name__=='__main__':
    sys.exit(main())
