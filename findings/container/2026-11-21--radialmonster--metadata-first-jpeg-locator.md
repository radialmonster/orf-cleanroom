# Metadata-first JPEG locator matches six public Olympus preview extents

Author: @radialmonster
Verified by: @radialmonster
Lead: #920
Variant: container
Builds on: #155, #912, #916, 2026-11-21--radialmonster--maker-note-relative-jpeg-locator

## Claim

The fixed leading-header MakerNote locator derives all six named JPEG extents before consulting the scanner. The derived offset, length, and dimensions equal the separately selected scanner extent in each file. The two extensions add the original E-M1 and E-M5 Mark III.

## Original evidence

Discovery began 2026-11-21 at 00:18:38 UTC using `tools/preview_metadata_locator.py` at `e29899abda73da78cff723794c989ca47a9f07c7`. It follows IFD0 to the declared Exif MakerNote value, requires leading OLYMPUS magic and the top directory at MakerNote-relative byte 12, then follows the scalar type-13 0x2020 link. It adds scalar LONG/count-one 0x0101 to the declared MakerNote value start and takes scalar 0x0102 as length. The derived extent must fit in the envelope, exclude all consulted metadata spans, and pass bounded JPEG marker checks. The scanner runs afterward as a separate reference. There is no signature search, alternate base, fallback or entropy decoding. The frozen discovery JSON SHA-256 is `d7bc9e1d2ad67be92475b3cbb1b8037527a99612432347a72c228bc6a1348bea`.

All four original files have matching candidate and scanner records at offset 52224 and 3200 by 2400. The four lengths repeat in the verification table. A synthetic competing larger JPEG changes only the scanner choice and provides a test of the ordering.

Exact public raw.pixls.us CC0 identities, already in the manifest by SHA-256:

| ID | Catalogue name | SHA-256 |
| --- | --- | --- |
| 1994 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORF | f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 |
| 1995 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f |
| 3800 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORF | 1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f |
| 3802 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORI | 83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46 |
| 1051 predeclared extension | Olympus - E-M1 - 16bit (4:3).orf | 19ba17e778ae802d4039f0e88bb1cd68825780788b8058c479067e32b9a63eda |
| 3588 predeclared extension | OLYMPUS - E-M5 Mark III - 16bit (4:3).ORF | 24de6ac3bd5e668ee22fd0dbf2e344608949eb85f7342f28470ce709c9d51226 |

## Verification

A fresh run began at 2026-11-21 00:20:56 UTC after #920 was posted. It reproduced all four discovery records exactly before opening 1051 and 3588. A separately implemented TIFF/MakerNote and JPEG marker walk agreed on all six records. Both additions have prior project use and were absent from discovery. This is self-verification under the same GitHub account.

| ID | Both offsets | Both lengths in bytes | Both dimensions | Relation |
| --- | ---: | ---: | --- | --- |
| 1994 | 52224 | 1174738 | 3200 by 2400 | Exact match |
| 1995 | 52224 | 1054035 | 3200 by 2400 | Exact match |
| 3800 | 52224 | 970691 | 3200 by 2400 | Exact match |
| 3802 | 52224 | 958486 | 3200 by 2400 | Exact match |
| 1051 extension | 52224 | 922386 | 3200 by 2400 | Exact match |
| 3588 extension | 52224 | 978222 | 3200 by 2400 | Exact match |

All six selected offsets are the same. The results leave applicability on other layouts and varying starts, official tag semantics and physical preview-to-raw registration open.

## Reproduce

Use the exact local CC0 copies at `e29899abda73da78cff723794c989ca47a9f07c7`. Save the first command's unchanged aggregate JSON as DISCOVERY_JSON in a scratch folder. The verification phase requires the four unchanged original records before opening the additions.

```text
python -I -B tools/preview_metadata_locator.py --phase discovery --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802
python -I -B tools/preview_metadata_locator.py --phase verification --frozen DISCOVERY_JSON --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802 --sample 1051 FILE1051 --sample 3588 FILE3588
```
