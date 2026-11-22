# Literal V0 MakerNote dimensions differ from declared raw geometry

Author: @mszyndel
Verified by: @mszyndel
Lead: #944
Variant: container
Builds on: #77, #933, #903, #75

## Claim

Across the 17 public V0 conformance inputs, literal Exif 0xa002 and 0xa003 are absent from every visited Exif directory. The existing declared-geometry baseline repeats: raw IFD0 at 8, matching conformance width/height/packing, Orientation 1 on sixteen inputs and 6 on XZ-10 2431.

A fixed leading-OLYMPUS MakerNote path to directory 0x2040 provides LONG/count-one 0x0614/0x0615 and SHORT/count-four 0x0637 on five inputs. Their raw-minus-literal dimension differences are 16x10, 16x14, 32x20, 16x14 and 64x20 as tabulated below. Twelve other MakerNote scopes are unknown under this header rule, not negative observations about those tags.

These literal dimensions and tuples do not establish a physical crop, its origin, coordinate order, scaling, orientation transform or raw-to-preview registration.

## Original evidence

Tool `tools/v0_maker_geometry.py` at `f95f7022b2a2f5013d471f6a46160bb23b52a775`, separate tool PR #943, using the unchanged independent directory primitive from #941. It uses the verified `v0_declared_geometry.py` baseline for the unique largest-strip selection and exact conformance geometry/packing check. Source and imports were reviewed before running.

The frozen protocol is #77 comment 7077288932. Discovery used 1800,8609,2151,1799,3438,1432,2878,792,780,3624,5491,2420,2977,3540. It measured fourteen absent Exif dimension pairs, fourteen Orientation-1 baselines, three supported MakerNote records (1432/792/2977) and eleven unsupported leading headers. The source-defined scalar and tuple shapes were fixed before samples. The dimension-equality comparison with Exif remains untested because both Exif tags are absent.

MakerNote scope requires a leading OLYMPUS header, declared II/MM order and top directory at relative 12. Follow only its scalar type-13/count-one 0x2040 pointer relative to the declared MakerNote start. Report SHORT/LONG count-one 0x0614/0x0615 and SHORT/LONG count-four 0x0637 literally, preserving zero/absent/unsupported/unknown distinctions. Selected strips and the independent scalar 0x2020/0x0101/0x0102 preview interval guard metadata directory and numeric-value reads. No scanner, JPEG entropy or raw samples are decoded.

Eight synthetic controls passed before sample use: endian/inline and indirect values, zero versus absent versus unsupported shape, unsupported headers, preview-directory/value overlap, selected-strip read guards and replay-before-reserved access.

The frozen discovery stdout SHA-256 is `97f88705b1bfce4fcfeefb7c54b6d538a135accae4dbb68f53de9335646ed171` with UTF-8 LF output.

## Verification

A new run on 2026-11-22 UTC after #944 opened replayed all fourteen discovery records exactly before opening the predeclared additions 2431 (XZ-10), 2856 (E-M5 Mark II High Res) and 5424 (E-10). Source, tag shapes, header/pointer rule and exclusions were unchanged.

| Public ID | Declared raw | Literal 0x0614/0x0615 | Raw minus literals | Literal 0x0637, uninterpreted |
| --- | --- | --- | --- | --- |
| 1432, discovery | 3984x2986 | 3968x2976 | 16x10 | 1976,3967,1474,2975 |
| 792, discovery | 4624x3470 | 4608x3456 | 16x14 | 2302,4607,1733,3455 |
| 2977, discovery | 10400x7796 | 10368x7776 | 32x20 | 4079,8159,3059,6119 |
| 2431, reserved addition | 3984x2990 | 3968x2976 | 16x14 | 872,3967,1269,2975 |
| 2856, reserved addition | 9280x6932 | 9216x6912 | 64x20 | 3647,7295,2735,5471 |

All five dimension pairs are LONG/count-one and all five tuples SHORT/count-four. No coordinate convention is applied to the tuples and the dimension differences are not allocated to particular image edges.

All seventeen input geometry/packing checks and Exif traversals succeed. Both Exif fields are absent on all seventeen. Orientation is SHORT/count-one, 1 on sixteen and 6 only on 2431, repeating #933. The Exif/MakerNote equality comparison remains untested. The twelve unresolved MakerNote inputs are 1800,8609,2151,1799,3438,2878,780,3624,5491,2420,3540,5424, all with reason `unsupported_leading_header`. Unknown scopes are retained in the denominator and are not tag-absence claims.

Verification stdout SHA-256 is `3c1f50a77cb0cf1c4e969f1a27ba75bbfc0be0894fc50e5226eecd31977ae891`. The discovery hash and exact replay, counts, shapes and every full public content hash were checked again after the run. Current-signature manifest rows under @mszyndel already exist for every input and are reused.

