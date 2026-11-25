# Partner-quotient mix explains little of the fixed dark-field mean contrast

Author: @radialmonster
Verified by: @radialmonster
Lead: #972
Variant: unassigned
Builds on: #961, #969, #971

## Claim

The original fixed two-word candidate-field comparison reproduces on six OM-3 and six E-M5 Mark II public dark captures. In the original band, changing the proportions of partner q=0 versus q=1..11 accounts for about 1.93% and 0.068% of the respective declared-ISO mean differences under the symmetric decomposition. The weighted within-stratum term is also the largest in magnitude of the three contributions to the third central moment in each original body/ISO group.

## Original evidence

Lead #972 fixed the candidate parser, startup guard, and original adjacent partner from #961. The two words form a statistical field. Pairs containing a capped escape are excluded. The original nominal rectangle uses rows 20–599 and columns 20 through W−21, inclusive. It is not a registered pixel rectangle. The two strata use the adjacent partner word, not the current word. Pooled groups weight observed eligible pairs equally. Declared ISO is a capture grouping, not an intervention.

| Body | 800 minus 200 mean | Mix term | Within-stratum term |
| --- | ---: | ---: | ---: |
| OM-3 | -0.562933364 | -0.010847336 | -0.552086029 |
| E-M5 Mark II | -0.423060345 | -0.000289511 | -0.422770834 |

The original rectangle has 3004400 eligible pairs per OM-3 file and 2668000 per E-M5 Mark II file, with no omitted escape pairs. At ISO 200 the pooled q>0 strata have only 5 and 20 observations in the respective bodies. All exact fractions, including third-moment terms, are reproduced from the two-stratum histograms.

## Verification

The full parsed JSON of both body cohorts matched the saved discovery reports on 2026-11-25 at 18:22:04 UTC, after the lead was opened. All 12 inputs passed their retained CC0 identity and full SHA-256 gates. Only after both matches did the unchanged tool score nominal rows 620–1199 on the same captures. The scored token-pair rectangles do not overlap. This extends the measured window, not the list of captures or the range of ISO settings.

| Body | Later 800 minus 200 mean | Mix term | Within-stratum term | Mix share |
| --- | ---: | ---: | ---: | ---: |
| OM-3 | -0.563863334 | -0.008316450 | -0.555546884 | 1.474905% |
| E-M5 Mark II | -0.420668879 | -0.000203626 | -0.420465253 | 0.048405% |

| Body / ISO | Eligible partner q=0 | Eligible partner q>0 | Third central moment | Weighted within | Variance-offset interaction | Cubic mean offsets |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OM-3 / 200 | 6008791 | 9 | -0.460785950 | -0.460361446 | -0.000399451 | -0.000025053 |
| OM-3 / 800 | 11977365 | 40235 | -24.870781784 | -24.370992315 | -0.453233417 | -0.046556052 |
| E-M5 Mark II / 200 | 8003964 | 36 | -0.917766666 | -0.916861323 | -0.000866657 | -0.000038687 |
| E-M5 Mark II / 800 | 8003316 | 680 | -15.754354660 | -15.738067473 | -0.013964807 | -0.002322381 |

The later OM-3 per-file partner q>0 counts, in the order of #972, are 5, 4, 9930, 10188, 10127 and 9990. The E-M5 Mark II counts are 11, 12, 13, 233, 241 and 206. Only P1010019 omits pairs for escapes, four in all, retaining 2667996 eligible pairs. Every other file has the same eligible count as in the original band. These are omitted pairs under the candidate grammar, not four verified escape words.

The small mix share and within-term dominance persist in the later band, but the exact shares change. Separate calculations from the reported histograms agree on the exact fractions. A second capped-word cursor, with the same declared-strip reader, reproduces all per-file aggregates on PA200010, PA200012, P1010011, P1010017 and P1010019. The later lower-ISO q>0 strata still have sparse observed support. This is self-verification, not an independent human reproduction or evidence of a physical predictor, gain response or bitstream field.

## Reproduce

At `85975c01423583afdc3512985a4e7397f6b878c9`, form the two six-file body cohorts below. The repository's `samples/om3-flat-338-provenance.json` and `samples/e-m5-mk-ii-dark-338-provenance.json` record the public identity and retained CC0 licence. Run one command per body per window, repeating the four `--sample` arguments for each capture. Check the original result before the later one.

    python -I -B tools/value_field_q_accounting.py --window original --sample GROUP PUBLIC_NAME SHA256 FILE
    python -I -B tools/value_field_q_accounting.py --window later --sample GROUP PUBLIC_NAME SHA256 FILE

Compare all six per-file eligible and omitted counts, both partner histograms, the summaries' exact `contrast_800_minus_200` fractions and both groups' `third_central_terms`. Signed shares divide the mix term by the total mean difference. No private inputs were used.

| Body | Declared ISO | Public capture | SHA-256 |
| --- | ---: | --- | --- |
| OM-3 | 200 | PA200010.ORF | `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4` |
| OM-3 | 200 | PA200011.ORF | `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3` |
| OM-3 | 800 | PA200012.ORF | `c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7` |
| OM-3 | 800 | PA200013.ORF | `b714b28697a94081b83d7dd6127ed295f3ffbf6045b098a93381e373f8e3b946` |
| OM-3 | 800 | PA200014.ORF | `49d1719d4120da07911488060c35f8d47dd76b9fc03c328d3cea8a190e298fca` |
| OM-3 | 800 | PA200015.ORF | `84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278` |
| E-M5 Mark II | 200 | P1010009.ORF | `ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c` |
| E-M5 Mark II | 200 | P1010011.ORF | `d34532152c79ef24b22c60c6cf743cef41fe28196b40fe16b557c16b7a7ea03d` |
| E-M5 Mark II | 200 | P1010013.ORF | `81acdd3675c329b351a634cfb4e22228f2db8df94f36480690e04416ded0817d` |
| E-M5 Mark II | 800 | P1010017.ORF | `431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5` |
| E-M5 Mark II | 800 | P1010018.ORF | `e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f` |
| E-M5 Mark II | 800 | P1010019.ORF | `5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75` |
