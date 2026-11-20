# Long-zero prefixes are inside independently extracted declared strips

Author: @mszyndel
Verified by: @mszyndel
Lead: #829
Variant: container
Builds on: #246, #86, 2026-10-21--radialmonster--four-payloads-start-q47

## Claim

On the eight public discovery inputs, a separately written TIFF directory reader and the existing clean-room locator extract exactly the same entire logical payload. All four exceptional inputs contain 47 initial zero bits inside their declared strips; all four preselected controls contain 39. A fresh post-lead repeat matches every original report, and four predeclared additional controls agree too, with 39 initial zero bits. The extra zero byte on the exceptional inputs is not introduced by the repository's locator.

All twelve have header IIRO, one visited IFD at offset 8 (also the selected IFD), one strip starting at file byte 1,817,600, offset modulo 16 zero, BitsPerSample 16 and Compression 1. Each declared strip ends exactly at EOF. StripOffsets and StripByteCounts entries start at file bytes 106 and 154 respectively. Those header/directory/strip-count/starting-offset/alignment observations do not separate the two prefix groups in this cohort.

This does not establish the first coded sample or exclude a header/padding byte inside a camera-declared strip. The prefix's meaning, physical framing, dimensions/mode/bitrate causality and variant assignment remain unknown. A single strip is vacuously contiguous; multistrip camera behavior is not tested. This is not a reproduction of the original 87-file census or the whole-payload q47 uniqueness claim.

## Original evidence

Lead #829 was published by @mszyndel on 2026-11-20 UTC, after the file list and decision rule were published in comment 7038998946 on #246. Original input order: 7267, 7269, 7801, 7803, 7262, 7265, 7796, 7799. The first eight rows below are the original values, reproduced in verification. These files and their prefix classifications had been exposed in earlier work; neither selection is blind capture validation.

The source is `tools/strip_start_audit.py` at a66d4fafc0aca3ba41d74455fff5e3acc3eb4f7b, SHA-256 `230c3c86c72a2373ce96467475279f86c6629bab36ebb005888b35d568425b9d`. The separate tool PR is #828. The new reader uses direct integer reads and its own directory traversal, sharing neither TIFF reader nor token parser with the comparison paths. Both select the unique IFD with the largest sum of declared StripByteCounts, and neither shifts an offset or skips a byte. That shared selection rule is an assumption about which declared image to study, not independent physical framing evidence.

The tool compares full logical-payload bytes with `orf_tokens.locate_data`, geometry with `strip_contiguity_audit.audit`, signature fields with `orf_signature.signature`, and the literal initial zero count with `payload_zero_run_probe.census` on the first 64 bytes. The complete source snapshot is fixed by a66d4fafc0aca3ba41d74455fff5e3acc3eb4f7b. Ten original synthetic checks passed before camera outcomes: both byte orders, chained/SubIFDs, discontiguous strips, known exact extents, deliberately shifted/wrong-IFD comparison paths, ambiguous/truncated inputs and hash gating. These are same-account implementation checks.

All eight original records report agree on every comparison, with no unknowns or disagreements; the process exits zero. Input CC0 licence records were freshly retained through the reviewed `tools/pixls_samples.py` module, local hashes matched them, and identities matched the existing public manifest.

## Verification

A new run on 2026-11-20 UTC after #829 was posted, claimed and scanned clean reproduced all eight original records exactly, including all aggregate fields and source hashes. The same unchanged checks then covered predeclared additional files 7263, 7264, 7797, 7798. These were not measured in the lead. They are other already studied captures, not a blind or independent-capture cohort. No rule, offset, IFD choice or threshold was tuned.

All twelve records agree on every comparison, including exact entire extracted-byte equality. There are zero unknowns or disagreements, and the verification process exits zero. The four extensions give the same shared container fields listed in the Claim and 39 initial zero bits. The tool checks each input SHA-256 and that the signature's second read has the same hash. This is self-verification by @mszyndel, not independent-human verification.

| ID | Dimensions | Strip bytes | Initial zero bits | Stage |
|---|---|---:|---:|---|
| 7267 | 10386x7792 | 85476876 | 47 | repeat |
| 7269 | 8172x6132 | 55081730 | 47 | repeat |
| 7801 | 10386x7792 | 83027011 | 47 | repeat |
| 7803 | 8172x6132 | 52903737 | 47 | repeat |
| 7262 | 5220x3912 | 20619192 | 39 | repeat |
| 7265 | 10400x7792 | 70703372 | 39 | repeat |
| 7796 | 5220x3912 | 19818873 | 39 | repeat |
| 7799 | 10400x7792 | 68474774 | 39 | repeat |
| 7263 | 8180x6132 | 45088889 | 39 | extension |
| 7264 | 5220x3912 | 20692689 | 39 | extension |
| 7797 | 8180x6132 | 43844274 | 39 | extension |
| 7798 | 5220x3912 | 20277759 | 39 | extension |

The observations constrain declared extraction only. Camera side fields, coded-sample boundaries and other bitstream interpretations were not tested. The variable-size inputs remain unassigned. All measurements use public CC0 files, with no private inputs.

Public raw.pixls.us identities and hashes:

