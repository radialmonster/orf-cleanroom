# Metadata-first JPEG locator matches 55 of 104 public preview extents

Author: @radialmonster
Verified by: @radialmonster
Lead: #924
Variant: container
Builds on: #155, #438, 2026-11-21--radialmonster--metadata-first-jpeg-locator

## Claim

The frozen leading-header MakerNote locator gives 55 valid extents on the published 104-file CC0 roster. All 55 equal the scanner offset, length and dimensions. Three derived extents violate declared MakerNote envelope containment, and 46 metadata outcomes remain unresolved. No pair of valid results disagrees. This measures the rule's scope on this cohort. The tag semantics and physical preview-to-raw registration remain open.

## Original evidence

Discovery began at 00:32:08 UTC on 2026-11-21 using tools/preview_locator_cohort.py at 65a4d31a9060509225ce8d3b50cd62f9be757cb1. The tool uses the unchanged metadata-first calculator and separate scanner from #920. The protocol was published before the run at #155 comment 7054139888.

The public names and SHA-256 values of all samples are in findings/container/2026-10-27--radialmonster--capture-metadata-104-cohort.md and samples/manifest.csv, checked against retained CC0 records. The canonical roster SHA-256 is efa234dec110ced00a181296cb3ac316f4aee695aa6741e1d372c29c23accbf0. The original 97 files exclude the seven IDs listed in Verification. All discovery inputs passed their identity and content hash gates. The discovery report SHA-256 was a48485a01d082eb9e1f6cb4ed55c15a72134b54814b52262ca0664dcdf8dcb5c.

| Metadata result | Scanner result | Relation | Discovery |
| --- | --- | --- | ---: |
| Valid | Valid | Exact match | 51 |
| Outside declared MakerNote envelope | Valid | Unresolved | 1 |
| Nonleading header | Valid | Unresolved | 37 |
| Nonleading header | No preview | Unresolved | 8 |

Matches by offset are 24576 (5), 32768 (1), 45056 (3) and 52224 (42). The discovery contradiction is ID 792, Olympus - SH-2 - 12bit (4:3).ORF, SHA-256 6e6b9b7dd9ded7c4b364b83116c817ca2d6daac15f2e9ef7796159b08c3288a1. Its scalar offset 196608 and length 1102178 equal the scanner numbers, but the extent failed envelope containment before marker validation.

## Verification

A fresh run started at 00:35:03 UTC on 2026-11-21 after #924 opened. It reproduced every one of the 97 original rows before opening the seven reserved TG/XZ inputs. All had prior project use. Verification used the same account, with a separate check of the saved report's identities, extents and counts. All 104 inputs passed their identity and content hash gates. The verification report SHA-256 was 45e525dd24d8cc3e245b0fb0d1d791ea56fe436d09d6620d338b4d4904390791.

| Reserved ID | Public catalogue name | SHA-256 | Metadata result | Scanner offset and length in bytes |
| --- | --- | --- | --- | --- |
| 1135 | Olympus - TG-4 - 16bit (4:3).ORF | a056d3fad56762d8a125806a0a4857341f115bc6303085b7297758be8d93b20a | Exact match | 52224, 1017780 |
| 1432 | Olympus - XZ-2 - 12bit (4:3).orf | 675fefe7c9e99281783b987889d723b5f46692f5c20e19fed5e422c7c6d2636b | Outside envelope | 196608, 1052054 |
| 1723 | Olympus - TG-5 - 16bit (4:3).ORF | 1fd6d09b8c93a9bb629e1871859c18a6763397301396844c34217330de094453 | Exact match | 52224, 1007656 |
| 1759 | Olympus - XZ-1 - 16bit (4:3).orf | 3f5fb6f36ad4132323cab790e30b0bc10217aa7fb703518005a5800c908ba8a3 | Exact match | 52224, 1109909 |
| 2431 | Olympus - XZ-10 - 12bit (4:3).ORF | a25383acad9b5bb0bb404715e0957f2eb80aa1aaad6c448a71025c03cfa631be | Outside envelope | 196608, 1074882 |
| 3210 | Olympus - TG-6 - 16bit (4:3).ORF | edd6f928bc790c79852a17fce56718d26563c7a593894d22970ef0fdb86ba45f | Exact match | 52224, 927086 |
| 6946 | OM System - TG-7 - 16bit (4:3).ORF | 4f7344c67bfcfcfec45f754195ba612fc2ad6312f5fab87812bf04b9e9e7d46a | Nonleading header | 52224, 973462 |

All seven scanner dimensions are 3200 by 2400. On both reserved outside-envelope cases, the unvalidated scalar offset and length equal the scanner values, as on the discovery SH-2 file. The rule requires containment in every case.

The full 104-file report has 55 exact matches, three contradictions with a valid scanner result, 38 unresolved metadata cases with a valid scanner result, and eight unresolved on both sides. All 46 unresolved metadata outcomes have reason nonleading_header. The match offsets are 24576 (5), 32768 (1), 45056 (3) and 52224 (46). Fifty matches are 3200 by 2400 and five are 1600 by 1200.

## Reproduce

Use 65a4d31a9060509225ce8d3b50cd62f9be757cb1 and the manifest and roster at that commit. Supply retained CC0 records and local copies. Save discovery stdout as UTF-8 JSON in a scratch folder. Report hashes above refer to LF line endings and the manifest as checked out. Exit 1 with a complete report indicates at least one unknown outcome.

    python -I -B tools/preview_locator_cohort.py --phase discovery --inventory RECORDS_JSON --corpus CORPUS_DIR --manifest samples/manifest.csv --roster findings/container/2026-10-27--radialmonster--capture-metadata-104-cohort.md
    python -I -B tools/preview_locator_cohort.py --phase verification --frozen DISCOVERY_JSON --inventory RECORDS_JSON --corpus CORPUS_DIR --manifest samples/manifest.csv --roster findings/container/2026-10-27--radialmonster--capture-metadata-104-cohort.md
