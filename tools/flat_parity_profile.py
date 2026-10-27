#!/usr/bin/env python3
"""Nominal W-token parity stability for #338; no physical row or CFA inference.

Uses bounded candidate k=5 tokens; q=0/suffix 0 or 8 define the contrast.
Training blocks 2:202 fix orientation. Later complete blocks are evaluated;
missing input, a tied template or zero eligible blocks yields undefined.
Coverage 0.9 and absolute contrast 0.1 are descriptive practical filters,
not calibrated significance. The within-block shuffle is descriptive only and
uses the real stream's fitted orientation. A null verdict is undefined even
when the input is complete; inspect zero_opposing rather than exit status alone.
"""
import argparse
import hashlib
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bayer_grid_probe as grid
import orf_tokens


def profile(qs, ss, width, fixed_orientation=None, use_fixed=False):
    if width <= 0 or len(qs) != len(ss):
        raise ValueError('invalid token arrays or width')
    blocks, tail = divmod(len(qs), width)
    rows = []
    for r in range(blocks):
        a = b = 0
        for col in range(width):
            i = r * width + col
            if qs[i] == 0 and ss[i] in (0, 8):
                if (col % 2 == 0 and ss[i] == 0) or (col % 2 == 1 and ss[i] == 8):
                    a += 1
                else:
                    b += 1
        numerator = (a - b) * (1 if r % 2 == 0 else -1)
        denominator = a + b
        eligible = denominator * 10 >= 9 * width and abs(numerator) * 10 >= denominator and denominator > 0
        rows.append(dict(block=r, numerator=numerator, denominator=denominator,
                         eligible=eligible, tie=numerator == 0))
    template = sum(row['numerator'] for row in rows[2:202]) if blocks >= 202 else 0
    orientation = fixed_orientation if use_fixed else (1 if template > 0 else -1 if template < 0 else None)
    evaluation = rows[202:]
    eligible = [r for r in evaluation if r['eligible']]
    opposing = sum(1 for r in eligible if r['numerator'] * orientation < 0) if orientation else None
    verdict = None if orientation is None or not eligible else opposing == 0
    return dict(complete=blocks >= 202, complete_blocks=blocks, partial_tokens=tail,
                training_numerator=template, orientation=orientation, evaluation_total=len(evaluation),
                eligible=len(eligible), low_information=len(evaluation)-len(eligible),
                ties=sum(r['tie'] for r in evaluation), opposing=opposing, zero_opposing=verdict, blocks=rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('file')
    ap.add_argument('--sha256', required=True)
    ap.add_argument('--tokens', type=int, help='profile this many prefix tokens (default: all)')
    args = ap.parse_args()
    if args.tokens is not None and args.tokens <= 0:
        ap.error('--tokens must be positive')
    try:
        with open(args.file, 'rb') as f:
            data = f.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != args.sha256:
            raise ValueError('hash mismatch')
        width, height, payload = orf_tokens.locate_data(data)
        del data
        qs, ss, used = grid.parse(payload)
        whole_tokens = len(qs)
        if args.tokens is not None and whole_tokens < args.tokens:
            raise ValueError('requested prefix unavailable')
        if args.tokens is not None:
            qs, ss = qs[:args.tokens], ss[:args.tokens]
        real = profile(qs, ss, width)
        control = profile(qs, grid.shuffled(ss, width, 20261023), width,
                          fixed_orientation=real['orientation'], use_fixed=True)
        print(json.dumps(dict(sha256=digest, width=width, height=height,
                              whole_tokens=whole_tokens, profile_tokens=len(qs),
                              consumed_bits=used, residual_bits=len(payload)*8-used,
                              seed=20261023, real=real, shuffled=control)))
        return 0 if real['complete'] else 1
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        print(json.dumps(dict(complete=False, error=type(exc).__name__)))
        return 1


if __name__ == '__main__':
    sys.exit(main())
