# OM-1 top-band luma comparison reproduces

Author: @mszyndel
Verified by: @radialmonster
Lead: #368
Variant: unassigned
Builds on: #351, 2026-10-26--radialmonster--normal-mode-luma-not-vertical-specific

## Claim

On public OM-1 normal-mode file 5283, the fixed top-band b2+b4 score is near the within-row shuffle baseline and the declared preview alignment ranks 16th among 23 circular alignments. This is a descriptive single-file result, not a calibrated significance test or evidence of physical row mapping, CFA phase, a predictor or codec.

## Original evidence

@mszyndel measured raw.pixls.us CC0 id 5283, `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`, using `tools/token_luma_probe.py` at `3f4501072bc0317af33eb20504adb8293ed52633`. The frozen measure used 300 token rows, box window 63, 20 within-row shuffles, seed 1, the sum map and all nonzero circular preview-row shifts. Payload geometry was 5220x3912, preview DC grid 400x300, with 23x400 used. The score was r=+0.00762, shuffle mean -0.00341, sample sd 0.02534 and z=+0.44; 1922 escape tokens were treated as zero. The best shifted alignment was k=7 at +0.02195; the observed alignment ranked 16/23. Shifted scores had mean +0.01051, sd 0.00810 and maximum +0.02195.

The top 300 candidate rows use fixed token stride 5220, the payload width, and phase 0; no stride or phase is fitted. These scores do not contradict probes using different candidate strides or phases and do not show that every luma mapping fails.

## Verification

After the lead was posted, @radialmonster reran the exact measure on 5283 at `3be87a1b0785e4ec17adeb4d7a55073076092cb6`; all displayed figures above matched. The finder and verifier are different people; the agents assisting the verifier do not constitute additional independent human verifiers.

The predeclared additional CC0 file was id 5286, `OM System - OM-1 - 16bit (4:3).ORI`, SHA-256 `2fd8bd46e2644fe28092fd921d9647007afd6d1e879c5ff19b1e3df50c578df1`. With identical settings it had the same payload and preview grid dimensions and used 23x400 DC blocks. Its r=+0.01514, shuffle mean +0.00413, sd 0.02234, z=+0.49 and escape count 1983. Best shifted alignment was k=13 at +0.03043; observed rank was 14/23, shifted mean +0.01667, sd 0.00865 and maximum +0.03043. This previously studied additional file is not a blind or independent-capture test and does not establish a body-wide result.

Both inputs were matched to retained verified CC0 records, existing manifest entries and their local hashes. For these exact inputs, the original and verification versions selected identical payload bytes and preview start, dimensions and length, and produced identical in-memory preview DC values. The preview is a numeric camera-rendering reference, not sensor ground truth. No image or preview data were exported. The current and original code differ in general container checks and luma arithmetic implementation; this compatibility observation is limited to these files.

The maintainer separately recomputed clamped box means with float32 storage, scalar block averages, row-centred Pearson correlations, all 20 seeded within-row shuffles and all 22 preview-row shifts. Both reports' score and summary statistics match within 1e-12; alignment ranks and escape counts match exactly. Separate metadata checks confirm one strip and the same historical payload and preview selection on each file, with ordinary three-component interleaved previews.

## Reproduce

At `3be87a1b0785e4ec17adeb4d7a55073076092cb6`, substitute the two hash-matched public files:

```sh
python -I -B tools/token_luma_probe.py "$FILE5283" --rows 300 --window 63 --perms 20 --seed 1 --map sum --shift-null
python -I -B tools/token_luma_probe.py "$FILE5286" --rows 300 --window 63 --perms 20 --seed 1 --map sum --shift-null
```
