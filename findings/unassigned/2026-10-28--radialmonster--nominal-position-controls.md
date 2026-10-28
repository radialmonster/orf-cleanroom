# Fixed nominal-position controls on four public files

Author: @radialmonster
Verified by: @radialmonster
Lead: #630
Variant: unassigned
Builds on: #29, #11, #185

## Claim

For two previously studied public files, the mean zero-position window contrast exceeds all three fixed nominal-position controls in both ordinary q and unsigned suffix for 1993 and in neither field for 5283. This is a descriptive candidate-token comparison, not a physical-row or historical-estimator claim.

## Original evidence

The lead used the first 262144 complete stop-1/five-suffix candidate words, partitioned from token zero into W-token nominal rows. Its exact four signed common-row contrasts for each field and file are in #630; the first two verification cases below reproduce them exactly. Both discovery files were already exposed in #185.

## Verification

After the lead, fresh runs reproduced both discovery records and evaluated the predeclared 524288-token extent on all four files. The two additional files are previously studied, not blind or independently verified captures. Each primary aggregate matched an independent bitwise parser and row aggregator exactly; both share the TIFF locator and assisted the same human. All six requested prefixes completed; all nominal rows had all four valid comparisons, with zero common exclusions and no zero-control ties.

For each row, the table gives file ID, prefix size, field, common rows, offsets, signed contrasts in offset order rounded to six decimals, whether the zero contrast exceeds all three, incomplete tail tokens and parsed escapes. Exact fractions follow. The offsets are 0, floor(W/4), floor(W/2), floor(3W/4), each window has 24 candidate positions, and its contrast is against its own complement. Ordinary q and unsigned suffix omit q>=17 tokens without compacting indices. Row contrasts are averaged equally over the common valid-row intersection.

| ID | Tokens | Field | Common rows | Offsets | Contrasts (offset order) | Zero exceeds all | Tail | Escapes |
|---|---:|---|---:|---|---|---|---:|---:|
| 1993 | 262144 | q | 50 | 0,1310,2620,3930 | +0.431483, -0.017598, +0.004169, -0.010063 | True | 144 | 1 |
| 1993 | 262144 | suffix | 50 | 0,1310,2620,3930 | +0.631741, +0.155685, -0.349127, +0.206752 | True | 144 | 1 |
| 5283 | 262144 | q | 50 | 0,1305,2610,3915 | -0.025821, -0.016310, +0.001273, +0.017867 | False | 1144 | 313 |
| 5283 | 262144 | suffix | 50 | 0,1305,2610,3915 | +0.257480, -0.439357, +0.207981, +0.316726 | False | 1144 | 313 |
| 1993 | 524288 | q | 100 | 0,1310,2620,3930 | +0.335133, -0.022517, +0.004273, -0.014564 | True | 288 | 1 |
| 1993 | 524288 | suffix | 100 | 0,1310,2620,3930 | +0.480476, -0.497189, -0.616067, +0.401929 | True | 288 | 1 |
| 5283 | 524288 | q | 100 | 0,1305,2610,3915 | -0.034233, +0.016951, -0.034226, +0.023755 | False | 2288 | 597 |
| 5283 | 524288 | suffix | 100 | 0,1305,2610,3915 | +0.255078, -0.425780, +0.176349, +0.285966 | False | 2288 | 597 |
| 6343 | 524288 | q | 100 | 0,1310,2620,3930 | -0.006289, -0.009328, -0.031931, -0.023141 | True | 288 | 67 |
| 6343 | 524288 | suffix | 100 | 0,1310,2620,3930 | -0.115091, -0.149805, -0.190826, -0.227243 | True | 288 | 67 |
| 4126 | 524288 | q | 100 | 0,1300,2600,3900 | +0.017592, +0.018959, +0.010588, -0.029179 | False | 4288 | 1 |
| 4126 | 524288 | suffix | 100 | 0,1300,2600,3900 | +0.141179, -0.007897, +0.068288, -0.045990 | True | 4288 | 1 |

