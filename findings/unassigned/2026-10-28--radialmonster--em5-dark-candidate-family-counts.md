# Candidate family counts on public E-M5 Mark II dark files

Author: @radialmonster
Verified by: @radialmonster
Lead: #597
Variant: unassigned
Builds on: #339, #552

## Claim

Literal candidate-family counts on two previously exposed public E-M5 Mark II dark files are reproducible. The real Rice stop-1 k=5 whole-payload counts exceed the stored-site count by 4 and 6; their corresponding whole-byte-shuffled counts are 2,217,254 and 2,269,362 below it. These counts alone do not establish a camera codec, a physical pixel mapping, or a causal sensitivity effect.

## Original evidence

The lead fixed nine candidate families and measured P1010009 and P1010017, using the complete payload and a byte shuffle seeded with 20261022 per file. Every count, consumed endpoint and residual is shown below. Both files have 4640 x 3472 = 16,110,080 stored sites. An independently implemented bitwise counter matched the original nine families. The P1010009 initial launcher did not record a process exit code; it produced complete JSON and empty stderr. P1010017 completed with exit 0.

## Verification

After the lead, an independent fresh nine-family run reproduced both original files' complete-word counts, prefix and whole endpoints and residuals in real and shuffled modes; the extra 19 families were not rerun on those originals. Four predeclared additional public files received a fresh full 28-family tool run, each with exit 0, and an independent nine-family check. All 72 reserved-file central-family/mode records matched on counts and endpoints. All 224 reserved-file family/mode outputs passed schema and endpoint/residual/prefix/site accounting; the other 19 families were not independently recounted.

Each cell below is `codewords minus sites / consumed bits / residual bits`; add 16,110,080 to the first number to obtain the whole complete-word count. A zero-word parse is a valid reported outcome, not a negative count; real Elias delta completes zero words on all six files. Files are owner-declared CC0 and were contributed by @mszyndel.

**P1010009.ORF**, SHA-256 `ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c`, payload 12087793 bytes:

| Family | Real delta / end / residual | Shuffled delta / end / residual |
|---|---:|---:|
| rice_stop1_k5 | +4 / 96702340 / 4 | -2217254 / 96702339 / 5 |
| rice_stop1_k4 | +32 / 96702342 / 2 | -411393 / 96702344 / 0 |
| rice_stop1_k3 | +1848065 / 96702341 / 3 | +2866060 / 96702341 / 3 |
| rice_stop0_k5 | -47840 / 96702341 / 3 | -1329552 / 96702344 / 0 |
| exp_golomb_k2 | +1424688 / 96702344 / 0 | +1797987 / 96702343 / 1 |
| exp_golomb_k3 | -839206 / 96702342 / 2 | -477736 / 96702344 / 0 |
| elias_gamma_k0 | +10774598 / 96702344 / 0 | +11933874 / 96702342 / 2 |
| elias_delta_k0 | -16110080 / 0 / 96702344 | -5957165 / 96702342 / 2 |
| fibonacci_k0 | -7917761 / 96702343 / 1 | -6961456 / 96702332 / 12 |

**P1010011.ORF**, SHA-256 `d34532152c79ef24b22c60c6cf743cef41fe28196b40fe16b557c16b7a7ea03d`, payload 12087791 bytes:

| Family | Real delta / end / residual | Shuffled delta / end / residual |
|---|---:|---:|
| rice_stop1_k5 | +4 / 96702327 / 1 | -2061678 / 96702323 / 5 |
| rice_stop1_k4 | +40 / 96702325 / 3 | -575202 / 96702324 / 4 |
| rice_stop1_k3 | +1847897 / 96702328 / 0 | +3003208 / 96702328 / 0 |
| rice_stop0_k5 | -47541 / 96702328 / 0 | -1160597 / 96702324 / 4 |
| exp_golomb_k2 | +1422112 / 96702326 / 2 | +1759054 / 96702322 / 6 |
| exp_golomb_k3 | -1670722 / 96702328 / 0 | -1551604 / 96702320 / 8 |
| elias_gamma_k0 | +10778568 / 96702328 / 0 | +11959872 / 96702328 / 0 |
| elias_delta_k0 | -16110080 / 0 / 96702328 | -6244249 / 96702322 / 6 |
| fibonacci_k0 | -7916822 / 96702327 / 1 | -7239491 / 96702316 / 12 |

**P1010013.ORF**, SHA-256 `81acdd3675c329b351a634cfb4e22228f2db8df94f36480690e04416ded0817d`, payload 12087791 bytes:

