# Held-out candidate phase-three sensitivity

Author: @radialmonster
Verified by: @radialmonster
Lead: #666
Variant: unassigned
Builds on: #29, #650, #658

## Claim

On two previously studied public files, a fixed phase-plus-lag3 model's q>0 held-out loss is slightly higher than the pooled lag3 model at rotation 0 and slightly lower at rotation 1. These are descriptive candidate-token comparisons, not a physical three-lane or codec claim.

## Original evidence

The lead measured train band 0 and test band 1 on 1993 and 5283 using `tools/token_phase3_heldout_probe.py` at commit `01a9cb322fdd4d185853aef17d06572c4e878860`. Fresh results for these original cases appear below.

## Verification

After publication, both original comparisons were freshly reproduced and the predeclared train-band-0/test-band-2 comparison was measured on 1993, 5283, 1995 and 6343. The later band and additional files qualify verification; all files were exposed in prior work and the verifier is the finder. Results vary with rotation: for example, band-2 q>0 pooled-minus-combined gain is negative for all rotations on 1995, and positive only at rotation 2 on 6343. No universal rotation superiority follows.

Parse stop-1/five-suffix words from payload bit zero without extra escape skip; band b comprises candidate-token indices b*262144 through (b+1)*262144-1. Within each band retain original-index 128-token blocks without q>=17 and use t=3..127 targets. Absolute phase is token index modulo 3, including the actual band offset; omitted blocks do not compact indices. Fit KT half-count pooled lag3, phase-only and phase-plus-lag3 models on training band-0 tables only, with no test updates. Test phases are rotated by 0, 1 or 2 while training phases remain fixed; no origin search. Unseen contexts predict 0.5 when training is nonempty. All requested words were parsed; each retained block contributes 125 targets.

The table reports loss in bits per target, pooled-minus-phase+lag3 and phase-only-minus-phase+lag3, and mean and range of the first gain under 16 whole-token within-block shuffles. Training and test controls use separate fresh `Random(20261021+replicate)` and `Random(20361021+replicate)` respectively; these are descriptive, not calibrated significance tests.

