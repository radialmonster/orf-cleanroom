# Candidate-token lag ranks across fixed bands

Author: @radialmonster
Verified by: @radialmonster
Lead: #650
Variant: unassigned
Builds on: #29, #11

## Claim

In the specified candidate-token bands, q>0 lag 3 has the largest observed mutual information and largest observed-minus-shuffle-mean excess among lags 1..5. The low3 maxima are lag 2 for the 1993 bands and lag 1 for the 5283 bands. These are descriptive finite-window ranks; they do not establish stationarity or physical row framing.

## Original evidence

The lead measured bands 0..3 on previously studied public files 1993 and 5283 with `tools/token_lag_band_probe.py` at commit `0e11c23af41913c777bf49fbbaf14f9a4cc2075f`. The fresh results for those eight cells appear below alongside the wider verification.

## Verification

After the lead was posted, the original eight cells were freshly reproduced, and the predeclared fifth band was measured on both original files and two additional files, 1995 and 6343. All four band-4 q>0 results also rank lag 3 highest for both observed MI and excess. For low3, both maxima are lag 2 on 1995 and lag 1 on 6343. The additional files and wider bands qualify this verification; they were previously exposed in other work and are not blind captures.

The parse starts at payload bit zero; band b comprises complete stop-1/five-suffix candidate-token indices b*262144 through (b+1)*262144-1, grouped into 2048 original 128-token blocks. Blocks containing q>=17 are omitted in their entirety. There was no token shortfall. Each field's unsmoothed MI is calculated within retained blocks at lags 1..5. The 16 descriptive controls independently shuffle whole tokens within each retained block, resetting `Random(20261021+replicate)` for each band and replicate. The table shows retained blocks, observed MI and observed-minus-mean-shuffled MI in bits, in lag order, and all maximizing lags. Ties use exact equality of the primary Python floats; displayed numbers are rounded and do not define ties.

