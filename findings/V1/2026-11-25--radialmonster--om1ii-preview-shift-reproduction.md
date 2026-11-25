# Fixed nominal preview alignment is not specific on OM-1 Mark II 7262

Author: @radialmonster
Verified by: @radialmonster
Lead: #980
Variant: V1
Builds on: #351, #368, 2026-10-26--radialmonster--normal-mode-luma-not-vertical-specific

## Claim

On public OM-1 Mark II 7262 the fixed nominal b2+b4 top-band comparison does not give its highest correlation at zero vertical preview shift. The nominal alignment ranks 13 of 23. The best nonzero circular shift is k=5 at r=+0.01740, compared with r=−0.00344 at zero. This is a score on candidate and preview grids and does not identify physical row registration.

The same comparison on the predeclared public OM-1 Mark II 7264 also places zero shift below another shift, ranking 15 of 23.

## Original evidence

Lead #980 fixed the original comparison from #368 under the predeclared scope on #351. The probe folds candidate words at the declared width from payload bit zero, computes the sum of two suffix bits, smooths horizontally with a 63-token window and block-averages the first 300 candidate rows to the top of the embedded preview DC grid. It compares those grids by row-centred correlation, moving only the preview rows in the circular-shift test. No phase, stride or value map is fitted. Candidate words marked q≥17 contribute zero in this map under the fixed parser, without establishing actual escape syntax.

The comparison used public CC0 OM-1 5283 as a known control before opening OM-1 Mark II 7262. Both completed the 300-row request, with declared 5220 × 3912 payload geometry, a 400 × 300 preview DC grid and 23 × 400 compared cells. The rank counts ties against zero. The 20 within-row shuffles are a separate diagnostic, and neither comparison is a calibrated test of physical alignment.

## Verification

The fresh control and discovery runs reproduced the complete saved stdout on 2026-11-25 after #980 was posted. The discovery match was checked at 18:31:03 UTC before opening reserved public 7264. All three public CC0 inputs passed full SHA-256 checks before and after, exited zero and had empty stderr. The new file also used all 300 requested candidate rows at 5220 × 3912, with a 400 × 300 preview DC grid and a 23 × 400 compared band.

| Public ID | Zero-shift r | Within-row shuffle mean ± SD | z | Candidate escapes set to zero | Best nonzero k and r | Zero-shift rank | Nonzero mean ± SD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5283 | +0.00762 | -0.00341 ± 0.02534 | +0.44 | 1922 | 7, +0.02195 | 16/23 | +0.01051 ± 0.00810 |
| 7262 | -0.00344 | +0.00104 ± 0.02252 | -0.20 | 5973 | 5, +0.01740 | 13/23 | -0.00462 ± 0.01166 |
| 7264 | +0.01871 | -0.00006 ± 0.01656 | +1.13 | 6325 | 16, +0.04368 | 15/23 | +0.02396 ± 0.01135 |

A separate correlation and rank implementation matched the zero score, best alternative and shift summary at printed precision on 7264. It verified all 23 scores were finite, using the same pinned parser, preview reader and token-grid calculation. The shuffle was not part of that separate audit.

7264 is new to this fixed comparison, not an unseen file to the project. This is same-account verification. In particular its nominal correlation is positive, but not the best among the tested shifts. Neither this rank nor the shuffle score licenses an inference about which shift is physically correct, about sensor values or about V1 membership.

## Reproduce

Use `tools/token_luma_probe.py` at `d67dbe3b99eb6a409bdd3c8dd9a09ff2cc8c5e31`. Verify each exact hash before processing. Run the same command on 5283 and 7262 before the reserved file 7264. No private input was used.

    python -I -B tools/token_luma_probe.py FILE --rows 300 --window 63 --perms 20 --seed 1 --map sum --shift-null

| Public ID and raw.pixls.us name | SHA-256 |
| --- | --- |
| 5283, OM System - OM-1 - 16bit (4:3).ORF | `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b` |
| 7262, OM System - OM-1 Mark II - 16bit (4:3).orf | `d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd` |
| 7264, OM System - OM-1 Mark II - 16bit (4:3).ori | `d7fea34029b9926e7d9cf6ecdfef9de90cbda41ff6eea009cc1a4f5b1813b8df` |
