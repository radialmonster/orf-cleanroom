# Fixed candidate prefix identity at nominal row starts

Author: @radialmonster
Verified by: @radialmonster
Lead: #691
Variant: unassigned
Builds on: #30, #646

## Claim

On two previously studied public files, none of the fixed candidate prefix values measured at nominal row offsets 0, 24 and 48 is identical across all 300 eligible rows, for any tested length 8, 16, 32 or 72 bits. This tests constant values at specified candidate starts; a fixed-length header can vary, and physical framing remains unknown.

## Original evidence

The lead measured 300 nominal rows of 1993 and 5283 with `tools/token_fixed_prefix_probe.py` at commit `f3db83551a68837c65565a176500f114d21ac47e`. The freshly reproduced cases are included below.

## Verification

After publication, both original cases were freshly reproduced and predeclared 600-row cases were measured on 1993, 5283, 1995 and 6343. The wider extent and additional files qualify verification; all were previously exposed and the verifier is the finder. Independent implementations matched all counts, endpoints and guard records exactly. The reference reused a previously authored literal parser; both share a TIFF locator and assisted the same human.

Parse literal stop-1 k=5 candidate words with no extra escape skipping, using original q+6 bit lengths and nominal W-token rows from token zero. At token offsets 0, 24 and 48 in each row, count exact identity of prefixes of 8, 16, 32 and 72 bits. Include only rows in which all three 72-bit windows fit inside the row's candidate bit endpoints; every cell uses the same eligible rows. Shorter lengths are comparison lengths and 72 is the historical length. No window values are printed. All requested prefixes completed.

