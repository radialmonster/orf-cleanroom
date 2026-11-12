#!/usr/bin/env python3
"""Secondary row-stride candidates against W*p/q, with three q-sequence controls.

Supports lead #724. For each file the tool runs the row-stride scan of
token_row_stride.py (imported, not copied: same score, same defaults), keeps
every secondary peak (z >= --z-min, greedy --suppress separation, at least
--min-distance tokens from the file's best stride), maps each peak to the
nearest integer to W*p/q for q <= --q-max, and reports how many peaks sit
within --tolerance tokens of such an integer, how many sit exactly on W*p/q,
and the share of the scored strides that lies inside the same windows (the
chance rate). Candidates at low-order rational multiples of W are fold
harmonics of a period at W, not wider rows.

--control replaces the real q prefix with a construction on the same tokens and
scores it identically: "synthetic" resamples every position from the file's own
head or rest q distribution taken at --period, "tiled" repeats the real prefix
at --period, "shuffle" is one Fisher-Yates permutation of the real prefix.
Those are descriptive controls: they separate what the score does when the
period, rather than the content, carries the row-start contrast.

A peak is a candidate periodicity in a prefix folded at a candidate stride; it
is not a physical row boundary, and the scan does not establish that W is the
true period, a whole-frame stride, or any value mapping. Reads sample files and
prints aggregate numbers only; no pixel or token dumps, no file writes.
Clean-room: original code and the files' own structure only.

Usage:
    python -I -B tools/stride_harmonics.py FILE [FILE ...] [--rows N]
        [--head K] [--min-stride S] [--max-stride S] [--z-min Z]
        [--suppress N] [--min-distance N] [--q-max Q] [--tolerance T] [--names]
    python -I -B tools/stride_harmonics.py FILE [FILE ...] --control CONTROL
        [--period P] [--seed N]
    python -I -B tools/stride_harmonics.py --self-test

Defaults: --rows 300, --head 32 (as token_row_stride.py), scan payload width ..
width + 1200, --z-min 4.0, --suppress 32, --min-distance 8, --q-max 12,
--tolerance 2, --seed 20261112, --period the file's payload width. Output is
keyed by input order; --names adds each input's basename.

Exit status: 0 when every input produced a report, 1 if any input failed
(unreadable, not a TIFF-structured ORF, no usable IFD), 2 for a usage error. A
scan too short for one row per candidate is reported in place, as
token_row_stride.py does, and is not counted as a failure.
"""
import argparse
import array
import bisect
import os
import random
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens as T  # noqa: E402
from token_row_stride import stride_scores  # noqa: E402

ESC_CAP = 40  # q is capped at 40 by the scan sink, as in token_row_stride.py


class UsageError(Exception):
    """A per-input argument problem that is reported as a usage error (exit 2)."""


def scan_q(buf, rows, max_stride):
    """The q prefix token_row_stride.py scores: same limit, sinks and q cap."""
    q = array.array("B")
    T.scan(buf, rows * max_stride, 0, 0, None, q, array.array("B"), ESC_CAP)
    return q


def picks(scores, z_min, suppress, min_distance):
    """Best stride and secondary peaks from stride_scores() output, best first.

    Greedy non-maximum suppression: accept candidates in descending z order while
    they are at least `suppress` tokens from every accepted one, stop at z < z_min.
    Secondary peaks are the accepted ones other than the best and at least
    `min_distance` from it, so `min_distance` 0 still never returns the best.
    """
    accepted = []
    for z, _, s, _ in scores:
        if z < z_min:
            break
        if all(abs(s - t) >= suppress for t, _ in accepted):
            accepted.append((s, z))
    if not accepted:
        return None, []
    best = accepted[0][0]
    return best, [(s, z) for s, z in accepted
                  if s != best and abs(s - best) >= min_distance]


def nearest(s, base, q_max):
    """Nearest Fraction p/q of the target family (q < p <= 2q) to s/base, and residual."""
    best = None
    for q in range(1, q_max + 1):
        for p in range(q + 1, 2 * q + 1):
            residual = s - base * p / float(q)
            frac = Fraction(p, q)
            if best is None or abs(residual) < abs(best[0]) - 1e-12:
                best = (residual, frac)
            elif abs(abs(residual) - abs(best[0])) <= 1e-12 and frac > best[1]:
                best = (residual, frac)
    return best


def target_map(base, lo, hi, q_max, tolerance):
    """{scanned stride: Fraction} inside the window of a rounded W*p/q centre.

    A centre outside [lo, hi] still contributes the part of its window that falls
    inside the scan; only grid points inside [lo, hi] are kept.
    """
    out = {}
    for q in range(1, q_max + 1):
        for p in range(q + 1, 2 * q + 1):
            centre = int(round(base * p / float(q)))
            for s in range(centre - tolerance, centre + tolerance + 1):
                if lo <= s <= hi and s not in out:
                    out[s] = Fraction(p, q)
    return out


