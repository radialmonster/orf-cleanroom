# Correct the E-300 identity in the legacy MakerNote top-directory finding

Author: @radialmonster
Verified by: @radialmonster
Lead: #977
Variant: container
Builds on: #964, #949
Corrects: 2026-11-24--mszyndel--legacy-maker-top-byte-blocks

## Claim

The public raw.pixls.us file 2878 is from an Olympus E-300, not an SP350. This corrects the earlier claim prose. Its source table already identifies the E-300 at that hash. The top-directory measurements are unchanged and were originally found and verified by @mszyndel in #964.

## Original evidence

Lead #977 reports literal TIFF Make and Model, read as ASCII with trailing padding removed, as `OLYMPUS IMAGING CORP.` and `E-300` on the hash-pinned CC0 file `Olympus - E-300 - 16bit (4:3).ORF`. The selected payload is 3360 by 2504, packed-12.8 by size, with compression tag 1. The earlier finding used this exact file in its legacy MakerNote comparison.

## Verification

After #977 was published and scanned on 2026-11-25, a fresh signature run repeated the name, full hash, dimensions, size classification and compression tag. A separate bounded IFD0 reader confirmed ASCII type 2 for Make (tag 0x010f, count 24) and Model (tag 0x0110, count 17), with spaces before the terminating NUL. This is same-account verification.

The wider check ran the original legacy reader on all five retained CC0 files from #964. It reproduced every published table row, including the unsupported case. Header values in the table describe literal bytes; they are not official format versions.

| Public ID and identity | SHA-256 | Packing / initial zero bits | MakerNote bytes | Top entries / end | 0x2040 type/count | 0x2050 type/count |
| --- | --- | --- | ---: | --- | --- | --- |
| 1800 Olympus E-1 | `042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c` | packed-16 / 1 | 3038 | 27/338 | 7/1320 | 7/600 |
| 1799 Olympus C5060WZ | `3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd` | packed-12 / 2 | 1182 | 32/398 | absent at top | absent at top |
| 780 Olympus C7070WZ | `9d55506f9d6ee31d2d4c4b6df0dcd1d016d358b3e5eb4ed31edd7227dfefd5f8` | packed-12 / 2 | unknown | unknown | unknown | unknown |
| 2878 Olympus E-300 | `6d818dbff78b3e2efa4835f568d04733052b9211e6bc65b0a3748a841170e95b` | packed-12.8 / 1 | 3290 | 27/338 | 7/1524 | 7/624 |
| 3540 Olympus E-500 | `fa5a4759b2de2b573f59629ad1baf64ad04a85fb8fe1fb3cbf68e08a42fff4f0` | packed-12.8 / 1 | 3194 | 27/338 | 7/1308 | 7/624 |

On the four supported notes, the outer order is little-endian, the bounded top directory begins eight bytes into the note and the next-directory pointer is zero. The leading bytes are `4f4c594d50000200` on 1800, 2878 and 3540 and `4f4c594d50000100` on 1799. The literal-header rule still does not identify the layout of file 780. The type-7 entries describe byte blocks, not type-13 pointers. The blocks' internal meanings, offset bases, and physical geometry remain unknown.

## Reproduce

Use `tools/orf_signature.py` at `9f748fdcf9dbf0bf8ef2cecff7c8992c2314c982` on file 2878 after matching its full local hash to the public CC0 identity. Use `tools/legacy_maker_directory.py` at `feff000c13e3fa5273538432f53dbdddc9033534` with the five CC0 records. For each object in the records JSON array supply `id`, full `name`, `sha256` and `licence` from the matching manifest row. Include all five inputs, with one `--sample ID FILE` argument per file.

    python -I -B tools/orf_signature.py FILE2878
    python -I -B tools/test_legacy_maker_directory.py
    python -I -B tools/legacy_maker_directory.py --records RETAINED_CC0_JSON --sample 1800 FILE1800 --sample 1799 FILE1799 --sample 780 FILE780 --sample 2878 FILE2878 --sample 3540 FILE3540

Compare the model after ASCII padding is removed and the exact table above. All inputs are public CC0 and already listed in the manifest. No numbers rely on private files.
