# Common-interval phase comparison on public files

Author: @radialmonster
Verified by: @radialmonster
Lead: #508
Variant: unassigned
Builds on: #144, 2026-10-27--radialmonster--phase-period-heldout-reproduction

## Claim

The four-file common-interval comparison in #508 reproduces the stated numerical contrasts and their signs. These descriptive candidate-model scores do not establish physical row boundaries, causal stride changes, independent captures or calibrated significance.

## Original evidence

The lead used `tools/token_phase_stride_compare.py` at commit `1687e35d85c3fe7f49bdfa0b197fe4a8338b24bc`. The frozen fitting design uses anchor 10480000, strides 5176 through 5304, every phase, 100 training rows, head 32 and q capped at 40. The joint-period/phase, fixed-period fitted-phase, and fixed-origin models are each scored on exactly the same half-open token interval [11021008, 11538608). A token is a head when `(i - anchor - phase) % stride < 32`; clipped heads are retained at interval edges and other tokens are rest. Each score is mean head q minus mean rest q. Models partition the same input differently, and their head counts need not be equal in other cases. This score is distinct from the earlier complete-row metric; no threshold or null test is applied.

| ID | Public name | SHA-256 | Joint | Fixed | Origin | Joint minus fixed |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1995 | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f | 0.1695494185 | 0.1333429664 | -0.1343942190 | +0.0362064521 |
| 1998 | Olympus - E-M1MarkII - 16bit (4:3).ORF | 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 | 0.0987701097 | 0.1098861257 | -0.1508638497 | -0.0111160160 |
| 1997 | Olympus - E-M1MarkII - 16bit (4:3).ORI | 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a | 0.1451858407 | 0.1213658065 | -0.1358905639 | +0.0238200343 |
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 | 0.4897032852 | -0.0381486746 | -0.0492646906 | +0.5278519598 |

For each model and file, the head count was 3168 and the rest count 514432. The negative 1998 difference and negative 1993 fixed contrast are part of the result.

Exact capped-q sums for the four original files (common head/rest counts are 3168/514432 per model):

| ID | Joint head sum | Fixed head sum | Origin head sum | Total q sum |
| --- | ---: | ---: | ---: | ---: |
| 1995 | 1049 | 935 | 92 | 84168 |
| 1998 | 835 | 870 | 49 | 85615 |
| 1997 | 975 | 900 | 90 | 84611 |
| 1993 | 1928 | 266 | 231 | 63085 |

## Verification

After #508 was posted, @radialmonster reran the four files at the pinned commit, matching each local hash to a retained CC0 record and existing manifest row. Every complete JSON report matched its original report exactly after excluding only elapsed time, including all 2703840 training phase scores, choices, sums, counts and scores. This is self-verification by the same human, not independent-human verification. The files and regions have prior research exposure. Nine synthetic tests passed. The maintainer separately matched all four fresh JSONs excluding elapsed time only and checked all fifteen common-interval model profiles with direct per-token modulo masks and exact Fraction arithmetic: counts and sums match exactly, means/differences within 1e-12. The additional file also passed an independent check of all 675960 training phase scores, exact fitting choices and complete-row profiles. Both agents represent the same human.

The predeclared additional file, ID 6343, `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`, completed with the same constants. Joint selection was stride 5296, phase 2329; fixed selection was stride 5240, phase 1199. On the common interval, the joint model had head count 3136 and sum 1936, rest count 514464 and sum 314942, for contrast 0.005171937220493694. The fixed model had head count 3136 and sum 1913, rest count 514464 and sum 314965, for contrast -0.0022069531768669215. The difference was +0.007378890397360616. Fixed origin had head count 3168 and sum 1930, rest count 514432 and sum 314948, for contrast -0.0030075732442614855. The tool parsed 11556712 tokens and consumed 76420800 bits. Lead #144 reports a prefix-profile candidate of 5472 for this file, outside the fixed 5176..5304 search family. This extension therefore tests that declared family only; it is not a body-tuned physical-row fit or body-wide transfer.

## Reproduce

At `1687e35d85c3fe7f49bdfa0b197fe4a8338b24bc`, substitute the local paths of the hash-matched public CC0 files for the placeholders:

```sh
python -I -B tools/test_token_phase_stride_compare.py
python -I -B tools/token_phase_stride_compare.py --sample 1995 'Olympus - E-M1MarkII - 16bit (4:3).ORI' 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f "$FILE1995"
python -I -B tools/token_phase_stride_compare.py --sample 1998 'Olympus - E-M1MarkII - 16bit (4:3).ORF' 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 "$FILE1998"
python -I -B tools/token_phase_stride_compare.py --sample 1997 'Olympus - E-M1MarkII - 16bit (4:3).ORI' 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a "$FILE1997"
python -I -B tools/token_phase_stride_compare.py --sample 1993 'Olympus - E-M1MarkII - 16bit (4:3).ORF' 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 "$FILE1993"
python -I -B tools/token_phase_stride_compare.py --sample 6343 'OM System - OM-5 - 16bit (4:3).ORF' ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7 "$FILE6343"
```
