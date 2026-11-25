"""Fixed #144 head sensitivity on candidate q tokens, not physical rows."""
import argparse
from array import array
import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens
import token_row_stride
import token_band_profile

HEADS = (8, 16, 32, 64, 128)
SAMPLES = {
    '1993': '0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8',
    '1995': '8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f',
    '1997': '89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a',
    '1998': '4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71',
    '6343': 'ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7',
    '6344': '42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512',
    '6345': 'c8277d133c7ac86c7e4af5787fa06515fef8fe044c1b22209c62704537c48e02',
    '8549': 'c6fe861982ddc18464cf6858d2700f6813cc3a17956bcb12d1179212c999c76a',
    '5283': 'bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b',
}


def later(q, stride, head):
    result = token_band_profile.profile(q, stride, 1000, 300, head)
    if not result['complete']:
        return {'status': 'insufficient', 'complete_rows': result['complete_rows']}
    return {'status': 'ok' if result['score_defined'] else 'undefined', **result}


def scan_payload(payload, requested):
    qs, suffixes = array('B'), array('B')
    _, bits = orf_tokens.scan(payload, requested, 0, 0, None, qs, suffixes, 40)
    return qs, bits


def compare(q, width):
    hi = width + 1200
    if len(q) < 300 * hi:
        return {'status': 'insufficient_prefix', 'parsed_tokens': len(q)}
    prefix = q[:300 * hi]
    tables = {h: token_row_stride.stride_scores(prefix, width, hi, 300, h) for h in HEADS}
    if any(not table for table in tables.values()):
        return {'status': 'insufficient_candidates'}
    legacy = tables[32][0][2]
    output = []
    for head in HEADS:
        scores = tables[head]
        z, elev, winner, n = scores[0]
        tied = sorted(row[2] for row in scores if row[0] == z)
        nominal = next((row for row in scores if row[2] == width), None)
        second = scores[1][0] if len(scores) > 1 else None
        margin = z - second if second is not None and math.isfinite(z) and math.isfinite(second) else None
        output.append({'head': head, 'status': 'ok' if math.isfinite(z) else 'nonfinite_prefix', 'winner': winner,
                       'ties_exact': tied, 'z': z if math.isfinite(z) else None,
                       'z_sign': ('positive_infinity' if z > 0 else 'negative_infinity') if not math.isfinite(z) else None,
                       'runner_up_margin': margin, 'elevation': elev, 'rows': n,
                       'width_z': nominal[0] if nominal and math.isfinite(nominal[0]) else None,
                       'width_status': 'ok' if nominal and math.isfinite(nominal[0]) else 'undefined',
                       'width_elevation': nominal[1] if nominal else None,
                       'winner_later': later(q, winner, head),
                       'head32_winner_later': later(q, legacy, head)})
    return {'status': 'ok', 'legacy_head32_winner': legacy, 'heads': output}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'invalid arguments\n')


def main():
    parser = SafeParser(description=__doc__)
    parser.add_argument('--sample', nargs=4, action='append', required=True, metavar=('ID', 'NAME', 'SHA256', 'PATH'))
    args = parser.parse_args()
    if any(sid not in SAMPLES or digest != SAMPLES[sid] or not name or not name.isprintable()
           or '/' in name or '\\' in name for sid, name, digest, path in args.sample):
        parser.error('identity')
    if len({sid for sid, _, _, _ in args.sample}) != len(args.sample):
        parser.error('duplicate')
    reports = []
    for sid, name, digest, path in args.sample:
        try:
            with open(path, 'rb') as stream:
                data = stream.read(128*1024*1024 + 1)
            if len(data) > 128*1024*1024 or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('size_or_hash')
            width, height, payload = orf_tokens.locate_data(data)
            requested = 1300 * (width + 1200)
            qs, bits = scan_payload(payload, requested)
            report = compare(qs, width)
            report.update(id=sid, name=name, sha256=digest, width=width, height=height,
                          requested_tokens=requested, parsed_tokens=len(qs), consumed_bits=bits)
        except (OSError, ValueError, IndexError, KeyError, TypeError, OverflowError) as exc:
            report = {'id': sid, 'name': name, 'sha256': digest, 'status': 'unknown', 'reason': type(exc).__name__}
        reports.append(report)
    print(json.dumps({'samples': reports}, allow_nan=False))
    return int(any(r['status'] != 'ok' or any(h['status'] != 'ok' or
               h['winner_later']['status'] != 'ok' or h['head32_winner_later']['status'] != 'ok'
               for h in r.get('heads', [])) for r in reports))


if __name__ == '__main__':
    sys.exit(main())
