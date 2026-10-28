# Conditional lag-three candidate-token information

Author: @radialmonster
Verified by: @radialmonster
Lead: #654
Variant: unassigned
Builds on: #29, #650

## Claim

On two previously studied public files, conditional and unconditional lag-3 mutual information differ for both q>0 and suffix b0 when calculated on the same candidate-token quadruples. The q>0 conditional MI is 0.0246073105 bits on 1993 and 0.00268782342 bits on 5283. These are descriptive associations, not causal or codec-state results.

## Original evidence

The lead used `tools/token_lag3_conditional_probe.py` at commit `0c57fa682ae983ba629b5c630f819b6fcaae214f` on 262144 candidate words from 1993 and 5283. The fresh results for these two prefixes are included below. An initial 1993 wrapper attempt stopped before sample access due to a source-hash transcription error; the corrected, separately saved run supplied the lead.

## Verification

After publication, the two original prefixes were freshly rerun and the predeclared 524288-word extent was measured on 1993, 5283, 1995 and 6343. The two additional files and wider extents qualify the verification; all four files had been exposed in earlier work and are not blind captures or independently verified by a second human.

Parse stop-1/five-suffix candidate words from payload bit zero, without extra escape skipping. Divide into original-index 128-token blocks, omit whole blocks containing q>=17, and use positions t=3..127 within each retained block. For each field set X=bit(t), Y=bit(t-3), Z=(bit(t-1),bit(t-2)). The table reports I(X;Y) and I(X;Y|Z) in bits on identical positions. Null columns show mean and range of 16 controls that shuffle whole tokens within each retained block with fresh `Random(20261021+replicate)` per replicate. These controls are descriptive, not calibrated significance tests. All runs reached the requested extent; each block contributes 125 quadruples.

| ID | Words | Field | Retained blocks | Quadruples | Context counts 00,01,10,11 | Unconditional MI | Conditional MI | Null mean (range), unconditional then conditional |
|---|---:|---|---:|---:|---|---:|---:|---|
| 1993 | 262144 | q_positive | 2047 | 255875 | 215638, 19428, 19416, 1393 | 0.0246230867 | 0.0246073105 | 8.25452889e-05 (3.58961038e-05..0.000118993742), 8.83088645e-05 (5.00088234e-05..0.000123260038) |
| 1993 | 262144 | suffix_b0 | 2047 | 255875 | 65376, 64056, 64028, 62415 | 1.51902656e-05 | 2.90353118e-05 | 2.04997335e-06 (3.03525398e-11..6.16672269e-06), 9.05687759e-06 (4.0541361e-06..2.33930611e-05) |
| 5283 | 262144 | q_positive | 1787 | 223375 | 65873, 53831, 53815, 49856 | 0.00221593312 | 0.00268782342 | 0.000591985198 (0.000349210127..0.000852476019), 0.000613237909 (0.000368411888..0.000863474983) |
| 5283 | 262144 | suffix_b0 | 1787 | 223375 | 61025, 55170, 55191, 51989 | 7.16777089e-06 | 2.51307689e-05 | 2.13942388e-06 (1.41195732e-09..9.83716276e-06), 1.09814431e-05 (1.82291272e-06..3.4341788e-05) |
| 1993 | 524288 | q_positive | 4095 | 511875 | 434685, 36948, 36918, 3324 | 0.0257606335 | 0.0260824346 | 0.000481328966 (0.000358189384..0.000584254963), 0.000435749642 (0.00032332633..0.00053372373) |
| 1993 | 524288 | suffix_b0 | 4095 | 511875 | 131180, 127927, 127910, 124858 | 5.82153573e-06 | 7.78511851e-06 | 8.2430654e-07 (2.07649979e-09..2.54981776e-06), 4.3255244e-06 (1.05666312e-06..1.08848886e-05) |
| 5283 | 524288 | q_positive | 3589 | 448625 | 132170, 108363, 108368, 99724 | 0.00210713478 | 0.00257596722 | 0.000471642365 (0.000374685171..0.000625849352), 0.000502981336 (0.000391867202..0.000660356891) |
| 5283 | 524288 | suffix_b0 | 3589 | 448625 | 122341, 110900, 110887, 104497 | 1.84045667e-07 | 1.2538306e-05 | 1.28304722e-06 (6.71349284e-09..4.67302042e-06), 5.63071311e-06 (1.33511051e-06..8.50460219e-06) |
| 1995 | 524288 | q_positive | 4095 | 511875 | 432517, 38280, 38287, 2791 | 0.0234975444 | 0.0234286972 | 7.27432993e-05 (5.17785011e-05..0.000107670185), 7.53755458e-05 (5.34397533e-05..0.000121956517) |
| 1995 | 524288 | suffix_b0 | 4095 | 511875 | 129802, 128170, 128217, 125686 | 6.99967923e-09 | 3.93203293e-07 | 7.94286968e-07 (3.45210696e-08..1.73072473e-06), 4.77428924e-06 (5.70197102e-07..1.36200667e-05) |
| 6343 | 524288 | q_positive | 4032 | 504000 | 237851, 97231, 97246, 71672 | 0.0211797705 | 0.0213417778 | 0.00477702502 (0.00457379326..0.00509532223), 0.00435957847 (0.00419502631..0.00463703191) |
| 6343 | 524288 | suffix_b0 | 4032 | 504000 | 132810, 124063, 124087, 123040 | 4.79039896e-05 | 5.06248482e-05 | 1.58848062e-06 (8.58145736e-09..4.43104244e-06), 6.84869601e-06 (2.15999863e-06..2.26904171e-05) |

Independent parsing and all observed and 16 shuffled 16-cell joint tables and four context totals for both fields matched exactly. Both MI measures agreed within 1e-12 for every table. The implementations share a TIFF locator and assisted the same human. Unknown framing and omission of escape-containing blocks limit interpretation; these comparisons do not establish physical structure or causation.

## Reproduce

The retained verified public CC0 inputs are:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`

At commit `0c57fa682ae983ba629b5c630f819b6fcaae214f`, verify identities and hashes, substitute local paths, and run:

```text
python -I -B tools/token_lag3_conditional_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --tokens 262144
python -I -B tools/token_lag3_conditional_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --tokens 262144
python -I -B tools/token_lag3_conditional_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --tokens 524288
python -I -B tools/token_lag3_conditional_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --tokens 524288
python -I -B tools/token_lag3_conditional_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --tokens 524288
python -I -B tools/token_lag3_conditional_probe.py --sample 6343 "OM System - OM-5 - 16bit (4:3).ORF" FILE6343 --tokens 524288
```

The output retains all counts, nulls, endpoints and source hashes. Separately justified conditioning and framing assumptions remain to be tested on the existing corpus.