| ID | Band | Field | Retained blocks | Observed MI lags 1..5 | Excess lags 1..5 | Observed maxima | Excess maxima |
|---|---:|---|---:|---|---|---|---|
| 1993 | 0 | q_positive | 2047 | 0.000184143388, 0.000335386475, 0.0246230867, 0.00654135105, 0.00260715704 | 0.000101460203, 0.000257233497, 0.0245405415, 0.00645272707, 0.00251862606 | 3 | 3 |
| 1993 | 0 | low3 | 2047 | 0.000540569983, 0.0414808534, 0.000224689284, 0.00113714527, 0.000187724885 | 0.00039432689, 0.0413420266, 7.88490467e-05, 0.000999637756, 4.23061349e-05 | 2 | 2 |
| 1993 | 1 | q_positive | 2048 | 0.000412679566, 0.000123801019, 0.0269347175, 0.00979945712, 0.00471950749 | -0.000868636199, -0.00107800057, 0.0256782382, 0.00853134846, 0.00346436993 | 3 | 3 |
| 1993 | 1 | low3 | 2048 | 0.00163436784, 0.0198102014, 0.000427916462, 0.00319141834, 0.000599247749 | 0.000837513449, 0.0190520577, -0.000378481414, 0.00237385277, -0.000171381097 | 2 | 2 |
| 1993 | 2 | q_positive | 2048 | 0.000633257008, 0.000330570298, 0.0239000011, 0.00839416051, 0.00498475864 | -0.000389249694, -0.000744408725, 0.0228375892, 0.0073775771, 0.00392541577 | 3 | 3 |
| 1993 | 2 | low3 | 2048 | 0.00448813272, 0.0128210238, 0.00266475976, 0.00829737543, 0.00321257103 | 0.00114066791, 0.00963501791, -0.000535046861, 0.00505777741, -2.60570215e-05 | 2 | 2 |
| 1993 | 3 | q_positive | 2048 | 0.00112046896, 0.000595305543, 0.0251396255, 0.0105356644, 0.00546818732 | 0.000139800334, -0.000296840909, 0.0242397568, 0.00954217691, 0.00451575381 | 3 | 3 |
| 1993 | 3 | low3 | 2048 | 0.0017674757, 0.019925269, 0.000298483174, 0.00354780026, 0.000640741876 | 0.00101878203, 0.0192165271, -0.000413358069, 0.00281838706, -5.64601456e-05 | 2 | 2 |
| 1993 | 4 | q_positive | 2048 | 0.00226622998, 0.00107574898, 0.0283265973, 0.0128413401, 0.00717385987 | 0.000289782297, -0.000853732137, 0.026368942, 0.0108661538, 0.00519773066 | 3 | 3 |
| 1993 | 4 | low3 | 2048 | 0.00201268301, 0.0173624055, 0.000267514208, 0.00271067704, 0.000350306291 | 0.00155041199, 0.0168753203, -0.00022528284, 0.00221349406, -0.000129321447 | 2 | 2 |
| 5283 | 0 | q_positive | 1787 | 0.000697381691, 0.000395093586, 0.00221593312, 0.00131175737, 0.00127523118 | 0.000144640219, -0.000199125046, 0.00162394792, 0.000788302677, 0.000725491851 | 3 | 3 |
| 5283 | 0 | low3 | 1787 | 0.00159732699, 0.000278207197, 0.000246149514, 0.000176510208, 0.000191153683 | 0.00140812506, 7.39879722e-05, 5.0910348e-05, -2.13296087e-05, 9.32038218e-06 | 1 | 1 |
| 5283 | 1 | q_positive | 1802 | 0.000484764304, 0.000194353993, 0.00200192192, 0.00101443965, 0.000990200927 | 0.000119342122, -0.000109645725, 0.00165892888, 0.000657336016, 0.000623837643 | 3 | 3 |
| 5283 | 1 | low3 | 1802 | 0.00132930675, 0.00036564298, 0.000212722408, 0.000229496109, 0.00026010098 | 0.00115991773, 0.000199701255, 5.51948127e-05, 6.46441345e-05, 0.000112450824 | 1 | 1 |
| 5283 | 2 | q_positive | 1760 | 0.000950139147, 0.000355777067, 0.00276426879, 0.0016007447, 0.0014122366 | 0.000266950877, -0.000343532338, 0.00208396327, 0.000932461679, 0.000749706155 | 3 | 3 |
| 5283 | 2 | low3 | 1760 | 0.00135577694, 0.000362781487, 0.000209252958, 0.000136729484, 0.000269882857 | 0.00117841328, 0.000167440735, 1.48731096e-05, -5.44141956e-05, 8.07088808e-05 | 1 | 1 |
| 5283 | 3 | q_positive | 1738 | 0.000802661071, 0.0005229409, 0.00252069253, 0.00167581497, 0.00132394883 | 0.000129319614, -0.000174155113, 0.00184814313, 0.000945784779, 0.000607974788 | 3 | 3 |
| 5283 | 3 | low3 | 1738 | 0.00137710084, 0.000403010637, 0.000104945613, 0.000258392946, 0.000268884558 | 0.00119319294, 0.000215291692, -8.81536035e-05, 6.81499847e-05, 7.98823083e-05 | 1 | 1 |
| 5283 | 4 | q_positive | 1771 | 0.00126379282, 0.000959843618, 0.00342909545, 0.00245358108, 0.00188740251 | 0.000324392169, 1.45634458e-05, 0.00245373072, 0.00145372853, 0.000946198073 | 3 | 3 |
| 5283 | 4 | low3 | 1771 | 0.00123425116, 0.000343153172, 0.000279106594, 0.000116949678, 0.000247621136 | 0.00105440631, 0.000172360605, 7.7411737e-05, -7.98021705e-05, 5.5052513e-05 | 1 | 1 |
| 1995 | 4 | q_positive | 2048 | 0.000157747082, 0.000363655573, 0.022733275, 0.00659749156, 0.00210654563 | 9.47695818e-05, 0.000303519748, 0.0226684075, 0.00652017174, 0.00203166171 | 3 | 3 |
| 1995 | 4 | low3 | 2048 | 0.00046925234, 0.0404635639, 0.00025843399, 0.000849996363, 0.00017727541 | 0.000331129687, 0.0403337283, 0.000110360731, 0.000718278652, 3.14930604e-05 | 2 | 2 |
| 6343 | 4 | q_positive | 2001 | 0.0147236539, 0.00916313093, 0.0221432465, 0.0175532629, 0.0144427979 | 0.00973124482, 0.00416129092, 0.0171607148, 0.0123820285, 0.00954647134 | 3 | 3 |
| 6343 | 4 | low3 | 2001 | 0.00649590725, 0.000828930539, 0.00165263498, 0.00186646549, 0.000886346417 | 0.00605067539, 0.00041532682, 0.00124546371, 0.00145013046, 0.000457841673 | 1 | 1 |

Independent literal parsing, selection, and joint counts matched exactly; observed and all 16 shuffled MI values matched within 1e-12. Maxima and exact-float ties were separately checked using the primary values. The two implementations share a TIFF locator and assisted the same human. These controls are not a calibrated significance test, and block omission does not establish the unknown framing.

## Reproduce

The retained verified public CC0 inputs are:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`

At commit `0e11c23af41913c777bf49fbbaf14f9a4cc2075f`, verify these identities and hashes, substitute the local paths, and run:

```text
python -I -B tools/token_lag_band_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --bands 0 1 2 3 4
python -I -B tools/token_lag_band_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --bands 0 1 2 3 4
python -I -B tools/token_lag_band_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --bands 4
python -I -B tools/token_lag_band_probe.py --sample 6343 "OM System - OM-5 - 16bit (4:3).ORF" FILE6343 --bands 4
```

The output includes block selection, pair tables, all shuffle values and endpoints. Other window and framing assumptions remain to be tested on the existing corpus.
