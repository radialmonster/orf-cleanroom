# The frozen suffix table has a unique nominal vertical peak on High Res 3803

Author: @radialmonster
Verified by: @radialmonster
Lead: #880
Variant: unassigned
Builds on: #155, #803, #840, #876, 2026-11-20--radialmonster--frozen-suffix-table-cross-body-transfer

## Claim

Under the fixed #155 suffix table and nominal preview mapping, High Res E-M1 Mark III 3803 is positive above all four within-row shuffles and has a unique positive vertical maximum at zero. High Res OM-5 6344 fails both criteria. The known positive E-M1 Mark III High Res 3801 fails the vertical specificity criterion despite its large unshifted correlation.

## Original evidence

Discovery began 2026-11-20 at 21:49:52 UTC. `tools/suffix_table_highres_probe.py` at `6a0cd8c2143049ff0c3882a5bf4dd2caafa00da3` uses the 1995-fitted legacy suffix table with no new fitting or alignment search on the targets. It scores the first 600 payload-width candidate rows against row-centered quantized first-component preview DC, with the same four whole-token within-row shuffles as #876. The training fingerprint and full unshifted control records for 3801, 3800 and 6343 match #876. The vertical curve compares the fixed prediction against the same target at every cyclic displacement, where positive k means prediction row (r+k) modulo the used preview rows. The vertical criterion requires r(0)>0 and r(0) greater than every competing score by more than 1e-12.

| Target | Zero-shift r | Four shuffle r range | Positive above all four | Zero rank / shifts | Best nonzero r | Unique positive zero maximum |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 3801 High Res, known positive control | +0.60330564 | -0.01156816 to +0.00095467 | yes | 24/29 | +0.60699202 | no |
| 3800 normal control | -0.00335946 | -0.00134604 to +0.00177945 | no | 17/46 | +0.03124874 | no |
| 6343 normal control | -0.00848141 | -0.00353132 to -0.00069597 | no | 46/46 | +0.01607741 | no |
| 6344 High Res | -0.00844202 | -0.00714387 to +0.00560824 | no | 26/29 | +0.00975237 | no |
| 3803 High Res | +0.41497890 | -0.00509216 to +0.01463996 | yes | 1/23 | +0.36291063 | yes |

All 29 scores on 3801 are positive, from +0.60266435 to +0.60699202, with the largest at shift 10. The zero-shift margin on 3803 is +0.05206827. The 8200x6132 High Res payloads use 29x400 DC blocks, the 10400x7792 High Res payload uses 23x400, and the 5240x3912 controls use 46x400. The selected previews are 3200x2400. Every covered r is defined.

Raw.pixls.us CC0 public sample identities used in discovery and verification:

- Training 1995, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`.
- Control 3801, `Olympus - E-M1MarkIII - 16bit (4:3).ORF`, `e9a21175493e9d9e5653aa91f1bd6fbf421aba42b59b4ffe7cd1f7cac2de385c`.
- Control 3800, `Olympus - E-M1MarkIII - 16bit (4:3).ORF`, `1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f`.
- Control 6343, `OM System - OM-5 - 16bit (4:3).ORF`, `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`.
- Discovery 6344, `OM System - OM-5 - 16bit (4:3).ORF`, `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512`.
- Discovery 3803, `Olympus - E-M1MarkIII - 16bit (4:3).ORF`, `4ad47518e3766fae6b98f8b18f3aae3c277e5966028e3f2e0d2702bb0f17a3cd`.
- Verification extension 6346, `OM System - OM-5 - 16bit (4:3).ORF`, `ffd47d5924b65abdd8af761665d67705fe028cfd08e5efbc264b64a20830d9f4`.
- Verification extension 3802, `Olympus - E-M1MarkIII - 16bit (4:3).ORI`, `83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46`.

## Verification

A fresh run started on 2026-11-20 at 21:54:23 UTC after #880 opened. All five original records, their full vertical curves, the shuffle ledgers and the fitted table fingerprint repeated exactly. The same frozen analysis added two predeclared public files:

| Additional target | Zero-shift r | Four shuffle r range | Zero rank / shifts | Best shift |
| --- | ---: | ---: | ---: | ---: |
| 6346 OM-5 High Res | -0.00483072 | -0.00841694 to +0.02138506 | 17/23 | 6 |
| 3802 E-M1 Mark III normal | -0.04764431 | -0.00197316 to +0.00109549 | 44/46 | 12 |

Neither added file passed the shuffle or vertical specificity criterion. A separate arithmetic implementation agreed within 1e-9 for all seven targets' shuffled and vertical scores and agreed on ranks and flags exactly, using the same project's token and JPEG readers. Both runs represent the same verifier.

The files were studied previously and are held out only from the fixed fit. Scene, mode, crop, rendering and the selected vertical band can affect scores. Circular wrapping also changes the seam. This is a descriptive comparison on the declared grids. Physical registration, population transfer, variant assignment, assembled values and a codec remain open.

## Reproduce

At the pinned tool commit, substitute local paths to the exact CC0 files. The tool checks the hashes and prints aggregate JSON.

```text
python -I -B tools/test_suffix_table_highres_probe.py
python -I -B tools/suffix_table_highres_probe.py --phase discovery --train TRAIN1995 --sample 3801 FILE3801 --sample 3800 FILE3800 --sample 6343 FILE6343 --sample 6344 FILE6344 --sample 3803 FILE3803
python -I -B tools/suffix_table_highres_probe.py --phase verification --train TRAIN1995 --sample 3801 FILE3801 --sample 3800 FILE3800 --sample 6343 FILE6343 --sample 6344 FILE6344 --sample 3803 FILE3803 --sample 6346 FILE6346 --sample 3802 FILE3802
```
