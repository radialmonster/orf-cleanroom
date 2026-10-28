# Previous-q context matched escape controls

Author: @radialmonster
Verified by: @radialmonster
Lead: #646
Variant: unassigned
Builds on: #30, #634, #11

## Claim
For two previously studied OM-1 candidate prefixes, adding a preceding-q-class match changes the matched-control score on the fixed common anchor set; 5283 changes from negative to positive at 262144 tokens. This is a descriptive control sensitivity, not physical escape syntax.

## Original evidence
Lead #646 measured both 262144-token prefixes. Each had 311 common pairs; suffix/context means were -5/933 and 3/1244 on 5283, and 7/1244 and 4/933 on 5286.

## Verification
After the lead, both original cases were freshly reproduced and four predeclared files were evaluated at 524288 tokens. The files were previously exposed; this is wider-prefix and additional-file verification by the same human, not blind captures. An independently structured bit parser and heap selection matched every aggregate field; both paths share the TIFF locator. All prefixes completed. Counts below use the same common anchor set for both control methods.

The four exclusion counts are no suffix / short horizon / no previous / no context. Escape and control counts are q=0 totals at skip 0 / skip 12. Sign counts are positive/tied/negative; sign counts and unique/reused controls are suffix ; context respectively. Denominator for each q=0 total is 24 times common pairs. Each method's mean is (E12 - E0 - C12 + C0) / (24 * common pairs); context minus suffix is the context mean minus the suffix mean.

| ID | Tokens | End bits | Anchors / original eligible / common pairs | Exclusions | Escape 0/12 | Suffix 0/12 | Context 0/12 | Suffix mean | Context mean | Context minus suffix | Signs suffix ; context | Unique/reused suffix ; context |
|---|---:|---:|---|---|---|---|---|---|---|---|---|---|
| 5283 | 262144 | 1822446 | 313 / 311 / 311 | 2 / 0 / 0 / 0 | 3520 / 3515 | 3510 / 3545 | 3570 / 3547 | -5/933 | 3/1244 | 29/3732 | 119/60/132 ; 129/59/123 | 304/7 ; 307/4 |
| 5286 | 262144 | 1821991 | 312 / 311 / 311 | 1 / 0 / 0 / 0 | 3560 / 3592 | 3481 / 3471 | 3392 / 3392 | 7/1244 | 4/933 | -5/3732 | 133/58/120 ; 131/65/115 | 303/8 ; 304/7 |
| 5283 | 524288 | 3645413 | 597 / 595 / 595 | 2 / 0 / 0 / 0 | 6695 / 6709 | 6734 / 6788 | 6874 / 6843 | -1/357 | 3/952 | 1/168 | 225/121/249 ; 239/121/235 | 585/10 ; 587/8 |
| 5286 | 524288 | 3642779 | 631 / 630 / 630 | 1 / 0 / 0 / 0 | 7072 / 7151 | 7160 / 7159 | 7086 / 7099 | 1/189 | 11/2520 | -1/1080 | 267/118/245 ; 269/128/233 | 615/15 ; 617/13 |
| 6343 | 524288 | 3443804 | 67 / 66 / 66 | 1 / 0 / 0 / 0 | 805 / 811 | 936 / 917 | 946 / 916 | 25/1584 | 1/44 | 1/144 | 31/17/18 ; 31/21/14 | 66/0 ; 66/0 |
| 6347 | 524288 | 3482989 | 258 / 257 / 257 | 1 / 0 / 0 / 0 | 3113 / 3163 | 3381 / 3353 | 3586 / 3507 | 13/1028 | 43/2056 | 17/2056 | 117/61/79 ; 129/60/68 | 256/1 ; 255/2 |

Original eligibility is measured before stricter matching. Both means are compared only on the common set; an index-zero escape is classified no-suffix before the no-previous check. Same preceding q class does not match full context, reused controls are dependent, and these fixed comparisons have no calibrated significance or physical framing interpretation.

## Reproduce
At commit aef91af339126bac9d6523049f78307cfcf6e326, verify retained CC0 identity and local SHA-256, then run:

`python -I -B tools/escape_context_match_probe.py --sample PUBLIC_NAME SHA256 FILE --tokens 262144`

Select the nearest preceding q=0 control with the same suffix; stricter selection additionally matches the previous candidate-token q class 0, 1..16, or >=17. Require both 24-word skip-0/12 control horizons to finish before the escape and both escape horizons to finish inside the baseline prefix. Compare the methods only on the same eligible anchors. No-control and short-horizon exclusions precede context checks; index-zero escapes are counted as no-control.

Frozen public CC0 identities, retained inventory and matching manifest:

- Discovery 5283: OM System - OM-1 - 16bit (4:3).ORF, SHA-256 bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b.
- Discovery 5286: OM System - OM-1 - 16bit (4:3).ORI, SHA-256 2fd8bd46e2644fe28092fd921d9647007afd6d1e879c5ff19b1e3df50c578df1.
- Reserved 6343: OM System - OM-5 - 16bit (4:3).ORF, SHA-256 ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7.
- Reserved 6347: OM System - OM-5 - 16bit (4:3).ORI, SHA-256 062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9.




For wider verification, use `--tokens 524288` for each of the four listed inputs.

## Limitations
The input files were previously studied and the candidate parse is assumed. Further independently justified context and framing evidence is needed before attributing the observed sensitivity to a physical escape mechanism.
