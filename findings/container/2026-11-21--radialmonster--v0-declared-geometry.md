# The V0 conformance cohort lacks the probed explicit DNG crop fields

Author: @radialmonster
Verified by: @radialmonster
Lead: #933
Variant: container
Builds on: #75, #77, 2026-10-19--radialmonster--independent-v0-hash-agreement

## Claim

All 17 public V0 conformance files have a supported literal Orientation field in the selected raw IFD, which is also IFD0 at byte 8. Sixteen report value 1 and XZ-10 2431 reports value 6. DNGVersion is absent from IFD0. DefaultScale, DefaultCropOrigin, DefaultCropSize and ActiveArea are absent from the selected raw IFD on all 17.

The result concerns only these explicit tags in these directories. Other crop declarations and physical raw-to-preview alignment remain open.

## Original evidence

Discovery started at 01:06:10 UTC on 2026-11-21 using tools/v0_declared_geometry.py at 48177dcaac97ac2e6c41b7699f5860bb0c0fa24c. Before the run, #77 comment 7054737341 fixed the 14 discovery and three verification identities by public CC0 name, SHA-256 and geometry. The files' public names and hashes are in samples/conformance-V0.csv and samples/manifest.csv at that commit. The canonical numeric-ID-ordered UTF-8 LF roster id|name|sha256|packing|width|height hashes to 27bba849e69a0a73502448cdbbe550a2432c56cb80ee7792a4027703b25e0484.

The tool selects the unique largest total strip declaration in the bounded outer TIFF graph and requires the selected dimensions and packing to match conformance. It checks whether visited directories and tables overlap a selected strip before reporting values. It inventories explicit tags and compares their type and count with the supported forms. The DNG syntax reference is [Adobe DNG 1.6, pages 28, 29 and 42](https://paulbourke.net/dataformats/dng/dng_spec_1_6_0_0.pdf).

The 14 discovery files are 1800, 8609, 2151, 1799, 3438, 1432, 2878, 792, 780, 3624, 5491, 2420, 2977 and 3540. The eight packed-12, four packed-12.8 and two packed-16 files all matched their conformance geometry. Orientation was 1 in all 14. The five checked DNG fields were absent in their respective directories on all 14. Frozen discovery JSON SHA-256 was 2fc2637dc7ac804bb415ac1c3758b0ab76539b1392dafab47c619a151d9a4a7f.

## Verification

A fresh run at 01:08:31 UTC on 2026-11-21 after #933 opened reproduced every frozen row before opening the three reserved files. Those files had prior project use but were absent from discovery. Verification used the same account, with a separate aggregate check of roster, geometry, tag status and exact replay.

| Reserved ID | Public catalogue name | SHA-256 | Raw IFD | Orientation |
| --- | --- | --- | ---: | ---: |
| 2431 | Olympus - XZ-10 - 12bit (4:3).ORF | a25383acad9b5bb0bb404715e0957f2eb80aa1aaad6c448a71025c03cfa631be | 8 | 6 |
| 2856 | Olympus - E-M5 Mark II - 16bit 16bit "high-res" (4:3).ORF | 5c42fa75d6b549514b722e2c50726c03e34fac4909ec3640e147ea7fa825fc8d | 8 | 1 |
| 5424 | Olympus - E-10 - 16bit (4:3).ORF | 2bfdade72439017a60a47aad1e5bbcb1aca36f2be7a21e94a4257a678fb6f4da | 8 | 1 |

All 17 selected raw IFDs were IFD0, so Orientation was measured once per file even though the report covers both scopes. Each Orientation was SHORT/count-one. DNGVersion 50706 was absent in IFD0 on all 17. Each of 50718, 50719, 50720 and 50829 was absent from the selected raw IFD on all 17. All 17 rows matched conformance geometry and packing, with nine packed-12, five packed-12.8 and three packed-16. Verification JSON SHA-256 was d0bb213d7eb648a55f40cd89d52956943704bb5c869026f6de793d1a8fd720b4.

The XZ-10 difference constrains any assumption of uniform Orientation across these samples. This inventory leaves the raw crop and its relationship to the physical JPEG geometry open.

## Reproduce

Use commit 48177dcaac97ac2e6c41b7699f5860bb0c0fa24c and the exact local CC0 copies. Save discovery stdout as UTF-8 JSON in scratch. The report hashes above use LF line endings.

    python -I -B tools/v0_declared_geometry.py --phase discovery --sample 1800 FILE1800 --sample 8609 FILE8609 --sample 2151 FILE2151 --sample 1799 FILE1799 --sample 3438 FILE3438 --sample 1432 FILE1432 --sample 2878 FILE2878 --sample 792 FILE792 --sample 780 FILE780 --sample 3624 FILE3624 --sample 5491 FILE5491 --sample 2420 FILE2420 --sample 2977 FILE2977 --sample 3540 FILE3540

For verification, replace --phase discovery with --phase verification --frozen DISCOVERY_JSON and append --sample 2431 FILE2431 --sample 2856 FILE2856 --sample 5424 FILE5424 in that order.
