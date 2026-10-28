#!/usr/bin/env python3
"""Audit TIFF strip-table contiguity in table order (lead #11).

Select the unique IFD with the largest sum of strip byte counts. Dimensions,
strip table counts and each nonempty extent must be valid and within the same
input snapshot; ties in the selection are rejected. Report adjacency, forward
gaps, nonascending order and physical overlap separately. A single strip is
vacuously contiguous and is counted separately. No pixels, payload bytes or
local paths are printed. This audits container geometry, not a codec claim.

Input is --sample PUBLIC_ID PUBLIC_NAME SHA256 PATH; verify CC0 provenance separately.
Each sample hash must match. Any input failure gives an error record and exits 1;
later samples still run. Public IDs and names must be printable basenames, and content hashes unique.
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys

sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff


class AuditError(ValueError):
    pass


def audit(data):
    t=Tiff(data)
    candidates=[]
    for tags in t.all_ifds():
        counts=tags.get(0x117)
        if counts is None:continue
        if not isinstance(counts,list) or not counts or any(type(x) is not int or x<=0 for x in counts):
            raise AuditError('invalid_strip_counts')
        candidates.append((sum(counts),tags))
    if not candidates:raise AuditError('no_strip_ifd')
    largest=max(x[0] for x in candidates)
    winners=[tags for n,tags in candidates if n==largest]
    if len(winners)!=1:raise AuditError('ambiguous_largest_ifd')
    tags=winners[0]; offsets=tags.get(0x111); counts=tags.get(0x117)
    if not isinstance(offsets,list) or len(offsets)!=len(counts) or not offsets:
        raise AuditError('mismatched_strip_tables')
    if any(type(x) is not int for x in offsets):raise AuditError('invalid_strip_offsets')
    for tag in (0x100,0x101):
        value=tags.get(tag)
        if not isinstance(value,list) or len(value)!=1 or type(value[0]) is not int or value[0]<=0:
            raise AuditError('invalid_dimensions')
    if any(o<0 or o+n>len(data) for o,n in zip(offsets,counts)):
        raise AuditError('strip_extent_outside_input')
    gaps=overlaps=backward=0
    for i in range(len(offsets)-1):
        delta=offsets[i+1]-(offsets[i]+counts[i])
        gaps+=delta>0;overlaps+=delta<0;backward+=offsets[i+1]<=offsets[i]
    ordered=sorted(zip(offsets,counts))
    physical_overlap=any(b[0] < a[0]+a[1] for a,b in zip(ordered,ordered[1:]))
    return {'width':tags[0x100][0],'height':tags[0x101][0],'strip_count':len(offsets),
            'payload_bytes':largest,'single_strip':len(offsets)==1,
            'table_adjacent':gaps==0 and overlaps==0,'forward_gaps':gaps,
            'negative_table_deltas':overlaps,'nonascending_transitions':backward,
            'physical_overlap':physical_overlap}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sample',nargs=4,action='append',required=True,metavar=('PUBLIC_ID','PUBLIC_NAME','SHA256','PATH'))
    a=ap.parse_args(argv)
    checked=[];seen=set()
    for sid,name,digest,path in a.sample:
        if not sid or not sid.isprintable() or '/' in sid or '\\' in sid or not name or not name.isprintable() or '/' in name or '\\' in name or not re.fullmatch('[0-9a-f]{64}',digest):
            ap.error('invalid public identity')
        if sid in seen or digest in seen:ap.error('duplicate public identity or content')
        seen.update((sid,digest));checked.append((sid,name,digest,path))
    results=[];failures=0
    for sid,name,digest,path in checked:
        r={'id':sid,'name':name,'sha256':digest}
        try:
            with open(path,'rb') as f:data=f.read()
            if hashlib.sha256(data).hexdigest()!=digest:raise AuditError('hash_mismatch')
            r.update(audit(data));r['status']='ok'
        except AuditError as exc:
            failures+=1;r.update(status='failed',error=str(exc))
        except (OSError,ValueError,TypeError,IndexError,KeyError,struct.error) as exc:
            failures+=1;r.update(status='failed',error=type(exc).__name__)
        results.append(r)
    print(json.dumps({'results':results,'failures':failures,'complete':failures==0},indent=2))
    return int(bool(failures))

if __name__=='__main__':sys.exit(main())
