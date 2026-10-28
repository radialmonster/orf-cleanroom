# Nominal half-width candidate difference energies

Author: @radialmonster
Verified by: @radialmonster
Lead: #677
Variant: unassigned
Builds on: #31, #671

## Claim

For two previously studied public files, fixed candidate-token difference energies at nominal half-width and its adjacent offsets differ by mapping and shuffle mode. These descriptive comparisons do not reproduce #31's unavailable private second-difference method or establish physical rows or a predictor.

## Original evidence

The lead used `tools/token_row_dpcm_probe.py` at commit `e7b15528c813489516894924404f58277c293a9e` on 300 nominal rows of 1993 and 5283. The freshly reproduced values are included below.

## Verification

After publication, both original 300-row cases were freshly reproduced and the predeclared 600-row extent was measured on 1993, 5283, 1995 and 6343. The later extent and additional files qualify the verification; all files were exposed previously, and the verifier is the finder. Independent implementations matched every real and shuffled energy, exact fraction and metadata. The reference reused a previously authored literal parser; both implementations share a TIFF locator and assisted the same human.

Parse stop-1 k=5 candidate words without extra escape skipping, retaining q>=17. Take the indicated number of nominal W-token rows, where W is payload width. Map each token with u=32*q+s, signed_digit=4*(s>>3)+(s&3)-8*((s>>2)&1), and signed_low3=(s&7)-8 when bit 2 is set, otherwise s&7. For all three offsets h-1, h, h+1, where h=floor(W/2), use identical target indices [2W+1,N), reporting the sum of squared differences. Four within-nominal-row and four global whole-value shuffles use independent generators with seed 20261021+1000*ID+10*mapping_index+replicate. Both modes preserve the overall multiset; only within-row preserves each nominal row multiset. These controls are descriptive, not calibrated significance tests.

The table gives the real sum, each mode's sum of four null sums (its mean is one quarter of that number), and exact real-over-mean-null fractions. W is 5240 for 1993/1995 and 5220 for 5283/6343. All three offsets share the shown pair count; a zero null denominator would be undefined. All requested prefixes completed.

