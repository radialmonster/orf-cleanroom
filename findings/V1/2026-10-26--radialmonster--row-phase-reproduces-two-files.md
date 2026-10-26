# Row-phase dependence reproduces on two further E-M1 Mark II files

Author: @radialmonster
Verified by: @radialmonster
Lead: #356
Variant: V1
Builds on: 2026-10-21--radialmonster--b2b4-local-luma-proxy, #149, #144, #351, #296
Partial: two further E-M1 Mark II files only; not the other bodies in the lead, the phase law across bands, a physical row origin, a value mapping or a decode

## Claim

On E-M1 Mark II ids 1997 and 1998, which lead #356 did not use, a new run after the lead was posted reproduces the phase dependence of the fixed b2+b4 top-band luma score. The phase-searched maximum is above the phase-0 value on both files and above a same-search shuffled-token null on 1997. The best phase is still file-specific: 28 on 1997 and 4620 on 1998, so this does not establish a physical row phase or a phase law.

## Original evidence

Lead #356, found by @radialmonster, with the method and the eight-file table in PR #355 (`tools/token_luma_phase_probe.py`, commit `74aa7b5`). The lead's phase-0 values reproduce the merged `tools/token_luma_stride_probe.py`; the phase search was step 16 then refine +/-16, top 300 candidate rows, window 63, v=b2+b4, 400x300 preview DC, row-centred r. The lead's public inputs and hashes are listed there.

The lead's claim is that the fixed map has a large, file-specific row-phase dependence, so phase 0 is not a neutral alignment, and that the phase is not stable across bands. It made no physical-row or decode claim.

## Verification

New run on 2026-10-26 UTC, after lead #356 was posted, at PR #355 commit `74aa7b5`. Neither file below is in the lead. Local SHA-256 values matched the retained verified-CC0 inventory and existing `samples/manifest.csv` rows before measurement; no download or catalogue request was repeated. Python 3.13.15.

Fixed before the run: the same tool, `--rows 300 --start-row 0 --step 16 --refine 16 --window 63 --map sum`, and the candidate stride S=5240 from #144. The null is `--perms 1 --seed 1`, which repeats the complete coarse+refine search after a global suffix shuffle.

| id | file | W x H | S | r at phase 0 | best phase | best r | shuffled-search max |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1997 | `Olympus - E-M1MarkII - 16bit (4:3).ORI` | 5240x3912 | 5240 | +0.12245 | 28 | +0.13970 | +0.02930 |
| 1998 | `Olympus - E-M1MarkII - 16bit (4:3).ORF` | 5240x3912 | 5240 | +0.09793 | 4620 | +0.14227 | not run |

Hashes: 1997 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`; 1998 `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`. Top phases on 1997 are 28:+0.13970, 29:+0.13962, 27:+0.13952, 30:+0.13938, 31:+0.13925; on 1998 they are 4620:+0.14227, 4617:+0.14223, 4616:+0.14222, 4621:+0.14219, 4618:+0.14217. Phase 28 is close to 0 on 1997; phase 4620 is 620 tokens before S on 1998.

This reproduces the lead's phase dependence on two new files but not the large gains seen on the lead's OM-5 6343/6347 and OM-5 Mark II 8549 rows. The maxima are modest, and the two best phases differ, so the result supports only the file-specific, non-neutral phase reading. It does not test the lead's later-band instability, the other bodies, a joint stride+phase law or a physical row origin. The same account measured the lead and this run, so this is self-verified, not independent human verification.

## Reproduce

Read the tool, its imports and the test file first; run from the repository root at `74aa7b5` with local copies of the exact hashes:

    python -I -B tools/test_token_luma_phase_probe.py
    python -I -B tools/token_luma_phase_probe.py FILE1997 --stride 5240 --rows 300 --step 16 --refine 16
    python -I -B tools/token_luma_phase_probe.py FILE1997 --stride 5240 --rows 300 --step 16 --refine 16 --perms 1 --seed 1
    python -I -B tools/token_luma_phase_probe.py FILE1998 --stride 5240 --rows 300 --step 16 --refine 16

The tool prints phase 0, the best phase and r, the top phases, the null maximum and the escape count, and writes no files. Both inputs are public CC0 raw.pixls.us files; no private or image data is used.