Ranking is separate from an elevated window: 6343 has the highest zero contrast among the four offsets for both fields at 524288, but its zero contrasts are negative for both fields. The 4126 q criterion is false and its suffix criterion true. These are not calibrated tests or causal conclusions.

Exact signed fractions, in the same offset order:

```text
EXACT 1993 262144 q 2588209/5998400 -71802139/4080216000 17009317/4080216000 -5865673/582888000
EXACT 1993 262144 suffix 11368307/17995200 10587139/68003600 -237419013/680036000 843593887/4080216000
EXACT 5283 262144 q -21814853649377901708444871175047129/844854666293588906626830865762056000 -1238233289850767146831943232565718489/75919714694798457470639957451658512000 16714420139369650298021359551435329363/13134110642200133142420712639136922576000 71792781967189307096740767717758383/4018150369388175874909236375367773600
EXACT 5283 262144 suffix 652598960246138448863316060059320151/2534563998880766719880492597286168000 -2457833608149740826243675379600160465953/5594158236492649301401414642595355912000 3490430744788937463612342449450670577423/16782474709477947904204243927786067736000 95677917728909109416614750961062178253931/302084544770603062275676390700149219248000
EXACT 1993 524288 q 12061579/35990400 -183747329/8160432000 34865477/8160432000 -16978093/1165776000
EXACT 1993 524288 suffix 4323133/8997600 -405728081/816043200 -5027375053/8160432000 409988939/1020054000
EXACT 5283 524288 q -344905974245079531047938508546904910261/10075314322884194505978271489645398828000 1525855705187485062844506648000285089831/90017722105492924017205866998866304701200 -84755394747953914287014806569533532296489/2476376861083916012489141637597270674784000 86982468315290124194454931925678621509/3661630845704279542735471402426051142400
EXACT 5283 524288 suffix 10279959054906332530354435055044174468187/40301257291536778023913085958581595312000 -5557520791422579511338937389823969757425079/13052569705296473982494850714835614181674000 3249604315203396720624542865198330153486197/18427157231006786798816259832709102374128000 705190591798408136923998688223354200547/2465996283841657651230011352654279340800
EXACT 6343 524288 q -356500008123057/56683574400252800 -172408972759399/18483774260952000 -295103455209907/9241887130476000 -71288326646907/3080629043492000
EXACT 6343 524288 suffix -97856762484663487/850253616003792000 -251723607538699/1680343114632000 -1763590221303121/9241887130476000 -2800204104515997/12322516173968000
EXACT 4126 524288 q 26179/1488100 8464081/446430000 630211/59524000 -3907963/133929000
EXACT 4126 524288 suffix 336141/2380960 -1322111/167411250 18291373/267858000 -123187499/2678580000
```

## Reproduce

At commit 944407a1fd16dbb67b081af2488cd1f982fde339 obtain the public CC0 files listed below and verify their manifest identities and retained licence records. Run `python -I -B tools/token_position_control_probe.py --sample <public-name> <sha256> <local-path> --tokens <262144-or-524288>` for each applicable case. The tool emits all exact counts, sums, means, endpoint, omissions, ties and shortfalls. Public names and SHA-256 values:

| ID | Public name | SHA-256 |
|---|---|---|
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 |
| 5283 | OM System - OM-1 - 16bit (4:3).ORF | bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b |
| 6343 | OM System - OM-5 - 16bit (4:3).ORF | ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7 |
| 4126 | Olympus - E-M10 Mark IV - 16bit (4:3).ORF | ce03e936cb2e8131343e7045a3249f78477bd2ae944e121ace72058b89fef509 |

## Limitations

The candidate parser, origin and W are assumptions; these are not established physical rows, a camera codec, or the historical unspecified #29 statistic. The correlated fixed windows do not form a calibrated null or significance test. Alternative candidate origins and field definitions on the existing corpus remain open, as does independent physical framing.