def target_fraction(s, base, q_max, tolerance):
    """The Fraction p/q whose rounded W*p/q centre is within tolerance of s, or None."""
    for q in range(1, q_max + 1):
        for p in range(q + 1, 2 * q + 1):
            if abs(s - int(round(base * p / float(q)))) <= tolerance:
                return Fraction(p, q)
    return None


def chance_rate(targets, scored):
    """Share of the scored strides that lies inside a target window."""
    return len([s for s in scored if s in targets]) / float(len(scored))


def tally(secondary, base, targets, q_max, tolerance):
    """Per-peak rows and the within/exact counts for one input.

    A row is (S, z, hit fraction or None, displayed fraction, exact residual,
    offset from the rounded centre). The hit fraction and the chance grid come
    from the same rule: |S - round(W*p/q)| <= tolerance.
    """
    rows, within, exact = [], 0, 0
    for s, z in secondary:
        target = target_fraction(s, base, q_max, tolerance)
        if target is None:
            residual, frac = nearest(s, base, q_max)
            rows.append((s, z, None, frac, residual, 0))
            continue
        residual = s - base * target
        within += 1
        exact += abs(residual) < 1e-9
        rows.append((s, z, target, target, residual, s - int(round(base * target))))
    return rows, within, exact


def cum_table(values):
    """Cumulative distribution of an integer q sample, for bisect draws."""
    hist = [0] * (ESC_CAP + 1)
    for v in values:
        hist[v] += 1
    cum, total = [], 0
    for count in hist:
        total += count
        cum.append(total / float(len(values)))
    return cum


def draw(cum, rng, n):
    rand = rng.random
    return array.array("B", [bisect.bisect_right(cum, rand()) for _ in range(n)])


def synthetic(q, period, head, seed, n):
    """iid q with head positions and other positions drawn from q's own halves."""
    heads, rest = [], []
    for start in range(0, n, period):
        heads.extend(q[start:start + head])
        rest.extend(q[start + head:start + period])
    if not rest:
        raise ValueError("prefix has no token outside the head")
    head_cum, rest_cum = cum_table(heads), cum_table(rest)
    rng = random.Random(seed)
    out = draw(rest_cum, rng, n)
    for start in range(0, n, period):
        for i in range(start, min(start + head, n)):
            out[i] = bisect.bisect_right(head_cum, rng.random())
    return out