| ID | Rows | Token offset | Bits | Eligible rows | Excluded rows | Distinct values | Modal multiplicity | Equal row pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1993 | 300 | 0 | 8 | 300 | 0 | 72 | 20 | 1135 |
| 1993 | 300 | 0 | 16 | 300 | 0 | 282 | 2 | 18 |
| 1993 | 300 | 0 | 32 | 300 | 0 | 300 | 1 | 0 |
| 1993 | 300 | 0 | 72 | 300 | 0 | 300 | 1 | 0 |
| 1993 | 300 | 24 | 8 | 300 | 0 | 90 | 16 | 957 |
| 1993 | 300 | 24 | 16 | 300 | 0 | 292 | 2 | 8 |
| 1993 | 300 | 24 | 32 | 300 | 0 | 300 | 1 | 0 |
| 1993 | 300 | 24 | 72 | 300 | 0 | 300 | 1 | 0 |
| 1993 | 300 | 48 | 8 | 300 | 0 | 93 | 16 | 808 |
| 1993 | 300 | 48 | 16 | 300 | 0 | 289 | 3 | 12 |
| 1993 | 300 | 48 | 32 | 300 | 0 | 300 | 1 | 0 |
| 1993 | 300 | 48 | 72 | 300 | 0 | 300 | 1 | 0 |
| 5283 | 300 | 0 | 8 | 300 | 0 | 177 | 4 | 164 |
| 5283 | 300 | 0 | 16 | 300 | 0 | 300 | 1 | 0 |
| 5283 | 300 | 0 | 32 | 300 | 0 | 300 | 1 | 0 |
| 5283 | 300 | 0 | 72 | 300 | 0 | 300 | 1 | 0 |
| 5283 | 300 | 24 | 8 | 300 | 0 | 175 | 5 | 181 |
| 5283 | 300 | 24 | 16 | 300 | 0 | 300 | 1 | 0 |
| 5283 | 300 | 24 | 32 | 300 | 0 | 300 | 1 | 0 |
| 5283 | 300 | 24 | 72 | 300 | 0 | 300 | 1 | 0 |
| 5283 | 300 | 48 | 8 | 300 | 0 | 191 | 4 | 140 |
| 5283 | 300 | 48 | 16 | 300 | 0 | 300 | 1 | 0 |
| 5283 | 300 | 48 | 32 | 300 | 0 | 300 | 1 | 0 |
| 5283 | 300 | 48 | 72 | 300 | 0 | 300 | 1 | 0 |
| 1993 | 600 | 0 | 8 | 600 | 0 | 133 | 29 | 3296 |
| 1993 | 600 | 0 | 16 | 600 | 0 | 556 | 3 | 48 |
| 1993 | 600 | 0 | 32 | 600 | 0 | 600 | 1 | 0 |
| 1993 | 600 | 0 | 72 | 600 | 0 | 600 | 1 | 0 |
| 1993 | 600 | 24 | 8 | 600 | 0 | 137 | 27 | 3146 |
| 1993 | 600 | 24 | 16 | 600 | 0 | 572 | 3 | 30 |
| 1993 | 600 | 24 | 32 | 600 | 0 | 600 | 1 | 0 |
| 1993 | 600 | 24 | 72 | 600 | 0 | 600 | 1 | 0 |
| 1993 | 600 | 48 | 8 | 600 | 0 | 136 | 25 | 2860 |
| 1993 | 600 | 48 | 16 | 600 | 0 | 565 | 3 | 37 |
| 1993 | 600 | 48 | 32 | 600 | 0 | 600 | 1 | 0 |
| 1993 | 600 | 48 | 72 | 600 | 0 | 600 | 1 | 0 |
| 5283 | 600 | 0 | 8 | 600 | 0 | 229 | 7 | 710 |
| 5283 | 600 | 0 | 16 | 600 | 0 | 597 | 3 | 4 |
| 5283 | 600 | 0 | 32 | 600 | 0 | 600 | 1 | 0 |
| 5283 | 600 | 0 | 72 | 600 | 0 | 600 | 1 | 0 |
| 5283 | 600 | 24 | 8 | 600 | 0 | 228 | 8 | 707 |
| 5283 | 600 | 24 | 16 | 600 | 0 | 598 | 2 | 2 |
| 5283 | 600 | 24 | 32 | 600 | 0 | 600 | 1 | 0 |
| 5283 | 600 | 24 | 72 | 600 | 0 | 600 | 1 | 0 |
| 5283 | 600 | 48 | 8 | 600 | 0 | 234 | 9 | 696 |
| 5283 | 600 | 48 | 16 | 600 | 0 | 597 | 2 | 3 |
| 5283 | 600 | 48 | 32 | 600 | 0 | 600 | 1 | 0 |
| 5283 | 600 | 48 | 72 | 600 | 0 | 600 | 1 | 0 |
| 1995 | 600 | 0 | 8 | 600 | 0 | 93 | 31 | 4189 |
| 1995 | 600 | 0 | 16 | 600 | 0 | 532 | 4 | 79 |
| 1995 | 600 | 0 | 32 | 600 | 0 | 600 | 1 | 0 |
| 1995 | 600 | 0 | 72 | 600 | 0 | 600 | 1 | 0 |
| 1995 | 600 | 24 | 8 | 600 | 0 | 142 | 26 | 2866 |
| 1995 | 600 | 24 | 16 | 600 | 0 | 563 | 3 | 39 |
| 1995 | 600 | 24 | 32 | 600 | 0 | 600 | 1 | 0 |
| 1995 | 600 | 24 | 72 | 600 | 0 | 600 | 1 | 0 |
| 1995 | 600 | 48 | 8 | 600 | 0 | 137 | 24 | 2630 |
| 1995 | 600 | 48 | 16 | 600 | 0 | 579 | 3 | 23 |
| 1995 | 600 | 48 | 32 | 600 | 0 | 600 | 1 | 0 |
| 1995 | 600 | 48 | 72 | 600 | 0 | 600 | 1 | 0 |
| 6343 | 600 | 0 | 8 | 600 | 0 | 215 | 14 | 984 |
| 6343 | 600 | 0 | 16 | 600 | 0 | 593 | 2 | 7 |
| 6343 | 600 | 0 | 32 | 600 | 0 | 600 | 1 | 0 |
| 6343 | 600 | 0 | 72 | 600 | 0 | 600 | 1 | 0 |
| 6343 | 600 | 24 | 8 | 600 | 0 | 218 | 11 | 916 |
| 6343 | 600 | 24 | 16 | 600 | 0 | 598 | 2 | 2 |
| 6343 | 600 | 24 | 32 | 600 | 0 | 600 | 1 | 0 |
| 6343 | 600 | 24 | 72 | 600 | 0 | 600 | 1 | 0 |
| 6343 | 600 | 48 | 8 | 600 | 0 | 214 | 13 | 1070 |
| 6343 | 600 | 48 | 16 | 600 | 0 | 596 | 3 | 5 |
| 6343 | 600 | 48 | 32 | 600 | 0 | 600 | 1 | 0 |
| 6343 | 600 | 48 | 72 | 600 | 0 | 600 | 1 | 0 |

A modal multiplicity below the eligible-row count rejects identical value only on that specified candidate offset, length and row set. Neighboring candidate-token starts share stop-bit alignment bias; counts are descriptive, not calibrated significance tests. This does not rule out a variable fixed-length header, a camera codec, or the unavailable historical private test.

## Reproduce

Retained verified public CC0 inputs:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`

At commit `f3db83551a68837c65565a176500f114d21ac47e`, verify identities and hashes, substitute local paths, and run:

```text
python -I -B tools/token_fixed_prefix_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --rows 300
python -I -B tools/token_fixed_prefix_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --rows 300
python -I -B tools/token_fixed_prefix_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --rows 600
python -I -B tools/token_fixed_prefix_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --rows 600
python -I -B tools/token_fixed_prefix_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --rows 600
python -I -B tools/token_fixed_prefix_probe.py --sample 6343 "OM System - OM-5 - 16bit (4:3).ORF" FILE6343 --rows 600
```

The tool emits aggregate counts and endpoints, not prefix bit values. Separately justified candidate origins and variable-header framing remain open on the existing corpus.
