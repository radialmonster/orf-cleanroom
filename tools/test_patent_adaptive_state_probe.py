#!/usr/bin/env python3
"""Synthetic state/coordinate fixtures; no benchmark or sample access."""
import os
import sys
import unittest
from contextlib import redirect_stderr
from io import StringIO
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patent_adaptive_state_probe as p


class TestAdaptiveState(unittest.TestCase):
    def test_cli_requires_explicit_split(self):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
            p.main([])
        self.assertEqual(error.exception.code, 2)

    def test_hand_trace_delayed_preceding_value(self):
        state = (5, 0, 0, 0)
        used = []
        for value in (3, 3, 15, 16, 1):
            used.append(state[0])
            state = p.next_state(state, value, 64)
        self.assertEqual(used, [5, 5, 2, 4, 5])

    def test_reset_happens_before_prior_value_update(self):
        self.assertEqual(p.next_state((2,5,5,63),3,64), (5,1,1,0))
        self.assertEqual(p.next_state((2,5,5,31),3,32), (5,1,1,0))
        self.assertEqual(p.next_state((2,5,5,31),3,64), (2,6,6,32))

    def test_generated_roundtrip_and_truncation(self):
        values = [0,3,15,16,31] * 20
        bits = p.encode(values)
        tokens, tail = p.parse(bits, 'adaptive64')
        self.assertEqual([x[2] for x in tokens], values)
        self.assertEqual(tail, 0)
        tokens, tail = p.parse(bits[:-1], 'adaptive64')
        self.assertEqual([x[2] for x in tokens], values[:-1])
        self.assertGreater(tail, 0)
        self.assertEqual(p.parse('0000','fixed5'), ([],4))

    def test_suffix_recovery_rejects_extra_changed_boundary_and_state(self):
        state=(5,0,0,0)
        original={b:(b-5,1,state) for b in (100,110,120,130)}
        self.assertEqual(p.suffix_stable(original, dict(original), 150, 50, True),50)
        changed=dict(original);changed[125]=(120,1,state)
        self.assertIsNone(p.suffix_stable(original, changed, 150, 50, True))
        changed=dict(original);changed[120]=(115,1,(4,0,0,0))
        self.assertIsNone(p.suffix_stable(original, changed, 150, 50, True))
        self.assertEqual(p.suffix_stable(original, changed, 150, 50, False),50)

    def test_boundary_recovery_does_not_imply_state_recovery(self):
        left = [(b-5,b,1,(5,0,0,0)) for b in (100,110,120,130)]
        right = [(b-5,b,1,(4,0,0,0)) for b in (100,110,120,130)]
        r = p.compare_tokens(left, right, 50, 0, 150, False)
        self.assertEqual((r['boundary_suffix_stable_distance'], r['boundary_censored']), (50,False))
        self.assertEqual((r['state_suffix_stable_distance'], r['state_censored']), (None,True))
        fixed = p.compare_tokens(left, right, 50, 0, 150, True)
        self.assertEqual((fixed['boundary_suffix_stable_distance'], fixed['state_censored']), (50,None))

    def test_value_comparison_excludes_edit_crossing_word(self):
        original = {20:(15,1,None), 26:(21,3,None), 32:(27,4,None)}
        mutant = {20:(15,9,None), 26:(21,7,None), 32:(28,4,None)}
        self.assertEqual(p.value_comparison(original, mutant, 17), (1,1))

    def test_wrong_law_self_recovery_is_not_truth_recovery(self):
        bits = p.encode([0] * 256)
        result = p.trial(bits, 'adaptive32', 17, 'flip', truth_reference=True)
        self.assertEqual(result['self_baseline']['state_suffix_stable_distance'], 1)
        self.assertIsNone(result['truth_reference']['state_suffix_stable_distance'])
        self.assertTrue(result['truth_reference']['different_transition_laws'])
        control = p.trial(bits, 'fixed5', 17, 'flip', truth_reference=True)
        self.assertIsNone(control['truth_reference']['transient_state_hits'])
        self.assertIsNone(control['truth_reference']['state_suffix_stable_distance'])
        self.assertIsNone(control['truth_reference']['state_censored'])
        no_truth = p.trial(bits, 'adaptive32', 17, 'flip')
        self.assertIsNone(no_truth['truth_reference'])

    def test_short_windows_and_separate_fixed_state(self):
        self.assertEqual(p.trial('0'*100, 'adaptive64', 17, 'flip')['status'], 'short_window')
        tokens, tail = p.parse('1'+'00000', 'fixed5')
        self.assertEqual((tokens[0][2],tokens[0][3],tail), (0,None,0))
        with self.assertRaises(ValueError):p.parse('2','adaptive64')
        with self.assertRaises(ValueError):p.encode([-1])


if __name__ == '__main__':
    unittest.main()
