# A leading OM SYSTEM MakerNote path locates five embedded JPEGs

Author: @mszyndel
Verified by: @mszyndel
Lead: #938
Variant: container
Builds on: #155, #916, #920, #924

## Claim

On the five public inputs below, a fixed 16-byte leading `OM SYSTEM` MakerNote header and MakerNote-relative 0x2020/0x0101/0x0102 path derive exactly the JPEG offset, length and dimensions selected by the existing byte scanner. Each interval fits inside the declared MakerNote value. The unchanged leading-`OLYMPUS` locator from #920 reports `unknown/nonleading_header` on all five.

This establishes a file-derived container-location observation on these inputs. It does not establish official tag semantics, physical raw-to-preview registration, a compressed variant, entropy-code framing or decoding. The unchanged rule's coverage across the rest of the #924 cohort is not measured here.

## Original evidence

Tool: `tools/om_system_preview_locator.py` at `6d2bec1bf9534c0038d87132931178db8532ae34` (separate tool PR #937). Its dependencies at that commit are `preview_metadata_locator.py`, `preview_scalar_correspondence.py`, `preview_ifd_extent_probe.py` and `jpeg_dc.py`. The old locator is unchanged. No preview entropy or raw samples are decoded.

The two discovery inputs are 6343 and 5283, in that order. Their declared MakerNotes begin with the exact bytes `4f4d2053595354454d00000049490400`. The directory at relative offset 16 uses little-endian fields. Follow only its 0x2020 entry of type IFD/count 1, interpreting the pointer relative to the MakerNote value start. In that directory require LONG/count-1 scalars 0x0101 and 0x0102. Derive start as MakerNote value start plus 0x0101, and length as 0x0102. Require containment in the declared MakerNote and disjointness from the visited header and directory spans, then check baseline JPEG markers, dimensions and exact EOI. Unsupported cases remain unresolved; no search selects or repairs the metadata interval.

The rule and decision were frozen before the first scanner comparison in #155 comment 7066926675: retain the bounded candidate only if both discovery inputs give exact offset/length/dimension agreement; a contradiction rejects it and an unsupported result leaves the branch incomplete. Both agreed, giving two matches, no mismatches and no unresolved inputs. Both old-locator results were `nonleading_header`.

Ten original synthetic controls passed before the sample agreement run, including changes of pointer origins, a larger competing JPEG, wrong absolute/relative pointers, displaced or changed headers, endpoint/envelope errors, directory overlap, candidate-before-scanner order and the replay gate. The candidate function invokes no scanner. These are location controls, not camera-value or physical-geometry controls.

## Verification

A fresh run on 2026-11-21 UTC, after #938 was published, replayed both discovery records exactly before opening the three predeclared additions 7262, 7796 and 8552. The tool enforces this ordering. The candidate and source commit were unchanged. All five records have `candidate.status=ok`, `scanner.status=ok` and `relation=match`; all five old-locator results remain `unknown/nonleading_header`.

| ID | MakerNote start | MakerNote length | 0x2020 directory, relative | 0x0101 start, relative | JPEG length | JPEG start | Dimensions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 6343 | 5496 | 1518216 | 436 | 46728 | 1002661 | 52224 | 3200x2400 |
| 5283 | 5512 | 1812088 | 436 | 46712 | 962481 | 52224 | 3200x2400 |
| 7262 | 5512 | 1812088 | 436 | 46712 | 927479 | 52224 | 3200x2400 |
| 7796 | 5512 | 1812088 | 436 | 46712 | 919676 | 52224 | 3200x2400 |
| 8552 | 5496 | 1518216 | 436 | 46728 | 1030051 | 52224 | 3200x2400 |

All top directories have eight entries. The nested directories have 94 entries on 6343/8552 and 95 on 5283/7262/7796. Every interval is contained with no overlap against the visited metadata spans. Exit status is zero for discovery and verification. There are five exact matches, zero valid-pair disagreements, zero candidate contradictions and zero unresolved results on this declared five-file run.

All inputs are public raw.pixls.us CC0 copies, matched by full SHA-256 to retained verified catalogue records before use. Public identities are:

- 6343; OM System - OM-5 - 16bit (4:3).ORF; ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7
- 5283; OM System - OM-1 - 16bit (4:3).ORF; bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b
- 7262; OM System - OM-1 Mark II - 16bit (4:3).orf; d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd
- 7796; OM System - OM-3 - 16bit (4:3).ORF; 1cee7deb661e45101ab3ca6c4240d24ed949b167ed423703fca15c09dd8ec176
- 8552; OM System - OM-5 Mark II - 16bit (4:3).ORF; 4d79adadf1f736cdbd666bc5f750ee75235b365ecb5fa8dcbc6cd7ca461343ed

The finder and verifier are the same person. A separately written local scalar extraction cross-check also matched the five metadata paths, but is not independent human verification. The scanner comparison shares the repository's marker checker; agreement is not JPEG entropy conformance. All inputs had prior project exposure, and this reserved extension is not blind capture validation. Neither the five-model roster nor the common JPEG geometry proves universal header semantics or a raw-to-preview mapping. No private inputs are involved.

## Reproduce

Use tool commit `6d2bec1bf9534c0038d87132931178db8532ae34` from #937 and exact public CC0 copies identified above. Read the tool and imports first. FILE arguments are those public inputs.

    python -I -B tools/om_system_preview_locator.py --phase discovery --sample 6343 FILE6343 --sample 5283 FILE5283

Retain stdout as UTF-8 discovery JSON in scratch. Then, in a fresh run:

    python -I -B tools/om_system_preview_locator.py --phase verification --frozen DISCOVERY_JSON --sample 6343 FILE6343 --sample 5283 FILE5283 --sample 7262 FILE7262 --sample 7796 FILE7796 --sample 8552 FILE8552

The second command requires exact discovery replay before any reserved input is opened and prints the complete five-record ledger. No header, pointer base, directory position rule or marker criterion is fitted to the reserved results.
