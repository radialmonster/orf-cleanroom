#!/usr/bin/env python3
"""Fixed suffix-table transfer and vertical shift comparison on named files."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_table_cross_body_probe as cross
from suffix_table_shift_probe import shift_scores

ADDITIONAL = {
    '6344': ('OM System - OM-5 - 16bit (4:3).ORF',
             '42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512', 8200, 6132),
    '6346': ('OM System - OM-5 - 16bit (4:3).ORF',
             'ffd47d5924b65abdd8af761665d67705fe028cfd08e5efbc264b64a20830d9f4', 10400, 7792),
    '3803': ('Olympus - E-M1MarkIII - 16bit (4:3).ORF',
             '4ad47518e3766fae6b98f8b18f3aae3c277e5966028e3f2e0d2702bb0f17a3cd', 10400, 7792),
    '3802': ('Olympus - E-M1MarkIII - 16bit (4:3).ORI',
             '83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46', 5240, 3912),
}
PHASES = {'discovery': ('3801', '3800', '6343', '6344', '3803'),
          'verification': ('3801', '3800', '6343', '6344', '3803', '6346', '3802')}


def measure(x, y, q, s, info, fit):
    transfer = cross.score(x, y, q, s, info, fit)
    prediction = cross.legacy.predict(x, fit)
    shifts = shift_scores(y, prediction, info['used_preview_rows'], info['preview_width_blocks'])
    if shifts['status'] != 'ok' or not math.isfinite(shifts['zero_r']):
        raise ValueError('undefined shift scores')
    if abs(shifts['zero_r'] - transfer['r']) > 1e-12:
        raise ValueError('legacy score disagreement')
    shifts['best_nonzero_r'] = max(shifts['scores'][1:])
    return {'transfer': transfer, 'vertical_shifts': shifts}


def main():
    parser = cross.SafeParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(PHASES), required=True,
                        help='verification adds 6346 and 3802')
    parser.add_argument('--train', required=True, help='path to the verified CC0 training file 1995')
    parser.add_argument('--sample', nargs=2, action='append', required=True, metavar=('ID', 'PATH'),
                        help='first supply 3801, 3800, 6343, 6344 and 3803 in that order')
    args = parser.parse_args()
    if tuple(item[0] for item in args.sample) != PHASES[args.phase]:
        parser.error('frozen sample order required')
    samples = dict(cross.SAMPLES)
    samples.update(ADDITIONAL)
    report, status = cross.run(args.phase, args.train, args.sample, samples, measure)
    print(json.dumps(report, allow_nan=False))
    return status


if __name__ == '__main__':
    sys.exit(main())
