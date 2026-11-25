# Unsigned 12-bit range does not distinguish two fixed dark-field recurrences from controls

Author: @radialmonster
Verified by: @radialmonster
Lead: #1015
Variant: unassigned
Builds on: #31, #961, #972, #1011

## Claim

On the six public OM-3 dark candidate rectangles, neither fixed unwrapped recurrence fails the unsigned 12-bit range condition. Both row/parity shuffled controls also fit. This is a bound on candidate sequences with free per-chain seeds, not evidence for a physical predictor.

## Original evidence

Lead #1015 froze the measurement in #31 and used `tools/value_field_predictor_range.py` at `5002a196f7de58354451bed8e6e0d4347f7f55b1`. It preserves the #961/#972 field, parser, adjacent partner, omissions, nominal rows 20–599 and columns 20 through W−21. The recurrence adds each candidate residual to the previous value in its chain with unit coefficient and no wrapping, clamping, intermediate resets or scaling. H has lag two columns and V has lag two nominal rows. Each chain can choose its own in-range initial value.

The span is max minus min over the constant-zero origin and all prefix sums. A shift puts the whole sequence in 0..4095 if and only if this span is at most 4095. Any omitted pair makes its chain unknown. The two controls shuffle separately within each nominal row and column parity, keeping omitted positions fixed, with seeds 1 and 2 reset per capture.

The six original captures have 3004400 eligible pairs and no omissions each. For every original and shuffled field, all 1160 H and 10360 V chains are complete and none exceeds 4095. The largest original maxima are H=1914 and V=300, with all per-file maxima in #1015.

## Verification

The full six-file original report matched the saved aggregate at 19:12:44 UTC on 2026-11-25, after the lead was posted. Only then did the same commands and rules score the reserved six E-M5 Mark II dark captures. Both cohorts passed the complete retained CC0 hash checks. The reserved files are new to this measurement, not unseen to the project.

Every E-M5 Mark II capture gives 2668000 eligible pairs and no omissions. The per-file field sums and q support match #972. There are 1160 H and 9200 V complete chains per file for the original and for each control. No chain exceeds 4095. The values below are maximum complete spans, not normalized by chain length.

| E-M5 Mark II capture | Declared ISO | Original H / V | Seed 1 H / V | Seed 2 H / V |
| --- | ---: | ---: | ---: | ---: |
| P1010009.ORF | 200 | 364 / 58 | 380 / 109 | 385 / 100 |
| P1010011.ORF | 200 | 361 / 50 | 365 / 103 | 358 / 104 |
| P1010013.ORF | 200 | 371 / 57 | 385 / 103 | 381 / 109 |
| P1010017.ORF | 800 | 1437 / 311 | 1455 / 333 | 1442 / 331 |
| P1010018.ORF | 800 | 1441 / 253 | 1437 / 333 | 1443 / 325 |
| P1010019.ORF | 800 | 1333 / 238 | 1324 / 325 | 1362 / 358 |

The bound still cannot distinguish either recurrence on the original arrangement from its row/parity shuffle controls. The directions use different chain lengths and are not ranked by the raw spans. An origin-interval implementation with the same field parser independently matches all 36 reserved summaries, including chain counts and maximum spans. This is verified by the finder, not by a second human. It is not a stationary or physical reconstruction, a CFA assignment, or a camera bit-depth determination.

## Reproduce

At `5002a196f7de58354451bed8e6e0d4347f7f55b1`, use the exact named public CC0 captures and full hashes in #972 and the pinned `samples/om3-flat-338-provenance.json` and `samples/e-m5-mk-ii-dark-338-provenance.json` records. Use the published order. The tool checks full hashes before parsing.

    python -I -B tools/test_value_field_predictor_range.py
    python -I -B tools/value_field_predictor_range.py --sample PA200010.ORF FILE0010 --sample PA200011.ORF FILE0011 --sample PA200012.ORF FILE0012 --sample PA200013.ORF FILE0013 --sample PA200014.ORF FILE0014 --sample PA200015.ORF FILE0015
    python -I -B tools/value_field_predictor_range.py --cohort repeat --sample P1010009.ORF FILE0009 --sample P1010011.ORF FILE0011 --sample P1010013.ORF FILE0013 --sample P1010017.ORF FILE0017 --sample P1010018.ORF FILE0018 --sample P1010019.ORF FILE0019

Compare `support` and the fixed `outcomes` counts and maxima. No private files were used.
