"""Direct synthetic checks for the conditional phase/period control."""
from array import array
from fractions import Fraction
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_phase_rotation_control as C


def oracle(q, anchor, center, radius, rows, head):
    scores = []
    for stride in range(center - radius, center + radius + 1):
        for phase in range(stride):
            blocks = [q[anchor + phase + r * stride:anchor + phase + (r + 1) * stride]
                      for r in range(rows)]
            value = sum((Fraction(sum(x[:head]), head) - Fraction(sum(x[head:]), stride - head)
                         for x in blocks), Fraction()) / rows
            scores.append((value, stride, phase))
    def choose(items):
        maximum = max(x[0] for x in items)
        return min((s, p) for v, s, p in items if v == maximum)
    joint = choose(scores)
    fixed = choose([x for x in scores if x[1] == center])
    barrier = anchor + (rows + 2) * (center + radius)
    end = barrier + rows * (center - radius)
    def score(choice):
        stride, phase = choice
        h = [q[i] for i in range(barrier, end) if (i - anchor - phase) % stride < head]
        r = [q[i] for i in range(barrier, end) if (i - anchor - phase) % stride >= head]
        return h, r, Fraction(sum(h), len(h)) - Fraction(sum(r), len(r)) if h and r else None
    return joint, fixed, score(joint), score(fixed)


class Tests(unittest.TestCase):
    def test_enumeration_and_clipped_edges(self):
        for q in (array('B', [(i * 17 + i // 7) % 13 for i in range(300)]),
                  array('B', [4] * 300), array('B', [10 if (i - 3) % 13 == 0 else 0 for i in range(300)])):
            with self.subTest(q=q[:20]):
                joint, fixed, expected_j, expected_f = oracle(q, 20, 12, 2, 5, 2)
                j, f, diff = C.fit(q, 20, 12, 2, 5, 2)
                self.assertEqual((j['stride'], j['phase']), joint)
                self.assertEqual((f['stride'], f['phase']), fixed)
                for actual, expected in ((j, expected_j), (f, expected_f)):
                    h, r, value = expected
                    self.assertEqual((actual['head_count'], actual['head_sum']), (len(h), sum(h)))
                    self.assertEqual((actual['rest_count'], actual['rest_sum']), (len(r), sum(r)))
                self.assertEqual(diff, expected_j[2] - expected_f[2])

    def test_nonzero_cross_stride_tie(self):
        q = array('B', [0, 0, 0, 2, 2, 0, 1] * 100)
        j, f, diff = C.fit(q, 0, 4, 1, 3, 1)
        self.assertEqual((j['stride'], j['phase']), oracle(q, 0, 4, 1, 3, 1)[0])
        self.assertEqual(j['stride'], 3)

    def test_rejection_order_partial_blocks_and_original(self):
        class Rng:
            def __init__(self):
                self.values = iter([7, 1, 2, 3, 0, 1])
                self.bits = []
            def getrandbits(self, bits):
                self.bits.append(bits)
                return next(self.values)
        q = array('B', range(15))
        before = q[:]
        rng = Rng()
        rotated, blocks = C.rotate(q, 1, 8, 14, 4, rng)
        self.assertEqual(q, before)
        self.assertEqual(rng.bits, [3, 3, 2, 3, 2])
        self.assertEqual(blocks, [{'start': 1, 'length': 4, 'shift': 1},
                                  {'start': 5, 'length': 3, 'shift': 2},
                                  {'start': 8, 'length': 4, 'shift': 3},
                                  {'start': 12, 'length': 2, 'shift': 0}])
        for b in blocks:
            s, n, k = b['start'], b['length'], b['shift']
            self.assertEqual(rotated[s:s+n], q[s+k:s+n] + q[s:s+k])
        self.assertEqual((rotated[0], rotated[14]), (q[0], q[14]))

    def test_test_data_never_changes_selection_and_replicas_do_not_mutate(self):
        q = array('B', [(i * 7) % 11 for i in range(300)])
        before = q[:]
        barrier = 20 + 7 * 14
        j, f, _ = C.fit(q, 20, 12, 2, 5, 2)
        changed = q[:]
        for i in range(barrier, len(changed)):
            changed[i] = (changed[i] + 5) % 11
        j2, f2, _ = C.fit(changed, 20, 12, 2, 5, 2)
        self.assertEqual((j['stride'], j['phase'], j['training_numerator']), (j2['stride'], j2['phase'], j2['training_numerator']))
        self.assertEqual((f['stride'], f['phase'], f['training_numerator']), (f2['stride'], f2['phase'], f2['training_numerator']))
        result = C.control(q, 20, 12, 2, 5, 2, 2)
        self.assertEqual(q, before)
        self.assertEqual(result, C.control(q, 20, 12, 2, 5, 2, 2))

    def test_ties_and_undefined(self):
        result = C.control(array('B', [4] * 300), 20, 12, 2, 5, 2, 2)
        self.assertEqual(result['equal_count'], 2)
        self.assertEqual(result['greater_equal_count'], 2)
        self.assertEqual(result['undefined_count'], 0)
        j, f, difference = C.fit(array('B', [0, 10] + [0] * 40), 0, 4, 2, 1, 1)
        self.assertIsNone(difference)
        self.assertEqual(f['head_count'], 0)

    def test_negative_observed_exact_rank_and_undefined(self):
        outcomes = [({}, {}, Fraction(-1, 3)), ({}, {}, Fraction(-2, 6)),
                    ({}, {}, Fraction(-1, 4)), ({}, {}, None)]
        with patch.object(C, 'fit', side_effect=outcomes):
            result = C.control(array('B', range(100)), 0, 4, 1, 3, 1, 3)
        self.assertEqual([r['comparison'] for r in result['replicates']], ['equal', 'greater', None])
        self.assertEqual((result['greater_equal_count'], result['equal_count'], result['undefined_count']), (2, 1, 1))


if __name__ == '__main__':
    unittest.main()
