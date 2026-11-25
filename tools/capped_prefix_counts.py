#!/usr/bin/env python3
"""Count the fixed candidate grammar of #951, with explicit residual scope.

Candidate only: q<12 zeros, one, five suffix bits; otherwise 12 zeros and
12 arbitrary raw bits. The leading zeros/one are excluded as a literal marker.
Reports both #950's 24-bit-remaining guard and all bounded complete words.
Neither count establishes code boundaries, physical rows or decoded values.
Standard library only; public hash-gated inputs, aggregate output only.
"""
import argparse
import hashlib
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_start_audit import independent_strips

OCTETS=tuple(format(i,'08b') for i in range(256))


def word_end(bits, at, k=5):
    """None for an incomplete word; an escape accepts every 12-bit value."""
    stop=bits.find('1',at,min(at+12,len(bits)))
    if stop<0:
        end=at+24
    else:
        end=stop+1+k
    return end if end<=len(bits) else None


def count(bits, marker):
    pos=marker
    tokens=non6=escapes=below=0
    legacy=None
    lengths={}
    while pos<len(bits):
        if legacy is None and pos+24>len(bits):
            legacy=dict(tokens=tokens,non6=non6,escapes=escapes,end=pos)
        end=word_end(bits,pos)
        if end is None:
            break
        length=end-pos
        lengths[length]=lengths.get(length,0)+1
        if length==24:
            escapes+=1
            below+=int(bits[pos+12:end],2)<384
        non6+=length!=6
        tokens+=1
        pos=end
    if legacy is None:
        legacy=dict(tokens=tokens,non6=non6,escapes=escapes,end=pos)
    return dict(guard24=legacy,complete=dict(tokens=tokens,non6=non6,escapes=escapes,
                low_raw_escapes=below,end=pos,lengths=lengths,residual_bits=len(bits)-pos))


def controls():
    # Six 8-bit fields plus six-bit ordinary words. No sensor or image exists.
    width=40
    row='10000000'*6+'100000'*(width-6)
    def end(head):
        at=0
        for i in range(width):
            at=word_end(row,at,7 if head and i<6 else 5)
        return at
    return dict(width=width,pitch=len(row),plain_end=end(False),head_end=end(True),
                non6_group_only=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--records')
    p.add_argument('--sample',nargs=2,action='append',metavar=('ID','FILE'))
    p.add_argument('--controls',action='store_true')
    args=p.parse_args()
    if args.controls:
        print(json.dumps(controls(),sort_keys=True))
        return 0
    if not args.records or not args.sample:
        p.error('--records and --sample are required unless --controls is used')
    with open(args.records,encoding='utf-8') as stream:
        records=json.load(stream)
    failed=False
    for sid,path in args.sample:
        hits=[r for r in records if str(r.get('id',r['name']))==sid and r['licence']=='CC0']
        if len(hits)!=1:
            p.error('public identity is missing or ambiguous')
        r=hits[0]
        out=dict(id=sid,name=r['name'],sha256=r['sha256'])
        try:
            with open(path,'rb') as stream:
                data=stream.read(160*1024*1024+1)
            if len(data)>160*1024*1024 or hashlib.sha256(data).hexdigest()!=r['sha256']:
                raise ValueError('size_or_hash')
            geometry,payload=independent_strips(data)
            bits=''.join(OCTETS[b] for b in payload)
            marker=bits.find('1')+1
            if not marker:
                raise ValueError('no_literal_marker_end')
            out.update(status='ok',width=geometry['width'],height=geometry['height'],
                       marker_bits=marker,payload_bits=len(bits),**count(bits,marker))
        except (OSError,ValueError,IndexError) as exc:
            failed=True
            out.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        print(json.dumps(out,sort_keys=True),flush=True)
    return int(failed)


if __name__=='__main__':
    sys.exit(main())
