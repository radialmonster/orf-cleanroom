# Independent reproduction of long-zero prefixes inside declared strips

Author: @mszyndel
Verified by: @radialmonster
Lead: #829
Variant: container
Builds on: #246, #86, 2026-10-21--radialmonster--four-payloads-start-q47
Reproduces: 2026-11-20--mszyndel--declared-strip-starts

## Claim

The pinned independent TIFF directory reader and existing clean-room locator extract identical entire payloads on the twelve public samples from the original finding. The four declared strips with 47 leading zero bits and eight with 39 reproduce. The extra zero byte is present inside the declared strip rather than introduced by the locator.

## Original evidence

Lead #829 used the first eight files below. The original self-verification repeated those records and added four predeclared control files. `tools/strip_start_audit.py` at `a66d4fafc0aca3ba41d74455fff5e3acc3eb4f7b` compares direct TIFF extraction with the existing locator byte for byte, compares dimensions and geometry with the existing strip/signature tools, and compares literal starting zeros to the census. Both extraction paths use the IFD with the largest sum of declared strip byte counts. Neither repositions the start.

Public raw.pixls.us CC0 identities, matched by manifest SHA-256:

| Id | Catalogue name | SHA-256 | Dimensions | Strip bytes | Initial zero bits |
| ---: | --- | --- | --- | ---: | ---: |
| 7267 | OM System - OM-1 Mark II - 16bit (4:3).orf | 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756 | 10386x7792 | 85476876 | 47 |
| 7269 | OM System - OM-1 Mark II - 16bit (4:3).orf | dd2a6c1c4ca4d86201207925477e2ea8e50ebd53d7df9117847093f5023540ec | 8172x6132 | 55081730 | 47 |
| 7801 | OM System - OM-3 - 16bit (4:3).ORF | 8832599870d20a96f28897e3e28d9705a4bd05871c9833c7c60a8b59d7d64b82 | 10386x7792 | 83027011 | 47 |
| 7803 | OM System - OM-3 - 16bit (4:3).ORF | 63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0 | 8172x6132 | 52903737 | 47 |
| 7262 | OM System - OM-1 Mark II - 16bit (4:3).orf | d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd | 5220x3912 | 20619192 | 39 |
| 7265 | OM System - OM-1 Mark II - 16bit (4:3).orf | c7bd43b29ed89542058534b867fa894b8550d1960503cf4b4cb9f5912fd242b3 | 10400x7792 | 70703372 | 39 |
| 7796 | OM System - OM-3 - 16bit (4:3).ORF | 1cee7deb661e45101ab3ca6c4240d24ed949b167ed423703fca15c09dd8ec176 | 5220x3912 | 19818873 | 39 |
| 7799 | OM System - OM-3 - 16bit (4:3).ORF | 9da7407d27007320c5bcf4e4d0b8c5c7bb533669cf4fabdf4e6a4b567cf318cc | 10400x7792 | 68474774 | 39 |
| 7263 | OM System - OM-1 Mark II - 16bit (4:3).orf | 780fa6a22ecd272cf3e86c04114439953b95fbc1bba8a05b4c99595a22e36bba | 8180x6132 | 45088889 | 39 |
| 7264 | OM System - OM-1 Mark II - 16bit (4:3).ori | d7fea34029b9926e7d9cf6ecdfef9de90cbda41ff6eea009cc1a4f5b1813b8df | 5220x3912 | 20692689 | 39 |
| 7797 | OM System - OM-3 - 16bit (4:3).ORF | 318e35647d93b2c598c0fec1d0d075336d2e2f5e6930faee05f32182c9a8ac5f | 8180x6132 | 43844274 | 39 |
| 7798 | OM System - OM-3 - 16bit (4:3).ORI | 6fab41a21d5c8c0469619049888b0a36c7b260d893e3c35c174044b7293e9d43 | 5220x3912 | 20277759 | 39 |

## Verification

A fresh run started on 2026-11-20 at 22:18:31 UTC under Python 3.14.10. It used the original tool snapshot at `a66d4fafc0aca3ba41d74455fff5e3acc3eb4f7b`, including the original tool SHA-256 `230c3c86c72a2373ce96467475279f86c6629bab36ebb005888b35d568425b9d`. It matched the retained CC0 records, manifest and local SHA-256 for all twelve inputs. All ten synthetic tests and twelve actual file invocations passed. The four rows beyond the original issue's inputs were also present in the author's self-verified finding.

All twelve fresh rows match the listed dimensions, byte counts and initial zero bits. Every report agrees on all five checks: strip geometry, locator dimensions, full payload bytes, literal prefix census and signature. All twelve are IIRO with one visited/selected IFD at offset 8, with BitsPerSample 16 and Compression 1. Each has one strip that starts at 1,817,600, has offset modulo 16 equal to zero and ends at EOF. StripOffsets and StripByteCounts entries start at 106 and 154. There are zero unknown or disagreeing rows.

This is an independent verifier repeating the same original reader comparison on previously exposed files. The data constrain declared extraction. The actual start of coded samples, internal header or padding bytes, physical framing and multistrip behavior remain open.

## Reproduce

At the pinned commit, substitute the exact values ID, PUBLIC_NAME and SHA256 from a table row and the corresponding local FILE. Run the synthetic test once and the audit command for every row.

```text
python -I -B tools/test_strip_start_audit.py
python -I -B tools/strip_start_audit.py --sample ID "PUBLIC_NAME" SHA256 FILE
```
