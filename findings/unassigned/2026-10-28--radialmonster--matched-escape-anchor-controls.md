# Matched candidate escape anchors on four public files

Author: @radialmonster
Verified by: @radialmonster
Lead: #634
Variant: unassigned
Builds on: #30, #11

## Claim
A fixed matched-anchor candidate-token comparison gives opposite signed mean differences on two public OM-1 files at 262144 tokens. The result is descriptive and does not establish escape syntax or physical framing.

## Original evidence
At commit 7e1c811f9c9f4236d5029b04b7faf31660a851df, lead #634 reported means -5/933 and +7/1244 on 5283 and 5286 respectively, with 311 paired anchors in each.

## Verification
After the lead was posted, fresh runs reproduced both original cases and tested the predeclared 524288-token extent on those two and two additional public OM-5 files. These are previously studied files, not blind captures or independent human verification. An independently structured bit parser and aggregator matched every field; both implementations share a TIFF locator. All requested prefixes completed.

Columns list candidate anchors / complete pairs / no match / incomplete escape horizon, then q=0 counts for escape skip 0 / escape skip 12 / control skip 0 / control skip 12, followed by the common denominator, exact paired mean, positive / tied / negative pair differences, and unique / reused controls.

| ID | Tokens | Endpoint bits | Anchors / pairs / no match / short | Four q=0 counts | Denominator | Mean | Positive / tied / negative | Unique / reuse |
|---|---:|---:|---|---|---:|---|---|---|
| 5283 | 262144 | 1822446 | 313 / 311 / 2 / 0 | 3520 / 3515 / 3510 / 3545 | 7464 | -5/933 | 119 / 60 / 132 | 304 / 7 |
| 5286 | 262144 | 1821991 | 312 / 311 / 1 / 0 | 3560 / 3592 / 3481 / 3471 | 7464 | 7/1244 | 133 / 58 / 120 | 303 / 8 |
| 5283 | 524288 | 3645413 | 597 / 595 / 2 / 0 | 6695 / 6709 / 6734 / 6788 | 14280 | -1/357 | 225 / 121 / 249 | 585 / 10 |
| 5286 | 524288 | 3642779 | 631 / 630 / 1 / 0 | 7072 / 7151 / 7160 / 7159 | 15120 | 1/189 | 267 / 118 / 245 | 615 / 15 |
| 6343 | 524288 | 3443804 | 67 / 66 / 1 / 0 | 805 / 811 / 936 / 917 | 1584 | 25/1584 | 31 / 17 / 18 | 66 / 0 |
| 6347 | 524288 | 3482989 | 258 / 257 / 1 / 0 | 3113 / 3163 / 3381 / 3353 | 6168 | 13/1028 | 117 / 61 / 79 | 256 / 1 |

The original opposite signs persist at the wider extent; exact mean values change. Both additional OM-5 cases have positive means. These observations are limited to the fixed candidate parses and selected anchors: same suffix does not match q class or neighboring context, and controls may be reused. No independent physical framing, causal effect or calibrated significance follows.

## Reproduce
At commit 7e1c811f9c9f4236d5029b04b7faf31660a851df run the public source with the fixed public name, SHA-256 and local path, after retained CC0 and manifest verification:

`python -I -B tools/escape_matched_control_probe.py --sample PUBLIC_NAME SHA256 FILE --tokens 262144`

Parse complete stop-1, five-bit-suffix candidate words from payload bit zero. Select q>=17 anchors among the first 262144 complete words, and freeze the endpoint of that prefix. For each anchor select the nearest preceding q=0 word with the same unsigned suffix for which both subsequent control parses, starting 0 or 12 bits after its end, contain 24 complete words and end no later than the escape start. Parse 24 words from each escape at the same two offsets; all horizons end no later than the frozen prefix endpoint. Report unmatchable anchors and matched anchors with incomplete escape horizons separately.

For complete pairs, report the four q=0 counts and common denominator 24 times the number of complete pairs, the exact mean paired difference [(escape12 - escape0) - (control12 - control0)] / 24, its positive/tied/negative counts, and distinct/reused control counts. The nearest eligible control may be reused; same suffix does not match preceding q, position or neighboring bit context. This is a descriptive candidate-token score, not evidence of physical escape semantics, independence, a calibrated significance test or adaptive-code falsification.

The verification also uses the 524288-token extent on all four files. These files have prior exposure and are not blind captures. All four identities and hashes below match retained CC0 and manifest metadata.

Frozen public CC0 identities, retained inventory and matching manifest:

- Discovery 5283: OM System - OM-1 - 16bit (4:3).ORF, SHA-256 bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b.
- Discovery 5286: OM System - OM-1 - 16bit (4:3).ORI, SHA-256 2fd8bd46e2644fe28092fd921d9647007afd6d1e879c5ff19b1e3df50c578df1.
- Reserved 6343: OM System - OM-5 - 16bit (4:3).ORF, SHA-256 ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7.
- Reserved 6347: OM System - OM-5 - 16bit (4:3).ORI, SHA-256 062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9.



## Limitations
This does not reproduce #30's private row-consumption calculation or identify a codec. Independently justified framing and better context controls remain open.
