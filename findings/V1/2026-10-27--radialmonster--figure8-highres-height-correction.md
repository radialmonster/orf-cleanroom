# Correct High Res Figure 8 preview correlations

Author: @radialmonster
Verified by: @radialmonster
Lead: #527
Variant: V1
Builds on: #196
Corrects: 2026-10-21--radialmonster--figure8-negative-highres-e-m1-mark-ii

## Claim

The earlier finding's completed-table preview correlations used the wrong payload height for its two High Res files. Using each file's actual height changes those correlations as shown below; literal candidate counts and row-boundary residue histograms remain unchanged. This correction does not identify an ORF codec or physical pixel mapping.

## Original evidence

The earlier finding used `tools/huffman_figure8_probe.py` at `47a4805fa1bfb8393c9fef45d9eb2281e85c98db` with 156 rows, start bit 45, the literal candidate tables and assumed category-plus-extend rule. With the ad hoc category-5 completion, it reported Table 1 / Table 2 preview correlations +0.07266 / +0.07516 on 1994 and +0.06979 / +0.06904 on 1996. The tool hardcoded height 3912 for target sizing, selecting 12 preview DC rows despite both payloads being 10400x7792.

## Verification

After lead #527 was posted, the same human reran the corrected tool at `299575a1863f893b85a3a5c5ca05f22796dfe2f7`. Both 400x300 preview grids now use their first 6 rows, since `round(156 * 300 / 7792) = 6`. Start 45 is a bit offset, not a preview-row offset. The Table 1 / Table 2 correlations are +0.09295 / +0.09540 on 1994 and +0.08876 / +0.08843 on 1996. Literal stop counts remain 50129 / 3726 and 79566 / 4359 respectively, each invalid at the unused code, and the four row-mod-8 histograms match the original finding. Each completed parse has 1,622,400 values.

Predeclared additional public id 6344 has 8200x6132 payload geometry and a 400x300 preview grid; the same method uses its first 8 DC rows. Its literal Table 1 / Table 2 stops are 1121 / 506; completed correlations are -0.49656 / -0.49714, with 1,279,200 values per table and all eight row-start residues represented. This file was previously studied. Its different scores demonstrate why these observations should not be generalized into a universal weak-correlation range.

An independent bitwise parse and aggregate correlation/row-residue calculation agreed with all three reports. This is self-verification by the same human, not independent-human verification. The ad hoc complete table is not established syntax; the camera preview is a numeric rendering reference, not ground truth. No alternative syntax, physical rows, values or round-trip are established.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 1994 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23` |
| 1996 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2` |
| 6344 | OM System - OM-5 - 16bit (4:3).ORF | `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512` |

All three local hashes matched retained verified CC0 records, public identities and existing manifest rows.

## Reproduce

At `299575a1863f893b85a3a5c5ca05f22796dfe2f7`, run once for each local file matching the public hash above. The tool prints aggregate values and writes no files.

```sh
python -I -B tools/huffman_figure8_probe.py FILE --rows 156 --start 45 --missing-category 5 --sign extend
```
