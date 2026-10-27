# Frozen-context six-file comparison reproduces

Author: @radialmonster
Verified by: @radialmonster
Lead: #541
Variant: unassigned
Builds on: #362, 2026-10-27--mszyndel--frozen-context-om5-transfer

## Claim

The frozen discovery order-8 model scores worse than order 0 in each of twelve predeclared single-file windows from six selected public files. This is predictive negative log likelihood plus model cost, not an ORF codec, encoded size, reconstruction or causal population claim.

## Original evidence

Lead #541 used `tools/frozen_bit_context.py` at `1728e0b2b9e9babd245423e666e7d963420da6d7`, with discovery 1993/1995 at logical strip offset 65536, 65536-byte windows, orders 0..8 and an exact-count seed-298 shuffled validation control. The chosen order-8 discovery table hash is `1f395ec3446c96b3c7415e2ff5e6d11ad79684695410315132a1e19584bbdc71`. Every single-file score charges the order-8 model 3076 bits and order 0 16 bits. The six files were tested separately at offsets 65536 and 131072.

## Verification

After the lead, @radialmonster reran all twelve single-file reports. Every complete nine-order ledger matched the original report exactly apart from elapsed time. Independently structured context counting and exact-rational quantization matched all 14 windows' nine-order hashes and scores within 1e-7 bit; both agents represent the same human, not independent-human verification.

| ID | Offset | Order 0 score | Order 8 score | Shuffled order 8 score |
|---:|---:|---:|---:|---:|
| 3800 | 65536 | 524631.702539 | 545222.164275 | 577377.263161 |
| 3800 | 131072 | 524627.419189 | 545484.857764 | 578080.034190 |
| 5286 | 65536 | 524015.035474 | 575184.426699 | 585329.189535 |
| 5286 | 131072 | 523992.987496 | 576669.478807 | 585479.122813 |
| 6347 | 65536 | 524201.834600 | 546297.319423 | 583172.393387 |
| 6347 | 131072 | 524242.999843 | 546713.909173 | 583022.646793 |
| 7262 | 65536 | 523614.294312 | 560149.832111 | 590758.839816 |
| 7262 | 131072 | 523532.730319 | 570098.518265 | 592615.752799 |
| 7804 | 65536 | 523853.079775 | 587351.678985 | 587276.225974 |
| 7804 | 131072 | 523898.798895 | 585735.058619 | 587162.813853 |
| 8549 | 65536 | 524602.440499 | 537651.748961 | 578663.810528 |
| 8549 | 131072 | 524554.692424 | 538160.671705 | 579255.586553 |

The predeclared additional 3801 reverses the comparison: at offsets 65536/131072 order 0 scores 523993.934341/523970.759166, order 8 scores 481076.615023/480315.303872, and shuffled order 8 scores 585196.944560/585896.913975. This is a separate extension, not a claim that all files behave alike. The first 7804 order-8 score is also slightly worse than its shuffled score. These previously studied files and windows do not establish independent captures, significance, body/scene causality or generality.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` |
| 1995 | Olympus - E-M1MarkII - 16bit (4:3).ORI | `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` |
| 3800 | Olympus - E-M1MarkIII - 16bit (4:3).ORF | `1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f` |
| 5286 | OM System - OM-1 - 16bit (4:3).ORI | `2fd8bd46e2644fe28092fd921d9647007afd6d1e879c5ff19b1e3df50c578df1` |
| 6347 | OM System - OM-5 - 16bit (4:3).ORI | `062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9` |
| 7262 | OM System - OM-1 Mark II - 16bit (4:3).orf | `d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd` |
| 7804 | OM System - OM-3 - 16bit (4:3).ORI | `bcc05bd57e78cbbb308a596f97987975f7167b17768d8c2d536c87e0c34298e0` |
| 8549 | OM System - OM-5 Mark II - 16bit (4:3).ORF | `c6fe861982ddc18464cf6858d2700f6813cc3a17956bcb12d1179212c999c76a` |
| 3801 | Olympus - E-M1MarkIII - 16bit (4:3).ORF | `e9a21175493e9d9e5653aa91f1bd6fbf421aba42b59b4ffe7cd1f7cac2de385c` |

All inputs matched retained verified CC0 records, public identities, existing manifest rows and local hashes.

## Reproduce

At `1728e0b2b9e9babd245423e666e7d963420da6d7`, substitute hash-matched paths. Run separately for each validation ID 3800, 5286, 6347, 7262, 7804, 8549 and 3801 and each OFFSET 65536 and 131072:

```sh
python -I -B tools/frozen_bit_context.py --manifest samples/manifest.csv --discovery FILE1993 FILE1995 --validation FILE --offset 65536 --validation-offset OFFSET --bytes 65536
```
