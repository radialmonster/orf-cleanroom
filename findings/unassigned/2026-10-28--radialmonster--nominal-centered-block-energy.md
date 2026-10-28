# Nominal row-centered candidate block energies

Author: @radialmonster
Verified by: @radialmonster
Lead: #681
Variant: unassigned
Builds on: #31, #671

## Claim

For two previously studied public files, fixed row-centered candidate 128 by 128 block energies differ across three mappings and two shuffle controls. On 1993 all three real-over-mean-null ratios exceed 4 under both controls; on 5283 all are below 1.5. These are descriptive observed comparisons. This squared-sum proxy does not reproduce #31's unavailable private rectangle-bound measure or establish physical rows or a predictor.

## Original evidence

The lead used `tools/token_planar_control_probe.py` at commit `80d2d9206375547305b3531baa6bf761e4f23260` on 300 nominal rows of 1993 and 5283. Fresh results for these original cases appear below.

## Verification

After publication, both original cases were freshly reproduced and predeclared 600-row cases were measured on 1993, 5283, 1995 and 6343. At 600 rows, 5283's u ratios exceed 1.5 under both controls, so its 300-row observation does not extend to that wider case. The wider extent and additional files qualify verification; all files had been exposed previously, and the verifier is the finder. Independent implementations agreed on all exact totals, fractions and metadata. The reference reused a previously authored literal parser; both implementations share a TIFF locator and assisted the same human.

Parse stop-1 k=5 candidate words without extra escape skipping, retaining q>=17. Lay the indicated number of nominal W-token rows out from token origin, W being payload width, and use nonoverlapping complete 128 by 128 blocks. For each block square the integer numerator W*block_sum - 128*sum(full-row sums across its 128 rows); report their total. Full-row means include all columns, even columns excluded from blocks, and are recomputed for each shuffle. The numerator squares are W squared times squared centered block sums.

Use mappings u=32*q+s, signed_digit=4*(s>>3)+(s&3)-8*((s>>2)&1), and signed_low3=(s&7)-8 when bit 2 is set, otherwise s&7. Four within-nominal-row and four global whole-value shuffles use independent generators with seed 20261021+1000*ID+10*mapping_index+replicate. Both preserve the overall multiset; only within-row preserves each nominal row multiset. These controls are descriptive, not calibrated significance tests.

The table gives block counts, excluded rows/columns, real total, each mode's sum of four null totals (its mean is one quarter of that number), and exact real-over-mean-null fractions. W is 5240 for 1993, 1995 and 6343, and 5220 for 5283. A zero null denominator would be undefined. All requested prefixes completed.

| ID | Rows | Mapping | Blocks | Excluded rows | Excluded columns | Real total | Within-row four-null total | Within-row ratio | Global four-null total | Global ratio |
|---|---:|---|---:|---:|---:|---:|---:|---|---:|---|
| 1993 | 300 | u | 80 | 44 | 120 | 1020680248024252160 | 21651912785475840 | 3189625775075788/16915556863653 | 28619212882895360 | 1594812887537894/11179380032381 |
| 1993 | 300 | signed_digit | 80 | 44 | 120 | 4258521524189440 | 4098822761551680 | 53231519052368/12808821129849 | 3849947032142720 | 26615759526184/6015542237723 |
| 1993 | 300 | signed_low3 | 80 | 44 | 120 | 18500014339951360 | 615311678376320 | 115625089624696/961424497463 | 511626996632640 | 231250179249392/1598834364477 |
| 5283 | 300 | u | 80 | 44 | 100 | 123201050803246640 | 365860830143464640 | 1540013135040583/1143315094198327 | 341255696965212480 | 1540013135040583/1066424053016289 |
| 5283 | 300 | signed_digit | 80 | 44 | 100 | 1450867573605040 | 4980771784253440 | 18135844670063/15564911825792 | 5823560735932160 | 18135844670063/18198627299788 |
| 5283 | 300 | signed_low3 | 80 | 44 | 100 | 243687140650800 | 659455075861200 | 270763489612/183181965517 | 751690825178000 | 2436871406508/1879227062945 |
| 1993 | 600 | u | 160 | 88 | 120 | 7914336333962008320 | 58806519798616000 | 98929204174525104/183770374370675 | 66363192975626560 | 98929204174525104/207384978048833 |
| 1993 | 600 | signed_digit | 160 | 88 | 120 | 13625165594988800 | 7960855125227840 | 170314569937360/24877672266337 | 7754401329229440 | 85157284968680/12116252076921 |
| 1993 | 600 | signed_low3 | 160 | 88 | 120 | 26486147830956800 | 1285039764473920 | 47296692555280/573678466283 | 1125024952858880 | 82769211971740/878925744421 |
| 5283 | 600 | u | 160 | 88 | 100 | 412423245540790320 | 753053515635430560 | 3436860379506586/1568861490907147 | 755401619180243360 | 10310581138519758/4721260119876521 |
| 5283 | 600 | signed_digit | 160 | 88 | 100 | 2780000443206320 | 9875553833377280 | 34750005540079/30861105729304 | 9616627593686160 | 139000022160316/120207844921077 |
| 5283 | 600 | signed_low3 | 160 | 88 | 100 | 414548959546160 | 1380824204834480 | 20727447977308/17260302560431 | 1421234826916960 | 10363723988654/8882717668231 |
| 1995 | 600 | u | 160 | 88 | 120 | 226756443639962880 | 38889819016144320 | 134974073595216/5787175448831 | 39969638526929600 | 2834455545499536/124905120396655 |
| 1995 | 600 | signed_digit | 160 | 88 | 120 | 1601139174301440 | 7237685612519680 | 5003559919692/5654441884781 | 8113040839042560 | 277975551094/352128508639 |
| 1995 | 600 | signed_low3 | 160 | 88 | 120 | 418596804849920 | 1215807381376320 | 5232460060624/3799398066801 | 1262334514508800 | 327028753789/246549709865 |
| 6343 | 600 | u | 160 | 88 | 120 | 244082429392133760 | 329085612321312960 | 1017010122467224/342797512834701 | 358491267916614080 | 3051030367401672/1120285212239419 |
| 6343 | 600 | signed_digit | 160 | 88 | 120 | 2719770595541120 | 9094544231414400 | 1545324202012/1291838669235 | 9459413699097920 | 33997132444264/29560667809681 |
| 6343 | 600 | signed_low3 | 160 | 88 | 120 | 417473599273600 | 1476157244189440 | 1304604997730/1153247847023 | 1369270281659200 | 1043683998184/855793926037 |

Unknown framing and candidate mappings limit interpretation. This proxy is not the historical private rectangle-bound measure; it establishes neither physical rows nor original pixel values.

## Reproduce

Retained verified public CC0 inputs:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`

At commit `80d2d9206375547305b3531baa6bf761e4f23260`, verify identities and hashes, substitute paths, and run:

```text
python -I -B tools/token_planar_control_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --rows 300
python -I -B tools/token_planar_control_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --rows 300
python -I -B tools/token_planar_control_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --rows 600
python -I -B tools/token_planar_control_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --rows 600
python -I -B tools/token_planar_control_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --rows 600
python -I -B tools/token_planar_control_probe.py --sample 6343 "OM System - OM-5 - 16bit (4:3).ORF" FILE6343 --rows 600
```

The tool emits each null total, seed, exact ratio and endpoint. Separately justified block, mapping and framing assumptions remain open on the existing corpus.
