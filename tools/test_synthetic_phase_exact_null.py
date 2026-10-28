import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import synthetic_phase_exact_null as s

class PhaseNullTests(unittest.TestCase):
    def test_hand_cases(self):
        self.assertEqual(s.fit((1,0,1,0,1,0,1,0))['gain'], 0)
        result = s.analyze((1,0,1,0,0,1,0,1))
        self.assertEqual(result['observed']['gain'], 4)
        self.assertEqual(result['tail_count_including_ties'], 2)
        self.assertEqual(result['tail_fraction'], {'numerator':1, 'denominator':35})
        self.assertEqual(s.fit((1,1,1,1,0,0,0,0))['gain'], 0)
    def test_exact_null(self):
        result = s.analyze((1,0,1,0,1,0,1,0))
        self.assertEqual(result['null_orderings'], 70)
        self.assertEqual(result['gain_histogram'], {0:52, 2:16, 4:2})
        self.assertTrue(result['exact_superuniform'])
        self.assertEqual(len(set(s.orbit())), 70)
        self.assertTrue(all(s.fit(x)['gain'] >= 0 for x in s.orbit()))
    def test_invalid(self):
        for bits in ((), (0,)*8, (0,0,0,0,1,1,1,2)):
            with self.assertRaises(ValueError): s.fit(bits)

if __name__ == '__main__': unittest.main()
