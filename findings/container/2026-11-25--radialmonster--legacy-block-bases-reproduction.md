# Two bounded legacy offset candidates fail on E-1, E-300 and reserved E-500

Author: @radialmonster
Verified by: @radialmonster
Lead: #982
Variant: container
Builds on: #949, #964, #978

## Claim

The two fixed interpretations of the type-7 value slots both fail the common containment requirement on E-1 1800 and E-300 2878. The result extends to reserved E-500 3540. The file-absolute candidate for 0x2050 ends 36 bytes beyond the declared MakerNote on all three. This is not evidence that the official format uses either base or a larger envelope.

## Original evidence

Lead #982 used the bounded leading OLYMP top-directory path from #964. It requires both type-7 ranges to fit inside the note while remaining outside its header and top directory and outside the declared raw strips, with no overlap between the ranges. It tests file byte zero and the declared note start as the only bases. The fixed block-relative inner-directory check is conditional on exactly one common base qualifying.

## Verification

On 2026-11-25 after #982 was posted and scanned, a fresh run on the four original files reproduced the entire saved aggregate. The equality gate passed at 17:46:55 UTC before reserved 3540 was opened. Both program runs exited zero without stderr. All files were matched to retained full public CC0 hashes.

| Public ID and camera | SHA-256 |
| --- | --- |
| 1800 Olympus E-1 | `042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c` |
| 2878 Olympus E-300 | `6d818dbff78b3e2efa4835f568d04733052b9211e6bc65b0a3748a841170e95b` |
| 1799 Olympus C5060WZ | `3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd` |
| 780 Olympus C7070WZ | `9d55506f9d6ee31d2d4c4b6df0dcd1d016d358b3e5eb4ed31edd7227dfefd5f8` |
| 3540 Olympus E-500 | `fa5a4759b2de2b573f59629ad1baf64ad04a85fb8fe1fb3cbf68e08a42fff4f0` |

Candidate ranges below are half-open file byte intervals, not claimed ownership spans. Each row failed both candidates due to being outside the declared envelope.

| ID | Declared MakerNote | Absolute 0x2040 and 0x2050 | MakerNote-relative 0x2040 and 0x2050 |
| --- | --- | --- | --- |
| 1800 | [788,3826) | [1936,3256), [3262,3862) | [2724,4044), [4050,4650) |
| 2878 | [788,4078) | [1960,3484), [3490,4114) | [2748,4272), [4278,4902) |
| 3540 reserved | [788,3982) | [2080,3388), [3394,4018) | [2868,4176), [4182,4806) |

The E-500 note has 3194 bytes, the top table ends at relative byte 338, and the two entries are type 7 with counts 1308 and 624, matching the older directory result. Its proposed absolute 0x2050 end is 4018, which is 36 past 3982. Both proposed note-relative ranges end outside the note.

The controls preserve exact distinctions. File 1799 has neither exact top entry under the accepted header rule. File 780 still has an unsupported leading layout. An independent bounded TIFF reader rederived the E-500 declaration and both ranges. This is same-account verification. No candidate qualified for the inner check. No inner values, official base, ownership of the exterior span, or broader absence inference are established.

## Reproduce

Use `tools/legacy_block_shape.py` at `855bd304fd51000aa7a26cf13ee491c7dc782255`, with the retained exact CC0 identities above. Each input already has manifest rows.

    python -I -B tools/test_legacy_block_shape.py
    python -I -B tools/legacy_block_shape.py --sample 1800 FILE1800 --sample 2878 FILE2878 --sample 1799 FILE1799 --sample 780 FILE780
    python -I -B tools/legacy_block_shape.py --cohort reserved --sample 3540 FILE3540

Compare both declared-candidate intervals and their statuses, preserving the unsupported and absent cases. No private files were used.
