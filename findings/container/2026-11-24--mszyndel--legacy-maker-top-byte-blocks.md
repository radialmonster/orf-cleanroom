# Legacy MakerNote top entries are byte blocks on three V0 inputs

Author: @mszyndel
Verified by: @mszyndel
Lead: #964
Variant: container
Builds on: #949

## Claim

Leading OLYMP version-2-byte MakerNotes on E-1 1800, SP350 2878 and
E-500 3540 contain top entries 0x2040/0x2050 as type 7 UNDEFINED byte
blocks, rather than type-13 IFD pointers. Each complete top directory
starts at relative byte 8, has 27 entries, ends at 338, and has next-IFD
zero. C5060WZ 1799 has the version-1-byte header, 32 entries ending at
398 and next zero, with neither top entry. C7070WZ 780 has a different
leading header and remains unknown under this explicit rule.

Thus a modern pointer-only lookup's null result is not evidence of
absent E-1 top entries. No value block is parsed here; whether inner
0x0620/0x0653 numeric fields occur in those legacy blocks remains unknown.
Absence is restricted to the exact top directory/path on 1799, not all
numeric occurrences in a file. Header-byte labels do not establish an
official private-format version or tag meanings.

## Original evidence

Lead #964 by @mszyndel publishes the first four rows after the #949
legacy follow-up protocol. Tool `tools/legacy_maker_directory.py` at
137fbb1 (#963) accepts only the exact leading OLYMP-NUL/01-00 or 02-00
bytes, directory at relative 8 and outer TIFF byte order. It reads the
entire bounded top directory with type/count, without signature search,
alternate-offset search or metadata value-block interpretation.

## Verification

Fresh run on 2026-11-24 after #964 publication/current clean scan. All
four original records repeat exactly, including 780's unsupported status.
Predeclared additional public 3540 supports the same 27-entry/type-7
layout, adding a third model. These samples were previously studied for
other questions; this is a procedural additional input, not blind capture
validation. Four generated tests cover both literal header bytes and
byte orders, present/absent/unknown, truncation and raw-overlap exclusion.
All five full hashes pass retained public CC0 records before/after.
Personal manifest rows already exist; no private-only numbers are used.

| Public identity | SHA-256 | Packing / initial zeros | Note bytes | Entries / end | 2040 type/count | 2050 type/count |
|---|---|---|---:|---|---|---|
| 1800 Olympus - E-1 - 16bit (4:3).ORF | `042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c` | packed-16 / 1 | 3038 | 27/338 | 7/1320 | 7/600 |
| 1799 Olympus - C5060WZ - 12bit (4:3).ORF | `3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd` | packed-12 / 2 | 1182 | 32/398 | absent top entry | absent top entry |
| 780 Olympus - C7070WZ - 12bit (4:3).ORF | `9d55506f9d6ee31d2d4c4b6df0dcd1d016d358b3e5eb4ed31edd7227dfefd5f8` | packed-12 / 2 | unknown | unknown | unknown | unknown |
| 2878 Olympus - E-300 - 16bit (4:3).ORF | `6d818dbff78b3e2efa4835f568d04733052b9211e6bc65b0a3748a841170e95b` | packed-12.8 / 1 | 3290 | 27/338 | 7/1524 | 7/624 |
| 3540 Olympus - E-500 - 16bit (4:3).ORF | `fa5a4759b2de2b573f59629ad1baf64ad04a85fb8fe1fb3cbf68e08a42fff4f0` | packed-12.8 / 1 | 3194 | 27/338 | 7/1308 | 7/624 |

All supported inputs have outer II byte order. Note sizes and directory
ends are bytes relative to each declared MakerNote. Out-of-line value
offset bases and block contents are not tested. The existing modern
leading-header reader remains unknown on these old layouts; no default
modern lookup or decoder behavior is changed by this inventory.

## Reproduce

At 137fbb1, using retained verified raw.pixls.us records with id, name,
sha256 and licence=CC0 (identities and hashes above):

```
python -I -B tools/test_legacy_maker_directory.py
python -I -B tools/legacy_maker_directory.py --records RETAINED_CC0_JSON --sample ID FILE
```

Repeat --sample for all five files. The output includes every top tag's
type/count, header, complete directory extent, next pointer and explicit
present_uninterpreted/absent_top_entry/unknown states. Unknown inputs must
not be changed to absence. No images, preview data or value bytes print.
The legacy blocks' internal structure and other leading headers remain
open on #949 and in V2 G4/V0 geometry gaps; independent declarations are
needed before assigning inner-field absence, offsets or semantics.
