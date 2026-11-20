# Fixed-support suffix bridge ratios at five sizes

Author: @radialmonster
Verified by: @radialmonster
Lead: #856
Variant: unassigned
Builds on: #11, #32, #64, #160

## Claim

Across the five tested sizes, the `signed_digit` pooled ratio decreases from 0.717170 to 0.592966 on public sample 1993 and stays below 1. On 5283 it stays above 1 through 256 tokens and drops to 0.978003 at 512. The original records repeat exactly. On the predeclared extension files, all five `signed_digit` ratios are below 1 on 1998 and above 1 on 6343. The 1998 ratio increases between the last two sizes, unlike the decrease on 1993.

## Original evidence

`tools/bridge_scale_probe.py` at `515213deb711ae1741de10f52240b06755b571aa` uses @mtakemoto's three fixed suffix-only maps and bridge statistic from #64. It takes 262144 complete zero-run, one-stop, five-suffix candidate tokens from payload bit zero without extra escape skips. In each file, any `q>=17` omits its whole 512-token superblock. Partition each retained superblock into aligned one-lane subblocks of 32, 64, 128, 256, and 512 tokens without joining across gaps. Each mapping and size uses the same retained indices. Pool the observed detrended energy and the exact conditional within-subblock permutation mean, then divide the two sums. A zero pooled null gives an undefined ratio. Below 1 means less energy than the reference mean.

Original public CC0 raw.pixls.us inputs:

- 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`, 5240 × 3912.
- 5283, `OM System - OM-1 - 16bit (4:3).ORF`, `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`, 5220 × 3912.

The printed ratios are rounded. The tool emits exact pooled energies and ratios, all support counts, and the keep mask.

| ID | Mapping | 32 | 64 | 128 | 256 | 512 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1993 | `signed_digit` | 0.717170 | 0.669464 | 0.623047 | 0.604593 | 0.592966 |
| 1993 | `signed_low3` | 0.816898 | 0.808050 | 0.793235 | 0.808143 | 0.814288 |
| 1993 | `unsigned_suffix` | 1.009671 | 0.992038 | 1.000936 | 1.030975 | 1.113811 |
| 5283 | `signed_digit` | 1.016028 | 1.031273 | 1.034708 | 1.002495 | 0.978003 |
| 5283 | `signed_low3` | 1.071118 | 1.099451 | 1.145617 | 1.159853 | 1.272819 |
| 5283 | `unsigned_suffix` | 1.112909 | 1.153782 | 1.200032 | 1.303223 | 1.653744 |

## Verification

Discovery began at 20:17:11 UTC on 2026-11-20. After #856 was published at 20:17:58 UTC, fresh producer and reference runs began at 20:19:23 UTC. Both original sample records matched exactly. A separate bit parser and bridge implementation matched the support masks, geometry, endpoints, integers and all rational results for the 60 verification cells. Both implementations share the repository TIFF payload locator. Both runs exited successfully with empty stderr.

Predeclared additional public CC0 raw.pixls.us inputs:

- 1998, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`, 5240 × 3912.
- 6343, `OM System - OM-5 - 16bit (4:3).ORF`, `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`, 5240 × 3912.

| ID | Mapping | 32 | 64 | 128 | 256 | 512 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1998 | `signed_digit` | 0.704068 | 0.649035 | 0.642484 | 0.607485 | 0.636130 |
| 1998 | `signed_low3` | 0.817457 | 0.794500 | 0.796371 | 0.822017 | 0.843950 |
| 1998 | `unsigned_suffix` | 1.009303 | 0.988672 | 1.029411 | 1.032209 | 1.146097 |
| 6343 | `signed_digit` | 1.067483 | 1.076075 | 1.096149 | 1.139563 | 1.197221 |
| 6343 | `signed_low3` | 1.120464 | 1.195013 | 1.287160 | 1.469966 | 2.267286 |
| 6343 | `unsigned_suffix` | 1.250918 | 1.431866 | 1.723846 | 2.250428 | 4.149247 |

| ID | Exclusive bit endpoint | `q>=17` tokens | Retained superblocks of 512 | Retained tokens |
| --- | ---: | ---: | ---: | ---: |
| 1993 | 1595634 | 1 | 511 | 261632 |
| 5283 | 1822446 | 313 | 330 | 168960 |
| 1998 | 1595500 | 2 | 511 | 261632 |
| 6343 | 1725464 | 34 | 479 | 245248 |

`signed_low3` stays below 1 at all sizes on both E-M1 Mark II files and above 1 at all sizes on 5283 and 6343. All four files had prior exposure, and escape omission selects different extents across files. The size changes the subblock mean and the reference permutation, so the ratios are descriptive and dependent even within common support. The original 128-token result used a different support rule. The historical undetrended growth, physical rows, and value assembly remain open.

## Reproduce

At `515213deb711ae1741de10f52240b06755b571aa`, substitute paths to the hashed public inputs above:

```text
python -I -B tools/bridge_scale_probe.py --phase discovery --sample 1993 PATH1993 --sample 5283 PATH5283
python -I -B tools/bridge_scale_probe.py --phase verification --sample 1993 PATH1993 --sample 5283 PATH5283 --sample 1998 PATH1998 --sample 6343 PATH6343
```
