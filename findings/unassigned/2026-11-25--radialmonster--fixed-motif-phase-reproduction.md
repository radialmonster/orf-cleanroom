# Fixed OM-3 motif phase persists on white but ends early on two dark captures

Author: @radialmonster
Verified by: @radialmonster
Lead: #1031
Variant: unassigned
Builds on: #30, #1023, #1027, #338

## Claim

At the previously fixed 31332-bit pitch, the literal six-field motif is present at every nominal index 2–3911 on white PA210010, but none after index 801 on dark PA200010 at its own fixed phase. Reserved dark PA200011 also loses the motif at its fixed phase and has no matches after index 541. Even exact early coverage does not imply whole-strip continuity. The measurements are bit-position predicates, not physical row identifications.

## Original evidence

Lead #1031 used `tools/fixed_motif_phase_continuity.py` at `97ed9f5bf8659c8eae1c745b9407e003200cb768` on the public, declared 5220 × 3912 OM-3 white PA210010 and dark PA200010 captures. Each nominal start is bit `40 + phase + j * 31332` in the declared strip, and all 48 bits must fit before checking six consecutive eight-bit fields matching `100xxxxx`. No alternatives are searched and no words parsed. Both discovery strips measure 122570968 bits. At phases 147 and 41 respectively, the white and dark files each give 398/400 and then 400/400 early matches. The white run is 2–3911, the dark run 2–801, with no other matches at their predicted locations.

## Verification

The original full discovery aggregates matched in a new run on 2026-11-25 at 20:07:46 UTC, after the lead was published at 20:06:44 UTC. Reserved public CC0 dark PA200011 was then run separately at 20:07:56 UTC with phase 43 unchanged, using 122570960 declared strip bits. All inputs passed the retained CC0 identity and full hash gates. Four generated checks passed. A separate direct bit-string predicate and run aggregation, using the same strip reader, agree on the reserved result. This is same-finder verification, not independent human verification.

| Capture | [0,400) | [400,800) | [800,1200) | [1200,3912) | Nominal matches | Sole present run (inclusive) |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| PA210010 white | 398/400 | 400/400 | 400/400 | 2712/2712 | 3910/3912 | 2–3911 |
| PA200010 dark | 398/400 | 400/400 | 2/400 | 0/2712 | 800/3912 | 2–801 |
| PA200011 dark, reserved | 242/400 | 142/400 | 0/400 | 0/2712 | 384/3912 | 158–541 |

All nominal positions fit on all three files. Complete but absent ranges are `[0,2)` on white, `[0,2)` and `[802,3912)` on the discovery dark, and `[0,158)` and `[542,3912)` on the reserved dark. The two darks have one complete prediction each beyond nominal height and neither matches it. White has no complete prediction there. Strip end minus the predicted start of index 3912 is −3, +103, and +93 bits respectively. Missing anchors do not distinguish phase change, variable lengths, or absence of the motif itself. The result does not identify physical rows, motif semantics, or the purpose of terminal bits.

## Reproduce

At `97ed9f5bf8659c8eae1c745b9407e003200cb768`, use the public CC0 files named and hashed below. Their sources are recorded in `samples/om3-flat-338-provenance.json` from #338, and the hashes are already in `samples/manifest.csv`. Substitute local paths for WHITE, DARK, and RESERVED.

    python -I -B tools/test_fixed_motif_phase_continuity.py
    python -I -B tools/fixed_motif_phase_continuity.py --sample PA210010.ORF WHITE --sample PA200010.ORF DARK
    python -I -B tools/fixed_motif_phase_continuity.py --cohort repeat --sample PA200011.ORF RESERVED

- `PA210010.ORF` `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`
- `PA200010.ORF` `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4`
- `PA200011.ORF` `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3`

Compare fixed window counts, nominal runs, separate absent and out-of-bounds counts, and complete and matched positions past nominal height. No private files were used.
