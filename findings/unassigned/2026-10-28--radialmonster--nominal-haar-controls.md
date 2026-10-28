# Nominal candidate Haar contrast controls

Author: @radialmonster
Verified by: @radialmonster
Lead: #687
Variant: unassigned
Builds on: #31, #671

## Claim

For the original 300-row runs on two previously studied public files, fixed unnormalized candidate 2 by 2 contrast energies vary by direction and mapping against two shuffle controls. For u on 1993 all three energies are below both shuffled means; on 5283 V is above and H/D below both. This defined surrogate does not reproduce #31's unavailable private Haar/lifting ratio or establish physical rows or a predictor.

## Original evidence

The lead used `tools/token_haar_control_probe.py` at commit `d8c47065da3d6f8115e650749d8387b5ce35f393` on 300 nominal rows of 1993 and 5283. Fresh results for those cases appear below.

## Verification

After publication, both original cases were freshly reproduced and predeclared 600-row cases were measured on 1993, 5283, 1995 and 6343. For 1995 at 600 rows, u V is below the within-row shuffled mean (487117529/490952088) but above the global shuffled mean (487117529/474634862). The wider extent and additional files qualify verification; all files had been exposed previously, and the verifier is the finder. Independent implementations agreed on all exact totals, fractions and metadata. The reference reused a previously authored literal parser; both share a TIFF locator and assisted the same human.

Parse stop-1 k=5 candidate words without extra escape skipping, retaining q>=17. Lay the indicated number of nominal W-token rows from token origin, W being payload width, and use nonoverlapping 2 by 2 blocks. For a,b on top and c,d below, use unnormalized H=a-b+c-d, V=a+b-c-d and D=a-b-c+d, without division by 2; sum the square of each direction separately. Selected payload W is 5240 for 1993, 1995 and 6343; W is 5220 for 5283.

Use mappings u=32*q+s, signed_digit=4*(s>>3)+(s&3)-8*((s>>2)&1), and signed_low3=(s&7)-8 when bit 2 is set, otherwise s&7. Four within-nominal-row and four global whole-value shuffles use independent generators with seed 20261021+1000*ID+10*mapping_index+replicate. Both preserve the overall multiset; only within-row preserves each nominal row multiset. These controls are descriptive, not calibrated significance tests.

The table reports every direction, block and excluded-row/column counts, real energy, each mode's sum of four null energies (its mean is one quarter of that number), and exact real-over-mean-null fractions. Zero null denominator would be undefined. All requested prefixes completed.

