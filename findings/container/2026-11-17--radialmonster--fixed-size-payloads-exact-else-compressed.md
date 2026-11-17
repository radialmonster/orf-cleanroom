# Fixed-size ORF payloads are exact; everything else is compressed

Author: @radialmonster
Verified by: @ruedbi
Lead: #28
Variant: container
Builds on: #10
Reproduces: 2026-10-19--radialmonster--fixed-size-payloads-exact-else-compressed

## Claim
On the CC0 Olympus / OM System ORF and ORI files on raw.pixls.us, a raw payload either has a size exactly equal to width x height x 12, 12.8 or 16 bits (`size_class` packed-12, packed-12.8, packed-16), or its size is data dependent (`variable`). Every file has compression tag 1, so the tag does not separate the two. In the current set (104 files, 63 distinct model spellings in the files' own tags):
- packed-12: 9 files, 9 models (C5060WZ, C7070WZ, SH-2, SP510UZ, SP550UZ, SP565UZ, SP570UZ, XZ-10, XZ-2).
- packed-12.8: 5 files, 5 models (E-300, E-330, E-500, and the High Res Shot files of E-M5MarkII and PEN-F).
- packed-16: 3 files, 3 models (E-1, E-10, E-400).
- variable: 87 files, 48 models, 6.02 to 8.79 bits per pixel. The maximum is above the 8.5 stated in the lead: the OM-1MarkII file 7269 (8172 wide High Res Shot) is 8.794, and 7267, 7803 are 8.45.
The model counts in the lead (65) add E-M5MarkII and PEN-F twice, because each has a packed High Res Shot file and a variable normal file; the distinct count is 63. The model lists of the lead otherwise match.

## Original evidence
Lead #28 by @radialmonster: `tools/orf_signature.py` (last changed in 67a763c at the time), census of every CC0 file at the time. The lead did not record file ids.

## Verification
Self-verification by @radialmonster, a new run on 2026-10-19 after the lead was posted (HEAD cc2d799, `orf_signature.py` last changed in 62c368a, Python 3.13). All 104 CC0 Olympus / OM files listed by `pixls_samples.py list` were freshly downloaded (SHA-256 verified by the tool) and `pixls_samples.py check` reported CC0 for each. The lead recorded no file ids, so I cannot say which of these it did not use; this is a whole-set run, with the file ids and hashes recorded below for the packed files and the extreme variable ones. Result:
- The packed counts and model lists (9, 5, 3 files) match the lead exactly. No model has files in more than one class except E-M5MarkII and PEN-F (High Res Shot packed, normal variable).
- All 87 variable files lie at least 4.0 bits per pixel away from 12.8, the nearest packing, so no near-miss size exists.
- Every file has compression tag 1; bits per sample 12 on the 9 packed-12 files, 16 on the other 95.
- Single-file models: 52 of the 63 model spellings have one CC0 file. That includes all 15 models whose only class is packed (E-300, E-330, E-500, E-1, E-10, E-400 and the nine packed-12 models), so those claims rest on one file each; no second CC0 file exists to check them, and no other model shows packed-12.8.
- Counts of files per model with more than one: E-M1MarkII 6, E-M1MarkIII 5, OM-1 5, OM-5 5, OM-1MarkII 9, OM-3 9, OM-5MarkII 5, E-M5MarkII 2, E-M5MarkIII 2, E-M10MarkIV 2, PEN-F 2; all consistent within the class rules above.

Files and sizes (raw.pixls.us id, model, payload size, bits per pixel, class, SHA-256), the 17 packed files plus the variable extremes:
- 1432 XZ-2 3984x2986, 12.000 bpp, packed-12, `675fefe7c9e99281783b987889d723b5f46692f5c20e19fed5e422c7c6d2636b`
- 1799 C5060WZ 2608x1949, 12.000 bpp, packed-12, `3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd`
- 1800 E-1 2624x1966, 16.000 bpp, packed-16, `042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c`
- 1994 E-M1MarkII 10400x7792, 6.021 bpp, variable, `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23`
- 1996 E-M1MarkII 10400x7792, 6.022 bpp, variable, `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2`
- 2151 E-400 3768x2840, 16.000 bpp, packed-16, `1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b`
- 2420 SP510UZ 3088x2309, 12.000 bpp, packed-12, `f0737d78bb2e588963a3d5038fab493cdff1c9c48475704de96d797bbb81e62a`
- 2431 XZ-10 3984x2990, 12.000 bpp, packed-12, `a25383acad9b5bb0bb404715e0957f2eb80aa1aaad6c448a71025c03cfa631be`
- 2856 E-M5MarkII 9280x6932, 12.800 bpp, packed-12.8, `5c42fa75d6b549514b722e2c50726c03e34fac4909ec3640e147ea7fa825fc8d`
- 2878 E-300 3360x2504, 12.800 bpp, packed-12.8, `6d818dbff78b3e2efa4835f568d04733052b9211e6bc65b0a3748a841170e95b`
- 2977 PEN-F 10400x7796, 12.800 bpp, packed-12.8, `f87a5f3295aeb4d6ab27bb5b41c5e0f3a211ec9b4e3b1d9f105a650bee1a2f13`
- 3438 SP565UZ 3664x2741, 12.000 bpp, packed-12, `5088771f83ce08a001b44672e1dd9f013e603933c37ce1bfb7030a02abbe801c`
- 3540 E-500 3360x2504, 12.800 bpp, packed-12.8, `fa5a4759b2de2b573f59629ad1baf64ad04a85fb8fe1fb3cbf68e08a42fff4f0`
- 3624 E-330 3280x2450, 12.800 bpp, packed-12.8, `ba11eb970ab32e1e9cf3d0176041e4bd11c501d445720c0a344217e785ad65a6`
- 5424 E-10 2256x1684, 16.000 bpp, packed-16, `2bfdade72439017a60a47aad1e5bbcb1aca36f2be7a21e94a4257a678fb6f4da`
- 5491 SP570UZ 3664x2741, 12.000 bpp, packed-12, `baab92391834076b427e406e98da79aaba48fb87243d6ccae60e08e299cfccf7`
- 7267 OM-1MarkII 10386x7792, 8.450 bpp, variable, `5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756`
- 7269 OM-1MarkII 8172x6132, 8.794 bpp, variable, `dd2a6c1c4ca4d86201207925477e2ea8e50ebd53d7df9117847093f5023540ec`
- 7803 OM-3 8172x6132, 8.446 bpp, variable, `63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0`
- 780 C7070WZ 3088x2309, 12.000 bpp, packed-12, `9d55506f9d6ee31d2d4c4b6df0dcd1d016d358b3e5eb4ed31edd7227dfefd5f8`
- 792 SH-2 4624x3470, 12.000 bpp, packed-12, `6e6b9b7dd9ded7c4b364b83116c817ca2d6daac15f2e9ef7796159b08c3288a1`
- 8609 SP550UZ 3088x2309, 12.000 bpp, packed-12, `05f49918e1b1894c3abd2b5451b356f7a00adb1c8568abc5babff33fcade1bb2`

The tool measures only the TIFF structure and decodes nothing.

Independent verification was conducted by @ruedbi on 2026-11-17 using `tools/orf_signature.py` with Python standard library (Python 3.8.10). Re-executing signature analysis on local files 1994 and 1996 confirmed variable payload dimensions 10400x7792, bits_per_sample 16, compression_tag 1, and bpp 6.021 and 6.022. Cross-referencing against the complete manifest confirmed the exact model groupings and counts across all size classes: packed-12 (9 models), packed-12.8 (5 models), packed-16 (3 models), and variable.

## Reproduce
    python tools/pixls_samples.py download ../orf-samples
    python tools/pixls_samples.py check ../orf-samples/*
    python tools/orf_signature.py ../orf-samples/* > sig.csv
    python -c "import csv,collections;m=collections.defaultdict(set);[m[r['size_class']].add(r['model']) for r in csv.DictReader(open('sig.csv'))];[print(k,len(m[k]),sorted(m[k])) for k in sorted(m)]"
