# Body-label holdout comparison reproduces on the frozen cohort

Author: @radialmonster
Verified by: @radialmonster
Lead: #329
Variant: unassigned
Builds on: #299, #307, #317

## Claim

On the frozen ten-file cohort, the leave-one-file-out body-label centroid diagnostic gives 7/10 correct for bits per pixel alone, 5/10 for the three raw-bit means and 6/10 for their union. This descriptive comparison does not establish statistical superiority, variant clusters, a causal body effect or independent-capture performance.

## Original evidence

The lead used `tools/payload_feature_probe.py` and `tools/body_label_holdout.py` at `cb7452d027d70450b8f67e0787ec5be1dcc60891`. Each file contributes three disjoint 65536-byte payload windows at both endpoints and the integer midpoint. Features are payload bits per pixel plus unweighted file means of one fraction, adjacent-bit transition fraction and byte entropy. Each leave-one-file-out fold estimates population variances on training files, omits zero-variance coordinates and predicts the nearest training body centroid by squared standardized Euclidean distance; exact ties use lexicographic make/model. The three ablations are fixed before measurement.

The ten public CC0 identities are:

| ID | raw.pixls.us name | SHA-256 |
| --- | --- | --- |
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 |
| 1994 | Olympus - E-M1MarkII - 16bit (4:3).ORF | f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 |
| 1995 | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f |
| 1996 | Olympus - E-M1MarkII - 16bit (4:3).ORF | eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2 |
| 5283 | OM System - OM-1 - 16bit (4:3).ORF | bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b |
| 5284 | OM System - OM-1 - 16bit (4:3).ORF | f0301e1b49a4ffbb366ec9800ebe9210f421fb25e75dcdf7d63e4b05bc063caf |
| 7262 | OM System - OM-1 Mark II - 16bit (4:3).orf | d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd |
| 7267 | OM System - OM-1 Mark II - 16bit (4:3).orf | 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756 |
| 6343 | OM System - OM-5 - 16bit (4:3).ORF | ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7 |
| 6344 | OM System - OM-5 - 16bit (4:3).ORF | 42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512 |

Incorrect IDs were 5283, 5284 and 6344 for bpp; 1993, 1995, 5284, 6343 and 6344 for bits; and 1993, 1995, 5284 and 6343 for the union.

## Verification

After the lead was posted, @radialmonster reran the fixed diagnostic at `7ce447377eabf961c7b6560793328fdf42fdd79d`, reproducing all three counts and incorrect-ID lists. All inputs matched retained CC0 verification and existing manifest rows by hash. This is self-verification by the finder; agents assisting the same person are not independent human verifiers.

The predeclared additional public file was id 1997, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`. Refitting the same leave-one-file-out diagnostic separately on all eleven files gave bpp 8/11, bits 5/11 and union 6/11. Incorrect IDs were 5283, 5284, 6344 for bpp; 1993, 1995, 5284, 6343, 6344, 1997 for bits; and 1993, 1995, 5284, 6343, 1997 for union. The extension can alter training centroids in every fold and is not a frozen-model independent validation.

An independent arithmetic check by the same human's other agent matched all 33 window counts and feature values, and every fold's predicted label, variance, centroid and distance within 1e-10. These files and scenes have prior exposure; file splits and multiple windows do not establish independent captures. No inference about variants, causality, population performance or a codec follows.

## Reproduce

At `7ce447377eabf961c7b6560793328fdf42fdd79d`, substitute each hash-matched public path below. Save the aggregate feature JSON to a scratch file, then run both diagnostics. Each command reads samples and prints aggregate output.

```sh
python -I -B tools/payload_feature_probe.py --window-bytes 65536 --windows 3 \
  --sample 1993 'Olympus - E-M1MarkII - 16bit (4:3).ORF' 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 "$F1993" \
  --sample 1994 'Olympus - E-M1MarkII - 16bit (4:3).ORF' f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 "$F1994" \
  --sample 1995 'Olympus - E-M1MarkII - 16bit (4:3).ORI' 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f "$F1995" \
  --sample 1996 'Olympus - E-M1MarkII - 16bit (4:3).ORF' eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2 "$F1996" \
  --sample 5283 'OM System - OM-1 - 16bit (4:3).ORF' bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b "$F5283" \
  --sample 5284 'OM System - OM-1 - 16bit (4:3).ORF' f0301e1b49a4ffbb366ec9800ebe9210f421fb25e75dcdf7d63e4b05bc063caf "$F5284" \
  --sample 7262 'OM System - OM-1 Mark II - 16bit (4:3).orf' d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd "$F7262" \
  --sample 7267 'OM System - OM-1 Mark II - 16bit (4:3).orf' 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756 "$F7267" \
  --sample 6343 'OM System - OM-5 - 16bit (4:3).ORF' ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7 "$F6343" \
  --sample 6344 'OM System - OM-5 - 16bit (4:3).ORF' 42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512 "$F6344" \
  --sample 1997 'Olympus - E-M1MarkII - 16bit (4:3).ORI' 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a "$F1997" > "$FEATURES"
python -I -B tools/body_label_holdout.py --features "$FEATURES" --manifest samples/manifest.csv --ids 1993 1994 1995 1996 5283 5284 7262 7267 6343 6344
python -I -B tools/body_label_holdout.py --features "$FEATURES" --manifest samples/manifest.csv --ids 1993 1994 1995 1996 5283 5284 7262 7267 6343 6344 1997
```
