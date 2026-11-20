# MakerNote scalar length correspondence on six E-M1 Mark II and III files

Author: @radialmonster
Verified by: @radialmonster
Lead: #912
Variant: container
Builds on: #155, #907, 2026-11-20--radialmonster--preview-outer-tiff-declaration-audit

## Claim

The literal LONG/count-one tag 0x0102 in MakerNote path 0x2020 equals the marker-bounded scanner JPEG length on the four discovery and two extension files. Each declared MakerNote envelope contains the JPEG. None of the checked scalars equals its file-absolute start at 52,224.

## Original evidence

Discovery began at 2026-11-20 23:53:19 UTC under the frozen protocol and correction in #155. The first tool revision (#910) left the two private paths unresolved because it rejected any JPEG overlap with the declared MakerNote envelope. The corrected `tools/preview_scalar_correspondence.py` at `b5d2ab9f649d36db242c53f5d2da6a1d86e35504` checks the marker-bounded JPEG extent independently of the Exif declaration. It excludes that byte range from header search and each consulted directory while preserving MakerNote-relative offsets. Within IFD0 and the existing nested paths 0x2020 and 0x2040, it compares only scalar LONG entries with the scanner's file-absolute start and marker-bounded length. The saved discovery JSON SHA-256 is `b47bd03554263828764dc44b8c216d9d8db6d6255bc8f465a580efb000ed8f40`.

Each of the original four files has 7, 6, and 3 inspected scalar LONG entries in those respective paths. The sole common length match is path 0x2020, tag 0x0102. No absolute-start match occurs. The selected lengths differ across the four files, as listed in the table below.

Exact public raw.pixls.us CC0 inputs, already in the manifest by SHA-256:

| ID | Catalogue name | SHA-256 |
| --- | --- | --- |
| 1994 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORF | f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 |
| 1995 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f |
| 3800 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORF | 1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f |
| 3802 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORI | 83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46 |
| 1998 predeclared extension | Olympus - E-M1MarkII - 16bit (4:3).ORF | 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 |
| 3801 predeclared extension | Olympus - E-M1MarkIII - 16bit (4:3).ORF | e9a21175493e9d9e5653aa91f1bd6fbf421aba42b59b4ffe7cd1f7cac2de385c |

## Verification

A fresh run began at 2026-11-20 23:55:32 UTC after #912 was posted. It confirmed all four original records and the frozen candidate map before opening the two predeclared additions. These were previously studied elsewhere and were absent from discovery. A separately implemented TIFF and JPEG marker walk agreed on all six. This is self-verification under the same GitHub account.

| ID | Scanner JPEG length in bytes | 0x2020/0x0102 equals length | Absolute-start matches | MakerNote envelope |
| --- | ---: | --- | ---: | --- |
| 1994 | 1174738 | Yes | 0 | Contains JPEG |
| 1995 | 1054035 | Yes | 0 | Contains JPEG |
| 3800 | 970691 | Yes | 0 | Contains JPEG |
| 3802 | 958486 | Yes | 0 | Contains JPEG |
| 1998 extension | 1061926 | Yes | 0 | Contains JPEG |
| 3801 extension | 933606 | Yes | 0 | Contains JPEG |

The literals are a length correspondence for the named files. The test leaves the tag's documented purpose, relative offsets, any association with other paths, and physical preview-to-raw registration open. It uses no JPEG entropy decoding or compressed raw parse.

## Reproduce

Use the exact public CC0 inputs and pinned commit `b5d2ab9f649d36db242c53f5d2da6a1d86e35504`. Save the first command's unchanged aggregate JSON as DISCOVERY_JSON in a scratch folder. The second command checks the original rows and candidate set before reading the additions.

```text
python -I -B tools/preview_scalar_correspondence.py --phase discovery --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802
python -I -B tools/preview_scalar_correspondence.py --phase verification --frozen DISCOVERY_JSON --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802 --sample 1998 FILE1998 --sample 3801 FILE3801
```
