# Column profiles explain the 3801 score while 3803 retains residual association

Author: @radialmonster
Verified by: @radialmonster
Lead: #892
Variant: unassigned
Builds on: #155, #880, 2026-11-20--radialmonster--frozen-suffix-table-highres-vertical-shifts

## Claim

Under the fixed nominal #155 table, the strong preview correlation on High Res file 3801 comes from its column profile shared across rows. The vertically varying contribution is negative. The residual correlation on High Res 3803 is positive and exceeds all four reprojected shuffles. OM-5 High Res 6344 has a negative residual correlation.

## Original evidence

Discovery began 2026-11-20 at 22:31:03 UTC. `tools/suffix_profile_probe.py` at `e59e70fc874aa50bb3a2fce153927351c5222419` uses the fixed table fitted on 1995 and 600 candidate rows at the declared payload width. All three vertical-shift curves match #880. The signed column and residual contributions divide their dot products by the full-vector norm product. Residual r instead uses the residual norm product. The tool recomputes column means for each legacy token shuffle, seed 20261021, using the same fixed fit. Within 1e-12, the column contribution equals the full vertical curve mean and the two contributions sum to zero-shift r.

| File | Unshifted r | Column contribution | Residual contribution | Target/prediction column energy fraction | Residual r | Four shuffled residual r, in order |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| 3801 | +0.60330564 | +0.60493125 | -0.00162561 | 0.98391339 / 0.60229191 | -0.02032365 | -0.00069447, -0.01083664, -0.00069327, -0.00057234 |
| 3803 | +0.41497890 | +0.26636620 | +0.14861270 | 0.25113258 / 0.40993880 | +0.22356557 | +0.00705388, -0.01206758, -0.00198758, +0.01441031 |
| 6344 | -0.00844202 | -0.00095746 | -0.00748456 | 0.34524167 / 0.00766189 | -0.00928530 | -0.00640133, +0.00180064, -0.00863192, -0.00661918 |

Public raw.pixls.us CC0 identities, matched by manifest SHA-256:

| ID | Catalogue name | SHA-256 |
| --- | --- | --- |
| 1995 training | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f |
| 3801 | Olympus - E-M1MarkIII - 16bit (4:3).ORF | e9a21175493e9d9e5653aa91f1bd6fbf421aba42b59b4ffe7cd1f7cac2de385c |
| 3803 | Olympus - E-M1MarkIII - 16bit (4:3).ORF | 4ad47518e3766fae6b98f8b18f3aae3c277e5966028e3f2e0d2702bb0f17a3cd |
| 6344 | OM System - OM-5 - 16bit (4:3).ORF | 42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512 |
| 3804 verification | Olympus - E-M1MarkIII - 16bit (4:3).ORI | d831692b608471ad64667eb2485bab553de0ddb9366d384c4ecb731092b5dc42 |
| 6347 verification | OM System - OM-5 - 16bit (4:3).ORI | 062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9 |

## Verification

A fresh run started on 2026-11-20 at 22:35:03 UTC after #892 was posted. The full three discovery records and training fingerprint repeat exactly. Two predeclared normal-mode files expand the cohort.

| File | Unshifted r | Column contribution | Residual contribution | Target/prediction column energy fraction | Residual r | Four shuffled residual r, in order |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| 3804 | +0.08036543 | +0.01270173 | +0.06766370 | 0.29662675 / 0.03176562 | +0.08199220 | +0.00281048, -0.00279246, -0.00077069, -0.00462698 |
| 6347 | -0.01020914 | +0.00064326 | -0.01085240 | 0.21433057 / 0.01695414 | -0.01234864 | +0.00088648, +0.00512461, -0.00492837, +0.01252428 |

The four control comparisons are defined on every file. The positive residual example extends to 3804, and 6347 gives a negative residual. An independent numerical implementation matches the fit, energies, correlations and all four reprojected shuffles on the five files. It shares the project's input readers, and both runs represent the same verifier.

The inputs have prior exposure and the two positive High Res examples were selected using #880. The two contributions are signed and can cancel. Removing a constant shared contribution leaves exact vertical-shift ordering unchanged. Scene, geometry, preview processing and mode can affect these descriptive results. Physical alignment, sample values and population transfer remain open.

## Reproduce

At the pinned commit, substitute paths to the exact CC0 identities above. The tool verifies SHA-256 and prints only aggregate results.

```text
python -I -B tools/test_suffix_profile_probe.py
python -I -B tools/suffix_profile_probe.py --phase discovery --train TRAIN1995 --sample 3801 FILE3801 --sample 3803 FILE3803 --sample 6344 FILE6344
python -I -B tools/suffix_profile_probe.py --phase verification --train TRAIN1995 --sample 3801 FILE3801 --sample 3803 FILE3803 --sample 6344 FILE6344 --sample 3804 FILE3804 --sample 6347 FILE6347
```
