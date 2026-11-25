# Permuted partner expectation does not account for the fixed dark-field mean contrast

Author: @radialmonster
Verified by: @radialmonster
Lead: #1011
Variant: unassigned
Builds on: #32, #961, #972, #1002

## Claim

The fixed candidate-field mean contrast on the six public OM-3 dark captures is not accounted for by the exact expected partner contribution after permuting within nominal rows and partner quotient classes. The current-only contrast is negative. The permuted expectation and pairing remainder contrasts are positive and offset it. This does not establish an interpretation of the field as a value or a predictor.

## Original evidence

Lead #1011 froze the calculation on #32 and used `tools/value_field_partner_null.py` at `7ba3e15cb36b0ada5f43e859b0ec9ca54851a090`. It keeps the original #972 parser, phase, adjacent partner, escape omissions, nominal rows 20–599 and columns 20 through W−21.

For current suffix a and partner suffix b, the field is C+S·B, where C=(a&3)−12·bit2(a), S=1−2·bit2(a), and B=8·bit4(b)−4·(1−bit3(b)). Within each capture, nominal row and partner q class (0 or 1..11), the expectation of the S·B sum over uniform permutations of B is (sum S)(sum B)/count. It uses both the observed current-sign and the observed partner-value marginals. The third contribution is observed S·B minus that expectation. Pool eligible pairs by count.

The six original OM-3 captures each have 3004400 eligible pairs and zero omissions. Their partner q>0 counts are 0, 5, 9555, 10038, 9879 and 9704. The exact observed contrast between the declared ISO 800 and 200 groups is −241611/429200.

## Verification

The six-file OM-3 report reproduced the entire saved JSON on 2026-11-25 at 18:57:47 UTC, after #1011 was posted. Only then did the unchanged calculation use the six reserved public E-M5 Mark II darks. All twelve captures passed their full hash checks against retained CC0 records. The reserved inputs were new to this calculation, not unseen to the project.

| Capture group | Declared ISO | Current only | Permuted partner expectation | Pairing remainder | Observed field mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| OM-3 | 200 | +1.238477566 | -1.243620008 | +0.006776711 | +0.001634270 |
| OM-3 | 800 | -0.055629743 | -0.985943596 | +0.480274245 | -0.561299095 |
| OM-3 | 800 minus 200 | -1.294107309 | +0.257676411 | +0.473497534 | -0.562933364 |
| E-M5 Mark II | 200 | +1.353605822 | -1.382525932 | +0.022658366 | -0.006261744 |
| E-M5 Mark II | 800 | +0.245352074 | -1.108979572 | +0.434305409 | -0.429322089 |
| E-M5 Mark II | 800 minus 200 | -1.108253748 | +0.273546361 | +0.411647042 | -0.423060345 |

Every E-M5 Mark II file gives 2668000 eligible pairs, zero omitted escapes and q>0 partner counts 6, 3, 11, 282, 225 and 248 in the listed order. The first three are declared ISO 200, with only 20 q>0 pairs pooled. The last three contain 755 in that stratum. Exact per-file support, histograms, and sums of current and observed partner contributions match the #972 original-band records. An independently written recount with the same parser and strip selection also matches the exact permutation expectation on all six reserved files. The E-M5 Mark II total is exactly −1963/4640.

The same three signs hold in both measured cohorts. The negative current contrast has the largest magnitude, with positive offsets from the permuted expectation and pairing remainder. These are descriptive identities for the named captures. Neither component isolates a causal ISO effect, and the preserving permutation is not a valid replacement bitstream or a significance test. The result provides no physical framing, sensor value mapping or predictor, and it is verified by the finder, not by a second human.

## Reproduce

At `7ba3e15cb36b0ada5f43e859b0ec9ca54851a090`, use the exact CC0 names and hashes recorded in #972 and `samples/om3-flat-338-provenance.json` or `samples/e-m5-mk-ii-dark-338-provenance.json`. Use the public captures in the declared order, replacing each FILE placeholder with the matching file. The tool checks full hashes before parsing.

    python -I -B tools/test_value_field_partner_null.py
    python -I -B tools/value_field_partner_null.py --sample PA200010.ORF FILE0010 --sample PA200011.ORF FILE0011 --sample PA200012.ORF FILE0012 --sample PA200013.ORF FILE0013 --sample PA200014.ORF FILE0014 --sample PA200015.ORF FILE0015
    python -I -B tools/value_field_partner_null.py --cohort repeat --sample P1010009.ORF FILE0009 --sample P1010011.ORF FILE0011 --sample P1010013.ORF FILE0013 --sample P1010017.ORF FILE0017 --sample P1010018.ORF FILE0018 --sample P1010019.ORF FILE0019

Check `summary.groups`, `summary.contrast_800_minus_200` and the per-file support counts. Use exact fractions before rounding. No private inputs were used.
