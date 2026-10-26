#!/usr/bin/env python3
"""Frozen synthetic generator discrimination for #300; builds on #303.

No camera inference. Three original stateless encoders from the reviewed
synthetic_resync_probe are crossed with its three parsers, three edits and
three anchors. Training seeds 400..403 and validation seeds 500..507 are fixed
before measurement; each generates 256 high-nibble LCG32 values. No fitting on
validation, threshold selection, search or significance claim is performed.

Separate nearest-centroid classifiers use (1) 27 recovery indicator bits,
(2) 27 recovery distances divided by 129 (censoring encoded as 129), or
(3) bit length / 4096 and ones / length. Squared Euclidean distances and class
centroids use exact fractions. Ties use fixed4, rice0, rice2 order. The distance
feature deliberately mixes failure and delay; the indicator ablation separates
that choice. All full 128-bit windows must fit and all parse tails are counted.

Each stream has an exact-length/popcount-preserving Fisher-Yates shuffled
control. A specified LCG32 and rejection sampling select unbiased indices
conditional on an ideal uniform 32-bit draw; the actual LCG is deterministic,
not a claim of independent uniform permutations or a calibrated null (index =
seed % bound uses the LCG's low bits, whose period is 2**k for the low k bits, so
small-bound swaps near the end are strongly patterned). Real and
shuffle training are separate; both classifiers evaluate both held-out groups.
Shuffle labels mean source generator, not that shuffled bits follow its codec.
In particular length/density can classify shuffles without coding structure.

CPU stdlib only, no file input/output except aggregate JSON on stdout. RTX3090
is available but unnecessary for this tiny exact-integer/fraction experiment.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys
import time
import tracemalloc
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synthetic_resync_probe as probe

TRAIN = tuple(range(400, 404))
VALIDATE = tuple(range(500, 508))
KINDS = ('real', 'shuffle')
FEATURES = ('recovery_count', 'recovery_distance', 'length_density')


def step(state):
    return (1664525 * state + 1013904223) % (1 << 32)


def values(seed):
    out = []
    for _ in range(256):
        seed = step(seed)
        out.append(seed >> 28)
    return out


def shuffle(bits, seed):
    """Descending Fisher-Yates; reject draws outside multiple of index range."""
    out = list(bits)
    for index in range(len(out) - 1, 0, -1):
        bound = index + 1
        limit = (1 << 32) - ((1 << 32) % bound)
        while True:
            seed = step(seed)
            if seed < limit:
                break
        other = seed % bound
        out[index], out[other] = out[other], out[index]
    return ''.join(out)


def features(bits):
    counts, distances = [], []
    tails = 0
    for parser in probe.GRAMMARS:
        for operation in ('flip', 'insert', 'delete'):
            for anchor in probe.ANCHORS:
                result = probe.measure(bits, parser, anchor, operation)
                if result['eof_shortened_window']:
                    raise ValueError('incomplete observation window')
                distance = result['sustained_boundary_distance']
                counts.append(Fraction(distance is not None))
                distances.append(Fraction(129 if distance is None else distance, 129))
                tails += result['original_tail_bits'] + result['changed_tail_bits']
    return {'recovery_count': counts, 'recovery_distance': distances,
            'length_density': [Fraction(len(bits), 4096),
                               Fraction(bits.count('1'), len(bits))]}, tails


def cohort(seeds):
    rows = []
    for seed in seeds:
        for generator_index, generator in enumerate(probe.GRAMMARS):
            original = probe.encode(values(seed), generator)
            # Seed separates generator controls; reset independently per stream.
            shuffled = shuffle(original, seed + 10000 + generator_index * 1000)
            for kind, bits in (('real', original), ('shuffle', shuffled)):
                vector, tails = features(bits)
                rows.append({'seed': seed, 'generator': generator, 'kind': kind,
                             'bits': len(bits), 'ones': bits.count('1'),
                             'parse_tail_bits_sum': tails, 'features': vector})
    return rows


def fit(rows, feature, kind):
    model = {}
    for generator in probe.GRAMMARS:
        vectors = [r['features'][feature] for r in rows
                   if r['kind'] == kind and r['generator'] == generator]
        if not vectors:
            raise ValueError('missing training class')
        model[generator] = [sum(column, Fraction()) / len(vectors)
                            for column in zip(*vectors)]
    return model


def predict(model, vector):
    if any(len(model[g]) != len(vector) for g in probe.GRAMMARS):
        raise ValueError('feature dimension mismatch')
    scores = {g: sum(((a - b) ** 2 for a, b in zip(model[g], vector)), Fraction())
              for g in probe.GRAMMARS}
    return min(probe.GRAMMARS, key=lambda g: scores[g]), scores


def experiment():
    training, validation = cohort(TRAIN), cohort(VALIDATE)
    reports = []
    for feature in FEATURES:
        for training_kind in KINDS:
            model = fit(training, feature, training_kind)
            for validation_kind in KINDS:
                matrix = [[0] * 3 for _ in range(3)]
                predictions = []
                for row in validation:
                    if row['kind'] != validation_kind:
                        continue
                    predicted, scores = predict(model, row['features'][feature])
                    matrix[probe.GRAMMARS.index(row['generator'])][
                        probe.GRAMMARS.index(predicted)] += 1
                    predictions.append({'seed': row['seed'], 'source': row['generator'],
                                        'predicted': predicted, 'squared_distances': scores})
                reports.append({'feature': feature, 'training_kind': training_kind,
                                'validation_kind': validation_kind, 'centroids': model,
                                'confusion_rows_source_columns_prediction': matrix,
                                'correct_source_labels': sum(matrix[i][i] for i in range(3)),
                                'total': len(predictions), 'predictions': predictions})
    return {'protocol': {'training_seeds': TRAIN, 'validation_seeds': VALIDATE,
                         'class_order': probe.GRAMMARS, 'values_per_stream': 256,
                         'anchors': probe.ANCHORS, 'window_bits': probe.WINDOW,
                         'recovery_run': probe.RUN, 'precision': 'exact fractions',
                         'feature_order': 'parser, operation(flip/insert/delete), anchor',
                         'shuffle_seed': 'value seed + 10000 + 1000 * generator index',
                         'limits': 'synthetic source labels only; no camera/null significance'},
            'cohorts': {'training': training, 'validation': validation},
            'classifications': reports}


class Tests(unittest.TestCase):
    def test_lcg_and_encoders(self):
        self.assertEqual(step(0), 1013904223)
        self.assertEqual(values(300), probe.values())
        for generator in probe.GRAMMARS:
            tokens, tail = probe.parse(probe.encode(values(400), generator), generator)
            self.assertEqual([v for _, _, v in tokens], values(400))
            self.assertEqual(tail, 0)

    def test_shuffle_preservation(self):
        for size in range(100):
            bits = ('01001' * 20)[:size]
            result = shuffle(bits, 77)
            self.assertEqual((len(result), result.count('1')), (size, bits.count('1')))
            self.assertEqual(result, shuffle(bits, 77))
        # Independently hand-applied swaps (5,2),(4,0),(3,2),(2,0),(1,0).
        self.assertEqual(shuffle('010011', 77), '101100')

    def test_exact_centroid_and_ties(self):
        rows = [{'kind': 'real', 'generator': g, 'features': {'x': [Fraction(i)]}}
                for g in probe.GRAMMARS for i in (0, 2)]
        model = fit(rows, 'x', 'real')
        self.assertEqual(model['rice0'], [Fraction(1)])
        label, scores = predict(model, [Fraction(3, 2)])
        self.assertEqual(label, 'fixed4')
        self.assertEqual(set(scores.values()), {Fraction(1, 4)})

    def test_frozen_split(self):
        self.assertFalse(set(TRAIN) & set(VALIDATE))
        self.assertEqual(len(TRAIN), 4)
        self.assertEqual(len(VALIDATE), 8)

    def test_features_and_censoring(self):
        vector, tails = features('0001' * 256)
        self.assertEqual(len(vector['recovery_count']), 27)
        self.assertEqual(vector['recovery_count'][:9], [1] * 3 + [0] * 6)
        self.assertEqual(vector['recovery_distance'][3:9], [1] * 6)
        self.assertEqual(vector['length_density'], [Fraction(1, 4), Fraction(1, 4)])
        self.assertGreaterEqual(tails, 0)
        with self.assertRaises(ValueError):
            features('0001' * 40)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    tracemalloc.start()
    start = time.perf_counter()
    report = experiment()
    report['benchmark'] = {'elapsed_seconds': time.perf_counter() - start,
                           'peak_traced_cpu_bytes': tracemalloc.get_traced_memory()[1]}
    tracemalloc.stop()
    # Rational strings preserve exact classifier decisions across JSON readers.
    print(json.dumps(report, default=str, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
