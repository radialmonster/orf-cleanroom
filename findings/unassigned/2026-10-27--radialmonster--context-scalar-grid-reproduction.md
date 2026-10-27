# Finite-grid context calibration result reproduces

Author: @radialmonster
Verified by: @radialmonster
Lead: #545
Variant: unassigned
Builds on: #298, #362, #541

## Claim

The declared seven-grid scalar calibration does not make order 8 beat equally calibrated order 0 on any of the six heldout windows from selected 3800, 5286 and 6347. This rejects that specific operational conjunction, not marginal mismatch generally; the predictive scores do not establish an ORF codec or causal effect.

## Original evidence

Lead #545 fixed discovery 1993/1995, the order-8 table SHA-256 `1f395ec3446c96b3c7415e2ff5e6d11ad79684695410315132a1e19584bbdc71`, calibration at logical-strip offset 196608 and heldout offsets 262144 and 327680, all 65536-byte windows. Independently for orders 0 and 8 it selected the best calibration NLL from odds multipliers 1/4, 1/2, 3/4, 1, 4/3, 2 and 4; rational quantization is nearest ties up with clamp 1..4095, and exact score ties choose the first grid index. Each heldout score charges 3 index bits plus 16 or 3076 model bits. Calibration-data transmission is excluded; this is NLL plus declared cost, not serialized size. An exact-count seed-298 shuffle is a descriptive control.

## Verification

After the lead, @radialmonster repeated the four reports at `7826f4442842fd2225e6e1140bed47485f7b3ddc`; their complete sample ledgers match exactly. Both orders select multiplier 1 in every file. A separately implemented Fraction/bitstring reference matched all 70 candidate grid cells and 60 heldout frozen/adjusted/shuffle scores on the five-file run within 1e-7 bit, with exact hashes, clamp counts, ties and choices. This is same-human self-verification, not independent-human verification.

| ID | Adjusted order8 minus order0, offset 262144 | Offset 327680 |
|---:|---:|---:|
| 3800 | +21447.012643 | +20613.015623 |
| 5286 | +51860.843108 | +51347.432796 |
| 6347 | +20939.480105 | +20437.156922 |
| 3801 | -42507.582642 | -44396.743131 |
| 3802 | +22178.754606 | +21617.851960 |

The first three files fail all six strictly negative comparisons; 3801's separately declared contrast stays negative. Predeclared 3802 is a post-lead descriptive extension with no directional criterion, and also selects multiplier 1 for both orders. Grid coarseness, scalar misspecification and nonstationarity remain possible explanations; these previously studied files do not establish independent captures or population generality.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` |
| 1995 | Olympus - E-M1MarkII - 16bit (4:3).ORI | `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` |
| 3800 | Olympus - E-M1MarkIII - 16bit (4:3).ORF | `1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f` |
| 5286 | OM System - OM-1 - 16bit (4:3).ORI | `2fd8bd46e2644fe28092fd921d9647007afd6d1e879c5ff19b1e3df50c578df1` |
| 6347 | OM System - OM-5 - 16bit (4:3).ORI | `062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9` |
| 3801 | Olympus - E-M1MarkIII - 16bit (4:3).ORF | `e9a21175493e9d9e5653aa91f1bd6fbf421aba42b59b4ffe7cd1f7cac2de385c` |
| 3802 | Olympus - E-M1MarkIII - 16bit (4:3).ORI | `83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46` |

Every local hash matched retained verified CC0 provenance and existing manifest identity. No image, preview or raw output was saved or viewed.

## Reproduce

At `7826f4442842fd2225e6e1140bed47485f7b3ddc`, substitute paths matching the listed hashes:

```sh
python -I -B tools/frozen_context_calibration.py --manifest samples/manifest.csv --discovery FILE1993 FILE1995 --validation FILE3800 FILE5286 FILE6347 FILE3801 FILE3802
```
