#!/usr/bin/env python3
"""Stratify numeric preview-screen pairs by recorded EXIF date (lead #347).

Consumes the full JSON-lines output of preview_pair_screen plus a fixed cohort
JSON array of {sha256, model, group} (group: original or extension) and local paths for every cohort member. Model
is exact supplied manifest text, not a physical camera identity. Valid EXIF
DateTimeOriginal values define same second, same day within 600 seconds,
same day beyond 600 seconds, or different recorded day. Missing, invalid and
ambiguities rejected by the repository EXIF parser are grouped as unavailable;
this is not a complete audit of every possible EXIF ambiguity. Timestamps do
not establish scene, capture independence, clock accuracy or timezone.

Reports eligible and positive pair counts for all and same-model scopes, with
unscored pairs separately. The fixed 0.98 screen threshold is not a calibrated
same-scene classifier. No timestamps, local paths, preview grids or pixels are
printed. Every cohort hash must match its input; incomplete pair lists fail.
"""
import argparse
import itertools
import json
import os
import re
import struct
import sys

sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import capture_pair_calibration as calibration

BINS=('same_second','same_day_within_600s','same_day_after_600s','different_day','unavailable')
THRESHOLD=.98


def bucket(a,b):
    if not a['dto'] or not b['dto']:
        return 'unavailable'
    if a['dto']==b['dto']:
        return 'same_second'
    if a['dto'][:10]!=b['dto'][:10]:
        return 'different_day'
    return 'same_day_within_600s' if abs((a['time']-b['time']).total_seconds())<=600 else 'same_day_after_600s'


def aggregate(records,cohort,metadata):
    """Validate complete unordered pair universe and return fixed-bin counts."""
    expected=set(cohort)
    if set(metadata)!=expected:
        raise ValueError('cohort and input hashes differ')
    summaries=[r['summary'] for r in records if 'summary' in r]
    if len(summaries)!=1 or not isinstance(summaries[0],dict):raise ValueError('invalid screen summary')
    summary=summaries[0]
    if summary.get('grid')!=12 or summary.get('min_sd')!=1.0 or summary.get('threshold')!=THRESHOLD or summary.get('alignment')!='identity_only':raise ValueError('incompatible screen settings')
    samples=[r['sample'] for r in records if 'sample' in r]
    if any(not isinstance(x,dict) or x.get('sha256') not in expected or x.get('status') not in ('ok','unsupported','low_information') for x in samples):raise ValueError('invalid screen samples')
    if len(samples)!=len(expected) or {x['sha256'] for x in samples}!=expected:raise ValueError('incomplete screen samples')
    # Existing analyser validates unique pair objects, hashes and finite scores.
    calibration.analyse(records,metadata,600)
    statuses={x['sha256']:x['status'] for x in samples}
    pairs={}
    for rec in records:
        if 'pair' not in rec: continue
        a,b=rec['pair']; key=tuple(sorted((a,b)))
        if a not in expected or b not in expected: raise ValueError('unknown pair hash')
        if (rec['r'] is None) != (statuses[a]!='ok' or statuses[b]!='ok'):raise ValueError('pair score and sample status differ')
        pairs[key]=rec['r']
    wanted=set(itertools.combinations(sorted(expected),2))
    if set(pairs)!=wanted: raise ValueError('incomplete pair universe')
    strata=('all_pairs','original_original','original_extension','extension_extension')
    counts={scope:{part:{name:{'eligible':0,'positive':0} for name in BINS} for part in strata} for scope in ('all','same_model')}
    unscored={scope:{part:0 for part in strata} for scope in ('all','same_model')}
    for (a,b),score in pairs.items():
        scopes=['all']
        if cohort[a][0]==cohort[b][0]:scopes.append('same_model')
        groups=sorted((cohort[a][1],cohort[b][1]))
        part={'originaloriginal':'original_original','extensionoriginal':'original_extension','extensionextension':'extension_extension'}[''.join(groups)]
        for scope in scopes:
            for partition in ('all_pairs',part):
                if score is None:unscored[scope][partition]+=1;continue
                row=counts[scope][partition][bucket(metadata[a],metadata[b])]
                row['eligible']+=1;row['positive']+=score>=THRESHOLD
    eligible=sum(x is not None for x in pairs.values())
    positive=sum(x is not None and x>=THRESHOLD for x in pairs.values())
    if (summary.get('samples'),summary.get('pairs'),summary.get('eligible_pairs'),summary.get('screen_positive'))!=(len(expected),len(pairs),eligible,positive):raise ValueError('screen summary differs from pairs')
    sample_counts={group:{'ok':0,'unsupported':0,'low_information':0,'metadata_unavailable':0} for group in ('original','extension')}
    for sha,status in statuses.items():
        group=cohort[sha][1]
        sample_counts[group][status]+=1
        sample_counts[group]['metadata_unavailable']+=not bool(metadata[sha]['dto'])
    return {'cohort_size':len(expected),'total_pairs':len(pairs),'threshold':THRESHOLD,
            'samples':sample_counts,'counts':counts,'unscored':unscored}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--screen',required=True)
    ap.add_argument('--cohort',required=True,help='JSON array of public sha256 and model fields')
    ap.add_argument('--files-from',required=True,help='UTF-8 paths, one per line')
    a=ap.parse_args(argv)
    try:
        with open(a.cohort,encoding='utf-8-sig') as f: raw=json.load(f,object_pairs_hook=calibration.unique_screen_object)
        if not isinstance(raw,list):raise ValueError('invalid cohort')
        cohort={}
        for row in raw:
            if not isinstance(row,dict):raise ValueError('invalid cohort row')
            sha,model,group=row.get('sha256'),row.get('model'),row.get('group')
            if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha) or not isinstance(model,str) or not model or group not in ('original','extension') or sha in cohort:raise ValueError('invalid cohort identity')
            cohort[sha]=(model,group)
        with open(a.files_from,encoding='utf-8-sig') as f: paths=[line.strip() for line in f if line.strip()]
        meta={}
        for path in paths:
            sha,m=calibration.file_meta(path)
            if sha in meta:raise ValueError('duplicate input content')
            meta[sha]=m
        print(json.dumps(aggregate(calibration.load_screen(a.screen),cohort,meta),indent=2,sort_keys=True))
        return 0
    except (OSError,UnicodeError,ValueError,TypeError,KeyError,IndexError,struct.error) as exc:
        print(json.dumps({'error':type(exc).__name__}))
        return 1

if __name__=='__main__': sys.exit(main())
