# The frozen suffix table misses two normal-mode cross-body targets

Author: @radialmonster
Verified by: @radialmonster
Lead: #876
Variant: unassigned
Builds on: #155, #803, #840, 2026-11-04--radialmonster--suffix-luma-table-weak-transfer

## Claim

The #155 suffix table fitted on E-M1 Mark II file 1995 scores below zero and below all four within-row shuffles on normal-mode E-M1 Mark III 3800 and OM-5 6343 at the fixed nominal alignment. The same-body E-M1 Mark II control 1997 reproduces the earlier positive score.

## Original evidence

The discovery run started on 2026-11-20 at 21:36:28 UTC. `tools/suffix_table_cross_body_probe.py` at `baf393df49b11abfdbc0c204070dc3a8a523dc48` uses the legacy stop-1, five-suffix-bit candidate with no escape skip, 600 complete payload-width token blocks, and quantized first-component preview DC. It fits the 32-suffix table on even preview rows of 1995 with lambda 1, smoothing 10 and no intercept. Prediction uses unchanged weights, nominal blocking and the original target row centering. For each file it compares Pearson r with four whole-token within-row shuffles from seed 20261021. The positive-above-all-four rule is descriptive.

| Target | Observed r | R2 | Four shuffled r values in draw order |
| --- | ---: | ---: | --- |
| 1997 E-M1 Mark II control | +0.10555837 | +0.00818347 | +0.00865748, -0.01544419, -0.00086859, -0.00250379 |
| 3800 E-M1 Mark III | -0.00335946 | -0.00157263 | -0.00127654, -0.00022999, -0.00134604, +0.00177945 |
| 6343 OM-5 | -0.00848141 | -0.01395162 | -0.00353132, -0.00152648, -0.00200756, -0.00069597 |

All four discovery inputs have 5240x3912 payloads, 3200x2400 previews, 46x400 used DC blocks and maximum first-component sampling of 2x1. First-component DC quantizers in training/control/discovery order are 4, 4, 4 and 23. R2 is a legacy residual comparison in quantized DC units. A uniform positive scale of the target DC cancels in r. Quantization and preview rendering can still change the association. On Python 3.14 the table SHA-256 for the 32 big-endian binary64 values in this run is `c7162dbb1376e8f8799dc717f3e93a51f65a38dbd80ca80065f2fbee402bda5f`.

Public CC0 files from raw.pixls.us, identified by manifest SHA-256:

- Training 1995, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`.
- Control 1997, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`.
- Discovery 3800, `Olympus - E-M1MarkIII - 16bit (4:3).ORF`, `1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f`.
- Discovery 6343, `OM System - OM-5 - 16bit (4:3).ORF`, `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`.
- Verification extension 3801 (High Res), `Olympus - E-M1MarkIII - 16bit (4:3).ORF`, `e9a21175493e9d9e5653aa91f1bd6fbf421aba42b59b4ffe7cd1f7cac2de385c`.
- Verification extension 5283, `OM System - OM-1 - 16bit (4:3).ORF`, `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`.

## Verification

The new run began on 2026-11-20 at 21:39:36 UTC, after #876 was published. The frozen table fingerprint and every original target record, including full-precision scores, shuffle values and geometry, repeated exactly. It also used the two predeclared files absent from discovery:

| Additional target | Observed r | R2 | Four shuffled r values in draw order |
| --- | ---: | ---: | --- |
| 3801 E-M1 Mark III High Res | +0.60330564 | +0.03178203 | +0.00095467, -0.01070226, -0.00560462, -0.01156816 |
| 5283 OM-1 normal | -0.00153120 | -0.01876655 | +0.00528136, -0.00574458, +0.01291441, +0.00352639 |

High Res 3801 passes the descriptive rule at 29x400 used DC blocks from its 8200x6132 payload. OM-1 5283 fails at 46x400 blocks from its 5220x3912 payload. Both have 3200x2400 previews, maximum first-component 2x1 sampling and DC quantizers 4 and 28 respectively. An independent calculation of the fit and scoring arithmetic agreed within 1e-9 for all five targets and all four shuffles per target, using the same project's token and JPEG readers. Both calculations represent the same verifier.

This preserves the earlier same-body result and adds a positive example on one High Res file. The normal and High Res E-M1 Mark III results come from different files. Mode, scene, preview processing and nominal registration are entangled. The findings apply to these previously studied inputs held out from the table fit. Physical row boundaries, variant assignment, calibrated inference, pixel values and codec behavior remain open.

## Reproduce

At the pinned tool commit, supply the locally available exact CC0 files named above. The tool checks the stored SHA-256 values and prints aggregate JSON.

```text
python -I -B tools/test_suffix_table_cross_body_probe.py
python -I -B tools/suffix_table_cross_body_probe.py --phase discovery --train TRAIN1995 --sample 1997 FILE1997 --sample 3800 FILE3800 --sample 6343 FILE6343
python -I -B tools/suffix_table_cross_body_probe.py --phase verification --train TRAIN1995 --sample 1997 FILE1997 --sample 3800 FILE3800 --sample 6343 FILE6343 --sample 3801 FILE3801 --sample 5283 FILE5283
```
