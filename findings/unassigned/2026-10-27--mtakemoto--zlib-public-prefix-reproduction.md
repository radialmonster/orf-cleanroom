# Public zlib prefix ratio reproduces

Author: @mtakemoto
Verified by: @radialmonster
Lead: #339
Variant: unassigned
Partial: zlib-9 first-four-million-byte ratios for original public id 1993

## Claim

The lead's zlib-9 recompression ratios for the first 4,000,000 payload bytes of public id 1993 reproduce in the stated environment, both in original order and after the declared whole-payload byte shuffle. These descriptive sizes do not identify or exclude a payload codec.

## Original evidence

Lead #339 reports zlib-9 ratios 0.9791 real and 0.9816 shuffled on 1993, using `tools/code_family_screen.py` at `4787e490c63df740785078c657de29ff4eee4612` and seed 20261022. A prior review comment reported 0.9819 / 0.9805 with Python 3.13.15 and zlib build/runtime 1.3.1; the reason for that discrepancy is not established.

## Verification

After the lead, @radialmonster reran the same measurement at `6578d28d738b1fba1be8f4a93b1f932b224dc19e`, with Python 3.14.7 and zlib build/runtime 1.3.1.zlib-ng. The entire payload was shuffled before selecting its first 4,000,000 bytes, with a fresh `random.Random(20261022)` for each shuffled run. An independent streaming zlib interface gave the same compressed lengths. This computational cross-check is not an additional human verifier.

| ID | Payload order | Input bytes | Compressed bytes | Ratio | Rounded ratio |
|---:|---|---:|---:|---:|---:|
| 1993 | real | 4000000 | 3916500 | 0.979125 | 0.9791 |
| 1993 | shuffled | 4000000 | 3926377 | 0.98159425 | 0.9816 |
| 7803 | real | 4000000 | 4001168 | 1.000292 | 1.0003 |
| 7803 | shuffled | 4000000 | 4001226 | 1.0003065 | 1.0003 |

Id 7803 was predeclared before its measurement and was not in the original lead's ratio cohort, though it was previously studied. Its results are a separate descriptive extension. Version differences are recorded, not asserted to explain the earlier mismatch. Flat frames, other compressors, container screens and other code families are outside this finding.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` |
| 7803 | OM System - OM-3 - 16bit (4:3).ORF | `63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0` |

Both local hashes matched retained verified CC0 records, public identities and existing manifest rows.

## Reproduce

At `6578d28d738b1fba1be8f4a93b1f932b224dc19e`, run the existing tool once per hash-matched public file in real and shuffled modes. It prints aggregate JSON; the zlib ratio is in `compressibility.zlib9`. The tool also performs its other documented screens.

```sh
python -I -B tools/code_family_screen.py FILE
python -I -B tools/code_family_screen.py FILE --shuffle --seed 20261022
```
