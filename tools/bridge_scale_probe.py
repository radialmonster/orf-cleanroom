#!/usr/bin/env python3
"""Fixed-support multiscale candidate-suffix bridge energies for #32.

Uses @mtakemoto's #64 mappings and bridge statistic. Nominal token blocks
are not physical rows; ratios are descriptive conditional permutation means.
"""
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_tokens import locate_data
from suffix_joint_probe import scan_prefix
import value_map_probe as legacy

LIMIT, SUPER = 262144, 512
SCALES = (32, 64, 128, 256, 512)
SAMPLES = {
    '1993': ('Olympus - E-M1MarkII - 16bit (4:3).ORF', '0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8'),
    '5283': ('OM System - OM-1 - 16bit (4:3).ORF', 'bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b'),
    '1998': ('Olympus - E-M1MarkII - 16bit (4:3).ORF', '4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71'),
    '6343': ('OM System - OM-5 - 16bit (4:3).ORF', 'ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7'),
}
PHASES = {'discovery': ('1993', '5283'), 'verification': ('1993', '5283', '1998', '6343')}


def measure(tokens):
    if len(tokens) != LIMIT:
        return {'status': 'unknown_short', 'returned_tokens': len(tokens)}
    decisions = [not any(q >= 17 for q, _ in tokens[i:i + SUPER]) for i in range(0, LIMIT, SUPER)]
    kept = [i for i, keep in enumerate(decisions) if keep]
    cells = []
    for mapping in legacy.MAPPINGS:
        mapped = [[legacy.map_suffix(s, mapping) for _, s in tokens[block * SUPER:(block + 1) * SUPER]]
                  for block in kept]
        for n in SCALES:
            terms = []
            for block in mapped:
                for start in range(0, SUPER, n):
                    _, a, v = legacy.bridge_energy_terms(block[start:start + n])
                    terms.append((a, v))
            a, v = sum(x for x, _ in terms), sum(y for _, y in terms)
            observed, expected = legacy.energies(n, a, v)
            ratio = legacy.ratio(n, a, v)
            cells.append({'mapping': mapping, 'scale': n, 'blocks': len(terms),
                          'zero_variance_blocks': sum(v0 == 0 for _, v0 in terms),
                          'sum_A': a, 'sum_V': v, 'observed': legacy.rational(observed),
                          'expected': legacy.rational(expected), 'R': legacy.rational(ratio),
                          'status': 'ok' if ratio is not None else 'unknown_zero_null'})
    return {'status': 'ok' if kept else 'unknown_empty', 'superblock_keep': decisions,
            'retained_superblocks': len(kept), 'omitted_superblocks': len(decisions) - len(kept),
            'retained_tokens': len(kept) * SUPER, 'omitted_tokens': (len(decisions) - len(kept)) * SUPER,
            'parsed_escapes': sum(q >= 17 for q, _ in tokens), 'cells': cells}


def report(sid, path):
    name, expected = SAMPLES[sid]
    with open(path, 'rb') as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != expected:
        return {'id': sid, 'name': name, 'status': 'unknown', 'reason': 'identity_mismatch'}
    w, h, payload = locate_data(data)
    if w <= 0 or h <= 0:
        raise ValueError('invalid geometry')
    tokens, end = scan_prefix(payload, LIMIT)
    result = {'id': sid, 'name': name, 'sha256': expected, 'width': w, 'height': h,
              'payload_bytes': len(payload), 'requested_tokens': LIMIT,
              'returned_tokens': len(tokens), 'bits_consumed': end}
    if len(tokens) != LIMIT:
        result.update(status='unknown', reason='short_input')
        return result
    result['measurement'] = measure(tokens)
    result['status'] = 'ok' if result['measurement']['status'] == 'ok' and all(c['status'] == 'ok' for c in result['measurement']['cells']) else 'unknown'
    return result


def main():
    ap = legacy.PrivateArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=sorted(PHASES), required=True)
    ap.add_argument('--sample', nargs=2, action='append', metavar=('ID', 'PATH'), required=True)
    args = ap.parse_args()
    if tuple(x[0] for x in args.sample) != PHASES[args.phase]:
        ap.error('sample order must match frozen phase')
    results = []
    for sid, path in args.sample:
        try:
            results.append(report(sid, path))
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            results.append({'id': sid, 'name': SAMPLES[sid][0], 'status': 'unknown', 'error_type': type(exc).__name__})
    sources = {}
    for name in ('bridge_scale_probe.py', 'value_map_probe.py', 'suffix_joint_probe.py', 'orf_tokens.py', 'orf_signature.py'):
        with open(os.path.join(os.path.dirname(__file__), name), 'rb') as f:
            sources[name] = hashlib.sha256(f.read()).hexdigest()
    print(json.dumps({'phase': args.phase, 'python_version': sys.version.split()[0],
                      'source_sha256': sources, 'samples': results}, allow_nan=False))
    return int(any(r['status'] != 'ok' for r in results))


if __name__ == '__main__':
    sys.exit(main())
