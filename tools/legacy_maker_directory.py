#!/usr/bin/env python3
"""Inventory the declared leading OLYMP legacy directory for #949.

Only literal OLYMP-NUL/version-1-or-2 headers and the directory at relative
byte 8, in the outer TIFF byte order, are accepted. Presence/absence means
that top directory only. Numeric IDs elsewhere and tag meanings are untested.
No metadata value blocks, previews or image samples are decoded.
"""
import argparse
import hashlib
import json
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from makernote_prefix_audit import Reader
from strip_start_audit import independent_strips, startup_zeros


def directory(data,spans):
    if data[:2] not in (b'II',b'MM'): raise ValueError('byte_order')
    order='little' if data[:2]==b'II' else 'big'
    outer=Reader(data,order,spans)
    if outer.uint(2,2) not in (42,0x4f52,0x5352): raise ValueError('magic')
    outer.spans=[(0,8)]
    root=outer.directory(outer.uint(4,4))
    exif=outer.directory(outer.pointer(root,0x8769))
    item=exif.get(0x927c)
    if item is None or item[0]!=7 or item[1]<14: raise ValueError('maker_envelope')
    _,size,slot=item
    base=outer.uint(slot,4)
    if any(base<b and base+size>a for a,b in outer.spans): raise ValueError('maker_directory_overlap')
    blob=outer.block(base,size)
    if blob[:8] not in (b'OLYMP\0\x01\0',b'OLYMP\0\x02\0'):
        return {'status':'unknown','reason':'unsupported_leading_header'}
    reader=Reader(blob,order)
    reader.spans=[(0,8)]
    top=reader.directory(8)
    end=8+6+12*len(top)
    present={format(tag,'04x'):{'type':entry[0],'count':entry[1]} for tag,entry in sorted(top.items())}
    return dict(status='ok',header_hex=blob[:8].hex(),order=order,note_bytes=size,
                directory_offset=8,directory_end=end,entries=len(top),
                next_ifd=reader.uint(end-4,4),tags=present,
                paths={format(tag,'04x'):('present_uninterpreted' if tag in top else 'absent_top_entry') for tag in (0x2040,0x2050)})


def measure(data):
    g,payload=independent_strips(data)
    spans=[(a,a+n) for a,n in zip(g['strip_offsets'],g['strip_byte_counts'])]
    n=g['width']*g['height']
    size=g['payload_bytes']
    packing='packed-12' if size*2==n*3 else 'packed-12.8' if size*5==n*8 else 'packed-16' if size==2*n else 'variable'
    return dict(width=g['width'],height=g['height'],payload_bytes=size,packing=packing,
                initial_zeros=startup_zeros(payload),metadata=directory(data,spans))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--records',required=True)
    p.add_argument('--sample',nargs=2,action='append',required=True,metavar=('ID','FILE'))
    a=p.parse_args()
    with open(a.records,encoding='utf-8') as stream: records=json.load(stream)
    failed=False
    for sid,path in a.sample:
        hits=[r for r in records if str(r['id'])==sid and r['licence']=='CC0']
        if len(hits)!=1: p.error('public identity missing or ambiguous')
        r=hits[0]
        out={k:r[k] for k in ('id','name','sha256')}
        try:
            with open(path,'rb') as stream: data=stream.read(160*1024*1024+1)
            if len(data)>160*1024*1024 or hashlib.sha256(data).hexdigest()!=r['sha256']: raise ValueError('size_or_hash')
            out.update(status='ok',**measure(data))
        except (OSError,ValueError,IndexError) as exc:
            failed=True
            out.update(status='unknown',reason=str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
        print(json.dumps(out,sort_keys=True),flush=True)
    return int(failed)


if __name__=='__main__': sys.exit(main())
