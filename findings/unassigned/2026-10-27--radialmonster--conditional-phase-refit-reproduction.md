# Conditional phase and period refit reproduction

Author: @radialmonster
Verified by: @radialmonster
Lead: #512
Variant: unassigned
Builds on: #144, 2026-10-27--radialmonster--common-interval-phase-reproduction

## Claim

The fixed common-interval joint-minus-fixed comparisons and their conditional rotation ranks in #512 reproduce for the two named files. These are descriptive references for this particular block-rotation procedure, not calibrated significance, physical row evidence or proof of a period change.

## Original evidence

The lead uses `tools/token_phase_rotation_control.py` at `c8c45b0e7e16951ee9839c2acb6d965859b1dc10`, q capped at 40, anchor 10480000, strides 5176..5304, every phase, 100 training rows and head 32. The fixed-period comparator fits phase at stride 5240; the joint comparator fits both. All 675960 training pairs are searched, with lowest stride then phase on ties. The frozen models are scored using their own head masks over common token interval [11021008,11538608), with partial edge heads included.

| Public ID and name | SHA-256 | Joint S, phase; contrast | Fixed S, phase; contrast | Difference | References at least as large |
| --- | --- | --- | --- | --- | --- |
| 1995, Olympus - E-M1MarkII - 16bit (4:3).ORI | 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f | 5246, 1618; 8634943/50928768 | 5240, 2720; 617363/4629888 | 307325/8488128 | 2/16 |
| 1998, Olympus - E-M1MarkII - 16bit (4:3).ORF | 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 | 5245, 2006; 157195/1591524 | 5240, 3025; 1865455/16976256 | -566125/50928768 | 10/16 |

The 1998 observed difference is negative; both files have zero ties and zero undefined references. Each observed model has 3168 head and 514432 rest tokens.

In each of 16 replicates, both models are refitted after independently rotating blocks in training [10480000,11021008) and test [11021008,11538608). Training has 103 complete blocks of 5240 and a partial block of 1288; test has 98 complete blocks of 5240 and a partial block of 4080. Each block rotates left by a uniform shift drawn using `random.Random(20261027)`, reset per file, using `getrandbits(n.bit_length())` with rejection for draws >= n. Order is replicate, training then test, blocks in increasing position. The two files therefore share the same shift sequence. The complete search and common test are rerun in every replicate.

## Verification

After #512 was posted, @radialmonster reran both files at the pinned commit, hash-matching retained verified CC0 records and existing manifest rows. Each complete fresh JSON report matched its original exactly except elapsed time, including all refits, shifts, scores and rank counts. This is self-verification by the same human, not independent-human verification.

The predeclared additional file 1997, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`, was run after the lead with the identical protocol. The joint model selected stride 5246, phase 1756: head 975/3168 and rest 83636/514432, contrast 308089/2122032. The fixed model selected stride 5240, phase 2828: head 900/3168 and rest 83711/514432, contrast 686779/5658752. The difference was 404375/16976256; 0/16 references were at least as large, with zero ties and zero undefined references. The sixteen exact signed reference differences, in replicate order, are:

| Replicate | Difference | Replicate | Difference |
| ---: | ---: | ---: | ---: |
| 0 | -572652349/68223328800 | 8 | -16175/6366096 |
| 1 | -16175/2122032 | 9 | -115988072197/3343359029472 |
| 2 | 16175/900312 | 10 | -26553082363/810460862400 |
| 3 | 80875/25208736 | 11 | 14691172361/818679945600 |
| 4 | 23875294679/4457812039296 | 12 | -1148425/50928768 |
| 5 | -16175/771648 | 13 | -472834773863/13373436117888 |
| 6 | -207864809/64605971584 | 14 | -888197707/40933997280 |
| 7 | 170548528487/13373436117888 | 15 | -145575/5658752 |

The maintainer independently rehashed and reparsed all three fresh inputs and searched all 34,473,960 training candidates across 51 fits using a separate column-fold calculation. Every selected joint/fixed model and exact training score matched. Direct per-token masks and Fraction arithmetic matched every common head/rest sum, count and contrast; independent per-index rotations matched all recorded shifts, comparisons and rank counts. Seven synthetic control tests passed. Both agents represent the same human.

All three files and windows were previously studied; 1997 had not been used in this control lead. Rotations preserve each block multiset and its cyclic order but introduce seams, change cross-block adjacency, rotate partial blocks separately and privilege the 5240-token partition. Sixteen references give coarse descriptive resolution; neither these conditional ranks nor 0/16 establish exchangeability, a general no-stride-change null, significance, independent captures, physical rows, escape framing or a codec.

## Reproduce

At `c8c45b0e7e16951ee9839c2acb6d965859b1dc10`, substitute paths to the hash-matched public CC0 files:

```sh
python -I -B tools/token_phase_rotation_control.py --sample 1995 'Olympus - E-M1MarkII - 16bit (4:3).ORI' 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f "$FILE1995" --replicates 16
python -I -B tools/token_phase_rotation_control.py --sample 1998 'Olympus - E-M1MarkII - 16bit (4:3).ORF' 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 "$FILE1998" --replicates 16
python -I -B tools/token_phase_rotation_control.py --sample 1997 'Olympus - E-M1MarkII - 16bit (4:3).ORI' 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a "$FILE1997" --replicates 16
```
