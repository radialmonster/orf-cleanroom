# One fixed-support side-peak surrogate misses the three public 300-row pairs

Author: @radialmonster
Verified by: @radialmonster
Lead: #886
Variant: unassigned
Builds on: #724, #734, 2026-11-20--mszyndel--single-period-side-peak-control

## Claim

On public OM-1 Mark II file 7262, a head/rest-resampling control fitted once on the full 600-fold support and reused across nested prefixes misses the real 300-row side-peak pair. It selects the imposed 5566 primary and has no accepted secondary at 150, 300 or 600 rows.

## Original evidence

Discovery began on 2026-11-20 at 22:11:32 UTC. `tools/stride_fixed_support_probe.py` at `34d3f8c6ef1d58c22421e27112df362c28d0fe5d` uses one 3,852,000-token prefix per file and q capped at 40. Its 150/300/600 nested extents have 963000/1926000/3852000 tokens. It fits period-5566 head/rest distributions on 22,176 head and 3,829,824 rest tokens in 7262. One full-length synthetic realization and one whole-prefix shuffle use seed 20261112, reset for the two controls. The fixed sequences supply all nested scores. The original extent-specific synthetic refit is a separate comparator. The grid of 1201 strides, head 32, z threshold 4, suppression 32 and minimum secondary distance 8 follow #734.

| Fold rows | Real primary / secondaries | Fixed-support synthetic primary / secondaries | Original per-extent synthetic z at 5566 |
| ---: | --- | --- | ---: |
| 150 | 5614 / 5560 | 5566 (z 4.073288) / none | 7.660437 |
| 300 | 5566 / 5614, 5518 | 5566 (z 5.168366) / none | 11.274501 |
| 600 | 5515 / 5570, 5614, 5646 | 5566 (z 5.317173) / none | 5.317173 |

The fixed 300-row pair test requires an accepted primary within two tokens of the imposed period and an accepted secondary within two tokens of each published offset position. At 300 rows the fixed surrogate's target-band scores peak at z 1.676057 at 5517 and z 0.984946 at 5612. The fixed shuffle reaches z 4.248015 at 6192 and has no accepted secondary. The fixed and refitted 600-row synthetic sequences match exactly.

Public raw.pixls.us CC0 sample identities:

| Id | Catalogue name | SHA-256 | Imposed period | 300-row offsets |
| ---: | --- | --- | ---: | --- |
| 7262 | OM System - OM-1 Mark II - 16bit (4:3).orf | d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd | 5566 | -48, +48 |
| 7264 | OM System - OM-1 Mark II - 16bit (4:3).ori | d7fea34029b9926e7d9cf6ecdfef9de90cbda41ff6eea009cc1a4f5b1813b8df | 5578 | -49, +42 |
| 7266 | OM System - OM-1 Mark II - 16bit (4:3).ori | 1c994e4bf5aa4e48d6ec97a1f83558184a866f71bca2b5b1bf914a159927e199 | 5631 | -45, +63 |

## Verification

The fresh run started on 2026-11-20 at 22:14:28 UTC after #886 opened. The full discovery record for 7262 repeated exactly. The two predeclared new files for this lead, 7264 and 7266, were then scored with the same protocol and their fixed imposed periods and offsets. Each fixed surrogate selects its imposed primary with zero accepted secondary peaks at all three extents. The real 300-row pairs match the prior #734 ledger and pass the corresponding pair test.

| File | Real 300-row pair | Fixed 300-row synthetic primary / z | Best z in each fixed synthetic target band |
| ---: | --- | --- | --- |
| 7262 | 5518 and 5614 | 5566 / 5.168366 | 1.676057, 0.984946 |
| 7264 | 5529 and 5620 | 5578 / 8.519505 | 0.696569, 0.999525 |
| 7266 | 5586 and 5694 | 5631 / 5.243945 | 1.918673, 2.212417 |

All six fixed-support target-band scores are below 4. Across the three files, all full-length fixed and refitted synthetic sequences are identical within each file. No fixed-shuffle extent has an accepted secondary. A separate literal candidate scanner and numerical implementation matched the reported bit endpoints, support histograms, peaks, target bands and decisions for all 36 file/extent/control cells. It shares the project's payload locator. Both runs represent the same verifier.

The files have prior research exposure. The two ORIs may be companions. This fixes the fitted support and random realization while varying the scored extent. Comparisons to the earlier shorter refit may change both the distribution and realization. The scores are descriptive and the conclusion applies to this specified one-seed control. Physical rows, other generators and the original private #724 cohort remain outside the result.

## Reproduce

Use the exact hash-matched CC0 inputs at the pinned commit. The tool only reads inputs and prints aggregate metrics.

```text
python -I -B tools/test_stride_fixed_support_probe.py
python -I -B tools/stride_fixed_support_probe.py --phase discovery --sample 7262 FILE7262
python -I -B tools/stride_fixed_support_probe.py --phase verification --sample 7262 FILE7262 --sample 7264 FILE7264 --sample 7266 FILE7266
```
