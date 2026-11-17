"""Summarize origin full-grid aggregate JSON without reintroducing failures."""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from free_anchor_origin import ORIGINS, STARTS, summarize_stages

IDENTITIES = {
    '1993': '0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8',
    '5283': 'bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b',
    '1995': '8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f',
    '6344': '42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512',
}


def missing_report(sample_id):
    """A missing fixed input contributes unknown cells, never a pass."""
    families = []
    for bits in (16, 12):
        for mapping, origins in ORIGINS.items():
            for stride in (1, 2):
                cases = [{'origin': c, 'status': 'missing_file', 'passes': None} for c in origins]
                families.append({'bits': bits, 'mapping': mapping, 'stride': stride, 'cases': cases})
    return {'sample': {'pixls_id': sample_id, 'sha256': IDENTITIES[sample_id],
                       'windows': [{'start_token': start, 'families': families} for start in STARTS]}}


def complete_fixed(reports, expected):
    by_id = {}
    for digest, report in reports:
        sample = report['sample']
        sid = sample['pixls_id']
        if sid not in expected or sid in by_id or sample['sha256'] != IDENTITIES[sid]:
            raise ValueError('unexpected, duplicate or hash-mismatched input')
        if [w['start_token'] for w in sample['windows']] != list(STARTS):
            raise ValueError('fixed windows required')
        by_id[sid] = (digest, report)
    return [by_id.get(sid, (None, missing_report(sid))) for sid in expected]


def load(paths):
    result = []
    for path in paths:
        with open(path, 'rb') as handle:
            data = handle.read()
        report = json.loads(data)
        result.append((hashlib.sha256(data).hexdigest(), report))
    return result


def status_counts(report):
    counts = {}
    windows = {}
    for window in report['sample']['windows']:
        for family in window['families']:
            name = '%s/B%d/d%d' % (family['mapping'], family['bits'], family['stride'])
            bucket = windows.setdefault(name, {'fully_adjudicated': 0, 'partly_adjudicated': 0,
                                                'unadjudicated': 0, 'escape': 0, 'short': 0})
            statuses = [case['status'] for case in family['cases']]
            observed = sum(case['passes'] is not None for case in family['cases'])
            if all(status == 'escape' for status in statuses):
                category = 'escape'
            elif all(status == 'short' for status in statuses):
                category = 'short'
            elif observed == len(statuses):
                category = 'fully_adjudicated'
            elif observed:
                category = 'partly_adjudicated'
            else:
                category = 'unadjudicated'
            bucket[category] += 1
            for case in family['cases']:
                status = case['status']
                counts[status] = counts.get(status, 0) + 1
    return counts, windows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--discovery', action='append', required=True, metavar='JSON')
    parser.add_argument('--postlead', action='append', default=[], metavar='JSON')
    parser.add_argument('--stage', required=True, choices=('discovery', 'verification'))
    args = parser.parse_args()
    if args.stage == 'discovery' and args.postlead:
        parser.error('post-lead reports require verification stage')
    discovery = complete_fixed(load(args.discovery), ('1993', '5283'))
    postlead = (complete_fixed(load(args.postlead), ('1993', '5283', '1995', '6344'))
                if args.stage == 'verification' else [])
    stages = summarize_stages([r for _, r in discovery], [r for _, r in postlead])
    inputs = []
    for phase, reports in (('discovery', discovery), ('postlead', postlead)):
        for digest, report in reports:
            counts, windows = status_counts(report)
            inputs.append({'phase': phase, 'aggregate_sha256': digest,
                           'pixls_id': report['sample']['pixls_id'],
                           'sample_sha256': report['sample']['sha256'],
                           'missing': digest is None,
                           'case_status_counts': counts, 'family_window_counts': windows})
    sources = {}
    for filename in ('free_anchor_origin_summary.py', 'free_anchor_origin.py',
                     'free_anchor_second_order.py', 'suffix_joint_probe.py', 'orf_signature.py'):
        with open(os.path.join(os.path.dirname(__file__), filename), 'rb') as handle:
            sources[filename] = hashlib.sha256(handle.read()).hexdigest()
    print(json.dumps({'source_sha256': sources, 'inputs': inputs, 'families': stages}, indent=2))


if __name__ == '__main__':
    main()
