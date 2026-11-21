# MakerNote-relative JPEG locator reproduces on four E-M1 Mark II and III files

Author: @radialmonster
Verified by: @radialmonster
Lead: #916
Variant: container
Builds on: #155, #907, #912, 2026-11-20--radialmonster--preview-maker-note-length-correspondence

## Claim

For the four named E-M1 Mark II/III files, the declared Exif MakerNote value start plus the scalar LONG/count-one `0x2020/0x0101`, with length from `0x2020/0x0102`, gives the exact marker-bounded scanner JPEG extent. No examined scalar in 0x2020 equals the file-absolute start. The two OM System extensions remain unresolved under the tested MakerNote header lookup.

## Original evidence

Discovery began at 2026-11-21 00:06:29 UTC using `tools/preview_relative_locator.py` at `19d69be9bdb6a04237317cdcfd9a7d02908c2754`. It requires the existing checked MakerNote layout and bounds. It validates the scanner JPEG extent and excludes it from the metadata traversal. It searches only scalar LONG/count-one entries in 0x2020 for a common tag equal to scanner start minus declared MakerNote value start. File-absolute equality is a separate control. The frozen 0x0102 length matches on all four files. The sole common start candidate is 0x0101. A marker walk validates the candidate extent inside the MakerNote envelope independently of the comparison against scanner offset and length. The frozen discovery JSON SHA-256 is `41443ecf716f3760b676ea5eefbef65a4bdbaadcace4f0a0c4ebd3a434b09dda`.

Exact public raw.pixls.us CC0 files, already in the manifest by SHA-256:

| ID | Catalogue name | SHA-256 |
| --- | --- | --- |
| 1994 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORF | f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 |
| 1995 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f |
| 3800 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORF | 1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f |
| 3802 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORI | 83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46 |
| 6343 predeclared extension | OM System - OM-5 - 16bit (4:3).ORF | ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7 |
| 5283 predeclared extension | OM System - OM-1 - 16bit (4:3).ORF | bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b |

## Verification

A fresh run began 2026-11-21 at 00:09:03 UTC after #916 was posted. The original four aggregate records and frozen candidate match exactly before either predeclared extension is opened. A separately implemented TIFF/MakerNote and JPEG marker walk agrees on the resolved records and independently leaves both extension inputs unresolved. The extensions have prior project use and were absent from discovery. This is self-verification under the same GitHub account.

| ID | Calculated and selected offset | Calculated and selected length | Outcome |
| --- | ---: | ---: | --- |
| 1994 | 52224 | 1174738 | Exact marker-bounded extent match |
| 1995 | 52224 | 1054035 | Exact marker-bounded extent match |
| 3800 | 52224 | 970691 | Exact marker-bounded extent match |
| 3802 | 52224 | 958486 | Exact marker-bounded extent match |
| 6343 extension | Unresolved | Unresolved | `maker_header` |
| 5283 extension | Unresolved | Unresolved | `maker_header` |

The extension exit status is 1 because the required unique MakerNote header was unresolved in both additions. The tool distinguishes an unresolved lookup from a calculable extent disagreement. Each resolved file has the same selected offset, leaving transfer across varying offsets open alongside other metadata layouts, documented tag semantics and physical registration.

## Reproduce

Use the exact local CC0 inputs at `19d69be9bdb6a04237317cdcfd9a7d02908c2754`. Save the first command's unchanged aggregate JSON as DISCOVERY_JSON in a scratch folder. The second command verifies the original rows and candidate set before opening either extension.

```text
python -I -B tools/preview_relative_locator.py --phase discovery --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802
python -I -B tools/preview_relative_locator.py --phase verification --frozen DISCOVERY_JSON --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802 --sample 6343 FILE6343 --sample 5283 FILE5283
```
