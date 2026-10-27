# Held-out phase and period comparison on four public files

Author: @radialmonster
Verified by: @radialmonster
Lead: #504
Variant: unassigned
Builds on: #144, #11, 2026-10-22--radialmonster--later-band-row-stride-drift

## Claim

For the three public files and fixed token-index experiment in #504, separately selecting stride and phase on the training band produces the held-out contrasts below. The results reproduce the lead's descriptive numerical comparison; they do not establish physical row boundaries, a stride change, independent captures, or general behavior of a camera or codec. The threshold of 0.02 is a predeclared practical comparison, not a calibrated significance test.

## Original evidence

The lead used `tools/token_phase_stride_compare.py` at commit `7dfe8fe900dc360d67d8c527496aa0eeab565508`. With q values capped at 40, it compares the mean of the first 32 tokens with the rest of each candidate row. It fits 100 training rows beginning at token 10,480,000 plus phase, searching strides 5,176 through 5,304 and every phase; the fixed-stride fit uses 5,240. After barrier 11,021,008, each model is evaluated on 100 complete rows beginning at its first predicted boundary at or after that barrier. Each file yields 675,960 training phase scores. Tie handling and the full calculation are specified by the tool.

| Public ID | Name | SHA-256 | Joint stride, phase | Fixed stride, phase | Joint held-out | Fixed held-out | Difference |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| 1995 | Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f | 5246, 1618 | 5240, 2720 | 0.1695623562 | 0.1338109639 | +0.0357513923 |
| 1998 | Olympus - E-M1MarkII - 16bit (4:3).ORF | 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 | 5245, 2006 | 5240, 3025 | 0.0977792898 | 0.1082104455 | -0.0104311557 |
| 1997 | Olympus - E-M1MarkII - 16bit (4:3).ORI | 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a | 5246, 1756 | 5240, 2828 | 0.1444641830 | 0.1199923195 | +0.0244718635 |

The corresponding fixed-origin held-out contrasts are -0.1338335253, -0.1498478303 and -0.1358438940. The first and third differences exceed the practical threshold; the second does not.

## Verification

After #504 was posted, @radialmonster reran all three files using the merged tool and verified retained CC0 records and local SHA-256 identities. Each complete report matched the discovery report exactly after excluding only the elapsed timing field (named `cpu_seconds` in the discovery report and `elapsed_seconds` in the merged tool). This comparison includes all 2,027,880 training phase scores, selections, intervals and held-out contrasts. Six synthetic tests passed. A separately structured numerical reference used column-folded q sums and sliding heads instead of the tool's per-row prefix-sum calculation. Across the four files it checked all 2,703,840 training phase scores, exact choices and ties, and all twelve selected held-out profiles; literal row slices and exact Fraction arithmetic matched the emitted test numerators/denominators. Both agents act for @radialmonster. This is self-verification by the same person, not independent-human verification.

The predeclared additional file, public ID 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`, was measured after the lead was posted. Its joint selection was stride 5250, phase 2891; fixed-stride phase was 3580. Their held-out contrasts were 0.48991316117286315 and -0.035529473886328725, respectively, a difference of +0.5254426350591919; the fixed-origin contrast was -0.04856806835637481. All four runs parsed 11,556,712 tokens. Their consumed bit counts, in ID order 1995, 1998, 1997, 1993, were 71,021,340; 71,042,812; 71,020,275; and 71,133,612.

Intervals below are half-open token-index ranges; the models have different test starts and hence do not necessarily use identical test tokens. They are not byte offsets.

| ID | Model | Training interval | Test interval |
| --- | --- | --- | --- |
| 1995 | joint | [10481618, 11006218) | [11021956, 11546556) |
| 1995 | fixed stride | [10482720, 11006720) | [11022440, 11546440) |
| 1998 | joint | [10482006, 11006506) | [11022241, 11546741) |
| 1998 | fixed stride | [10483025, 11007025) | [11022745, 11546745) |
| 1997 | joint | [10481756, 11006356) | [11022094, 11546694) |
| 1997 | fixed stride | [10482828, 11006828) | [11022548, 11546548) |
| 1993 | joint | [10482891, 11007891) | [11023641, 11548641) |
| 1993 | fixed stride | [10483580, 11007580) | [11023300, 11547300) |

The fixed-origin interval is [10480000, 11004000) for training and [11024960, 11548960) for test in all four files. Prior #144 analyses overlap the proposed 1995 and 1998 windows; 1997 and 1993 are also previously studied files. Test rows were held out from this specific model selection, but are not blind or fresh with respect to prior research.

## Reproduce

Use the public files identified above, checking their hashes against retained CC0 records. At commit `7dfe8fe900dc360d67d8c527496aa0eeab565508`, substitute their local paths for the four placeholders:

```sh
python -I -B tools/test_token_phase_stride_compare.py
python -I -B tools/token_phase_stride_compare.py --sample 1995 'Olympus - E-M1MarkII - 16bit (4:3).ORI' 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f "$FILE_1995"
python -I -B tools/token_phase_stride_compare.py --sample 1998 'Olympus - E-M1MarkII - 16bit (4:3).ORF' 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 "$FILE_1998"
python -I -B tools/token_phase_stride_compare.py --sample 1997 'Olympus - E-M1MarkII - 16bit (4:3).ORI' 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a "$FILE_1997"
python -I -B tools/token_phase_stride_compare.py --sample 1993 'Olympus - E-M1MarkII - 16bit (4:3).ORF' 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 "$FILE_1993"
```