| ID | Test band | Field | Rotation | Train blocks | Test blocks | Train targets | Test targets | Unseen phase+lag3 targets | Losses pooled, phase, phase+lag3 | Pooled minus combined | Phase minus combined | Shuffled pooled-minus-combined mean (range) |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| 1993 | 1 | q_positive | 0 | 2047 | 2048 | 255875 | 256000 | 0 | 0.360805886, 0.387665471, 0.360808714 | -2.82756631e-06 | 0.0268567573 | -1.42267563e-05 (-4.51272311e-05..8.92171532e-06) |
| 1993 | 1 | q_positive | 1 | 2047 | 2048 | 255875 | 256000 | 0 | 0.360805886, 0.387662309, 0.36079988 | 6.00621342e-06 | 0.0268624288 | -1.06857376e-05 (-4.33042644e-05..1.56245763e-05) |
| 1993 | 1 | q_positive | 2 | 2047 | 2048 | 255875 | 256000 | 0 | 0.360805886, 0.387682007, 0.360822136 | -1.62494381e-05 | 0.0268598709 | -1.93429067e-05 (-4.34249392e-05..2.8136505e-06) |
| 1993 | 1 | suffix_b0 | 0 | 2047 | 2048 | 255875 | 256000 | 0 | 0.999882698, 0.99987834, 0.999883836 | -1.13769499e-06 | -5.49599655e-06 | -1.03403871e-05 (-7.59860331e-05..5.96821479e-06) |
| 1993 | 1 | suffix_b0 | 1 | 2047 | 2048 | 255875 | 256000 | 0 | 0.999882698, 0.999870902, 0.99988098 | 1.71871636e-06 | -1.00773607e-05 | -1.74770213e-05 (-6.16407325e-05..2.34335811e-06) |
| 1993 | 1 | suffix_b0 | 2 | 2047 | 2048 | 255875 | 256000 | 0 | 0.999882698, 0.999880862, 0.999890005 | -7.30628203e-06 | -9.14237323e-06 | -1.30922741e-05 (-3.19190522e-05..6.4219222e-06) |
| 5283 | 1 | q_positive | 0 | 1787 | 1802 | 223375 | 225250 | 0 | 0.994204369, 0.996206084, 0.994224597 | -2.02279065e-05 | 0.00198148653 | -9.24591958e-06 (-4.45552228e-05..1.8978974e-05) |
| 5283 | 1 | q_positive | 1 | 1787 | 1802 | 223375 | 225250 | 0 | 0.994204369, 0.996193846, 0.994204006 | 3.63202977e-07 | 0.00198984003 | -1.16480128e-05 (-4.1269823e-05..4.4458898e-06) |
| 5283 | 1 | q_positive | 2 | 1787 | 1802 | 223375 | 225250 | 0 | 0.994204369, 0.996206863, 0.994220406 | -1.60367685e-05 | 0.00198645666 | -1.20769077e-05 (-5.69575625e-05..4.54826148e-06) |
| 5283 | 1 | suffix_b0 | 0 | 1787 | 1802 | 223375 | 225250 | 0 | 0.998899677, 0.998887468, 0.998903775 | -4.09744387e-06 | -1.63064735e-05 | -1.40227786e-05 (-7.83843974e-05..1.24835416e-05) |
| 5283 | 1 | suffix_b0 | 1 | 1787 | 1802 | 223375 | 225250 | 0 | 0.998899677, 0.998896777, 0.998913359 | -1.3681266e-05 | -1.65817121e-05 | -1.60732097e-05 (-4.98515301e-05..3.34161489e-06) |
| 5283 | 1 | suffix_b0 | 2 | 1787 | 1802 | 223375 | 225250 | 0 | 0.998899677, 0.998898381, 0.998919488 | -1.98111043e-05 | -2.11076944e-05 | -1.00595121e-05 (-3.25431785e-05..1.42031691e-05) |
| 1993 | 2 | q_positive | 0 | 2047 | 2048 | 255875 | 256000 | 0 | 0.254016369, 0.280640311, 0.254014235 | 2.13323204e-06 | 0.0266260755 | -1.45742018e-05 (-3.54625225e-05..8.47155501e-06) |
| 1993 | 2 | q_positive | 1 | 2047 | 2048 | 255875 | 256000 | 0 | 0.254016369, 0.280651736, 0.254022095 | -5.7262111e-06 | 0.026629641 | -7.77416849e-06 (-3.16429031e-05..1.77842159e-05) |
| 1993 | 2 | q_positive | 2 | 2047 | 2048 | 255875 | 256000 | 0 | 0.254016369, 0.280658137, 0.254028222 | -1.18528651e-05 | 0.026629915 | -1.32250071e-05 (-3.94422243e-05..6.53317576e-06) |
| 1993 | 2 | suffix_b0 | 0 | 2047 | 2048 | 255875 | 256000 | 0 | 1.00005513, 1.00004262, 1.00005572 | -5.94626057e-07 | -1.3097703e-05 | -6.70245687e-06 (-3.51340643e-05..7.42104068e-06) |
| 1993 | 2 | suffix_b0 | 1 | 2047 | 2048 | 255875 | 256000 | 0 | 1.00005513, 1.00004291, 1.00006127 | -6.14444949e-06 | -1.83604992e-05 | -1.48755264e-05 (-3.89656575e-05..3.07202876e-06) |
| 1993 | 2 | suffix_b0 | 2 | 2047 | 2048 | 255875 | 256000 | 0 | 1.00005513, 1.00003876, 1.00005515 | -2.50534062e-08 | -1.63899625e-05 | -1.94024235e-05 (-6.40855453e-05..7.77604562e-06) |
| 5283 | 2 | q_positive | 0 | 1787 | 1760 | 223375 | 220000 | 0 | 0.993449544, 0.996180618, 0.993440328 | 9.21585045e-06 | 0.00274028985 | -9.19396934e-06 (-3.49198113e-05..7.82356168e-06) |
| 5283 | 2 | q_positive | 1 | 1787 | 1760 | 223375 | 220000 | 0 | 0.993449544, 0.996196172, 0.993478678 | -2.91343062e-05 | 0.0027174934 | -1.10368351e-05 (-6.18986958e-05..1.88233899e-05) |
| 5283 | 2 | q_positive | 2 | 1787 | 1760 | 223375 | 220000 | 0 | 0.993449544, 0.9961777, 0.99346565 | -1.61062198e-05 | 0.00271204954 | -1.29996067e-05 (-4.16370303e-05..1.45588953e-05) |
| 5283 | 2 | suffix_b0 | 0 | 1787 | 1760 | 223375 | 220000 | 0 | 0.99880358, 0.998816148, 0.998816919 | -1.33395168e-05 | -7.71222246e-07 | -1.21450152e-05 (-4.78254129e-05..1.88507641e-05) |
| 5283 | 2 | suffix_b0 | 1 | 1787 | 1760 | 223375 | 220000 | 0 | 0.99880358, 0.998822033, 0.998821657 | -1.80775353e-05 | 3.75700843e-07 | -9.86010145e-06 (-4.03021867e-05..9.21805646e-06) |
| 5283 | 2 | suffix_b0 | 2 | 1787 | 1760 | 223375 | 220000 | 0 | 0.99880358, 0.998813556, 0.998809991 | -6.41096954e-06 | 3.56495595e-06 | -1.82134662e-05 (-5.62784551e-05..3.56846911e-06) |
| 1995 | 2 | q_positive | 0 | 2047 | 2048 | 255875 | 256000 | 0 | 0.381449812, 0.405418471, 0.381452209 | -2.39701022e-06 | 0.0239662625 | -7.40602521e-06 (-2.54730797e-05..2.5652676e-06) |
| 1995 | 2 | q_positive | 1 | 2047 | 2048 | 255875 | 256000 | 0 | 0.381449812, 0.405436228, 0.381468856 | -1.90440904e-05 | 0.023967372 | -9.30960156e-06 (-2.39512296e-05..8.74805857e-06) |
| 1995 | 2 | q_positive | 2 | 2047 | 2048 | 255875 | 256000 | 0 | 0.381449812, 0.405428293, 0.381474157 | -2.43451784e-05 | 0.0239541363 | -8.13223732e-06 (-2.61044894e-05..6.88675826e-06) |
| 1995 | 2 | suffix_b0 | 0 | 2047 | 2048 | 255875 | 256000 | 0 | 0.999889624, 0.999913619, 0.999916914 | -2.72902503e-05 | -3.29502066e-06 | -1.94463878e-05 (-8.03145662e-05..3.30680535e-06) |
| 1995 | 2 | suffix_b0 | 1 | 2047 | 2048 | 255875 | 256000 | 0 | 0.999889624, 0.999897621, 0.999891131 | -1.50721643e-06 | 6.4891926e-06 | -8.10565346e-06 (-4.41929117e-05..5.13670212e-06) |
| 1995 | 2 | suffix_b0 | 2 | 2047 | 2048 | 255875 | 256000 | 0 | 0.999889624, 0.999893275, 0.999892408 | -2.78410984e-06 | 8.66545702e-07 | -1.01754403e-05 (-3.30356133e-05..1.18840717e-05) |
| 6343 | 2 | q_positive | 0 | 2014 | 2019 | 251750 | 252375 | 0 | 0.891842361, 0.915786353, 0.891850537 | -8.17586703e-06 | 0.023935816 | -1.10257733e-05 (-3.97260035e-05..1.41628594e-06) |
| 6343 | 2 | q_positive | 1 | 2014 | 2019 | 251750 | 252375 | 0 | 0.891842361, 0.91578364, 0.891851539 | -9.17805154e-06 | 0.0239321008 | -9.55484442e-06 (-3.61835044e-05..5.18623585e-06) |
| 6343 | 2 | q_positive | 2 | 2014 | 2019 | 251750 | 252375 | 0 | 0.891842361, 0.915775148, 0.891841496 | 8.65298951e-07 | 0.0239336522 | -6.30985463e-06 (-2.44310866e-05..6.67967561e-06) |
| 6343 | 2 | suffix_b0 | 0 | 2014 | 2019 | 251750 | 252375 | 0 | 0.999674887, 0.999709111, 0.999691266 | -1.63791486e-05 | 1.7844965e-05 | -1.96747541e-05 (-5.15308662e-05..1.0260402e-06) |
| 6343 | 2 | suffix_b0 | 1 | 2014 | 2019 | 251750 | 252375 | 0 | 0.999674887, 0.999709479, 0.99967018 | 4.70692794e-06 | 3.92981669e-05 | -1.35035571e-05 (-4.96491644e-05..1.25423858e-05) |
| 6343 | 2 | suffix_b0 | 2 | 2014 | 2019 | 251750 | 252375 | 0 | 0.999674887, 0.99970893, 0.999690002 | -1.51151556e-05 | 1.89273309e-05 | -1.08360257e-05 (-3.51502211e-05..1.44849949e-05) |

Each band has 2048 complete blocks; omitted blocks are 2048 minus retained counts above. Independent implementations matched all observed and 16 shuffled training/test tables exactly and all losses/gains within 1e-12. The reference reused a previously authored literal parser, both implementations share a TIFF locator, and both assisted the same human. Window choice, escape omission and unknown framing limit interpretation.

## Reproduce

Retained verified public CC0 inputs:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`

At commit `01a9cb322fdd4d185853aef17d06572c4e878860`, verify identities and hashes, substitute local paths, and run:

```text
python -I -B tools/token_phase3_heldout_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --test-band 1
python -I -B tools/token_phase3_heldout_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --test-band 1
python -I -B tools/token_phase3_heldout_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --test-band 2
python -I -B tools/token_phase3_heldout_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --test-band 2
python -I -B tools/token_phase3_heldout_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --test-band 2
python -I -B tools/token_phase3_heldout_probe.py --sample 6343 "OM System - OM-5 - 16bit (4:3).ORF" FILE6343 --test-band 2
```

The tool emits all observed and shuffled tables, rotations, losses, endpoints and source hashes. Separately justified phase and framing assumptions remain open on the existing corpus.
