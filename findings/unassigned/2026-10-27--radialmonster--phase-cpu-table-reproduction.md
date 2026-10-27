# Phase-search CPU table reproduces

Author: @radialmonster
Verified by: @radialmonster
Lead: #356
Variant: unassigned
Builds on: #144, #149, #351, 2026-10-27--radialmonster--om5-phase-band-reproduction

## Claim

The lead's eight-file CPU top-band phase-search table and its two single-shuffle maxima reproduce at the reported precision. The search evaluates a coarse phase family and refinement around its coarse winner; these are sampled-family maxima, not necessarily global maxima. Preview luma is a numeric camera-rendering reference, not ground truth, and a candidate phase is not established as a physical row origin.

## Original evidence

Lead #356 reported phase-0 scores and selected phases and scores for eight public files, using fixed candidate strides and a 300-row top band, a 63-token b2+b4 sum window, step 16 and refinement +/-16. It also reported one seed-1 shuffled-search maximum each for 6343 and 8549. Its exploratory GPU full-phase scan is outside this reproduction. Its 6343 later-band comparison was separately reproduced in `2026-10-27--radialmonster--om5-phase-band-reproduction`.

## Verification

After the lead, the same human reran the CPU search at `f3b52f264ac650d4718b9b4e17ac77e5fdcffe5d`, with the same parameters and fixed strides, obtaining the following rounded values. Public file hashes matched retained verified CC0 records and existing manifest rows. An independent scalar calculation checked each phase-0 and selected-phase score and the two selected shuffled-phase scores; this point check does not independently establish the search maxima. Agents working for the same human do not constitute independent human verification.

| ID | Stride | Phase 0 r | Selected phase | Selected r | One shuffled-search maximum |
|---:|---:|---:|---:|---:|---:|
| 6343 | 5472 | +0.07506 | 716 | +0.40894 | +0.03978 |
| 6347 | 5540 | +0.01978 | 680 | +0.27533 | not run |
| 5283 | 6010 | +0.20590 | 5395 | +0.28618 | not run |
| 5286 | 5978 | +0.04418 | 5140 | +0.20303 | not run |
| 7262 | 5566 | +0.06729 | 1147 | +0.25453 | not run |
| 8549 | 5327 | -0.11156 | 4730 | +0.12607 | +0.04827 |
| 1993 | 5240 | +0.47214 | 35 | +0.48369 | not run |
| 1995 | 5240 | +0.10846 | 4916 | +0.13321 | not run |

Predeclared additional id 1997 at stride 5240 gave phase 0 +0.12245 and selected phase 28 at +0.13970, with no shuffle in this run. It was not in the original lead table but was previously studied, including in the earlier #356 Partial finding; it is not blind or an independent capture test. This descriptive result and the single-shuffle maxima do not establish calibrated significance, a phase law, physical framing, pixel values or a decode.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 6343 | OM System - OM-5 - 16bit (4:3).ORF | `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7` |
| 6347 | OM System - OM-5 - 16bit (4:3).ORI | `062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9` |
| 5283 | OM System - OM-1 - 16bit (4:3).ORF | `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b` |
| 5286 | OM System - OM-1 - 16bit (4:3).ORI | `2fd8bd46e2644fe28092fd921d9647007afd6d1e879c5ff19b1e3df50c578df1` |
| 7262 | OM System - OM-1 Mark II - 16bit (4:3).orf | `d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd` |
| 8549 | OM System - OM-5 Mark II - 16bit (4:3).ORF | `c6fe861982ddc18464cf6858d2700f6813cc3a17956bcb12d1179212c999c76a` |
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` |
| 1995 | Olympus - E-M1MarkII - 16bit (4:3).ORI | `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` |
| 1997 | Olympus - E-M1MarkII - 16bit (4:3).ORI | `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a` |

## Reproduce

At `f3b52f264ac650d4718b9b4e17ac77e5fdcffe5d`, use the local file matching each public hash. Replace `FILE` and `S` with its file and stride above; run once for each row, using `--perms 1` for ids 6343 and 8549 and `--perms 0` for the others. The existing tool reads samples and prints aggregates only.

```sh
python -I -B tools/token_luma_phase_probe.py FILE --stride S --rows 300 --start-row 0 --window 63 --map sum --step 16 --refine 16 --perms 0 --seed 1
```
