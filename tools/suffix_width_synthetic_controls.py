#!/usr/bin/env python3
"""Synthetic candidate-width endpoint controls for #29 item 1.

For fixed polarity, next-stop position is nondecreasing in the start bit;
therefore increasing k strictly increases each equal-index completed endpoint
when both parses exist. Equal counts can still have different residual tails.
Unknown polarity can allow exact closure at the same word count for two widths.
These finite fixtures identify neither camera framing nor a suffix width.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_width_probe


def trace(data, k, stop):
    """Independent bit-string endpoint trace for these bounded fixtures."""
    bits = ''.join(format(b, '08b') for b in data)
    pos, ends = 0, []
    while True:
        found = bits.find(str(stop), pos)
        if found < 0 or found + 1 + k > len(bits):
            return ends
        pos = found + 1 + k
        ends.append(pos)


def case(data, specs):
    results = []
    for k, stop in specs:
        report = suffix_width_probe.scan(data, k, stop)
        ends = trace(data, k, stop)
        if (report['tokens'] != len(ends) or
                report['bits_consumed'] != (ends[-1] if ends else 0)):
            raise AssertionError('scanner and trace disagree')
        results.append({'k': k, 'stop_bit': stop, 'word_ends': ends,
                        'q_histogram': report['q_histogram'],
                        'unconsumed_bits': report['unconsumed_bits']})
    return results


def repeated_bits(word, count):
    bits = word * count
    if len(bits) % 8:
        raise ValueError('synthetic fixture must end at a byte boundary')
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def run(phase):
    result = {'opposite_polarity_exact_end': case(repeated_bits('0101010', 8), ((5, 1), (6, 0))),
              'same_polarity_residual': case(bytes.fromhex('0040'), ((5, 1), (6, 1)))}
    if phase == 'verification':
        result['extension_opposite_polarity_exact_end'] = case(repeated_bits('0111010', 16), ((5, 1), (6, 0)))
        result['extension_same_polarity_truncated_suffix'] = case(bytes.fromhex('0041'), ((5, 1), (6, 1)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('discovery', 'verification'), default='discovery')
    args = parser.parse_args()
    print(json.dumps({'phase': args.phase, 'cases': run(args.phase)}, indent=2))


if __name__ == '__main__':
    main()
