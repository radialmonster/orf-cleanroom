# Plain per-row running-sum growth equals the within-row shuffle null (Partial #31)

Author: @radialmonster
Verified by: @ruedbi
Lead: #31
Variant: unassigned
Builds on: #11, #284
Reproduces: 2026-10-21--radialmonster--running-sum-growth-equals-within-row-null
Partial: plain per-row running sum (R1) on five public CC0 files only; not the per-parity R2 variant (14 of 15 cells inside the predeclared band, one at 1.501252), the leaky variants, the double-integration/Lorenzo bullet (a separate predeclared check did not meet its threshold and is reported on #31), physical rows, values, predictors or a decode.

## Claim

On five public compressed ORF files from four bodies, a plain per-nominal-row
running sum (R1) of three fixed token mappings has peak-to-peak growth that is
inside the predeclared 0.5..1.5 band of its same-token, within-row shuffle
null in all 15 file x mapping cells. The ratios are 0.973940 to 1.035422.

This reproduces the scoped negative in lead #31 that a plain running sum's
growth is equal to the null on these public inputs. The per-parity running sum
(R2) is inside the same band in 14 of 15 cells; the one exception, 1.501252 on
id 1995 with the `signed_low3` mapping, is retained and is not claimed. The
leaky variants are reported descriptively. This is a token-growth measurement,
not a value mapping, a predictor, a physical-row model or a decode.

## Original evidence

Lead #31 (2026-10-18) reports this among its negative predictor/transform/
integration results from private research notes. It gives no public file list
or method and no tolerance for "growth equal to null", so its exact historical
figures cannot be reproduced. Its running-sum text is:

> Plain running sum per row, one running sum per pixel parity (stride 2), leaky
> running sums with coefficient 0.0 to 0.5 and 0.9-0.99. Growth equal to null;
> the leaky versions are bounded only because they filter white noise.

The same lead's double-integration and Lorenzo bullet gives example figures
(growth 176-193 against 76-83; Lorenzo 18 against 4-6), but those private
numbers and method are unavailable and are not reproduced here.

The earlier public predictor finding for #31
(`2026-10-21--radialmonster--predictor-probe-no-cross-body-transfer`) covers
fixed readings plus causal predictors, not running-sum growth.

All inputs are public CC0 raw.pixls.us files. Their local SHA-256 values matched
the retained verified CC0 inventory and existing `samples/manifest.csv` rows
before measurement; no download or catalogue request was repeated.

- 1993 `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256
  `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`;
  5240x3912, 6.151 bpp, variable payload, compression tag 1.
- 1995 `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256
  `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`;
  5240x3912, 6.154 bpp, variable payload, compression tag 1.
- 241 `Olympus - E-P3 - 16bit (4:3).ORF`, SHA-256
  `540edabdd9d4e6ef8602f56443730cc3133d714dc4d3d2c607e2f0aa6be5cbcd`;
  4080x3040, 6.725 bpp, variable payload, compression tag 1.
- 5283 `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256
  `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`;
  5220x3912, 7.836 bpp, variable payload, compression tag 1.
- 6946 `OM System - TG-7 - 16bit (4:3).ORF`, SHA-256
  `4f7344c67bfcfcfec45f754195ba612fc2ad6312f5fab87812bf04b9e9e7d46a`;
  4040x3016, 8.076 bpp, variable payload, compression tag 1.

## Verification

A new run was made on 2026-10-21 UTC after the lead and after the design was
posted in [the claim comment](https://github.com/radialmonster/orf-cleanroom/issues/31#issuecomment-6328343017)
and [the running-sum predeclaration](https://github.com/radialmonster/orf-cleanroom/issues/31#issuecomment-6328396963).
The tool is `tools/token_loop_probe.py` at commit
`d2ebb4d7640e796dee5c0ac3ebc87b1b098dca30` (PR #284, open at the time of this
finding), SHA-256
`af75c48eb1f7c343e776a04f31cdf5698922b528ca568a988720b8ea148f33d9`, with
`tools/orf_tokens.py` SHA-256
`c6f51ed26793b1bb400a1dc1b29d8e20f9ef734373770310c665228ce02f08ad` and
`tools/orf_signature.py` SHA-256
`b1b6f091bfb986ab7aca3ad1f513202acfaaccc424272523589142444d025afb`.
Python 3.13.15.

Settings fixed before the run: first 300 x payload-width candidate tokens,
q-zero/stop-one/five-suffix parse with zero extra escape bits, rows as nominal
blocks of exactly W tokens, three mappings (`u = 32*q + s`, `signed_digit =
4*(s>>3) + (s&3) - 8*((s>>2)&1)`, `signed_low3 = (s&7)-8 if (s&4) else
(s&7)`), peak-to-peak range as growth, and four within-row token shuffles per
file and mapping with seed 20261021. All five prefixes were complete (no
shortfall).

R1 real/null growth ratios, by file and mapping:

- 1993: `u` 1.000000, `signed_digit` 0.999316, `signed_low3` 1.035422.
- 1995: `u` 1.000000, `signed_digit` 0.999347, `signed_low3` 0.973940.
- 241: `u` 1.000000, `signed_digit` 0.999743, `signed_low3` 1.001085.
- 5283: `u` 1.000000, `signed_digit` 0.999500, `signed_low3` 1.020202.
- 6946: `u` 1.000000, `signed_digit` 0.999615, `signed_low3` 1.006173.

The three `u` R1 cells are exactly 1.000000 because a row's running sum is
invariant under a permutation of that row; the twelve signed-mapping cells are
the non-trivial comparison, and all are within 0.974 to 1.036 of the null.

R2 (per-parity running sum) is inside the band in 14 of 15 cells. The exception
is id 1995 with `signed_low3`: real range 1949, mean null range 1298.25, ratio
1.501252. The other R2 ratios are 0.937429 to 1.278914. Leaky R1 variants:
`LK05` ratios 0.946953 to 1.011916; `LK09` ratios 0.960479 to 1.131997 (all
inside the band, reported descriptively).

A separate predeclared check of the lead's double-integration/Lorenzo bullet
used the same files, null and range measure but did not meet its 1.5x rule:
only 1 of 60 cells reached 1.5 (`P2`, id 1995, `signed_low3`, 1.521154); the
L1 ratios were 0.99999985 to 1.00000004, L2 0.997590 to 1.179230, and P1/P2
0.897725 to 1.293168. That part is reported on #31 and is not claimed here.

Limits: rows are nominal W-token blocks, not established physical rows. The
within-row null preserves each row's mapped-value multiset and mean, so the
Lorenzo and `u`-R1 cells are largely or exactly insensitive to row order; this
finding does not use those as evidence beyond the stated band. Ratios are
descriptive, not significance tests. No sensor values, value assembly,
predictor, scan order, image-likeness, round-trip or decoder is claimed. The
lead's private file list and exact figures are unavailable.

Independent verification was conducted by @ruedbi on 2026-11-17 using
`tools/token_loop_probe.py` on local samples 1993 and 1995 with Python 3.8.10.
The self-test passed all 29 unit tests. The probe reproduced the exact R1 ratios
for both samples (`1993`: `u` 1.000000, `signed_digit` 0.999316, `signed_low3` 1.035422;
`1995`: `u` 1.000000, `signed_digit` 0.999347, `signed_low3` 0.973940) and confirmed the
outlier behavior on `1995` `signed_low3` R2 (1.501252).

## Reproduce

Read the complete tool, test and imported modules first, then match each local
file to the retained CC0 hash above. Use `tools/token_loop_probe.py` at commit
`d2ebb4d7640e796dee5c0ac3ebc87b1b098dca30` (PR #284) or the same file on main
after that PR merges. The commands read only the public samples and print
aggregate JSON:

    python -I -B tools/token_loop_probe.py --self-test
    python -I -B tools/token_loop_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --sample 241 "Olympus - E-P3 - 16bit (4:3).ORF" FILE241 --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --sample 6946 "OM System - TG-7 - 16bit (4:3).ORF" FILE6946 --rows 300 --perms 4

The JSON summary should show `running_sum_in_0_5_1_5` = 29 of 30,
`running_sum_all_in_0_5_1_5` = false, `double_lorenzo_at_least_1_5` = 1 of 60,
and `incomplete_prefixes` = 0. The 1995 `signed_low3` R2 cell is the only
running-sum outlier.
