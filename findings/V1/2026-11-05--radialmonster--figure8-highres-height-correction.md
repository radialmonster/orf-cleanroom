# Correct High Res Figure 8 preview correlations

Author: @radialmonster
Verified by: @ruedbi
Lead: #527
Variant: V1
Builds on: #196
Reproduces: 2026-10-27--radialmonster--figure8-highres-height-correction
Corrects: 2026-10-21--radialmonster--figure8-negative-highres-e-m1-mark-ii

## Claim

The earlier finding's completed-table preview correlations used the wrong payload height for its two High Res files. Using each file's actual height changes those correlations as shown below; literal candidate counts and row-boundary residue histograms remain unchanged. This correction does not identify an ORF codec or physical pixel mapping.

## Original evidence

The earlier finding used `tools/huffman_figure8_probe.py` at `47a4805fa1bfb8393c9fef45d9eb2281e85c98db` with 156 rows, start bit 45, the literal candidate tables and assumed category-plus-extend rule. With the ad hoc category-5 completion, it reported Table 1 / Table 2 preview correlations +0.07266 / +0.07516 on 1994 and +0.06979 / +0.06904 on 1996. The tool hardcoded height 3912 for target sizing, selecting 12 preview DC rows despite both payloads being 10400x7792.

## Verification

Independent verification by @ruedbi on 2026-11-05 UTC using sample files in `ruedbi-orf-samples` (`python -I -B tools/huffman_figure8_probe.py`, Python 3.13 on Windows 11), following the self-verification by @radialmonster (2026-10-27).

Ran `tools/huffman_figure8_probe.py FILE --rows 156 --start 45 --missing-category 5 --sign extend` on the two High Res E-M1 Mark II CC0 files (1994 and 1996).
Both 400x300 preview grids use their first 6 rows (`round(156 * 300 / 7792) = 6`). Every reported metric reproduces exactly:
- 1994: Table 1 / Table 2 completed-table correlations are +0.09295 / +0.09540. Literal stop counts are 50129 / 3726 values (`invalid=1`), end bits 271685 / 43846. Row-mod-8 histograms match `{0: 20, 1: 12, 2: 19, 3: 19, 4: 21, 5: 19, 6: 25, 7: 21}` and `{0: 16, 1: 25, 2: 15, 3: 22, 4: 23, 5: 21, 6: 19, 7: 15}`. Completed values: 1,622,400.
- 1996: Table 1 / Table 2 completed-table correlations are +0.08876 / +0.08843. Literal stop counts are 79566 / 4359 values (`invalid=1`), end bits 430865 / 51269. Row-mod-8 histograms match `{0: 17, 1: 21, 2: 18, 3: 22, 4: 21, 5: 22, 6: 23, 7: 12}` and `{0: 26, 1: 23, 2: 14, 3: 18, 4: 20, 5: 21, 6: 14, 7: 20}`. Completed values: 1,622,400.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 1994 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23` |
| 1996 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2` |
| 6344 | OM System - OM-5 - 16bit (4:3).ORF | `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512` |

All three local hashes matched retained verified CC0 records, public identities and existing manifest rows.

## Reproduce

```sh
python -I -B tools/huffman_figure8_probe.py FILE --rows 156 --start 45 --missing-category 5 --sign extend
```
