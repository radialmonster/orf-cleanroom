# E-M1 Mark II payload dimensions and literal MakerNote values

Author: @radialmonster
Verified by: @radialmonster
Lead: #903
Variant: container
Builds on: #11, #163

## Claim

The declared payload dimensions and literal MakerNote values reported in #163 repeat on the four original E-M1 Mark II files. Two predeclared files give the same values as their respective normal and High Res groups. Under the conditional inclusive left/right/top/bottom interpretation only, the tuple spans exactly half of neither reported MakerNote dimension in any file.

## Original evidence

Discovery began at 2026-11-20 23:14:10 UTC with `tools/orf_active_area.py` at `b3993c3a566ded6f96d35f6d4032223adfd22b57`. It reads declared width and height from the IFD with the largest declared strip-byte total, and literal tags 0x0614, 0x0615 and 0x0637 from the Olympus MakerNote ImageProcessing directory. A separate directory walk checks the unique selected strip geometry, the Exif MakerNote value extent and observed nested offset convention, and the exact values in the saved report.

Public raw.pixls.us CC0 inputs, already recorded in the manifest by SHA-256:

| ID | Catalogue name | SHA-256 |
| --- | --- | --- |
| 1993 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORF | 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 |
| 1995 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f |
| 1997 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORI | 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a |
| 1996 discovery | Olympus - E-M1MarkII - 16bit (4:3).ORF | eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2 |
| 1998 predeclared extension | Olympus - E-M1MarkII - 16bit (4:3).ORF | 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 |
| 1994 predeclared extension | Olympus - E-M1MarkII - 16bit (4:3).ORF | f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 |

The original three normal inputs repeated 5240 by 3912 declared, 5184 by 3888 in 0x0614/0x0615, and 0x0637 values (2607, 5183, 1959, 3887). High Res 1996 repeated 10400 by 7792 declared, 10368 by 7776 in those tags, and (4104, 8159, 3084, 6119). Both match the corrected #163 report. The declared-minus-tag dimension differences are 56 by 24 and 32 by 16, respectively.

## Verification

A fresh run began at 2026-11-20 23:17:46 UTC after #903 was posted. It reproduced each original record exactly. The separately implemented metadata walk agreed on all six files. The extension files were previously studied elsewhere and were absent from this discovery run. This is self-verification under the same GitHub account.

| IDs | Declared payload | Literal 0x0614/0x0615 | Literal 0x0637 | Conditional inclusive spans | Half of literal dimensions |
| --- | --- | --- | --- | --- | --- |
| 1993, 1995, 1997 | 5240 by 3912 | 5184 by 3888 | 2607, 5183, 1959, 3887 | 2577 by 1929 | 2592 by 1944 |
| 1996 High Res | 10400 by 7792 | 10368 by 7776 | 4104, 8159, 3084, 6119 | 4056 by 3036 | 5184 by 3888 |
| 1998 normal, extension | 5240 by 3912 | 5184 by 3888 | 2607, 5183, 1959, 3887 | 2577 by 1929 | 2592 by 1944 |
| 1994 High Res, extension | 10400 by 7792 | 10368 by 7776 | 4104, 8159, 3084, 6119 | 4056 by 3036 | 5184 by 3888 |

The conditional comparison fails on both axes for both groups. The exact tag meanings, crop origin, and physical token-grid registration remain open. The files and their shared extraction convention leave generalization to other models and capture settings open.

## Reproduce

Validate the public CC0 identities and hashes, then use the pinned tool at `b3993c3a566ded6f96d35f6d4032223adfd22b57`.

```text
python -I -B tools/orf_active_area.py FILE_1993 FILE_1995 FILE_1997 FILE_1996
python -I -B tools/orf_active_area.py FILE_1993 FILE_1995 FILE_1997 FILE_1996 FILE_1998 FILE_1994
```

For tuple (a, b, c, d), compare twice the inclusive spans (b − a + 1, d − c + 1) with the respective 0x0614/0x0615 values. Keep any missing, malformed or ambiguous metadata lookup unresolved.
