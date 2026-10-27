#!/usr/bin/env python3
"""Frozen cyclic phase prediction for hypothesis #296 (builds on #144).

Candidate grammar only: zero-run, stop one, five suffix bits; no escape skip.
q>=17 is retained and q capped40. Cyclic heads wrap WITHIN fixed candidate
blocks, not physical rows. First three bands select phases and fit constant
and linear unwrapped phase; remaining bands only evaluate frozen predictions.
Exact shortest-arc half-turn ties go negative; phase-max ties go lowest;
rational predictions round by floor(x+1/2). Row-wise rotations rerun selection
and fitting. References are descriptive, not calibrated p-values. No decoding,
preview access, significance threshold, stride selection or physical-row claim.
Reads samples and prints aggregates only; original stdlib Python3.8+ code.
Sample IDs must be distinct positive ASCII decimals and names printable basenames;
invalid identities are argument errors before any sample is measured.
"""
import argparse
import array
from fractions import Fraction
import hashlib
import json
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff, size_class


def scan_bands(payload, stride, starts, rows):
    """Stream candidate tokens, retaining only designated disjoint bands."""
    boundaries = {r * stride: (i, False) for i, r in enumerate(starts)}
    boundaries.update({(r + rows) * stride: (i, True) for i, r in enumerate(starts)})
    bands = [array.array('B') for _ in starts]
    coordinates = [{} for _ in starts]
    pos = index = 0
    active = None
    limit = (starts[-1] + rows) * stride
    nbits = len(payload) * 8
    while index <= limit:
        if index in boundaries:
            i, end = boundaries[index]
            coordinates[i]['end_bit' if end else 'start_bit'] = pos
            active = None if end else i
        if index == limit or pos + 6 > nbits:
            break
        begin = pos
        while pos < nbits and not ((payload[pos >> 3] >> (7 - (pos & 7))) & 1):
            pos += 1
        if pos + 6 > nbits:
            pos = begin
            break
        q = min(pos - begin, 40)
        if active is not None:
            bands[active].append(q)
        pos += 6
        index += 1
    if active is not None:
        coordinates[active]['partial_end_bit'] = pos
    return bands, coordinates, index, pos


