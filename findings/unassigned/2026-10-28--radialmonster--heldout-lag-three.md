# Held-out candidate-token lag-three comparison

Author: @radialmonster
Verified by: @radialmonster
Lead: #658
Variant: unassigned
Builds on: #29, #650, #654

## Claim

On two previously studied public files, an order-3 KT model trained on candidate-token band 0 has lower held-out q>0 log loss on band 1 than an order-2 model, by 0.0276848692 and 0.00245779568 bits per target respectively. The suffix-b0 control has a negative gain on both files. This fixed comparison does not establish physical codec state or causal structure.

## Original evidence

The lead measured train band 0 and test band 1 on 1993 and 5283 using `tools/token_lag3_heldout_probe.py` at commit `3b4d799e421d88f46f2bc4c8f779430c42b7b965`. The fresh results for those comparisons are included below.

## Verification

After publication, both original comparisons were freshly rerun; the predeclared band-0-to-band-2 comparison was also measured on 1993, 5283, 1995 and 6343. The band-2 q>0 gains are positive on all four files. The band-2 suffix-b0 gains are negative on 1993 and 5283 and positive on 1995 and 6343. The new files and wider window qualify the verification; all files had been exposed in earlier work and are not blind captures or independently verified by a second human.

Parse stop-1/five-suffix candidate words from payload bit zero, without extra escape skip. Each band has 262144 candidate words. Within each band split original-index 128-token blocks, omit whole blocks containing q>=17, and use targets t=3..127. Fit orders 0, 2 and 3 on training band-0 outcome tables only, using KT half counts: P(v|context)=(count(v)+0.5)/(context total+1). Context is preceding same-field bits at lags 1..order. Do not update on test; unseen contexts predict 0.5. The signed gain is order-2 loss minus order-3 loss in bits per target. All requested words were parsed, and each retained block contributes 125 targets.

| ID | Test band | Field | Train blocks | Test blocks | Train targets | Test targets | Unseen order-3 test targets | Held-out losses order 0,2,3 | Gain 2 minus 3 | Shuffled gain mean (range) |
|---|---:|---|---:|---:|---:|---:|---:|---|---:|---|
| 1993 | 1 | q_positive | 2047 | 2048 | 255875 | 256000 | 0 | 0.387667853, 0.388820659, 0.361135789 | 0.0276848692 | 0.000473194718 (0.000201842788..0.000587666614) |
| 1993 | 1 | suffix_b0 | 2047 | 2048 | 255875 | 256000 | 0 | 0.999874755, 0.999884262, 0.999920012 | -3.5749644e-05 | -8.00954784e-06 (-1.61284453e-05..9.88204788e-06) |
| 5283 | 1 | q_positive | 1787 | 1802 | 223375 | 225250 | 0 | 0.996200912, 0.995449394, 0.992991599 | 0.00245779568 | 0.000365021403 (0.000189348007..0.000509149842) |
| 5283 | 1 | suffix_b0 | 1787 | 1802 | 223375 | 225250 | 0 | 0.998882871, 0.998853378, 0.998866017 | -1.26386307e-05 | -9.55398478e-06 (-3.58372377e-05..7.98136479e-06) |
| 1993 | 2 | q_positive | 2047 | 2048 | 255875 | 256000 | 0 | 0.280646682, 0.282609517, 0.254757247 | 0.0278522705 | 0.000568150549 (0.000395876358..0.00075848136) |
| 1993 | 2 | suffix_b0 | 2047 | 2048 | 255875 | 256000 | 0 | 1.00003949, 1.00003063, 1.00007951 | -4.88801685e-05 | -9.52805422e-06 (-3.56503394e-05..6.68343603e-06) |
| 5283 | 2 | q_positive | 1787 | 1760 | 223375 | 220000 | 0 | 0.996183477, 0.994801088, 0.991458576 | 0.00334251145 | 0.000686371843 (0.000480081958..0.000909775782) |
| 5283 | 2 | suffix_b0 | 1787 | 1760 | 223375 | 220000 | 0 | 0.998805909, 0.998703212, 0.998721245 | -1.80332045e-05 | -1.25184309e-05 (-6.7749561e-05..4.93466669e-06) |
| 1995 | 2 | q_positive | 2047 | 2048 | 255875 | 256000 | 0 | 0.405416242, 0.404591492, 0.380790384 | 0.023801108 | 3.40614569e-05 (-4.62953324e-05..9.5387134e-05) |
| 1995 | 2 | suffix_b0 | 2047 | 2048 | 255875 | 256000 | 0 | 0.999897187, 0.999901455, 0.999890062 | 1.13936372e-05 | -1.10762645e-05 (-2.81944361e-05..2.41122125e-06) |
| 6343 | 2 | q_positive | 2014 | 2019 | 251750 | 252375 | 0 | 0.915779412, 0.893497296, 0.869679135 | 0.0238181617 | 0.0056186389 (0.00533328338..0.00598574813) |
| 6343 | 2 | suffix_b0 | 2014 | 2019 | 251750 | 252375 | 0 | 0.999709072, 0.999590894, 0.999547988 | 4.29059665e-05 | -1.46215895e-05 (-4.22865913e-05..8.99068384e-06) |

Each band contains 2048 complete blocks; omitted counts are 2048 minus retained counts above. The 16 controls independently shuffle whole tokens within retained train/test blocks, resetting `Random(20261021+replicate)` for train and `Random(20361021+replicate)` for test. These controls are descriptive, not calibrated significance tests. Independent implementations agreed on every observed and shuffled training/test count table exactly and on losses/gains within 1e-12. They share a TIFF locator and assisted the same human. Unknown framing and escape-block omission limit interpretation.

## Reproduce

The retained verified public CC0 inputs are:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`

At commit `3b4d799e421d88f46f2bc4c8f779430c42b7b965`, verify these identities and hashes, substitute local paths, and run:

```text
python -I -B tools/token_lag3_heldout_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --test-band 1
python -I -B tools/token_lag3_heldout_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --test-band 1
python -I -B tools/token_lag3_heldout_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --test-band 2
python -I -B tools/token_lag3_heldout_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --test-band 2
python -I -B tools/token_lag3_heldout_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --test-band 2
python -I -B tools/token_lag3_heldout_probe.py --sample 6343 "OM System - OM-5 - 16bit (4:3).ORF" FILE6343 --test-band 2
```

The tool prints all observed and shuffled tables, unseen counts, losses, selection, endpoints and source hashes. Separately justified context and framing assumptions remain to be tested on the existing corpus.