| Family | Real delta / end / residual | Shuffled delta / end / residual |
|---|---:|---:|
| rice_stop1_k5 | +3 / 96702328 / 0 | -2028985 / 96702324 / 4 |
| rice_stop1_k4 | +39 / 96702326 / 2 | -398691 / 96702325 / 3 |
| rice_stop1_k3 | +1850464 / 96702325 / 3 | +3135135 / 96702327 / 1 |
| rice_stop0_k5 | -47771 / 96702323 / 5 | -1145647 / 96702323 / 5 |
| exp_golomb_k2 | +1422283 / 96702327 / 1 | +2005576 / 96702324 / 4 |
| exp_golomb_k3 | +126350 / 96702326 / 2 | +815195 / 96702324 / 4 |
| elias_gamma_k0 | +10781740 / 96702328 / 0 | +12326080 / 96702328 / 0 |
| elias_delta_k0 | -16110080 / 0 / 96702328 | -5600441 / 96702315 / 13 |
| fibonacci_k0 | -7912330 / 96702328 / 0 | -7423345 / 96702327 / 1 |

**P1010017.ORF**, SHA-256 `431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5`, payload 12088020 bytes:

| Family | Real delta / end / residual | Shuffled delta / end / residual |
|---|---:|---:|
| rice_stop1_k5 | +6 / 96704155 / 5 | -2269362 / 96704160 / 0 |
| rice_stop1_k4 | +13374 / 96704160 / 0 | -350079 / 96704155 / 5 |
| rice_stop1_k3 | +2682860 / 96704159 / 1 | +2953888 / 96704158 / 2 |
| rice_stop0_k5 | -827876 / 96704156 / 4 | -1520032 / 96704159 / 1 |
| exp_golomb_k2 | +2282748 / 96704160 / 0 | +2061008 / 96704160 / 0 |
| exp_golomb_k3 | -482497 / 96704160 / 0 | -538071 / 96704156 / 4 |
| elias_gamma_k0 | +12145632 / 96704160 / 0 | +12286483 / 96704159 / 1 |
| elias_delta_k0 | -16110080 / 0 / 96704160 | -5735695 / 96704159 / 1 |
| fibonacci_k0 | -5692473 / 96704159 / 1 | -5043333 / 96704159 / 1 |

**P1010018.ORF**, SHA-256 `e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f`, payload 12088007 bytes:

| Family | Real delta / end / residual | Shuffled delta / end / residual |
|---|---:|---:|
| rice_stop1_k5 | +6 / 96704052 / 4 | -2209871 / 96704053 / 3 |
| rice_stop1_k4 | +13423 / 96704054 / 2 | -313141 / 96704052 / 4 |
| rice_stop1_k3 | +2681812 / 96704054 / 2 | +3051699 / 96704055 / 1 |
| rice_stop0_k5 | -827305 / 96704053 / 3 | -1469523 / 96704050 / 6 |
| exp_golomb_k2 | +2279772 / 96704056 / 0 | +2145234 / 96704054 / 2 |
| exp_golomb_k3 | +235882 / 96704054 / 2 | +293941 / 96704054 / 2 |
| elias_gamma_k0 | +12146620 / 96704056 / 0 | +12440944 / 96704052 / 4 |
| elias_delta_k0 | -16110080 / 0 / 96704056 | -5512977 / 96704053 / 3 |
| fibonacci_k0 | -5695368 / 96704055 / 1 | -5207916 / 96704051 / 5 |

**P1010019.ORF**, SHA-256 `5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75`, payload 12088017 bytes:

| Family | Real delta / end / residual | Shuffled delta / end / residual |
|---|---:|---:|
| rice_stop1_k5 | +8 / 96704135 / 1 | -2271142 / 96704136 / 0 |
| rice_stop1_k4 | +13149 / 96704133 / 3 | -336136 / 96704133 / 3 |
| rice_stop1_k3 | +2680438 / 96704136 / 0 | +2956313 / 96704132 / 4 |
| rice_stop0_k5 | -827243 / 96704130 / 6 | -1521478 / 96704131 / 5 |
| exp_golomb_k2 | +2277847 / 96704135 / 1 | +2068702 / 96704136 / 0 |
| exp_golomb_k3 | -322794 / 96704134 / 2 | -353542 / 96704134 / 2 |
| elias_gamma_k0 | +12140640 / 96704136 / 0 | +12298842 / 96704136 / 0 |
| elias_delta_k0 | -16110080 / 0 / 96704136 | -5684099 / 96703988 / 148 |
| fibonacci_k0 | -5696661 / 96704136 / 0 | -5055363 / 96704135 / 1 |
The source tool's default 28-family and 3,000,000-byte prefix outputs are predeclared supplemental results; the original #339 claim did not assert the additional 19 families. The independent nine-family implementation shares the TIFF payload locator, and both implementations assisted the same human. All files were previously studied and are from one session; capture settings, temperature and processing are not independently controlled. No significance, sensitivity causality, codec, variant assignment or physical-row inference follows.

## Reproduce

At commit 22e7d090548a14122480c0f03a27178602774563, obtain all six public files, verify the retained CC0 provenance and hashes above, and run the existing public tool with each local path:

```text
python -I -B tools/code_family_screen.py <local-sample-path>
python -I -B tools/code_family_screen.py <local-sample-path> --shuffle --seed 20261022
```

The tool also performs its documented container and compression screens. Family counts are of complete words only; consumed and residual bits are reported separately. The 28-family and prefix outputs can be regenerated with these commands.
