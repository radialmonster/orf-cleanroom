# Figure 8 candidate counts on normal files reproduce

Author: @radialmonster
Verified by: @ruedbi
Lead: #196
Variant: unassigned
Builds on: #11, #29, #31, #32, #155
Reproduces: 2026-10-27--radialmonster--figure8-normal-count-reproduction
Partial: original four normal-file numeric counts, completed-table correlations and row-boundary residues under the stated category-plus-extend assumption

## Claim

The lead's reported normal-file counts and correlations reproduce for the literal 12-code candidate table and its ad hoc completed version, under the assumed category-plus-magnitude and extend rule. These are bounded tests of that assumption, not a patent transcription verification, established ORF codec or physical pixel mapping.

## Original evidence

Lead #196 used `tools/huffman_figure8_probe.py` at `47a4805fa1bfb8393c9fef45d9eb2281e85c98db`, start bit 45 and 156 candidate rows. For Table 1, its literal parse stops at the unused code after 3,483, 470, 51 and 2,608 values on ids 1993, 1995, 1997 and 1998 respectively. Adding the unused code with category 5 is an ad hoc completion, not part of the literal table. The lead reports its Table 1/2 completed-parse preview correlations as -0.12956/-0.16255, +0.07010/-0.02927, +0.07637/+0.05443 and +0.06454/+0.05349 respectively, and reports all eight row-boundary residues, including the 1995 Table 1 histogram below.

## Verification

Independent verification by @ruedbi on 2026-11-05 UTC using sample files in `ruedbi-orf-samples` (`python -I -B tools/huffman_figure8_probe.py`, Python 3.13 on Windows 11), following the self-verification by @radialmonster (2026-10-27).

Ran `tools/huffman_figure8_probe.py FILE --rows 156 --start 45 --missing-category 5 --sign extend` on the four normal-mode E-M1 Mark II CC0 files (1993, 1995, 1997, 1998). Every single metric reproduced exactly:
- 1993: Table 1 transcribed 3,483 values (`invalid=1`), completed r = -0.12956; Table 2 transcribed 2,484 values (`invalid=1`), completed r = -0.16255.
- 1995: Table 1 transcribed 470 values (`invalid=1`), completed r = +0.07010; Table 2 transcribed 236 values (`invalid=1`), completed r = -0.02927. Table 1 row-boundary residues 0 through 7 match `{0: 20, 1: 18, 2: 16, 3: 22, 4: 17, 5: 20, 6: 21, 7: 22}`.
- 1997: Table 1 transcribed 51 values (`invalid=1`), completed r = +0.07637; Table 2 transcribed 59 values (`invalid=1`), completed r = +0.05443.
- 1998: Table 1 transcribed 2,608 values (`invalid=1`), completed r = +0.06454; Table 2 transcribed 3,561 values (`invalid=1`), completed r = +0.05349.

All completed parses contain 817,440 values and all eight residues mod 8 occur across row boundaries.

| ID | Literal Table 1 / Table 2 values before invalid code | Completed Table 1 / Table 2 r |
|---:|---:|---:|
| 1993 | 3483 / 2484 | -0.12956 / -0.16255 |
| 1995 | 470 / 236 | +0.07010 / -0.02927 |
| 1997 | 51 / 59 | +0.07637 / +0.05443 |
| 1998 | 2608 / 3561 | +0.06454 / +0.05349 |
| 6343 | 806 / 1100 | +0.26451 / +0.45896 |

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` |
| 1995 | Olympus - E-M1MarkII - 16bit (4:3).ORI | `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` |
| 1997 | Olympus - E-M1MarkII - 16bit (4:3).ORI | `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a` |
| 1998 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71` |
| 6343 | OM System - OM-5 - 16bit (4:3).ORF | `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7` |

## Reproduce

```sh
python -I -B tools/huffman_figure8_probe.py FILE --rows 156 --start 45 --missing-category 5 --sign extend
```
