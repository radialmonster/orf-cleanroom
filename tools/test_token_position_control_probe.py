import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from token_position_control_probe import measure


def encode(words):
    bits = ''.join('0' * q + '1' + format(s, '05b') for q, s in words)
    return int(bits.ljust((len(bits) + 7) // 8 * 8, '0'), 2).to_bytes((len(bits) + 7) // 8, 'big')


class PositionControlsTest(unittest.TestCase):
    def test_planted_and_ties(self):
        words = [(0, 10 if i % 100 < 24 else 0) for i in range(200)]
        x = measure(encode(words), 100, 200)
        self.assertEqual(x['offsets'], [0, 25, 50, 75])
        self.assertEqual(x['complete_rows'], 2)
        self.assertEqual(x['cells']['0']['paired_suffix_mean'], {'numerator': 10, 'denominator': 1})
        self.assertTrue(x['comparison']['suffix']['zero_exceeds_all_controls'])
        self.assertEqual(x['comparison']['q']['zero_ties_controls'], [25, 50, 75])

    def test_escape_missing_and_tail(self):
        words = [(17, 9) if i < 24 else (0, 1) for i in range(100)] + [(17, 2)]
        x = measure(encode(words), 100, 101)
        self.assertEqual((x['complete_rows'], x['tail_tokens'], x['parsed_escapes'], x['tail_escapes']), (1, 1, 25, 1))
        self.assertEqual(x['cells']['0']['undefined_rows'], 1)
        self.assertFalse(x['identical_valid_row_sets'])
        self.assertIsNone(x['comparison']['q'])
        self.assertEqual(x['cells']['25']['window_n'], 24)

    def test_shortfall_and_validation(self):
        x = measure(encode([(0, 0)]), 100, 100)
        self.assertEqual(x['parsed_tokens'], 1)
        self.assertEqual(x['tail_tokens'], 1)
        with self.assertRaises(ValueError): measure(b'', 95, 1)

    def test_common_rows_exclude_mismatched_validity(self):
        words = [(17, 0) if i < 24 else (0, 3) for i in range(100)]
        words += [(0, 10 if i < 24 else 0) for i in range(100)]
        x = measure(encode(words), 100, 200)
        self.assertEqual((x['common_rows'], x['common_excluded_rows']), (1, 1))
        self.assertTrue(x['comparison']['suffix']['zero_exceeds_all_controls'])
        self.assertEqual(x['comparison']['suffix']['means'][0], {'numerator': 10, 'denominator': 1})


if __name__ == '__main__': unittest.main()