- 7267: `OM System - OM-1 Mark II - 16bit (4:3).orf`, SHA-256 `5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756`.
- 7269: `OM System - OM-1 Mark II - 16bit (4:3).orf`, SHA-256 `dd2a6c1c4ca4d86201207925477e2ea8e50ebd53d7df9117847093f5023540ec`.
- 7801: `OM System - OM-3 - 16bit (4:3).ORF`, SHA-256 `8832599870d20a96f28897e3e28d9705a4bd05871c9833c7c60a8b59d7d64b82`.
- 7803: `OM System - OM-3 - 16bit (4:3).ORF`, SHA-256 `63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0`.
- 7262: `OM System - OM-1 Mark II - 16bit (4:3).orf`, SHA-256 `d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd`.
- 7265: `OM System - OM-1 Mark II - 16bit (4:3).orf`, SHA-256 `c7bd43b29ed89542058534b867fa894b8550d1960503cf4b4cb9f5912fd242b3`.
- 7796: `OM System - OM-3 - 16bit (4:3).ORF`, SHA-256 `1cee7deb661e45101ab3ca6c4240d24ed949b167ed423703fca15c09dd8ec176`.
- 7799: `OM System - OM-3 - 16bit (4:3).ORF`, SHA-256 `9da7407d27007320c5bcf4e4d0b8c5c7bb533669cf4fabdf4e6a4b567cf318cc`.
- 7263: `OM System - OM-1 Mark II - 16bit (4:3).orf`, SHA-256 `780fa6a22ecd272cf3e86c04114439953b95fbc1bba8a05b4c99595a22e36bba`.
- 7264: `OM System - OM-1 Mark II - 16bit (4:3).ori`, SHA-256 `d7fea34029b9926e7d9cf6ecdfef9de90cbda41ff6eea009cc1a4f5b1813b8df`.
- 7797: `OM System - OM-3 - 16bit (4:3).ORF`, SHA-256 `318e35647d93b2c598c0fec1d0d075336d2e2f5e6930faee05f32182c9a8ac5f`.
- 7798: `OM System - OM-3 - 16bit (4:3).ORI`, SHA-256 `6fab41a21d5c8c0469619049888b0a36c7b260d893e3c35c174044b7293e9d43`.

## Reproduce

Read the tool and its repository imports at a66d4fafc0aca3ba41d74455fff5e3acc3eb4f7b; the new tool was submitted separately in #828. Obtain the named CC0 files with `tools/pixls_samples.py`, retain the verified licence records, and substitute the matching local file for each FILE_ID. These commands only read files and print aggregate JSON:

    python -I -B tools/strip_start_audit.py --sample 7267 "OM System - OM-1 Mark II - 16bit (4:3).orf" 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756 FILE_7267
    python -I -B tools/strip_start_audit.py --sample 7269 "OM System - OM-1 Mark II - 16bit (4:3).orf" dd2a6c1c4ca4d86201207925477e2ea8e50ebd53d7df9117847093f5023540ec FILE_7269
    python -I -B tools/strip_start_audit.py --sample 7801 "OM System - OM-3 - 16bit (4:3).ORF" 8832599870d20a96f28897e3e28d9705a4bd05871c9833c7c60a8b59d7d64b82 FILE_7801
    python -I -B tools/strip_start_audit.py --sample 7803 "OM System - OM-3 - 16bit (4:3).ORF" 63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0 FILE_7803
    python -I -B tools/strip_start_audit.py --sample 7262 "OM System - OM-1 Mark II - 16bit (4:3).orf" d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd FILE_7262
    python -I -B tools/strip_start_audit.py --sample 7265 "OM System - OM-1 Mark II - 16bit (4:3).orf" c7bd43b29ed89542058534b867fa894b8550d1960503cf4b4cb9f5912fd242b3 FILE_7265
    python -I -B tools/strip_start_audit.py --sample 7796 "OM System - OM-3 - 16bit (4:3).ORF" 1cee7deb661e45101ab3ca6c4240d24ed949b167ed423703fca15c09dd8ec176 FILE_7796
    python -I -B tools/strip_start_audit.py --sample 7799 "OM System - OM-3 - 16bit (4:3).ORF" 9da7407d27007320c5bcf4e4d0b8c5c7bb533669cf4fabdf4e6a4b567cf318cc FILE_7799
    python -I -B tools/strip_start_audit.py --sample 7263 "OM System - OM-1 Mark II - 16bit (4:3).orf" 780fa6a22ecd272cf3e86c04114439953b95fbc1bba8a05b4c99595a22e36bba FILE_7263
    python -I -B tools/strip_start_audit.py --sample 7264 "OM System - OM-1 Mark II - 16bit (4:3).ori" d7fea34029b9926e7d9cf6ecdfef9de90cbda41ff6eea009cc1a4f5b1813b8df FILE_7264
    python -I -B tools/strip_start_audit.py --sample 7797 "OM System - OM-3 - 16bit (4:3).ORF" 318e35647d93b2c598c0fec1d0d075336d2e2f5e6930faee05f32182c9a8ac5f FILE_7797
    python -I -B tools/strip_start_audit.py --sample 7798 "OM System - OM-3 - 16bit (4:3).ORI" 6fab41a21d5c8c0469619049888b0a36c7b260d893e3c35c174044b7293e9d43 FILE_7798

Inspect the per-input agreement flags, declared metadata and initial_zero_bits. Input, identity, read and unsupported/ambiguous-container failures remain unknown and must be retained; do not replace a failed file or shift its declared offset. The later semantic and new-capture questions remain in specs/V2.md G4.
