#!/usr/bin/env python3
"""Synthetic patent-derived adaptive Rice state perturbation diagnostic (#300).

Only supplied-state synthetic magnitudes are used; no camera input or predictor
is modeled. The example thresholds are from US7715639B2. Startup k=5,
bit_length(0)=0, line length and serialization are explicit test conventions.
Each edited parse is compared to its own unedited baseline and, for generated real streams, separately to the adaptive64 generating parse. Shuffled streams have no generator-truth reference. Matches within a finite window do not prove permanent recovery or a codec.
"""
import argparse
import json
import random

LAWS = ('adaptive64', 'fixed5', 'adaptive32')
ANCHORS = (17, 61, 127)
OPS = ('flip', 'insert', 'delete')
WINDOW = 128


def next_state(state, magnitude, period):
    """Next-decision state; reset counters before processing prior magnitude."""
    _, one, two, phase = state
    phase = (phase + 1) % period
    if phase == 0:
        one = two = 0
    one = one + 1 if magnitude <= 3 else 0
    two = two + 1 if magnitude <= 15 else 0
    k = max(magnitude.bit_length(), min(2 if one >= 2 else 5,
                                        4 if two >= 2 else 5))
    return (k, one, two, phase)


def encode(values):
    state = (5, 0, 0, 0)
    out = []
    for v in values:
        if not isinstance(v, int) or v < 0:
            raise ValueError('nonnegative integer magnitudes required')
        k = state[0]
        out.append('0' * (v >> k) + '1' + format(v & ((1 << k)-1), '0%db' % k))
        state = next_state(state, v, 64)
    return ''.join(out)


def parse(bits, law):
    if law not in LAWS or any(x not in '01' for x in bits):
        raise ValueError('bad bits or law')
    state = (5, 0, 0, 0)
    period = 64 if law == 'adaptive64' else 32
    out, pos = [], 0
    while pos < len(bits):
        start = pos
        k = 5 if law == 'fixed5' else state[0]
        stop = bits.find('1', pos)
        if stop < 0 or stop + 1 + k > len(bits):
            break
        pos = stop + 1 + k
        v = ((stop-start) << k) + int(bits[stop+1:pos] or '0', 2)
        if law != 'fixed5':
            state = next_state(state, v, period)
        out.append((start, pos, v, state if law != 'fixed5' else None))
    return out, len(bits)-pos


def suffix_stable(original, mutant, end, anchor, require_state):
    """Finite bidirectional boundary/state agreement with fixed exposure."""
    common = sorted(original.keys() & mutant.keys())
    for b in common:
        old = sorted(x for x in original if x >= b)
        new = sorted(x for x in mutant if x >= b)
        if end-b < 32 or len(old) < 4 or old != new:
            continue
        if require_state and any(original[x][2] != mutant[x][2] for x in old):
            continue
        return b-anchor
    return None


def value_comparison(original, mutant, anchor):
    """Compare matching unchanged spans; zero mismatches are structural.

    The first stop and common complete span length determine q and k, so
    identical mapped bits force the same Rice value, including k=0. This
    sanity check is not independent evidence of state or value recovery.
    """
    common = original.keys() & mutant.keys()
    comparable = [b for b in common if original[b][0] > anchor and
                  mutant[b][0] > anchor and original[b][0] == mutant[b][0]]
    return len(comparable), sum(original[b][1] != mutant[b][1] for b in comparable)


def compare_tokens(original_tokens, mutant_tokens, anchor, delta, end, state_na):
    """Compare two complete-token ledgers in mapped original coordinates."""
    original = {e: (s, v, st) for s, e, v, st in original_tokens if e > anchor}
    mutant = {e-delta: (s-delta, v, st) for s, e, v, st in mutant_tokens if e > anchor+delta}
    common = sorted(original.keys() & mutant.keys())
    state_hits = None if state_na else sum(original[b][2] == mutant[b][2] for b in common)
    comparable, mismatch = value_comparison(original, mutant, anchor)
    boundary = suffix_stable(original, mutant, end, anchor, False)
    state = None if state_na else suffix_stable(original, mutant, end, anchor, True)
    return {'common_boundaries':len(common), 'transient_state_hits':state_hits,
            'comparable_values':comparable, 'value_mismatches':mismatch,
            'boundary_suffix_stable_distance':boundary, 'boundary_censored':boundary is None,
            'state_suffix_stable_distance':state, 'state_censored':None if state_na else state is None}


def trial(bits, law, anchor, operation, truth_reference=False):
    end = anchor + WINDOW
    if anchor < 0 or end > len(bits) or operation not in OPS:
        return {'status': 'short_window'}
    if operation == 'flip':
        changed = bits[:anchor] + ('1' if bits[anchor] == '0' else '0') + bits[anchor+1:]
        delta = 0
    elif operation == 'insert':
        changed = bits[:anchor] + '1' + bits[anchor:]
        delta = 1
    else:
        changed = bits[:anchor] + bits[anchor+1:]
        delta = -1
    original, otail = parse(bits[:end], law)
    mutant, mtail = parse(changed[:end+delta], law)
    own = compare_tokens(original, mutant, anchor, delta, end, law == 'fixed5')
    truth = None
    if truth_reference:
        truth_tokens, truth_tail = parse(bits[:end], 'adaptive64')
        truth = compare_tokens(truth_tokens, mutant, anchor, delta, end, law == 'fixed5')
        truth['original_tail_bits'] = truth_tail
        truth['different_transition_laws'] = law != 'adaptive64'
    return {'status':'ok', 'original_tail_bits':otail, 'changed_tail_bits':mtail,
            'original_truncated_word':otail > 0, 'changed_truncated_word':mtail > 0,
            'self_baseline':own, 'truth_reference':truth, 'exposure_bits':WINDOW}


def experiment(split):
    if split not in ('discovery', 'validation'):
        raise ValueError('split required')
    reports=[]
    seeds = range(400,404) if split == 'discovery' else range(500,508)
    for split, seeds in ((split, seeds),):
        for seed in seeds:
            rng=random.Random(seed)
            values = ([rng.randrange(32) for _ in range(256)] if split == 'discovery'
                      else [rng.randrange(4) if rng.randrange(2)==0 else 16+rng.randrange(16)
                            for _ in range(256)])
            raw=encode(values)
            shuffled=list(raw); random.Random(seed+10000).shuffle(shuffled)
            for kind, bits in (('real',raw), ('shuffle',''.join(shuffled))):
                for law in LAWS:
                    for operation in OPS:
                        for anchor in ANCHORS:
                            reports.append({'split':split,'seed':seed,'kind':kind,'law':law,
                                            'operation':operation,'anchor':anchor,
                                            'result':trial(bits,law,anchor,operation, truth_reference=(kind == 'real'))})
    return {'protocol':{'discovery_seeds':list(range(400,404)),
                        'validation_seeds':list(range(500,508)),
                        'values_per_stream':256,'anchors':ANCHORS,'window_bits':WINDOW,
                        'reset_convention':'counters reset before processing prior magnitude',
                        'shuffle_seed':'seed+10000','zero_bit_length':0,
                        'limits':'synthetic only; finite recovery, not camera framing'},
            'trials':reports}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--split', required=True, choices=('discovery','validation'))
    args=ap.parse_args(argv)
    print(json.dumps(experiment(args.split),indent=2))


if __name__ == '__main__':
    main()
