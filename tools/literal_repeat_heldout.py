#!/usr/bin/env python3
"""Frozen extra input and larger windows for independent #864 reproduction.

Reuses the original literal description exactly; the comparator is never fit.
Public CC0 hashes are pinned in samples/om3-flat-338-provenance.json. No
encoded streams, template bits, images, value arrays or paths are output.
"""
import argparse
import hashlib
import json
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import literal_repeat_probe as p
from strip_start_audit import independent_strips

DARK='a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--white',required=True)
    ap.add_argument('--dark',required=True,help='public PA200011.ORF')
    a=ap.parse_args()
    w,h,white=p.snapshot('PA210010.ORF',a.white)
    template,costs=p.fit(white[p.WINDOW:2*p.WINDOW],8*p.WINDOW)
    with open(a.dark,'rb') as stream: data=stream.read(160*1024*1024+1)
    if len(data)>160*1024*1024 or hashlib.sha256(data).hexdigest()!=DARK: raise ValueError('dark_identity')
    geometry,dark=independent_strips(data)
    larger=[]
    for offset in (1048576,2097152):
        window=white[offset:offset+131072]
        if len(window)!=131072: raise ValueError('short_larger_window')
        larger.append(p.description(window,8*offset,template))
    print(json.dumps(dict(training_costs=costs,period=len(template),
          template_sha256_ascii_bits=hashlib.sha256(template.encode('ascii')).hexdigest(),
          white=dict(name='PA210010.ORF',sha256=p.SAMPLES['PA210010.ORF'],width=w,height=h,larger_windows=larger),
          dark=dict(name='PA200011.ORF',sha256=DARK,width=geometry['width'],height=geometry['height'],
                    payload_bytes=len(dark),records=p.intervals(dark,template,'verification'))),sort_keys=True))
    return 0


if __name__=='__main__': sys.exit(main())