def phase_profile(band, stride, head, shifts=None):
    """Exact A=S*head_sum-head*row_sum, summed over complete rows."""
    if len(band) % stride:
        raise ValueError('incomplete candidate block')
    profile = [0] * stride
    for r in range(len(band) // stride):
        row = band[r * stride:(r + 1) * stride]
        total, hs = sum(row), sum(row[:head])
        shift = shifts[r] if shifts is not None else 0
        for phase in range(stride):
            profile[(phase - shift) % stride] += stride * hs - head * total
            hs += row[(phase + head) % stride] - row[phase]
    return profile


def fit_predict(profiles, starts, stride):
    """No validation profile participates in phase selection or fitting."""
    ties = []
    for profile in profiles[:3]:
        maximum = max(profile)
        ties.append([p for p, value in enumerate(profile) if value == maximum])
    selected = [t[0] for t in ties]
    unwrapped = [selected[0]]
    half_ties = []
    for i in range(1, 3):
        delta = (selected[i] - selected[i - 1]) % stride
        half_ties.append(2 * delta == stride)
        if 2 * delta >= stride:
            delta -= stride
        unwrapped.append(unwrapped[-1] + delta)
    xs = starts[:3]
    mx, my = Fraction(sum(xs), 3), Fraction(sum(unwrapped), 3)
    slope = (sum((x - mx) * (y - my) for x, y in zip(xs, unwrapped)) /
             sum((x - mx) ** 2 for x in xs))
    intercept = my - slope * mx
    def rounded(value):
        return (value + Fraction(1, 2)).numerator // (value + Fraction(1, 2)).denominator % stride
    constant = [rounded(my) for x in starts[3:]]
    linear = [rounded(intercept + slope * x) for x in starts[3:]]
    cs = [p[phase] for p, phase in zip(profiles[3:], constant)]
    ls = [p[phase] for p, phase in zip(profiles[3:], linear)]
    return dict(discovery_maximum_phases=ties, discovery_selected_phases=selected,
                unwrapped_discovery_phases=unwrapped, half_circle_ties=half_ties,
                slope_numerator=slope.numerator, slope_denominator=slope.denominator,
                intercept_numerator=intercept.numerator, intercept_denominator=intercept.denominator,
                constant_validation_phases=constant, linear_validation_phases=linear,
                constant_validation_contrasts=cs, linear_validation_contrasts=ls,
                constant_validation_sum=sum(cs), linear_validation_sum=sum(ls),
                linear_minus_constant=sum(ls) - sum(cs))


def experiment(bands, stride, starts, head, replicates, seed):
    profiles = [phase_profile(b, stride, head) for b in bands]
    observed = fit_predict(profiles, starts, stride)
    rng = random.Random(seed)
    nulls = []
    for _ in range(replicates):
        rotated = [phase_profile(b, stride, head,
                                [rng.randrange(stride) for _ in range(len(b) // stride)])
                   for b in bands]
        nulls.append(fit_predict(rotated, starts, stride))
    return dict(observed=observed, rotation_results=nulls,
                rotation_linear_minus_constant_ge=sum(n['linear_minus_constant'] >= observed['linear_minus_constant']
                                                      for n in nulls),
                rotation_linear_sum_ge=sum(n['linear_validation_sum'] >= observed['linear_validation_sum']
                                           for n in nulls),
                sum_contrast_numerator_by_band_and_phase=profiles)


def measure(path, digest, stride, starts, rows, head, replicates, seed):
    with open(path, 'rb') as source:
        data = source.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest.lower():
        raise ValueError('hash mismatch against retained verified record')
    best = max(Tiff(data).all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
    w, h = best[0x100][0], best[0x101][0]
    offsets, sizes = best[0x111], best[0x117]
    if len(offsets) != 1 or len(sizes) != 1:
        raise ValueError('single strip required')
    off, size = offsets[0], sizes[0]
    if off < 0 or size <= 0 or off + size > len(data) or min(w, h) <= 0:
        raise ValueError('invalid strip geometry')
    if size_class(size, w, h) != 'variable' or best.get(0x103) != [1]:
        raise ValueError('variable-size compression-tag-1 input required')
    bands, coords, parsed, end = scan_bands(data[off:off + size], stride, starts, rows)
    accounting = []
    for start, b, coord in zip(starts, bands, coords):
        entry = dict(start_candidate_row=start, start_token=start * stride,
                     requested_tokens=rows * stride, retained_tokens=len(b),
                     complete=len(b) == rows * stride,
                     escape_tokens=sum(q >= 17 for q in b), **coord)
        for key in ('start_bit', 'end_bit', 'partial_end_bit'):
            if key in coord:
                entry['absolute_file_' + key] = off * 8 + coord[key]
        accounting.append(entry)
    complete = all(len(b) == rows * stride for b in bands)
    complete_bits = sum(c.get('end_bit', c.get('start_bit', 0)) - c.get('start_bit', 0) for c in coords)
    partial_bits = sum(c.get('partial_end_bit', c.get('start_bit', 0)) - c.get('start_bit', 0) for c in coords)
    out = dict(sha256=actual, payload_width=w, payload_height=h, payload_offset=off,
               payload_bytes=size, variant='unassigned', size_class='variable', compression_tag=1,
               parsed_tokens=parsed, consumed_bits=end, requested_tokens=(starts[-1] + rows) * stride,
               band_accounting=accounting, bands_complete=complete,
               complete_band_bits=complete_bits, partial_band_bits=partial_bits,
               payload_bits_outside_complete_bands=size * 8 - complete_bits)
    if complete:
        out['results'] = experiment(bands, stride, starts, head, replicates, seed)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sample', nargs=4, action='append', required=True, metavar=('ID', 'NAME', 'SHA256', 'FILE'))
    ap.add_argument('--stride', type=int, default=5240)
    ap.add_argument('--starts', nargs='+', type=int, default=[0, 500, 1000, 1500, 2000, 2500])
    ap.add_argument('--rows', type=int, default=32)
    ap.add_argument('--head', type=int, default=32)
    ap.add_argument('--replicates', type=int, default=15)
    ap.add_argument('--seed', type=int, default=296)
    args = ap.parse_args(argv)
    if (len(args.starts) < 4 or args.starts != sorted(set(args.starts)) or min(args.starts) < 0
            or args.rows < 2 or not args.stride > args.head >= 1 or args.replicates < 1
            or any(b - a <= args.rows for a, b in zip(args.starts, args.starts[1:]))):
        ap.error('require >=4 ordered separated bands, rows>=2, stride>head>=1, replicates>=1')
    ids = [sample[0] for sample in args.sample]
    try:
        invalid_ids = any(not sid.isascii() or not sid.isdecimal() or int(sid) < 1 for sid in ids) or len(set(map(int, ids))) != len(ids)
    except ValueError:
        invalid_ids = True
    if invalid_ids:
        ap.error('sample IDs must be distinct positive ASCII decimals')
    if any(not name or not name.isprintable() or any(c in name for c in '/\\') for _, name, _, _ in args.sample):
        ap.error('sample public name must be a printable basename')
    samples = []
    for sid, name, digest, path in args.sample:
        out = dict(pixls_id=sid, pixls_name=name)
        try:
            if len(digest) != 64 or any(c not in '0123456789abcdefABCDEF' for c in digest):
                raise ValueError('invalid hash')
            out.update(measure(path, digest, args.stride, args.starts, args.rows, args.head, args.replicates, args.seed))
            out['ok'] = out['bands_complete']
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            out.update(ok=False, error=type(exc).__name__)
        samples.append(out)
    hashes = {}
    for name in ('token_phase_drift.py', 'orf_signature.py'):
        with open(os.path.join(os.path.dirname(__file__), name), 'rb') as source:
            hashes[name] = hashlib.sha256(source.read()).hexdigest()
    print(json.dumps(dict(schema_version=1, method='discovery-unwrapped-phase-prediction-q40',
                          python_version=sys.version.split()[0], source_sha256=hashes,
                          stride=args.stride, starts=args.starts, rows=args.rows, head=args.head,
                          escape_extra_bits=0, seed=args.seed, replicates=args.replicates,
                          rotation_rng='Python Random MT19937; replicate/band/row; reset per sample',
                          contrast_denominator=args.rows * args.head * (args.stride - args.head),
                          samples=samples), indent=2, allow_nan=False))
    return int(any(not s['ok'] for s in samples))


if __name__ == '__main__':
    sys.exit(main())
