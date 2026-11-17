# Local conditional suffix ordering on two public files

Author: @radialmonster
Verified by: @radialmonster
Lead: #765
Variant: unassigned
Builds on: #29, #757

## Claim
On public E-M1 id 1051, four consecutive 262144-candidate windows have the conditional proportions P(b2=1 | b1b0=j), ordered j=00,01,10,11, in adjacent comparison pattern `>`, `>`, `<`; neither strict increase nor nondecrease holds. This tests a fixed stronger ordering property and does not reproduce or categorically reject #29's historical roughly linear method or unavailable private files. The file and all discovery windows were previously exposed; these are not independent captures or population evidence.

## Original evidence
The finder reduced previously saved discovery aggregates on 2026-11-17 UTC with `tools/suffix_conditional_order.py` at `5efd5290ff0e726db26d6c8dee72931d95e4cc9c`; the aggregates were produced using `tools/suffix_balance_windows.py` at `15213501fd0346761c96190a0590f871749e203f`. The protocol preceded reduction in #29 comment 6954824471. CC0 raw.pixls.us id 1051, `Olympus - E-M1 - 16bit (4:3).orf`, SHA-256 `19ba17e778ae802d4039f0e88bb1cd68825780788b8058c479067e32b9a63eda`, supplied the original four rows below.

## Verification
Fresh post-lead production and reduction on 2026-11-17 UTC reproduced the original four 1051 tables and conditional counts and extended to the next four windows plus their overlapping combination. The predeclared second public file, CC0 id 6343, `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`, was measured at the same nine intervals. Both retained CC0 inventories and manifest rows match the local hashes. Both files were previously studied; their overlapping windows are not independent captures. All 18 windows completed. On 1051 the pattern is `>`, `>`, `<` in all nine; on 6343 it is `>`, `<`, `<` in eight and `>`, `>`, `<` in one. Strict increase and nondecrease are false in all 18 windows. An independently written literal-bit parser and Fraction oracle matched all tables, counts and comparisons; it shared the TIFF locator and human account. Exact numerator/denominator pairs follow, in category order 00, 01, 10, 11.

File | Start | Length | Retained | Escapes | 00 | 01 | 10 | 11 | Adjacent
---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---
1051 | 0 | 262144 | 262141 | 3 | 35552/66468 | 34186/66923 | 32042/68090 | 29074/60660 | >, >, <
1051 | 262144 | 262144 | 262144 | 0 | 35175/66873 | 34080/67056 | 31580/67514 | 28863/60701 | >, >, <
1051 | 524288 | 262144 | 262144 | 0 | 35300/67388 | 34183/67456 | 31511/67309 | 28679/59991 | >, >, <
1051 | 786432 | 262144 | 262144 | 0 | 35615/68708 | 33397/66510 | 31609/67591 | 28131/59335 | >, >, <
1051 | 1048576 | 262144 | 262144 | 0 | 35601/68714 | 33789/66925 | 31179/67378 | 27990/59127 | >, >, <
1051 | 1310720 | 262144 | 262142 | 2 | 35668/68360 | 33774/66698 | 31602/67825 | 28109/59259 | >, >, <
1051 | 1572864 | 262144 | 262143 | 1 | 35715/68044 | 33839/66968 | 31518/67991 | 28162/59140 | >, >, <
1051 | 1835008 | 262144 | 262144 | 0 | 35487/67322 | 34292/67100 | 31676/67790 | 28720/59932 | >, >, <
1051 | 1048576 | 524288 | 524286 | 2 | 71269/137074 | 67563/133623 | 62781/135203 | 56099/118386 | >, >, <
6343 | 0 | 262144 | 262110 | 34 | 29120/68857 | 28193/67270 | 27198/64708 | 26990/61275 | >, <, <
6343 | 262144 | 262144 | 262111 | 33 | 28152/68309 | 27617/67412 | 27015/65173 | 26758/61217 | >, <, <
6343 | 524288 | 262144 | 262115 | 29 | 28620/69007 | 27680/67117 | 26829/64750 | 26889/61241 | >, <, <
6343 | 786432 | 262144 | 262116 | 28 | 28433/69066 | 27754/67586 | 26412/64636 | 26468/60828 | >, >, <
6343 | 1048576 | 262144 | 262097 | 47 | 28086/68602 | 27467/67639 | 26467/64999 | 26421/60857 | >, <, <
6343 | 1310720 | 262144 | 262115 | 29 | 28769/68936 | 27679/67078 | 27113/64552 | 27154/61549 | >, <, <
6343 | 1572864 | 262144 | 262116 | 28 | 29113/69265 | 28457/67739 | 27338/64552 | 26565/60560 | >, <, <
6343 | 1835008 | 262144 | 262105 | 39 | 30253/68834 | 28994/67238 | 28151/64927 | 27578/61106 | >, <, <
6343 | 1048576 | 524288 | 524212 | 76 | 56855/137538 | 55146/134717 | 53580/129551 | 53575/122406 | >, <, <

Indices include all complete candidate tokens; q>=17 tokens are individually omitted from counts. Sum the H rows of the 4x8 H/L table to C[0..7]; numerator C[j+4] and denominator C[j]+C[j+4] define each conditional proportion. Comparisons use integer cross-products. Incomplete or empty windows are undefined; a missing denominator makes its fraction and comparisons touching it undefined, and both overall flags undefined. This candidate MSB-first q-zero/stop-one/five-bit parse from payload bit zero assumes no extra escape skip. These descriptive results do not establish significance, linearity, physical framing, a decoder, causality or population generality.

## Reproduce
After reading the scripts and imports and matching local hashes to the retained CC0 records, run the producer at its named commit for each input, save each aggregate JSON, then run the reducer at its named commit:

    python -I -B tools/suffix_balance_windows.py --mode verification --sample 1051 'Olympus - E-M1 - 16bit (4:3).orf' PATH_TO_1051
    python -I -B tools/suffix_balance_windows.py --mode verification --sample 6343 'OM System - OM-5 - 16bit (4:3).ORF' PATH_TO_6343
    python -I -B tools/suffix_conditional_order.py AGGREGATE.json
