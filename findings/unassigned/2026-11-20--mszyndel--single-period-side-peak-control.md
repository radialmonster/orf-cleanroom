# Independent reproduction of the fixed single-period side-peak control

Author: @mszyndel
Verified by: @radialmonster
Lead: #734
Variant: unassigned
Builds on: #724, #144, #197
Reproduces: 2026-11-13--mszyndel--single-period-side-peak-control

## Claim

The specified fixed single-period head/rest-resampling control reproduces none of the real 300-row side-peak pairs on the three public files in the original finding. Each control selects its imposed primary and produces zero accepted secondary peaks. This tests the declared one-seed surrogate.

## Original evidence

Lead #734 tested file 7262. The original finding reproduced its nine cases and extended to the named 7264 and 7266 files. It used `tools/stride_harmonics.py` at repository commit `d50e4739c7ba5c64052da8867eb5ab8ecf9ee9a4`, with head 32, stride grid 5220..6420, z threshold 4, suppression 32, minimum distance 8, maximum rational denominator 12, tolerance 2 and seed 20261112 reset between invocations. The real, fixed single-period head/rest control and whole-prefix shuffle were all scored at 150, 300 and 600 folded rows. The synthetic distributions were fitted separately at each extent.

| Raw.pixls.us id | CC0 catalogue name | SHA-256 | Imposed period |
| ---: | --- | --- | ---: |
| 7262 | OM System - OM-1 Mark II - 16bit (4:3).orf | d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd | 5566 |
| 7264 | OM System - OM-1 Mark II - 16bit (4:3).ori | d7fea34029b9926e7d9cf6ecdfef9de90cbda41ff6eea009cc1a4f5b1813b8df | 5578 |
| 7266 | OM System - OM-1 Mark II - 16bit (4:3).ori | 1c994e4bf5aa4e48d6ec97a1f83558184a866f71bca2b5b1bf914a159927e199 | 5631 |

## Verification

On 2026-11-20 at 22:01 UTC, a fresh run used Python 3.14.10 at repository commit `6a0cd8c2143049ff0c3882a5bf4dd2caafa00da3`. The four source files `tools/stride_harmonics.py`, `tools/token_row_stride.py`, `tools/orf_tokens.py` and `tools/orf_signature.py` match the corresponding Git objects at the original run commit. Local input hashes matched their retained verified CC0 records and manifest entries. The three files include two beyond the original lead's discovery file, both previously measured in the author's self-verification. The known-period synthetic test passes.

All 27 CLI cases exit successfully. Their geometry, 963000/1926000/3852000 parsed token extents, all primary strides and every accepted secondary stride and z match the original published ledger at its two-decimal precision. Real secondary counts are 1/2/3 on 7262, 1/2/2 on 7264 and 1/2/3 on 7266 at 150/300/600 rows. The fixed-period and shuffled controls accept zero secondary peaks at all nine file/extent pairs. At 300 rows:

| File | Real primary | Real secondary pair | Synthetic primary | Synthetic secondaries |
| ---: | ---: | --- | ---: | ---: |
| 7262 | 5566 | 5518 and 5614 | 5566 | 0 |
| 7264 | 5578 | 5529 and 5620 | 5578 | 0 |
| 7266 | 5631 | 5586 and 5694 | 5631 | 0 |

The real 7266 peak at 5694 is the only rounded rational-window hit across the 27 cases. Its target is 12/11 and its exact residual displays as -0.55 tokens. There are zero exact rational hits. Each synthetic primary is within the frozen two-token bound, but the empty secondary lists fail the pair test on all three files.

The two reserved ORI files remain one possibly related group. The repeat uses the same token parser, score, files and single seed. The fitted support and prefix vary with extent. Independent framing, physical row geometry and nonstationary alternatives remain open. All inputs are public.

## Reproduce

Use `tools/stride_harmonics.py` at either pinned commit with the verified local FILE for each table row, its imposed PERIOD, and each value N of 150, 300 and 600. Run the synthetic test once and the three case commands for every file/extent pair.

```text
python -I -B tools/stride_harmonics.py --self-test
python -I -B tools/stride_harmonics.py --rows N --seed 20261112 FILE
python -I -B tools/stride_harmonics.py --rows N --seed 20261112 --control synthetic --period PERIOD FILE
python -I -B tools/stride_harmonics.py --rows N --seed 20261112 --control shuffle FILE
```