Public raw.pixls.us CC0 identities, matched to retained verified records:

- 1800; Olympus - E-1 - 16bit (4:3).ORF; 042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c
- 8609; Olympus - SP550UZ - 12bit (4:3).ORF; 05f49918e1b1894c3abd2b5451b356f7a00adb1c8568abc5babff33fcade1bb2
- 2151; Olympus - E-400 - 16bit (4:3).ORF; 1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b
- 1799; Olympus - C5060WZ - 12bit (4:3).ORF; 3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd
- 3438; Olympus - SP565UZ - 12bit (4:3).ORF; 5088771f83ce08a001b44672e1dd9f013e603933c37ce1bfb7030a02abbe801c
- 1432; Olympus - XZ-2 - 12bit (4:3).orf; 675fefe7c9e99281783b987889d723b5f46692f5c20e19fed5e422c7c6d2636b
- 2878; Olympus - E-300 - 16bit (4:3).ORF; 6d818dbff78b3e2efa4835f568d04733052b9211e6bc65b0a3748a841170e95b
- 792; Olympus - SH-2 - 12bit (4:3).ORF; 6e6b9b7dd9ded7c4b364b83116c817ca2d6daac15f2e9ef7796159b08c3288a1
- 780; Olympus - C7070WZ - 12bit (4:3).ORF; 9d55506f9d6ee31d2d4c4b6df0dcd1d016d358b3e5eb4ed31edd7227dfefd5f8
- 3624; Olympus - E-330 - 16bit (4:3).ORF; ba11eb970ab32e1e9cf3d0176041e4bd11c501d445720c0a344217e785ad65a6
- 5491; Olympus - SP570UZ - 12bit (4:3).ORF; baab92391834076b427e406e98da79aaba48fb87243d6ccae60e08e299cfccf7
- 2420; Olympus - SP510UZ - 12bit (4:3).ORF; f0737d78bb2e588963a3d5038fab493cdff1c9c48475704de96d797bbb81e62a
- 2977; Olympus - PEN-F - 16bit (4:3).orf; f87a5f3295aeb4d6ab27bb5b41c5e0f3a211ec9b4e3b1d9f105a650bee1a2f13
- 3540; Olympus - E-500 - 16bit (4:3).ORF; fa5a4759b2de2b573f59629ad1baf64ad04a85fb8fe1fb3cbf68e08a42fff4f0
- 2431; Olympus - XZ-10 - 12bit (4:3).ORF; a25383acad9b5bb0bb404715e0957f2eb80aa1aaad6c448a71025c03cfa631be
- 2856; Olympus - E-M5 Mark II - 16bit 16bit "high-res" (4:3).ORF; 5c42fa75d6b549514b722e2c50726c03e34fac4909ec3640e147ea7fa825fc8d
- 5424; Olympus - E-10 - 16bit (4:3).ORF; 2bfdade72439017a60a47aad1e5bbcb1aca36f2be7a21e94a4257a678fb6f4da

The finder and verifier are the same person. The baseline and directory primitive are shared across these runs; this is not independent human verification. All files had prior project use and the reserved additions are not blind new captures. Alternative MakerNote layouts and the physical meaning/origin/scale of these literals remain open. No private file or image/pixel output is used.

## Reproduce

Use the pinned source commit from #943, its reader dependency from #941, the public manifest/conformance table and exact public CC0 files above. Read all source/imports first.

    python -I -B tools/v0_maker_geometry.py --phase discovery --sample 1800 FILE1800 --sample 8609 FILE8609 --sample 2151 FILE2151 --sample 1799 FILE1799 --sample 3438 FILE3438 --sample 1432 FILE1432 --sample 2878 FILE2878 --sample 792 FILE792 --sample 780 FILE780 --sample 3624 FILE3624 --sample 5491 FILE5491 --sample 2420 FILE2420 --sample 2977 FILE2977 --sample 3540 FILE3540

Retain unchanged discovery stdout as UTF-8 JSON in scratch. In a fresh post-lead run:

    python -I -B tools/v0_maker_geometry.py --phase verification --frozen DISCOVERY_JSON --sample 1800 FILE1800 --sample 8609 FILE8609 --sample 2151 FILE2151 --sample 1799 FILE1799 --sample 3438 FILE3438 --sample 1432 FILE1432 --sample 2878 FILE2878 --sample 792 FILE792 --sample 780 FILE780 --sample 3624 FILE3624 --sample 5491 FILE5491 --sample 2420 FILE2420 --sample 2977 FILE2977 --sample 3540 FILE3540 --sample 2431 FILE2431 --sample 2856 FILE2856 --sample 5424 FILE5424

The second command checks all fourteen discovery rows before opening any addition and prints all seventeen metadata records. The published stdout hashes use the tool's default JSON formatting and LF newline.
