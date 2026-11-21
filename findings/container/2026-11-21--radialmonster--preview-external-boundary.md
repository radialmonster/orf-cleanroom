# Three scalar preview intervals start beyond their declared MakerNotes

Author: @radialmonster
Verified by: @radialmonster
Lead: #928
Variant: container
Builds on: #155, #907, #924, 2026-11-21--radialmonster--metadata-first-jpeg-cohort

## Claim

The fixed MakerNote scalar interval starts after the declared MakerNote end in public SH-2 792, XZ-2 1432 and XZ-10 2431. The XZ-1 1759 control is contained. The visited outer TIFF graph gives no positive same-directory LONG 513/514 pair on any of the four. The selected strip follows the candidate without overlapping it or sharing either endpoint in all four.

## Original evidence

The discovery run started at 00:47:59 UTC on 2026-11-21 using tools/preview_external_boundary.py at c1ddb04445c1584c644c9cf8543466d51291a693. The pre-run protocol is in #155 comment 7054439030. The tool derives a fixed scalar interval from the declared MakerNote value start plus 0x0101 and length 0x0102. It compares that interval with declarations from the bounded outer IFD0, next IFD and SubIFD graph. Candidate bytes cannot serve as outer directory or table data. The unique largest strip declaration by total byte count supplies the selected strip after validation. This procedure uses metadata only.

| ID | Public catalogue name | SHA-256 |
| --- | --- | --- |
| 792 | Olympus - SH-2 - 12bit (4:3).ORF | 6e6b9b7dd9ded7c4b364b83116c817ca2d6daac15f2e9ef7796159b08c3288a1 |
| 1432 | Olympus - XZ-2 - 12bit (4:3).orf | 675fefe7c9e99281783b987889d723b5f46692f5c20e19fed5e422c7c6d2636b |
| 1759 | Olympus - XZ-1 - 16bit (4:3).orf | 3f5fb6f36ad4132323cab790e30b0bc10217aa7fb703518005a5800c908ba8a3 |
| 2431 reserved | Olympus - XZ-10 - 12bit (4:3).ORF | a25383acad9b5bb0bb404715e0957f2eb80aa1aaad6c448a71025c03cfa631be |

All identities are public CC0 from the retained records and existing manifest and roster. The discovery JSON SHA-256 was 0cdb46945456cde697b6404ae8df2cae902abbff5955eb0e155399eabea76130. The first three rows in the table below are the three frozen discovery measurements.

## Verification

After #928 opened, the first verification stopped before opening the reserved sample because an in-memory strip tuple differed in type from its saved JSON array. A separate discovery-only run reproduced the frozen report byte for byte. #929 made the interval representation identical to the loaded JSON without changing serialized results.

A fresh run at 00:53:50 UTC on 2026-11-21 using 499d22df40a64b34fe8664b07d4c1b5fa50664bf matched all three frozen rows before opening XZ-10 2431. That file has prior project use and did not enter the discovery measurement. The saved verification JSON SHA-256 was 4793473e1402dee6a9bd51ba1cf67ee1f9a718b78c457a84fc3887e66bdf3c32. An aggregate audit separately checked the identities, signed deltas, graph and strip outcomes. Verification used the same GitHub account.

All intervals are half-open byte ranges. The last two columns subtract the MakerNote end from the candidate start and end.

| ID | MakerNote interval | Scalar interval | Selected strip | Start delta | End delta |
| --- | --- | --- | --- | ---: | ---: |
| 792 | [1862, 167016) | [196608, 1298786) | [1476608, 25544528) | 29592 | 1131770 |
| 1432 | [1850, 147660) | [196608, 1248662) | [1476608, 19320944) | 48948 | 1101002 |
| 1759 | [3172, 1478144) | [52224, 1162133) | [1478144, 10811567) | -1425920 | -316011 |
| 2431 reserved | [1850, 147800) | [196608, 1271490) | [1476608, 19344848) | 48808 | 1123690 |

All four walks completed with zero positive, disabled, or orphan 513/514 declarations. Each selected strip comes from IFD offset 8. All three exterior examples started at byte 196608 and shared selected strip start 1476608. Their scalar-derived ends differ. Neither tested declaration scope supplies the external preview boundary on these files. Alternative declaration scopes, tag meanings and physical preview-to-raw registration remain open.

## Reproduce

Use exact CC0 copies and the corrected tool at 499d22df40a64b34fe8664b07d4c1b5fa50664bf. Save discovery stdout as UTF-8 JSON in a scratch folder. The hashes above use LF line endings. The corrected discovery command preserves the original JSON.

    python -I -B tools/preview_external_boundary.py --phase discovery --sample 792 FILE792 --sample 1432 FILE1432 --sample 1759 FILE1759
    python -I -B tools/preview_external_boundary.py --phase verification --frozen DISCOVERY_JSON --sample 792 FILE792 --sample 1432 FILE1432 --sample 1759 FILE1759 --sample 2431 FILE2431
