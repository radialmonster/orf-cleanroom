# Direct block-choice BYTE tag absent in the visited public ORF directory graphs

Author: @radialmonster
Verified by: @radialmonster
Lead: #900
Variant: container
Builds on: #197, #829

## Claim

The visited TIFF directory graphs of public ORF IDs 1993, 1994, 1997 and 7265 contain no TIFF BYTE entry with either exact element count in the tested full-image 8-by-8 table-choice example. Each file has an unvisited MakerNote.

## Original evidence

Figure 9 of [Japanese patent JP4493551B2](https://patentimages.storage.googleapis.com/c2/26/72/4767bd56c305cc/JP4493551B2.pdf) gives an illustrative 8-by-8 block grid. Figures 20–21 and paragraphs 0079–0090 describe an example of recording per-block coding-table choices. This test combines the illustrated geometry with a single direct TIFF BYTE entry. It uses the declared dimensions from the unique IFD with the greatest declared strip byte total. For a full exact-divisible grid, N = (W / 8) times (H / 8). The exact element counts for unpacked and packed choices are N and floor(N / 4) + 1. For a valid exact-count entry that does not overlap the selected strips, the probe checks assigned values 0 through 2, including both packed slot orders and ignoring unassigned slots.

The probe follows IFD0, next IFDs, declared SubIFDs and standard Exif, GPS and Interoperability links. Private nested MakerNotes are outside the visited scope. It uses no candidate-token parser. Discovery started on 2026-11-20 at 23:05:39 UTC using `tools/patent_tag_inventory.py` at `0c15306b4b65902369794a8c213ad9e1f20a7eca`. IDs 1993 and 1994 each had three visited IFDs, one unvisited MakerNote and one in-bounds BYTE entry. Neither had an exact-count entry.

All inputs are public raw.pixls.us CC0 files and are already in the manifest by SHA-256.

| ID | Catalogue name | SHA-256 |
| --- | --- | --- |
| 1993 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORF | 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 |
| 1994 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORF | f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 |
| 1997 extension | Olympus - E-M1MarkII - 16bit (4:3).ORI | 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a |
| 7265 extension | OM System - OM-1 Mark II - 16bit (4:3).orf | c7bd43b29ed89542058534b867fa894b8550d1960503cf4b4cb9f5912fd242b3 |

## Verification

A fresh run began on 2026-11-20 at 23:07:14 UTC after lead #900 was posted. It reproduced both original aggregate records exactly and added the two predeclared public files 1997 and 7265, previously studied elsewhere but absent from discovery. A separately implemented directory and entry walk agreed on all four results. The same GitHub account performed both runs.

| ID | Declared width by height | N | Packed bytes | IFDs visited | MakerNotes unvisited | BYTE entries | Out of bounds | Exact-count entries |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1993 | 5240 by 3912 | 320295 | 80074 | 3 | 1 | 1 | 0 | 0 |
| 1994 | 10400 by 7792 | 1266200 | 316551 | 3 | 1 | 1 | 0 | 0 |
| 1997 | 5240 by 3912 | 320295 | 80074 | 3 | 1 | 1 | 0 | 0 |
| 7265 | 10400 by 7792 | 1266200 | 316551 | 3 | 1 | 2 | 0 | 0 |

The class-value checks had no exact-count entries to evaluate. The grant gives illustrative choices, so this absence is limited to the tested direct BYTE representation in the visited directories. Other tag types, block sizes, offset conventions, private MakerNotes, and embedded or split metadata remain outside scope. The test supplies no coded-sample boundary and does not establish which codec any file uses.

## Reproduce

Use the exact CC0 copies above at `0c15306b4b65902369794a8c213ad9e1f20a7eca`. The tool checks full-file hashes and prints aggregate JSON.

```text
python -I -B tools/patent_tag_inventory.py --phase discovery --sample 1993 FILE_1993 --sample 1994 FILE_1994
python -I -B tools/patent_tag_inventory.py --phase verification --sample 1993 FILE_1993 --sample 1994 FILE_1994 --sample 1997 FILE_1997 --sample 7265 FILE_7265
```
