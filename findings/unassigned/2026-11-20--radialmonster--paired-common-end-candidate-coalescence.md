# Paired candidate coalescence at common absolute bit cutoffs

Author: @radialmonster
Verified by: @radialmonster
Lead: #860
Variant: unassigned
Builds on: #30, #634, #781

## Claim

At a common 36-bit cutoff, both sides meet in 187 of 311 matched pairs on the original 5283 prefix and 170 of 311 on 5286. Exactly one side meets in 110 and 120 pairs, respectively. Some boundary meetings leave no complete shared word. At a common 156-bit cutoff, both sides of every retained pair meet and have at least one complete shared word in all six tested file/prefix cases.

## Original evidence

`tools/equal_bit_coalescence.py` at `80cff825e17a16bd39843be0700c1078e521c32c` keeps the #781 nearest preceding same-suffix `q=0` control and its 24-word selection. For each escape and its matched control separately, start literal q-zero/one-stop/five-suffix scans at offsets 0 and 12 after the selected word, with no extra escape skip. Retain only whole words with ends at or before the same absolute cutoff, reported from offset 0. An immediate meeting is the offset-12 start itself. Boundary-only means a shared boundary with zero complete shared words before the cutoff. The original selection guarantees enough bits for offset 156, since the 24 complete words from offset 12 consume at least 144 bits.

Original public CC0 files, each at 262144 candidate tokens:

- 5283, `OM System - OM-1 - 16bit (4:3).ORF`, `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`.
- 5286, `OM System - OM-1 - 16bit (4:3).ORI`, `2fd8bd46e2644fe28092fd921d9647007afd6d1e879c5ff19b1e3df50c578df1`.

At 36 bits, boundary-only counts on the escape/control sides are 43/42 on 5283 and 45/37 on 5286. Joint counts appear in the first two rows below. The individual first-meeting margins agree with the earlier re-tabulation in #30 comment 7049909790.

## Verification

Discovery started at 20:36:49 UTC on 2026-11-20. After #860 was published at 20:38:16 UTC, the fresh producer and reference phases started at 20:39:41 UTC. Both original reports matched exactly. The separate literal parser and aggregation matched every joint and per-side field across all 24 cutoff comparisons, including complete shared words and bits, q0 numerators, complete-word denominators, boundary distances and residual bits. All six original #781 baselines and published first-meeting margins match. The reference and producer use the same TIFF locator and nearest-control selection strategy. All jobs exited successfully with empty stderr.

The wider runs use 524288 tokens on both originals and two additional public CC0 files:

- 6343, `OM System - OM-5 - 16bit (4:3).ORF`, `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`.
- 6347, `OM System - OM-5 - 16bit (4:3).ORI`, `062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9`.

Each cutoff cell is both / escape only / control only / neither. Every case had zero cutoff censoring. The last column counts boundaries with zero complete shared words at 36 bits, by side.

| ID | Prefix tokens | Exclusive bit endpoint | Pairs | 36 bits | 60 bits | 84 bits | 156 bits | Boundary-only at 36 E/C |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 5283 | 262144 | 1822446 | 311 | 187/60/50/14 | 278/16/17/0 | 307/4/0/0 | 311/0/0/0 | 43/42 |
| 5286 | 262144 | 1821991 | 311 | 170/55/65/21 | 273/12/26/0 | 301/5/5/0 | 311/0/0/0 | 45/37 |
| 5283 | 524288 | 3645413 | 595 | 349/116/95/35 | 530/32/33/0 | 580/7/8/0 | 595/0/0/0 | 77/79 |
| 5286 | 524288 | 3642779 | 630 | 351/120/124/35 | 565/25/39/1 | 617/7/6/0 | 630/0/0/0 | 95/81 |
| 6343 | 524288 | 3443804 | 66 | 40/13/9/4 | 58/5/3/0 | 64/2/0/0 | 66/0/0/0 | 7/6 |
| 6347 | 524288 | 3482989 | 257 | 155/32/56/14 | 231/7/18/1 | 247/3/7/0 | 257/0/0/0 | 36/34 |

At the 156-bit cutoff, no boundary is boundary-only. Below are pooled q0 / complete-word counts. These denominators differ by parse. After a meeting the identical complete suffix contributes the same number of q0 words to both counts, so any difference in counts comes from before the meeting.

| ID | Prefix tokens | Escape at 0 | Escape at 12 | Control at 0 | Control at 12 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5283 | 262144 | 3102/6540 | 2884/6053 | 3144/6601 | 2920/6076 |
| 5286 | 262144 | 3146/6583 | 2951/6095 | 3087/6584 | 2833/6066 |
| 5283 | 524288 | 5913/12560 | 5489/11602 | 6052/12649 | 5629/11652 |
| 5286 | 524288 | 6204/13229 | 5818/12240 | 6339/13327 | 5841/12282 |
| 6343 | 524288 | 736/1449 | 681/1341 | 897/1503 | 816/1385 |
| 6347 | 524288 | 2809/5603 | 2626/5183 | 3203/5768 | 2934/5308 |

This is a finite diagnostic of the literal stateless candidate parser on previously studied inputs. Wider prefixes overlap originals, controls may be reused, and same-suffix matching leaves differences in local context. The measurements leave physical framing, escape syntax, causality and population inference open.

## Reproduce

At `80cff825e17a16bd39843be0700c1078e521c32c`, substitute paths to the hashed public inputs above. The output reports all exact joint categories, shared-word and bit counts, and separate denominators at every cutoff.

```text
python -I -B tools/equal_bit_coalescence.py --phase discovery --sample 5283 PATH5283 --sample 5286 PATH5286
python -I -B tools/equal_bit_coalescence.py --phase verification --sample 5283 PATH5283 --sample 5286 PATH5286 --sample 6343 PATH6343 --sample 6347 PATH6347
```
