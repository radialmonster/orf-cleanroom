#!/usr/bin/env python3
"""Bounded literal MakerNote/payload-prefix cross-check for lead #949.

No tag meanings or codec parameters are inferred. Leading OLYMPUS and
OM SYSTEM layouts only; unsupported scope remains unknown, not tag absence.
Only public identities and aggregate metadata are printed. No image decoding.
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_start_audit import independent_strips, startup_zeros

WANTED = {0x2040: [0x0611, 0x0620]+list(range(0x0640, 0x064a))+list(range(0x0650, 0x0655)),
          0x2050: [0x1800]}


class Reader:
    def __init__(self, data, order, forbidden=()):
        self.data, self.order, self.forbidden = data, order, list(forbidden)
        self.spans = []

    def block(self, at, size):
        if at < 0 or size < 0 or at+size > len(self.data):
            raise ValueError('bounds')
        if any(at < b and at+size > a for a,b in self.forbidden):
            raise ValueError('metadata_overlap')
        return self.data[at:at+size]

    def uint(self, at, size):
        return int.from_bytes(self.block(at,size), self.order)

    def directory(self, at):
        n=self.uint(at,2)
        if n>4096:
            raise ValueError('directory_limit')
        end=at+6+12*n
        self.block(at,end-at)
        if any(at < b and end > a for a,b in self.spans):
            raise ValueError('directory_overlap')
        self.spans.append((at,end))
        result={}
        for slot in range(at+2,end-4,12):
            tag=self.uint(slot,2)
            if tag in result:
                raise ValueError('duplicate_tag')
            result[tag]=(self.uint(slot+2,2),self.uint(slot+4,4),slot+8)
        return result

    def pointer(self, tags, tag, typ=4):
        item=tags.get(tag)
        if item is None or item[:2]!=(typ,1):
            raise ValueError('pointer_shape')
        return self.uint(item[2],4)

    def value(self, tags, tag):
        entry=tags.get(tag)
        if entry is None:
            return {'status':'absent'}
        typ,n,slot=entry
        result={'type':typ,'count':n}
        if not ((typ==3 and 1<=n<=8) or (typ==4 and n==1)):
            return dict(result,status='unsupported_shape')
        unit=2 if typ==3 else 4
        at=slot if n*unit<=4 else self.uint(slot,4)
        if n*unit>4 and any(at < b and at+n*unit > a for a,b in self.spans):
            raise ValueError('value_directory_overlap')
        return dict(result,status='ok',values=[self.uint(at+i*unit,unit) for i in range(n)])


def metadata(data, strips, wanted_paths=None):
    if data[:2] not in (b'II',b'MM'):
        raise ValueError('tiff_order')
    outer=Reader(data,'little' if data[:2]==b'II' else 'big',strips)
    if outer.uint(2,2) not in (42,0x4f52,0x5352):
        raise ValueError('tiff_magic')
    outer.spans=[(0,8)]
    root=outer.directory(outer.uint(4,4))
    exif=outer.directory(outer.pointer(root,0x8769))
    note=exif.get(0x927c)
    if note is None or note[0]!=7 or note[1]<18:
        raise ValueError('maker_envelope')
    _,size,slot=note
    base=outer.uint(slot,4)
    if any(base < b and base+size > a for a,b in outer.spans):
        raise ValueError('maker_directory_overlap')
    blob=outer.block(base,size)
    if blob.startswith(b'OLYMPUS\0'):
        prefix=8
    elif blob.startswith(b'OM SYSTEM\0\0\0'):
        prefix=12
    else:
        return {'status':'unknown','reason':'unsupported_leading_header'}
    if blob[prefix:prefix+2] not in (b'II',b'MM'):
        return {'status':'unknown','reason':'maker_order'}
    maker=Reader(blob,'little' if blob[prefix:prefix+2]==b'II' else 'big')
    maker.spans=[(0,prefix+4)]
    top=maker.directory(prefix+4)
    # The declared scalar preview interval is an exclusion, not an endorsed JPEG.
    settings=maker.directory(maker.pointer(top,0x2020,13))
    start=maker.pointer(settings,0x0101)
    length=maker.pointer(settings,0x0102)
    if not length or base+start+length>len(data):
        raise ValueError('preview_extent_unknown')
    if any(start < b and start+length > a for a,b in maker.spans):
        raise ValueError('preview_directory_overlap')
    maker.forbidden.append((start,start+length))
    paths={}
    for parent,wanted in (WANTED if wanted_paths is None else wanted_paths).items():
        path='%04x'%parent
        ref=top.get(parent)
        if ref is None:
            paths[path]={'status':'absent_directory'}
            continue
        try:
            directory=maker.directory(maker.pointer(top,parent,13))
            paths[path]={'status':'ok','tags':{'%04x'%tag:maker.value(directory,tag) for tag in wanted}}
        except ValueError as exc:
            paths[path]={'status':'unknown','reason':str(exc)}
    return {'status':'ok','header_bytes':prefix,'paths':paths}


def measure(data):
    geometry,payload=independent_strips(data)
    spans=[(a,a+b) for a,b in zip(geometry['strip_offsets'],geometry['strip_byte_counts'])]
    count=geometry['width']*geometry['height']
    size=geometry['payload_bytes']
    packing=('packed-12' if 2*size==3*count else 'packed-12.8' if 5*size==8*count
             else 'packed-16' if size==2*count else 'variable')
    return {'payload':[geometry['width'],geometry['height']], 'size_class':packing,
            'leading_zero_bits':startup_zeros(payload), 'metadata':metadata(data,spans)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records',required=True,help='retained verified public CC0 records')
    parser.add_argument('--sample',nargs=2,action='append',required=True,metavar=('ID','PATH'))
    args=parser.parse_args()
    with open(args.records,encoding='utf-8') as stream:
        records=json.load(stream)
    rows=[]
    for sid,path in args.sample:
        hits=[r for r in records if str(r['id'])==sid and r['licence']=='CC0']
        if len(hits)!=1:
            raise ValueError('public_identity')
        r=hits[0]
        row={k:r[k] for k in ('id','name','sha256')}
        try:
            with open(path,'rb') as stream:
                data=stream.read(160*1024*1024+1)
            if len(data)>160*1024*1024 or hashlib.sha256(data).hexdigest()!=r['sha256']:
                raise ValueError('size_or_hash')
            row.update(status='ok',**measure(data))
        except (OSError,ValueError,IndexError) as exc:
            row.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        rows.append(row)
    print(json.dumps({'samples':rows},indent=2))
    return int(any(r['status']!='ok' for r in rows))


if __name__=='__main__':
    sys.exit(main())
