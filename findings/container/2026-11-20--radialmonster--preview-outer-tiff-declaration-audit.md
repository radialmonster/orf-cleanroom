# Scanner-selected preview extents and outer TIFF declarations on six ORFs

Author: @radialmonster
Verified by: @radialmonster
Lead: #907
Variant: container
Builds on: #155, #313, 2026-10-22--radialmonster--preview-dc-pair-screen-reproduction

## Claim

The six named public E-M1 Mark II and III files each have a 3200-by-2400 scanner-selected JPEG starting at 52,224, with varying marker-bounded lengths. The outer IFD0/next-IFD/SubIFD graph spans one IFD for each file and contains no direct TIFF 513/514 pair for these previews.

## Original evidence

Discovery began at 2026-11-20 23:33:03 UTC using `tools/preview_ifd_extent_probe.py` at `13d282faba9066f923dff3757886e44bd645e1fc`. The tool uses the current `jpeg_dc.find_preview` selection and checks the bounded SOI, SOF0, SOS, segment lengths and EOI. It inventories scalar LONG JPEGInterchangeFormat (513) and JPEGInterchangeFormatLength (514) in the outer IFD0/next-IFD/SubIFD graph as defined in [TIFF 6.0 section 22](https://www.itu.int/itudoc/itu-t/com16/tiff-fx/docs/tiff6.pdf). It does not decode entropy. The older #313 calculation used the selected offset and did not use its scanner's returned length. Here lengths come from the current scanner and were checked separately through EOI.

The original four files had one reached directory each and zero pairs, zero disabled offsets and zero orphan lengths. The selected 3200-by-2400 previews all started at 52,224. Their measured lengths repeat in the table below.

All inputs are public raw.pixls.us CC0 files already in the manifest by SHA-256.

| ID | Catalogue name | SHA-256 |
| --- | --- | --- |
| 1994 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORF | f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 |
| 1995 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f |
| 3800 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORF | 1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f |
| 3802 discovery | Olympus - E-M1MarkIII - 16bit (4:3).ORI | 83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46 |
| 1996 predeclared extension | Olympus - E-M1MarkII - 16bit (4:3).ORF | eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2 |
| 3804 predeclared extension | Olympus - E-M1MarkIII - 16bit (4:3).ORI | d831692b608471ad64667eb2485bab553de0ddb9366d384c4ecb731092b5dc42 |

## Verification

A fresh run began at 2026-11-20 23:35:13 UTC after lead #907 was posted. It reproduced the four original records exactly and added predeclared 1996 and 3804. Both were previously studied elsewhere and were absent from discovery. A separate TIFF and marker walk agreed on all six. The same GitHub account performed both runs.

| ID | Scanner offset | Marker-bounded length in bytes | Dimensions | Outer IFDs reached | Positive 513/514 pairs |
| --- | ---: | ---: | --- | ---: | ---: |
| 1994 | 52224 | 1174738 | 3200 by 2400 | 1 | 0 |
| 1995 | 52224 | 1054035 | 3200 by 2400 | 1 | 0 |
| 3800 | 52224 | 970691 | 3200 by 2400 | 1 | 0 |
| 3802 | 52224 | 958486 | 3200 by 2400 | 1 | 0 |
| 1996 extension | 52224 | 1173671 | 3200 by 2400 | 1 | 0 |
| 3804 extension | 52224 | 1056123 | 3200 by 2400 | 1 | 0 |

The two additions also had zero disabled offsets and orphan lengths. Private MakerNotes, nested JPEG Exif and other declaration types remain outside scope. A shared scanner offset on these named files leaves any universal fixed-offset rule and preview-to-raw registration open.

## Reproduce

Use the exact CC0 files at pinned commit `13d282faba9066f923dff3757886e44bd645e1fc`. The tool checks hashes and prints aggregate JSON.

```text
python -I -B tools/preview_ifd_extent_probe.py --phase discovery --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802
python -I -B tools/preview_ifd_extent_probe.py --phase verification --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802 --sample 1996 FILE1996 --sample 3804 FILE3804
```
