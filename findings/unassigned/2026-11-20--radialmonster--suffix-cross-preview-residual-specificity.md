# Normal-mode suffix residuals can favor another file's preview

Author: @radialmonster
Verified by: @radialmonster
Lead: #896
Variant: unassigned
Builds on: #155, 2026-11-20--radialmonster--suffix-table-column-profile-and-residual

## Claim

In the fixed two-file normal-mode E-M1 Mark III matrix, the 3804 prediction favors its own preview and the 3800 prediction favors the 3804 preview. Both positive diagonal scores exceed their four same-file within-row shuffle controls. In the predeclared three-file extension, no source has a positive response to its own preview that exceeds both other previews. The shuffles and the competing previews test different properties of the candidate prediction.

## Original evidence

The frozen discovery run began on 2026-11-20 at 22:48:16 UTC with `tools/suffix_cross_preview_probe.py` at `904e162e2cadf03f390036a05f5750b07a95d29d`. The source prediction uses the unchanged table fitted to 1995 on even used preview rows. Its big-endian binary64 SHA-256 is `c7162dbb1376e8f8799dc717f3e93a51f65a38dbd80ca80065f2fbee402bda5f`. The probe uses the first 600 nominal-width candidate rows and the first component of each selected baseline JPEG. It centers the DC values within rows and subtracts across-row column profiles separately from targets and predictions. It measures Pearson r on the residual fields. For each source, it generates four seeded within-row candidate-pair shuffles and compares the same four reprojected shuffle predictions against all targets. The random seed is 20261021.

All public raw.pixls.us inputs are CC0 and already in the manifest. A hash is checked before the tool uses each file.

| ID | Catalogue name | SHA-256 |
| --- | --- | --- |
| 1995 training | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f |
| 3800 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORF | 1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f |
| 3804 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORI | d831692b608471ad64667eb2485bab553de0ddb9366d384c4ecb731092b5dc42 |
| 3802 predeclared extension | Olympus - E-M1MarkIII - 16bit (4:3).ORI | 83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46 |

Both discovery targets have a declared 5240 by 3912 raw size, a selected 3200 by 2400 JPEG and a 46 by 400 used DC grid. Components 1, 2 and 3 have sampling factors (2,1), (1,1) and (1,1). The first-component DC quantizers are 4 and 7 for 3800 and 3804, respectively. The probe uses quantized coefficients. The corresponding candidate bit counts are 20,166,048 and 20,272,518.

Rows identify prediction sources and columns identify preview targets. In discovery, the 3800 row is +0.01478223 against 3800 and +0.02668423 against 3804. The 3804 row is +0.01321844 against 3800 and +0.08199220 against 3804. The own-minus-other margins are -0.01190200 and +0.06877377, respectively. Their four controls per cell appear in the repeated matrix below. The reporting rule requires a positive diagonal and a margin over every real off-diagonal greater than 1e-12.

## Verification

A new run began on 2026-11-20 at 22:51:36 UTC after lead #896 was posted. It reproduced exactly the fit digest, metadata, all four original coefficients and all 16 original shuffled coefficients and energies. It added predeclared 3802 both as a prediction source and as a target. That file was used in other studies and was absent from the discovery run. It has the same raw and preview geometry, component order and sampling. Its first-component DC quantizer is 4 and its nominal candidate bit count is 20,391,184.

| Source | Preview | Residual r | Four shuffled residual r, in order |
| --- | --- | ---: | --- |
| 3800 | 3800 | +0.01478223 | -0.00045416, +0.00031830, -0.00226183, +0.00156390 |
| 3800 | 3804 | +0.02668423 | +0.00184859, +0.00310174, +0.00051786, +0.00084682 |
| 3800 | 3802 | -0.04180493 | +0.00086642, +0.00169058, -0.00004241, +0.00081866 |
| 3804 | 3800 | +0.01321844 | +0.00222395, -0.00025609, -0.00239181, -0.00192150 |
| 3804 | 3804 | +0.08199220 | +0.00281048, -0.00279246, -0.00077069, -0.00462698 |
| 3804 | 3802 | +0.08631487 | +0.00174309, -0.00160081, +0.00224919, +0.00061113 |
| 3802 | 3800 | -0.01274990 | -0.00000162, -0.00134309, -0.00285248, -0.00059704 |
| 3802 | 3804 | -0.00880724 | -0.00464291, -0.00139729, -0.00047456, -0.00270231 |
| 3802 | 3802 | -0.03128048 | +0.00173285, -0.00155694, -0.00173318, -0.00030374 |

The own-minus-best-other margins in this order are -0.01190200, -0.00432266 and -0.02247324. The extension changes the 3804 decision because its score against the added preview is higher than its unchanged own-preview score. The 3802 diagonal is negative. The two positive diagonals still exceed all four same-file shuffles.

This is self-verification. The ordered file set is small and previously exposed, and captures may be related. Equal dimensions and sampling leave physical registration and held-out scene, body and mode comparisons open.

## Reproduce

Use the exact local copies identified above at commit `904e162e2cadf03f390036a05f5750b07a95d29d`. The tool reads inputs and prints aggregate JSON.

```text
python -I -B tools/suffix_cross_preview_probe.py --phase discovery --train TRAIN1995 --sample 3800 FILE3800 --sample 3804 FILE3804
python -I -B tools/suffix_cross_preview_probe.py --phase verification --train TRAIN1995 --sample 3800 FILE3800 --sample 3804 FILE3804 --sample 3802 FILE3802
```
