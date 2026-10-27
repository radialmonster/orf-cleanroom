# Figure 8 candidate counts on normal files reproduce

Author: @radialmonster
Verified by: @radialmonster
Lead: #196
Variant: unassigned
Builds on: #11, #29, #31, #32, #155
Partial: original four normal-file numeric counts, completed-table correlations and row-boundary residues under the stated category-plus-extend assumption

## Claim

The lead's reported normal-file counts and correlations reproduce for the literal 12-code candidate table and its ad hoc completed version, under the assumed category-plus-magnitude and extend rule. These are bounded tests of that assumption, not a patent transcription verification, established ORF codec or physical pixel mapping.

## Original evidence

Lead #196 used `tools/huffman_figure8_probe.py` at `47a4805fa1bfb8393c9fef45d9eb2281e85c98db`, start bit 45 and 156 candidate rows. For Table 1, its literal parse stops at the unused code after 3,483, 470, 51 and 2,608 values on ids 1993, 1995, 1997 and 1998 respectively. Adding the unused code with category 5 is an ad hoc completion, not part of the literal table. The lead reports its Table 1/2 completed-parse preview correlations as -0.12956/-0.16255, +0.07010/-0.02927, +0.07637/+0.05443 and +0.06454/+0.05349 respectively, and reports all eight row-boundary residues, including the 1995 Table 1 histogram below.

## Verification

After the lead, the same human reran the fixed method at `8206efb97003f9a0a6dedd8019e48a86dec92017`; all inputs matched retained verified CC0 records, public names, manifest rows and local hashes. An independent bit-by-bit counter and completed-parse arithmetic check matched both tables' literal counts/end bits, correlations and row-residue histograms. These are computational cross-checks by agents assisting the same human, not independent-human verification.

| ID | Literal Table 1 / Table 2 values before invalid code | Completed Table 1 / Table 2 r |
|---:|---:|---:|
| 1993 | 3483 / 2484 | -0.12956 / -0.16255 |
| 1995 | 470 / 236 | +0.07010 / -0.02927 |
| 1997 | 51 / 59 | +0.07637 / +0.05443 |
| 1998 | 2608 / 3561 | +0.06454 / +0.05349 |
| 6343 | 806 / 1100 | +0.26451 / +0.45896 |

For all ten completed table/file cases, all eight residues occur among 156 candidate row starts. The Table 1 histogram for 1995, residues 0 through 7, is 20, 18, 16, 22, 17, 20, 21, 22, matching the lead. This is descriptive, not a formal uniformity test. All completed parses contain 817,440 values.

The predeclared additional OM-5 file 6343 was not in the original four-file lead but was previously studied. Its payload is 5240x3912; for 156 candidate rows the tool compares the first 12 rows of its 400x300 preview DC grid. Start 45 is a bit offset, not a preview-row offset. Its completed-table correlations are higher than the four original results; no general weak-correlation claim follows. Preview DC is a numeric camera-rendering reference, not ground truth, and the ad hoc complete code can parse arbitrary input. The earlier High Res finding's reported preview correlations have a separately identified height issue and remain to be corrected; this normal-file run does not resolve it.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` |
| 1995 | Olympus - E-M1MarkII - 16bit (4:3).ORI | `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` |
| 1997 | Olympus - E-M1MarkII - 16bit (4:3).ORI | `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a` |
| 1998 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71` |
| 6343 | OM System - OM-5 - 16bit (4:3).ORF | `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7` |

## Reproduce

At `8206efb97003f9a0a6dedd8019e48a86dec92017`, run once per local file matching the public identities and hashes above. The tool prints aggregate results and writes no files.

```sh
python -I -B tools/huffman_figure8_probe.py FILE --rows 156 --start 45 --missing-category 5 --sign extend
```