| ID | Rows | Mapping | Direction | Blocks | Excluded rows | Excluded columns | Real energy | Within-row four-null sum | Within-row ratio | Global four-null sum | Global ratio |
|---|---:|---|---|---:|---:|---:|---:|---:|---|---:|---|
| 1993 | 300 | u | H | 393000 | 0 | 0 | 241826583 | 1130350556 | 241826583/282587639 | 1164003536 | 241826583/291000884 |
| 1993 | 300 | u | V | 393000 | 0 | 0 | 262456707 | 1155342856 | 262456707/288835714 | 1160171712 | 87485569/96680976 |
| 1993 | 300 | u | D | 393000 | 0 | 0 | 239578095 | 1130504464 | 239578095/282626116 | 1163091552 | 79859365/96924296 |
| 1993 | 300 | signed_digit | H | 393000 | 0 | 0 | 43711415 | 169865818 | 87422830/84932909 | 170048558 | 87422830/85024279 |
| 1993 | 300 | signed_digit | V | 393000 | 0 | 0 | 40507955 | 169664934 | 81015910/84832467 | 169880270 | 16203182/16988027 |
| 1993 | 300 | signed_digit | D | 393000 | 0 | 0 | 43639727 | 170272454 | 87279454/85136227 | 170005906 | 87279454/85002953 |
| 1993 | 300 | signed_low3 | H | 393000 | 0 | 0 | 6236695 | 25849724 | 6236695/6462431 | 26091486 | 12473390/13045743 |
| 1993 | 300 | signed_low3 | V | 393000 | 0 | 0 | 6440035 | 26174076 | 6440035/6543519 | 26063350 | 2576014/2606335 |
| 1993 | 300 | signed_low3 | D | 393000 | 0 | 0 | 6222063 | 25779480 | 2074021/2148290 | 26120614 | 12444126/13060307 |
| 5283 | 300 | u | H | 391500 | 0 | 0 | 3986205759 | 16712760666 | 2657470506/2785460111 | 16677526880 | 3986205759/4169381720 |
| 5283 | 300 | u | V | 391500 | 0 | 0 | 4281600251 | 16708023730 | 8563200502/8354011865 | 16736245540 | 4281600251/4184061385 |
| 5283 | 300 | u | D | 391500 | 0 | 0 | 3984483815 | 16700504586 | 7968967630/8350252293 | 16744529784 | 3984483815/4186132446 |
| 5283 | 300 | signed_digit | H | 391500 | 0 | 0 | 57492271 | 232314152 | 57492271/58078538 | 231932130 | 114984542/115966065 |
| 5283 | 300 | signed_digit | V | 391500 | 0 | 0 | 58562219 | 232129588 | 58562219/58032397 | 232078806 | 117124438/116039403 |
| 5283 | 300 | signed_digit | D | 391500 | 0 | 0 | 57529895 | 231992768 | 57529895/57998192 | 232290286 | 115059790/116145143 |
| 5283 | 300 | signed_low3 | H | 391500 | 0 | 0 | 8092287 | 32914732 | 8092287/8228683 | 32937224 | 8092287/8234306 |
| 5283 | 300 | signed_low3 | V | 391500 | 0 | 0 | 8357115 | 32940772 | 8357115/8235193 | 32948288 | 8357115/8237072 |
| 5283 | 300 | signed_low3 | D | 391500 | 0 | 0 | 8080263 | 32994076 | 8080263/8248519 | 32949172 | 8080263/8237293 |
| 1993 | 600 | u | H | 786000 | 0 | 0 | 598481834 | 2810998360 | 299240917/351374795 | 2886727226 | 1196963668/1443363613 |
| 1993 | 600 | u | V | 786000 | 0 | 0 | 646746374 | 2842771976 | 323373187/355346497 | 2888022822 | 1293492748/1444011411 |
| 1993 | 600 | u | D | 786000 | 0 | 0 | 595680534 | 2810945048 | 297840267/351368131 | 2887554398 | 1191361068/1443777199 |
| 1993 | 600 | signed_digit | H | 786000 | 0 | 0 | 90679218 | 354757484 | 90679218/88689371 | 354760198 | 181358436/177380099 |
| 1993 | 600 | signed_digit | V | 786000 | 0 | 0 | 85819326 | 354293864 | 42909663/44286733 | 354530894 | 171638652/177265447 |
| 1993 | 600 | signed_digit | D | 786000 | 0 | 0 | 90437214 | 354810808 | 45218607/44351351 | 355035102 | 60291476/59172517 |
| 1993 | 600 | signed_low3 | H | 786000 | 0 | 0 | 12902394 | 53461276 | 12902394/13365319 | 53800076 | 12902394/13450019 |
| 1993 | 600 | signed_low3 | V | 786000 | 0 | 0 | 13397430 | 53789356 | 13397430/13447339 | 53750328 | 2232905/2239597 |
| 1993 | 600 | signed_low3 | D | 786000 | 0 | 0 | 12889510 | 53369080 | 1288951/1334227 | 53765120 | 1288951/1344128 |
| 5283 | 600 | u | H | 783000 | 0 | 0 | 7963402861 | 33243533808 | 7963402861/8310883452 | 33290017850 | 15926805722/16645008925 |
| 5283 | 600 | u | V | 783000 | 0 | 0 | 8524401413 | 33275184472 | 8524401413/8318796118 | 33254738262 | 17048802826/16627369131 |
| 5283 | 600 | u | D | 783000 | 0 | 0 | 7953849421 | 33243568764 | 1136264203/1187270313 | 33267933270 | 15907698842/16633966635 |
| 5283 | 600 | signed_digit | H | 783000 | 0 | 0 | 115076845 | 465139088 | 115076845/116284772 | 464945080 | 23015369/23247254 |
| 5283 | 600 | signed_digit | V | 783000 | 0 | 0 | 117144453 | 464475108 | 39048151/38706259 | 465265712 | 117144453/116316428 |
| 5283 | 600 | signed_digit | D | 783000 | 0 | 0 | 115355565 | 464448852 | 12817285/12901357 | 464288124 | 38451855/38690677 |
| 5283 | 600 | signed_low3 | H | 783000 | 0 | 0 | 16219149 | 65909098 | 32438298/32954549 | 65934260 | 16219149/16483565 |
| 5283 | 600 | signed_low3 | V | 783000 | 0 | 0 | 16707365 | 65841694 | 33414730/32920847 | 65902212 | 16707365/16475553 |
| 5283 | 600 | signed_low3 | D | 783000 | 0 | 0 | 16200301 | 65923798 | 32400602/32961899 | 65863752 | 16200301/16465938 |
| 1995 | 600 | u | H | 786000 | 0 | 0 | 449254761 | 1875039520 | 449254761/468759880 | 1896331892 | 449254761/474082973 |
| 1995 | 600 | u | V | 786000 | 0 | 0 | 487117529 | 1963808352 | 487117529/490952088 | 1898539448 | 487117529/474634862 |
| 1995 | 600 | u | D | 786000 | 0 | 0 | 450065709 | 1874545184 | 450065709/468636296 | 1899880112 | 450065709/474970028 |
| 1995 | 600 | signed_digit | H | 786000 | 0 | 0 | 95421921 | 373691464 | 95421921/93422866 | 373661722 | 27263406/26690123 |
| 1995 | 600 | signed_digit | V | 786000 | 0 | 0 | 91332993 | 374146240 | 91332993/93536560 | 374008394 | 182665986/187004197 |
| 1995 | 600 | signed_digit | D | 786000 | 0 | 0 | 95613109 | 373448140 | 95613109/93362035 | 373478498 | 191226218/186739249 |
| 1995 | 600 | signed_low3 | H | 786000 | 0 | 0 | 13486425 | 54542654 | 26972850/27271327 | 54768472 | 13486425/13692118 |
| 1995 | 600 | signed_low3 | V | 786000 | 0 | 0 | 13991785 | 55307878 | 27983570/27653939 | 54794692 | 13991785/13698673 |
| 1995 | 600 | signed_low3 | D | 786000 | 0 | 0 | 13490429 | 54607706 | 26980858/27303853 | 54751356 | 13490429/13687839 |
| 6343 | 600 | u | H | 786000 | 0 | 0 | 3386482215 | 15955955720 | 677296443/797797786 | 15985093198 | 6772964430/7992546599 |
| 6343 | 600 | u | V | 786000 | 0 | 0 | 4378173499 | 15966683572 | 625453357/570238699 | 16002909930 | 1250906714/1143064995 |
| 6343 | 600 | u | D | 786000 | 0 | 0 | 3385011595 | 15967366404 | 3385011595/3991841601 | 16004959334 | 967146170/1143211381 |
| 6343 | 600 | signed_digit | H | 786000 | 0 | 0 | 108474511 | 446288908 | 108474511/111572227 | 446440228 | 108474511/111610057 |
| 6343 | 600 | signed_digit | V | 786000 | 0 | 0 | 114204003 | 446078492 | 114204003/111519623 | 446373424 | 114204003/111593356 |
| 6343 | 600 | signed_digit | D | 786000 | 0 | 0 | 108901331 | 446421800 | 9900121/10145950 | 446222108 | 108901331/111555527 |
| 6343 | 600 | signed_low3 | H | 786000 | 0 | 0 | 15193143 | 64267448 | 2170449/2295266 | 64288748 | 15193143/16072187 |
| 6343 | 600 | signed_low3 | V | 786000 | 0 | 0 | 16820363 | 64301692 | 2402909/2296489 | 64172892 | 2402909/2291889 |
| 6343 | 600 | signed_low3 | D | 786000 | 0 | 0 | 15172443 | 64269244 | 1167111/1235947 | 64289432 | 15172443/16072358 |

Unknown framing and candidate mappings limit interpretation. The defined surrogate is not the historical private Haar/lifting ratio; it establishes neither physical rows nor original values.

## Reproduce

Retained verified public CC0 inputs:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`

At commit `d8c47065da3d6f8115e650749d8387b5ce35f393`, verify identities and hashes, substitute paths, and run:

```text
python -I -B tools/token_haar_control_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --rows 300
python -I -B tools/token_haar_control_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --rows 300
python -I -B tools/token_haar_control_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --rows 600
python -I -B tools/token_haar_control_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --rows 600
python -I -B tools/token_haar_control_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --rows 600
python -I -B tools/token_haar_control_probe.py --sample 6343 "OM System - OM-5 - 16bit (4:3).ORF" FILE6343 --rows 600
```

The output contains individual null energies, seeds, exact ratios and endpoints. Separately justified transforms, mappings and framing remain open on the existing corpus.
