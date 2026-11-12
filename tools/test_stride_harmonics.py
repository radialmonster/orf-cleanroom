"""Synthetic checks for stride_harmonics.py (no sample or image data)."""
import array
import contextlib
import io
import os
import sys
import unittest
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stride_harmonics as S  # noqa: E402

W, LO, HI = 5240, 5240, 6440


def scores(*pairs):
    """stride_scores()-shaped rows, best first."""
    return [(z, 0.05, s, 300) for z, s in pairs]


def period_q(head, period, rows):
    """q with an exact row-start contrast at `period` and zeros elsewhere."""
    q = array.array("B")
    for _ in range(rows):
        q.extend([3] * head)
        q.extend([0] * (period - head))
    return q


class RationalTests(unittest.TestCase):
    def test_integer_targets_are_found_and_fractional_ones_round(self):
        self.assertEqual(S.nearest(6288, W, 12), (0.0, Fraction(6, 5)))
        self.assertEqual(S.nearest(5895, W, 12), (0.0, Fraction(9, 8)))
        self.assertEqual(S.nearest(5764, W, 12), (0.0, Fraction(11, 10)))
        residual, frac = S.nearest(6115, W, 12)
        self.assertEqual(frac, Fraction(7, 6))
        self.assertAlmostEqual(residual, 6115 - W * 7 / 6.0)

    def test_target_family_starts_above_the_base(self):
        # q < p <= 2q, so the base itself (p == q) is never a target.
        self.assertEqual(S.nearest(5402, 5402, 12)[1], Fraction(13, 12))

    def test_denominator_limit(self):
        # 6288 = 6/5 of W; with q <= 4 the nearest allowed fraction is 5/4.
        self.assertEqual(S.nearest(6288, W, 4)[1], Fraction(5, 4))

    def test_chance_grid_is_the_hit_set(self):
        for base, lo, hi in ((W, LO, HI), (5220, 5220, 6420)):
            targets = S.target_map(base, lo, hi, 12, 2)
            hits = set(s for s in range(lo, hi + 1)
                       if S.target_fraction(s, base, 12, 2) is not None)
            self.assertEqual(set(targets), hits)
        self.assertEqual(len(S.target_map(W, LO, HI, 12, 2)), 50)
        self.assertEqual(len(S.target_map(W, LO, HI, 12, 0)), 10)
        self.assertIn(6404, S.target_map(W, LO, HI, 12, 0))
        self.assertAlmostEqual(S.chance_rate(S.target_map(W, LO, HI, 12, 2),
                                             list(range(LO, HI + 1))), 50 / 1201.0)

    def test_chance_denominator_is_the_scored_strides(self):
        targets = S.target_map(W, LO, HI, 12, 2)
        scored = [s for s in range(LO, HI + 1) if s % 2 == 0]
        self.assertAlmostEqual(S.chance_rate(targets, scored),
                               len([s for s in scored if s in targets]) / float(len(scored)))

    def test_window_of_a_centre_outside_the_range_still_counts(self):
        # 6/5 of 1200 is 1440, one token above hi; its window reaches 1438 and 1439.
        targets = S.target_map(1200, 1200, 1439, 12, 2)
        self.assertEqual(targets[1438], Fraction(6, 5))
        self.assertIn(1439, targets)


class PeakTests(unittest.TestCase):
    def test_suppression_and_threshold(self):
        best, secondary = S.picks(scores((9.0, 100), (5.0, 132), (4.5, 101), (3.9, 300)),
                                  4.0, 32, 8)
        self.assertEqual(best, 100)
        self.assertEqual([s for s, _ in secondary], [132])

    def test_min_distance_keeps_exact_tie_out(self):
        best, secondary = S.picks(scores((9.0, 100), (5.0, 108), (4.9, 107)), 4.0, 1, 8)
        self.assertEqual(best, 100)
        self.assertEqual([s for s, _ in secondary], [108])
        self.assertEqual(S.picks(scores((3.9, 100)), 4.0, 32, 8), (None, []))

    def test_min_distance_zero_still_excludes_the_best(self):
        best, secondary = S.picks(scores((9.0, 100), (5.0, 132)), 4.0, 32, 0)
        self.assertEqual(best, 100)
        self.assertEqual([s for s, _ in secondary], [132])
        self.assertEqual(S.picks(scores((9.0, 100)), 4.0, 32, 0), (100, []))