| ID | Rows | Mapping | Offset | Pairs | Real sum | Within-row four-null sum | Within-row ratio | Global four-null sum | Global ratio |
|---|---:|---|---:|---:|---:|---:|---|---:|---|
| 1993 | 300 | u | 2619 | 1561519 | 571227891 | 2244252405 | 761637188/748084135 | 2310543109 | 2284911564/2310543109 |
| 1993 | 300 | u | 2620 | 1561519 | 570286085 | 2245383720 | 114057217/112269186 | 2309971695 | 456228868/461994339 |
| 1993 | 300 | u | 2621 | 1561519 | 570842325 | 2247680771 | 2283369300/2247680771 | 2310248826 | 126853850/128347157 |
| 1993 | 300 | signed_digit | 2619 | 1561519 | 84972803 | 337282005 | 339891212/337282005 | 337567933 | 339891212/337567933 |
| 1993 | 300 | signed_digit | 2620 | 1561519 | 83764221 | 337461578 | 167528442/168730789 | 337657040 | 83764221/84414260 |
| 1993 | 300 | signed_digit | 2621 | 1561519 | 85039765 | 337575122 | 170079530/168787561 | 337692609 | 340159060/337692609 |
| 1993 | 300 | signed_low3 | 2619 | 1561519 | 13028915 | 51436384 | 13028915/12859096 | 51811809 | 52115660/51811809 |
| 1993 | 300 | signed_low3 | 2620 | 1561519 | 12937333 | 51486900 | 12937333/12871725 | 51838486 | 25874666/25919243 |
| 1993 | 300 | signed_low3 | 2621 | 1561519 | 13009013 | 51474766 | 26018026/25737383 | 51830938 | 26018026/25915469 |
| 5283 | 300 | u | 2609 | 1555559 | 8390588001 | 33139539802 | 16781176002/16569769901 | 33202691299 | 33562352004/33202691299 |
| 5283 | 300 | u | 2610 | 1555559 | 8378071899 | 33140828554 | 16756143798/16570414277 | 33206255315 | 33512287596/33206255315 |
| 5283 | 300 | u | 2611 | 1555559 | 8397621820 | 33151956623 | 33590487280/33151956623 | 33206807661 | 33590487280/33206807661 |
| 5283 | 300 | signed_digit | 2609 | 1555559 | 115298721 | 461176064 | 115298721/115294016 | 461088682 | 230597442/230544341 |
| 5283 | 300 | signed_digit | 2610 | 1555559 | 115275275 | 461147181 | 461101100/461147181 | 461009385 | 92220220/92201877 |
| 5283 | 300 | signed_digit | 2611 | 1555559 | 115147724 | 460889099 | 460590896/460889099 | 460806231 | 460590896/460806231 |
| 5283 | 300 | signed_low3 | 2609 | 1555559 | 16379105 | 65455270 | 6551642/6545527 | 65455192 | 16379105/16363798 |
| 5283 | 300 | signed_low3 | 2610 | 1555559 | 16369563 | 65485526 | 32739126/32742763 | 65539708 | 16369563/16384927 |
| 5283 | 300 | signed_low3 | 2611 | 1555559 | 16363484 | 65483785 | 3444944/3446515 | 65476738 | 32726968/32738369 |
| 1993 | 600 | u | 2619 | 3133519 | 1441707440 | 5611455677 | 5766829760/5611455677 | 5753726692 | 1441707440/1438431673 |
| 1993 | 600 | u | 2620 | 3133519 | 1439557706 | 5611995855 | 5758230824/5611995855 | 5755572837 | 5758230824/5755572837 |
| 1993 | 600 | u | 2621 | 3133519 | 1440864012 | 5614281666 | 137225144/133673373 | 5757130253 | 823350864/822447179 |
| 1993 | 600 | signed_digit | 2619 | 3133519 | 177678224 | 706815837 | 710712896/706815837 | 707094591 | 710712896/707094591 |
| 1993 | 600 | signed_digit | 2620 | 3133519 | 175939282 | 706803033 | 703757128/706803033 | 707157252 | 175939282/176789313 |
| 1993 | 600 | signed_digit | 2621 | 3133519 | 177779132 | 707191228 | 10457596/10399871 | 707227652 | 177779132/176806913 |
| 1993 | 600 | signed_low3 | 2619 | 3133519 | 26870480 | 106650996 | 26870480/26662749 | 107250529 | 107481920/107250529 |
| 1993 | 600 | signed_low3 | 2620 | 3133519 | 26727706 | 106739036 | 26727706/26684759 | 107213884 | 26727706/26803471 |
| 1993 | 600 | signed_low3 | 2621 | 3133519 | 26869516 | 106684605 | 107478064/106684605 | 107196426 | 53739032/53598213 |
| 5283 | 600 | u | 2609 | 3121559 | 16756105863 | 66235169155 | 67024423452/66235169155 | 66334185825 | 22341474484/22111395275 |
| 5283 | 600 | u | 2610 | 3121559 | 16746321617 | 66240391797 | 66985286468/66240391797 | 66323736617 | 66985286468/66323736617 |
| 5283 | 600 | u | 2611 | 3121559 | 16760928475 | 66242950673 | 67043713900/66242950673 | 66343922802 | 33521856950/33171961401 |
| 5283 | 600 | signed_digit | 2609 | 3121559 | 231589223 | 926533705 | 926356892/926533705 | 926217899 | 926356892/926217899 |
| 5283 | 600 | signed_digit | 2610 | 3121559 | 231511601 | 926576573 | 926046404/926576573 | 926226968 | 231511601/231556742 |
| 5283 | 600 | signed_digit | 2611 | 3121559 | 231389043 | 926071258 | 462778086/463035629 | 926770578 | 154259362/154461763 |
| 5283 | 600 | signed_low3 | 2609 | 3121559 | 32879751 | 131346450 | 21919834/21891075 | 131364135 | 43839668/43788045 |
| 5283 | 600 | signed_low3 | 2610 | 3121559 | 32835121 | 131402311 | 131340484/131402311 | 131383065 | 11940044/11943915 |
| 5283 | 600 | signed_low3 | 2611 | 3121559 | 32845259 | 131403805 | 131381036/131403805 | 131398893 | 131381036/131398893 |
| 1995 | 600 | u | 2619 | 3133519 | 945725524 | 3770872317 | 3782902096/3770872317 | 3782230499 | 3782902096/3782230499 |
| 1995 | 600 | u | 2620 | 3133519 | 940298346 | 3769256488 | 470149173/471157061 | 3783127836 | 313432782/315260653 |
| 1995 | 600 | u | 2621 | 3133519 | 944134805 | 3768070935 | 755307844/753614187 | 3784257752 | 944134805/946064438 |
| 1995 | 600 | signed_digit | 2619 | 3133519 | 187616396 | 745716247 | 750465584/745716247 | 745139582 | 34112072/33869981 |
| 1995 | 600 | signed_digit | 2620 | 3133519 | 184749274 | 745144525 | 738997096/745144525 | 745220124 | 184749274/186305031 |
| 1995 | 600 | signed_digit | 2621 | 3133519 | 187783165 | 745642428 | 187783165/186410607 | 745063795 | 150226532/149012759 |
| 1995 | 600 | signed_low3 | 2619 | 3133519 | 27376388 | 109180235 | 109505552/109180235 | 109167943 | 109505552/109167943 |
| 1995 | 600 | signed_low3 | 2620 | 3133519 | 27193386 | 109187613 | 36257848/36395871 | 109190676 | 9064462/9099223 |
| 1995 | 600 | signed_low3 | 2621 | 3133519 | 27407301 | 109251032 | 27407301/27312758 | 109210246 | 54814602/54605123 |
| 6343 | 600 | u | 2619 | 3133519 | 8148246583 | 31777617892 | 8148246583/7944404473 | 31905559929 | 32592986332/31905559929 |
| 6343 | 600 | u | 2620 | 3133519 | 8148933706 | 31765511411 | 32595734824/31765511411 | 31913627206 | 16297867412/15956813603 |
| 6343 | 600 | u | 2621 | 3133519 | 8146486959 | 31766945707 | 32585947836/31766945707 | 31898834186 | 16292973918/15949417093 |
| 6343 | 600 | signed_digit | 2619 | 3133519 | 222393855 | 889442868 | 74131285/74120239 | 889611061 | 889575420/889611061 |
| 6343 | 600 | signed_digit | 2620 | 3133519 | 222503938 | 889418101 | 890015752/889418101 | 889597376 | 111251969/111199672 |
| 6343 | 600 | signed_digit | 2621 | 3133519 | 222565655 | 889851105 | 13696348/13690017 | 889744262 | 445131310/444872131 |
| 6343 | 600 | signed_low3 | 2619 | 3133519 | 32131399 | 128087818 | 64262798/64043909 | 128199559 | 128525596/128199559 |
| 6343 | 600 | signed_low3 | 2620 | 3133519 | 32130266 | 128117883 | 128521064/128117883 | 128179313 | 128521064/128179313 |
| 6343 | 600 | signed_low3 | 2621 | 3133519 | 32138527 | 128091846 | 64277054/64045923 | 128094029 | 128554108/128094029 |

Unknown framing and the candidate mappings limit interpretation. These nominal strides do not establish physical rows or original values; no original private-method reproduction or causal claim is made.

## Reproduce

Retained verified public CC0 inputs:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`

At commit `e7b15528c813489516894924404f58277c293a9e`, verify identities and hashes, substitute local paths, and run:

```text
python -I -B tools/token_row_dpcm_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --rows 300 --offset-family half
python -I -B tools/token_row_dpcm_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --rows 300 --offset-family half
python -I -B tools/token_row_dpcm_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --rows 600 --offset-family half
python -I -B tools/token_row_dpcm_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --rows 600 --offset-family half
python -I -B tools/token_row_dpcm_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --rows 600 --offset-family half
python -I -B tools/token_row_dpcm_probe.py --sample 6343 "OM System - OM-5 - 16bit (4:3).ORF" FILE6343 --rows 600 --offset-family half
```

The output contains individual null sums, seeds, exact ratios and endpoints. Separately justified offsets, mappings and framing remain open on the existing corpus.
