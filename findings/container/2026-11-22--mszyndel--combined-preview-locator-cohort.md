# Two fixed metadata rules locate 89 of 104 public previews

Author: @mszyndel
Verified by: @mszyndel
Lead: #946
Variant: container
Builds on: #155, #938, #924, #920, #438

## Claim

On the frozen 104-file public CC0 roster, the unchanged OM SYSTEM rule adds 34 exact scanner matches to the historical Olympus rule's 55. Combined metadata coverage is 89/104, with zero valid-result disagreements. Three original MakerNote-envelope contradictions remain rejected. Twelve combined metadata outcomes remain unsupported/unknown, including four with valid scanner previews and eight without a selected scanner preview.

The combined result accepts exactly one valid fixed metadata rule and no candidate contradiction. Neither locator nor their combination uses the scanner to select or repair the interval. This is a bounded container-location observation, not official tag semantics, physical preview-to-raw registration or a compressed decoder.

## Original evidence

Tool: `tools/om_system_preview_cohort.py` at `34d5859eb28628c425c344ab571d700a91252d8c`, separate tool PR #937. The original Olympus and OM SYSTEM candidate functions and their dependencies are byte-identical to the sources used for #920 and #938. Both candidates run before the unchanged scanner; the combined choice is a function only of their metadata results.

The protocol was fixed before sample measurement in #155 comment 7079670988. It uses the public roster in `findings/container/2026-10-27--radialmonster--capture-metadata-104-cohort.md` (#438), with canonical UTF-8 LF id/name/SHA-256 digest `efa234dec110ced00a181296cb3ac316f4aee695aa6741e1d372c29c23accbf0`. Every input's public name and full hash are pinned there and in the manifest. The input gates check retained CC0 identity, manifest identity, bounded file size and exact content SHA-256 before measurement.

Discovery used the 96 numeric-ID-ordered roster entries excluding reserved 1432,5284,5424,6347,6946,7269,7803,8553. All 96 input gates passed. The old rule gave 55 matches, two envelope contradictions and 39 unknown metadata outcomes. The OM SYSTEM rule added 28 exact matches. Combined results were 83 matches, two contradictions, four unknown metadata cases with valid scanners and seven unknown on both sides. No valid pair disagreed.

All 28 additions were 3200x2400 previews at offset 52224. Discovery stdout SHA-256 is `51b826584d7880c90ef6bb85d16a7dfe2da67ef656e1d8ed36ba007ec811d0a6`. The measurement manifest SHA-256 is `28e7b21b5be23bb0b42989f52d7a1e5adcad2a0d3a17b271692045e1c2c3400d` at the source commit above.

Fifteen original synthetic controls passed before the sample run: ten fixed-header controls and five cohort controls, including pointer-origin changes, wrong bases, larger JPEG decoys, exact bounds and metadata overlap, scanner ordering, no contradiction/overlap rescue, denominator accounting and replay-before-reserved access.

## Verification

A fresh run on 2026-11-22 UTC after #946 opened exactly replayed all 96 discovery rows and their configuration before measuring the eight reserved identities. No rule, comparison, bound, header, pointer convention or cohort identity changed. All 104 input gates passed, and all 104 content hashes were rechecked against retained CC0 records after the run.

| Full-cohort method | Exact matches | Metadata contradictions | Metadata unknown, scanner valid | Metadata unknown, scanner unknown |
| --- | ---: | ---: | ---: | ---: |
| Historical Olympus | 55 | 3 | 38 | 8 |
| Fixed OM SYSTEM | 34 | 0 | 62 | 8 |
| Combined | 89 | 3 | 4 | 8 |

The full old-rule control reproduces #924's 55 exact matches, three envelope contradictions and 46 unresolved metadata cases, all with the same source rules. Every valid old-rule result matches its scanner. Combined matching offsets/dimensions are 52224/3200x2400 (80), 24576/1600x1200 (5), 45056/3200x2400 (3), and 32768/3200x2400 (1).