def tiled(q, period, n):
    tiles = -(-n // period)
    return array.array("B", (q[k % period] for k in range(tiles * period)))[:n]


def shuffled(q, seed):
    out = array.array("B", q)
    random.Random(seed).shuffle(out)
    return out


def self_test():
    """Imposed period P: integer P*p/q peaks of the fold, none after shuffling."""
    head, period, rows, hi = 8, 120, 300, 170
    q = array.array("B")
    for _ in range(rows):
        q.extend([3] * head)
        q.extend([0] * (period - head))
    scores = stride_scores(q, period, hi, rows, head)
    best, loose = picks(scores, 4.0, 4, 8)
    assert best == period and scores[0][0] > 10, (best, scores[0])
    found = [s for s, _ in loose]
    # 4/3, 5/4, 6/5, 7/5 and 7/6 of the period, all exact token counts.
    assert found == [160, 150, 144, 168, 140], found
    _, default = picks(scores, 4.0, 32, 8)
    assert [s for s, _ in default] == [160], default  # 32-token suppression
    residual, frac = nearest(144, period, 12)
    assert abs(residual) < 1e-9 and str(frac) == "6/5", (residual, frac)
    assert abs(chance_rate(target_map(5240, 5240, 6440, 12, 2),
                           list(range(5240, 6441))) - 50 / 1201.0) < 1e-12
    _, after_shuffle = picks(stride_scores(shuffled(q, 20261112), period, hi, rows, head),
                             4.0, 32, 8)
    assert not after_shuffle, after_shuffle
    print("self-test ok: period %d peaks at %s (4/3, 5/4, 6/5, 7/5, 7/6 of it), "
          "none above z=4 after shuffling" % (period, found))


def report(index, path, a, name):
    """One input: scan or control, peaks, target mapping, per-file summary."""
    w, h, buf = T.locate(path)
    lo = a.min_stride if a.min_stride is not None else w
    hi = a.max_stride if a.max_stride is not None else w + 1200
    if hi <= lo:
        raise UsageError("empty stride range %d..%d" % (lo, hi))
    q = scan_q(buf, a.rows, hi)
    sequence, period = q, None
    if a.control in ("synthetic", "tiled"):
        period = a.period if a.period is not None else w
        sequence = (synthetic(q, period, a.head, a.seed, len(q)) if a.control == "synthetic"
                    else tiled(q, period, len(q)))
    elif a.control == "shuffle":
        sequence = shuffled(q, a.seed)
    print("== input %d%s" % (index, " " + name if a.names else ""))
    print("payload: %dx%d  tokens=%d  scan=%d..%d  rows=%d  head=%d" % (
        w, h, len(sequence), lo, hi, a.rows, a.head))
    if a.control is not None:
        print("control: %s  seed=%d%s" % (a.control, a.seed,
                                          "" if period is None else "  period=%d" % period))
    scores = stride_scores(sequence, lo, hi, a.rows, a.head)
    if not scores:
        print("no stride with enough rows")
        return 0, 0, 0, None
    _, secondary = picks(scores, a.z_min, a.suppress, a.min_distance)
    scored = [s for _, _, s, _ in scores]
    targets = target_map(w, lo, hi, a.q_max, a.tolerance)
    rows, within, exact = tally(secondary, w, targets, a.q_max, a.tolerance)
    chance = chance_rate(targets, scored)
    print("best: S=%d  z=%.2f" % (scores[0][2], scores[0][0]))
    for s, z, target, shown, residual, offset in rows:
        if target is None:
            print("peak: S=%d  z=%.2f  S/W=%.5f  no target; nearest %s  "
                  "exact residual=%+.2f" % (s, z, s / float(w), shown, residual))
        else:
            print("peak: S=%d  z=%.2f  S/W=%.5f  target %s  offset=%+d  "
                  "exact residual=%+.2f" % (s, z, s / float(w), target, offset, residual))
    print("peaks=%d within=%d exact=%d chance=%.4f" % (len(secondary), within, exact, chance))
    return len(secondary), within, exact, chance


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--rows", type=int, default=300, help="rows used per stride")
    ap.add_argument("--head", type=int, default=32, help="row-start tokens compared")
    ap.add_argument("--min-stride", type=int, help="smallest candidate (default: payload width)")
    ap.add_argument("--max-stride", type=int, help="largest candidate (default: width + 1200)")
    ap.add_argument("--z-min", type=float, default=4.0, help="smallest peak z")
    ap.add_argument("--suppress", type=int, default=32, help="greedy peak separation, tokens")
    ap.add_argument("--min-distance", type=int, default=8,
                    help="skip peaks this close to the best stride")
    ap.add_argument("--q-max", type=int, default=12,
                    help="largest denominator of the W*p/q family")
    ap.add_argument("--tolerance", type=int, default=2,
                    help="tokens from the nearest integer to W*p/q")
    ap.add_argument("--names", action="store_true", help="print each input's basename")
    ap.add_argument("--control", choices=("synthetic", "tiled", "shuffle"))
    ap.add_argument("--period", type=int, help="period of the synthetic and tiled controls")
    ap.add_argument("--seed", type=int, default=20261112, help="control RNG seed")
    ap.add_argument("--self-test", action="store_true", help="run the synthetic test")
    a = ap.parse_args(argv)
    if a.head <= 0:
        ap.error("--head must be positive")
    if a.z_min < 0:
        ap.error("--z-min must not be negative")
    if a.suppress < 1:
        ap.error("--suppress must be positive")
    if a.min_distance < 0:
        ap.error("--min-distance must not be negative")
    if a.q_max < 1:
        ap.error("--q-max must be positive")
    if a.tolerance < 0:
        ap.error("--tolerance must not be negative")
    if a.min_stride is not None and a.max_stride is not None and a.max_stride <= a.min_stride:
        ap.error("--max-stride must exceed --min-stride")
    if (a.control in ("synthetic", "tiled") and a.period is not None
            and a.period <= a.head):
        ap.error("--period must exceed --head")
    if a.self_test:
        self_test()
        return 0
    if not a.files:
        ap.error("no files (or use --self-test)")
    failed = False
    files = peaks = within = exact = 0
    chances = []
    for index, path in enumerate(a.files, 1):
        name = os.path.basename(path) if a.names else ""
        try:
            n_peaks, n_within, n_exact, chance = report(index, path, a, name)
        except UsageError as exc:
            ap.error(str(exc))
        except (ValueError, KeyError, TypeError, OSError) as exc:
            # No local path in the diagnostic: OSError messages carry one.
            detail = (exc.strerror or type(exc).__name__) if isinstance(exc, OSError) else str(exc)
            print("input %d: %s: %s" % (index, type(exc).__name__, detail), file=sys.stderr)
            failed = True
            continue
        files += 1
        peaks += n_peaks
        within += n_within
        exact += n_exact
        if chance is not None:
            chances.append(chance)
    if files:
        if chances:
            mean_chance = sum(chances) / len(chances)
            tail = "chance=%.4f expected=%.1f" % (mean_chance, peaks * mean_chance)
        else:
            tail = "chance=n/a"
        print("\ncohort: files=%d peaks=%d within=%d exact=%d %s" % (
            files, peaks, within, exact, tail))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
