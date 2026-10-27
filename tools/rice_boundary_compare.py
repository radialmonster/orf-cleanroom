#!/usr/bin/env python3
"""Compare literal Rice stop-1 k=4 and k=5 word boundaries (lead #339).

Both parses start at bit 0, MSB first. Positive shared endpoints delimit
intervals (previous shared, next shared]; bit 0 is an anchor, not a hit.
Only complete words count. Unmatched complete words after the last shared
endpoint and incomplete suffix bits are reported separately. Histogram bins
are inclusive spans in bits; word-count bins use the same numerical bounds
in words. The final bin has no upper bound. A shared
boundary does not establish physical framing, hidden-state synchronization,
or the correct code family. No pixel or decoded data is emitted.

Usage: python -I -B tools/rice_boundary_compare.py FILE --prefix-bytes 3000000 [--shuffle]
"""
import argparse
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens

BINS = ((1, 30), (31, 60), (61, 120), (121, 240), (241, 480), (481, 960), (961, None))


def endpoints(bits, k):
    """Yield completed word endpoints without retaining a boundary list."""
    pos = 0
    while pos < len(bits):
        stop = bits.find('1', pos)
        if stop < 0 or stop + 1 + k > len(bits):
            return
        pos = stop + 1 + k
        yield pos


def compare(bits):
    """Streaming merge of endpoint iterators and fixed-size interval summaries."""
    streams = [iter(endpoints(bits, k)) for k in (4, 5)]
    end = [next(it, None) for it in streams]
    count = [0, 0]
    last = [0, 0]
    at_shared = [0, 0]
    anchor = 0
    shared = 0
    sums = [0, 0]
    word_bins = [[0] * len(BINS) for _ in range(2)]
    word_max = [None, None]
    span_sum = 0
    maximum = None
    bins = [0] * len(BINS)
    while end[0] is not None or end[1] is not None:
        x = min(v for v in end if v is not None)
        both = end[0] == x and end[1] == x
        for i in range(2):
            if end[i] == x:
                count[i] += 1
                last[i] = x
                end[i] = next(streams[i], None)
        if both:
            span = x - anchor
            shared += 1
            span_sum += span
            maximum = max(maximum or 0, span)
            for j, (lo, hi) in enumerate(BINS):
                if span >= lo and (hi is None or span <= hi):
                    bins[j] += 1
                    break
            for i in range(2):
                words = count[i] - at_shared[i]
                sums[i] += words
                word_max[i] = max(word_max[i] or 0, words)
                for j, (lo, hi) in enumerate(BINS):
                    if words >= lo and (hi is None or words <= hi):
                        word_bins[i][j] += 1
                        break
                at_shared[i] = count[i]
            anchor = x
    return {'input_bits': len(bits), 'positive_shared': shared,
            'last_shared': anchor if shared else None,
            'intervals': {'bins': ([{'min': lo, 'max': hi, 'count': n} for (lo, hi), n in zip(BINS, bins)] if shared else []),
                          'span_sum': span_sum, 'span_max': maximum,
                          'mean_span': span_sum / shared if shared else None,
                          'word_counts': sums, 'word_max': word_max,
                          'word_bins': word_bins if shared else [[], []]},
            'parses': [{'k': k, 'words': count[i], 'last_endpoint': last[i],
                        'residual_bits': len(bits) - last[i],
                        'open_tail_words': count[i] - at_shared[i],
                        'open_tail_bits': last[i] - anchor} for i, k in enumerate((4, 5))]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('file')
    ap.add_argument('--prefix-bytes', type=int, required=True)
    ap.add_argument('--shuffle', action='store_true')
    ap.add_argument('--seed', type=int, default=20261022)
    a = ap.parse_args(argv)
    if a.prefix_bytes <= 0:
        ap.error('--prefix-bytes must be positive')
    try:
        with open(a.file, 'rb') as f:
            data = f.read()
        digest = hashlib.sha256(data).hexdigest()
        w, h, payload = orf_tokens.locate_data(data)
        del data
        if len(payload) < a.prefix_bytes or w <= 0 or h <= 0:
            raise ValueError('invalid geometry or short payload')
        p = bytearray(payload)
        del payload
        if a.shuffle:
            random.Random(a.seed).shuffle(p)
        prefix = p[:a.prefix_bytes]
        del p
        bits = bin(int.from_bytes(prefix, 'big'))[2:].zfill(len(prefix) * 8)
        del prefix
        result = compare(bits)
        result.update({'sha256': digest, 'width': w, 'height': h,
                       'prefix_bytes': a.prefix_bytes, 'shuffled': a.shuffle,
                       'seed': a.seed if a.shuffle else None})
        print(json.dumps(result, indent=1))
        return 0
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        print(json.dumps({'error': type(exc).__name__}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