class TallyTests(unittest.TestCase):
    def setUp(self):
        self.head, self.period, self.rows, self.hi = 8, 120, 300, 170
        self.q = period_q(self.head, self.period, self.rows)
        self.scores = S.stride_scores(self.q, self.period, self.hi, self.rows, self.head)
        _, self.secondary = S.picks(self.scores, 4.0, 4, 8)
        self.targets = S.target_map(self.period, self.period, self.hi, 12, 2)

    def test_tally_on_a_known_period(self):
        rows, within, exact = S.tally(self.secondary, self.period, self.targets, 12, 2)
        self.assertEqual([r[0] for r in rows], [160, 150, 144, 168, 140])
        self.assertEqual((within, exact), (5, 5))
        self.assertTrue(all(r[2] is not None for r in rows))
        scored = [s for _, _, s, _ in self.scores]
        self.assertAlmostEqual(S.chance_rate(self.targets, scored),
                               len([s for s in scored if s in self.targets]) / float(len(scored)))

    def test_tally_after_shuffling_is_empty(self):
        shuffled = S.shuffled(self.q, 20261112)
        self.assertEqual(
            S.tally(S.picks(S.stride_scores(shuffled, self.period, self.hi, self.rows,
                                            self.head), 4.0, 32, 8)[1],
                    self.period, self.targets, 12, 2), ([], 0, 0))

    def test_tally_miss_keeps_the_nearest_fraction(self):
        # The lowest target above period 120 is 13/12 of it, 130, so 122 is a miss.
        rows, within, exact = S.tally([(122, 4.5)], self.period, self.targets, 12, 2)
        self.assertEqual((within, exact), (0, 0))
        self.assertIsNone(rows[0][2])
        self.assertIsNotNone(rows[0][3])

    def test_tally_counts_a_rounded_hit_that_is_not_exact(self):
        rows, within, exact = S.tally([(6115, 4.07)], W, S.target_map(W, LO, HI, 12, 2),
                                      12, 2)
        self.assertEqual((within, exact), (1, 0))
        self.assertEqual(rows[0][2], Fraction(7, 6))
        self.assertEqual(rows[0][5], 2)                       # offset from round(W*7/6)
        self.assertAlmostEqual(rows[0][4], 6115 - W * 7 / 6.0)

    def test_self_test_passes(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            S.self_test()
        self.assertTrue(out.getvalue().startswith("self-test ok"))


class ControlTests(unittest.TestCase):
    def test_tiled_repeats_the_period(self):
        q = array.array("B", [1, 2, 3, 4])
        self.assertEqual(list(S.tiled(q, 4, 10)), [1, 2, 3, 4, 1, 2, 3, 4, 1, 2])

    def test_shuffle_is_seeded_and_changes_order(self):
        q = array.array("B", list(range(40)) * 5)
        first = S.shuffled(q, 20261112)
        self.assertEqual(list(first), list(S.shuffled(q, 20261112)))
        self.assertNotEqual(list(first), list(q))
        self.assertEqual(sorted(first), sorted(q))

    def test_synthetic_keeps_values_and_length(self):
        q = array.array("B", [0] * 3 + [1, 2] + [0] * 5)
        out = S.synthetic(q, 5, 2, 20261112, 60)
        self.assertEqual(len(out), 60)
        self.assertTrue(all(0 <= v <= S.ESC_CAP for v in out))
        self.assertEqual(list(S.synthetic(q, 5, 2, 7, 60)),
                         list(S.synthetic(q, 5, 2, 7, 60)))

    def test_synthetic_needs_a_token_outside_the_head(self):
        with self.assertRaises(ValueError):
            S.synthetic(array.array("B", [1, 2, 3, 4]), 4, 8, 20261112, 4)


class CliTests(unittest.TestCase):
    def test_bad_input_sets_status_and_prints_no_path(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(S.main(["missing-synthetic-file.ORF"]), 1)
        self.assertIn("input 1", err.getvalue())
        self.assertNotIn("missing-synthetic-file", err.getvalue())

    def test_period_is_validated_only_for_the_controls_that_use_it(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertRaises(SystemExit, S.main,
                              ["--control", "synthetic", "--period", "4", "--head", "8",
                               "x.ORF"])
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(S.main(["--control", "shuffle", "--period", "4", "--head", "8",
                                     "missing-synthetic-file.ORF"]), 1)

    def test_usage_errors(self):
        for argv in (["--head", "0", "x.ORF"], ["--suppress", "0", "x.ORF"],
                     ["--min-stride", "6000", "--max-stride", "5000", "x.ORF"],
                     ["--tolerance", "-1", "x.ORF"], []):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                self.assertRaises(SystemExit, S.main, argv)

    def test_help_exits_zero(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertRaises(SystemExit, S.main, ["--help"])
        self.assertIn("--control", out.getvalue())


if __name__ == "__main__":
    unittest.main()
