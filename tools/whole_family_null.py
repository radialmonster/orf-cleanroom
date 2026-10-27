#!/usr/bin/env python3
"""Whole-payload candidate family counts and measured-density Bernoulli control.

Supports specs/V2.md G0. Parses literal candidate words from payload bit 0,
MSB first, without asserting a codec or pixel correspondence. Null bytes are
packed in MSB order with one Random.random() draw per bit; p is the full-payload
ones fraction and one reset seed is shared across all families. Density is
preserved in expectation only. Prefix and full-file identity must be checked
against retained public CC0 records and manifest before use.

Packed payload and generated null are retained as bytes, so memory is O(payload
bytes); no full bit string or per-bit list is allocated. Zero completed words
and their unconsumed residual are recorded as such. One null is descriptive,
not significance or independent capture evidence.
"""
import argparse
import hashlib
import json
import os
import random
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens

FAMILIES = [('rice_stop1',5),('rice_stop1',4),('rice_stop1',3),('rice_stop0',5),
            ('exp_golomb',2),('exp_golomb',3),('elias_gamma',0),
            ('elias_delta',0),('fibonacci',0)]


def first_bit(buf, start, bit):
    """Return the first requested bit position at or after start, or None."""
    n = len(buf)*8
    pos = start
    while pos < n:
        off = pos & 7
        byte = buf[pos >> 3] ^ (255 if bit == 0 else 0)
        byte &= (1 << (8-off)) - 1
        if byte:
            return (pos & ~7) + 8 - byte.bit_length()
        pos = (pos & ~7) + 8
    return None


def bit_at(buf, pos):
    return (buf[pos >> 3] >> (7-(pos & 7))) & 1


def next_end(buf, pos, family, k):
    n = len(buf)*8
    if family == 'fibonacci':
        previous = 0
        for i in range(pos, n):
            current = bit_at(buf, i)
            if previous and current:
                return i+1
            previous = current
        return None
    stop = first_bit(buf, pos, 0 if family == 'rice_stop0' else 1)
    if stop is None:
        return None
    q = stop-pos
    if family.startswith('rice_'):
        end = stop+1+k
    elif family == 'exp_golomb':
        end = stop+1+q+k
    elif family == 'elias_gamma':
        end = stop+1+q
    elif family == 'elias_delta':
        field_end = stop+1+q
        if field_end > n:
            return None
        length = 1
        for i in range(stop+1,field_end):
            length = length*2 + bit_at(buf,i)
            if length-1 > n-field_end:
                return None
        end = field_end+length-1
    else:
        raise ValueError('unknown family')
    return end if end <= n else None


def count(buf, family, k):
    pos = total = 0
    while pos < len(buf)*8:
        end = next_end(buf,pos,family,k)
        if end is None:
            break
        pos = end
        total += 1
    return pos,total


def bernoulli(nbytes,p,seed):
    """Generate packed bytes with identical per-bit draws to the prefix tool."""
    rng = random.Random(seed)
    out = bytearray(nbytes)
    for i in range(nbytes):
        value = 0
        for _ in range(8):
            value = (value << 1) | (rng.random() < p)
        out[i] = value
    return out


def measure(path,seed):
    with open(path,'rb') as f:
        data=f.read()
    digest=hashlib.sha256(data).hexdigest()
    w,h,payload=orf_tokens.locate_data(data)
    del data
    if w<=0 or h<=0 or not payload:
        raise ValueError('invalid geometry or empty payload')
    n=len(payload)*8
    ones=sum(bin(b).count('1') for b in payload)
    null=bernoulli(len(payload),ones/n,seed)
    results={}
    for label,buf in (('real',payload),('bernoulli',null)):
        families={}
        for family,k in FAMILIES:
            end,total=count(buf,family,k)
            families[family+'_k'+str(k)]={'count':total,'consumed_bits':end,
                                          'residual_bits':n-end,'count_per_site':total/(w*h)}
        results[label]=families
    return {'sha256':digest,'width':w,'height':h,'payload_bytes':len(payload),'ones_count':ones,
            'seed':seed,'null_sha256':hashlib.sha256(null).hexdigest(),'models':results}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('file')
    ap.add_argument('--seed',type=int,default=20261021)
    a=ap.parse_args(argv)
    try:
        start=time.perf_counter(); result=measure(a.file,a.seed)
        result['elapsed_seconds']=time.perf_counter()-start
        result['python']=sys.version.split()[0]
        print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,TypeError,IndexError,KeyError,struct.error) as exc:
        print(json.dumps({'error':type(exc).__name__}))
        return 1


if __name__=='__main__':
    sys.exit(main())