| Reserved ID | Combined result | Scanner offset | Scanner length | Scanner dimensions |
| --- | --- | ---: | ---: | --- |
| 1432 | envelope contradiction retained | 196608 | 1052054 | 3200x2400 |
| 5284 | new exact match | 52224 | 952389 | 3200x2400 |
| 5424 | metadata unknown; no scanner preview | unavailable | unavailable | unavailable |
| 6347 | new exact match | 52224 | 986721 | 3200x2400 |
| 6946 | new exact match | 52224 | 973462 | 3200x2400 |
| 7269 | new exact match | 52224 | 903991 | 3200x2400 |
| 7803 | new exact match | 52224 | 886784 | 3200x2400 |
| 8553 | new exact match | 52224 | 912347 | 3200x2400 |

All 34 additions have the exact fixed OM SYSTEM header and are contained, marker-bounded 3200x2400 JPEGs at 52224. Their public IDs are 5283,5284,5285,5286,5287,6343,6344,6345,6346,6347,6946,7262,7263,7264,7265,7266,7267,7268,7269,7270,7796,7797,7798,7799,7800,7801,7802,7803,7804,8549,8550,8552,8553,8554. The retained catalogue labels are OM-1 (5), OM-5 (5), OM-1 Mark II (9), OM-3 (9), OM-5 Mark II (5), TG-7 (1). These are annotations, not a model-based variant or layout selector.

The three retained envelope contradictions are 792,1432,2431. The twelve combined metadata unknowns are 780,1799,1800,2151,2420,2878,3438,3540,3624,5424,5491,8609. Of those, 2151,2878,3540,3624 have valid scanner previews; the other eight have scanner reason `no_preview`. All 70 OM SYSTEM-rule unknowns have reason `unsupported_leading_header`. A missing scanner result is not proof of image absence; unsupported metadata is not tag absence. No rejected interval is endorsed from scanner agreement.

Verification stdout SHA-256 is `9a8b137b8a0f07a449c00546a417baa66509182e35a3a114428e16b952b78550`. The saved discovery hash and exact 96-row replay also match. The public roster supplies every input's raw.pixls.us name/hash, with 65 new measured-signature rows under @mszyndel appended and 39 existing exact personal rows reused.

The finder and verifier are the same person. All inputs had prior project exposure; these additions were reserved from this experiment's metadata measurement, not blind new captures. The parser, scanner and marker checker remain shared assumptions across the runs. This result measures the two declared rules on this cohort and establishes no universal tag meaning, entropy conformance, pixel mapping or physical registration. No private input, image or pixel array is used.

## Reproduce

Use tool commit `34d5859eb28628c425c344ab571d700a91252d8c` from #937, its unchanged dependencies, and the roster and manifest at that commit. Supply retained verified public CC0 records and exact local copies. Read source/imports first. The manifest digest above pins the report configuration; later manifest appends do not replace that pinned measurement input.

    python -I -B tools/om_system_preview_cohort.py --phase discovery --inventory RECORDS_JSON --corpus CORPUS_DIR --manifest samples/manifest.csv --roster findings/container/2026-10-27--radialmonster--capture-metadata-104-cohort.md

Retain unchanged stdout as UTF-8 JSON in scratch. In a fresh post-lead run:

    python -I -B tools/om_system_preview_cohort.py --phase verification --frozen DISCOVERY_JSON --inventory RECORDS_JSON --corpus CORPUS_DIR --manifest samples/manifest.csv --roster findings/container/2026-10-27--radialmonster--capture-metadata-104-cohort.md

Exit 1 with a complete report is expected because rejected and unsupported cases remain. `input_counts` must show 96 then 104 `ok` inputs; failures are kept separate. `counts` gives each method's full denominator and exact-match/contradiction/unknown cells. The verification phase checks every discovery record and config before any reserved metadata is measured.
