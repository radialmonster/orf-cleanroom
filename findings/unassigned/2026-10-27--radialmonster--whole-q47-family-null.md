# Whole-payload candidate family null counts reproduce on a fourth q47 file

Author: @radialmonster
Verified by: @radialmonster
Lead: #581
Variant: unassigned
Builds on: #86, 2026-10-27--radialmonster--q47-family-null-reproduction

## Claim
The fixed nine-family whole-payload real and measured-density Bernoulli counts reproduce on three selected public q47 files. Predeclared 7803 is a separate additional previously studied file. These candidate counts do not identify a codec, framing, physical pixel correspondence, statistical significance or variant membership.

## Original evidence
Use the full logical payload from bit 0, MSB first, with nine candidate families frozen before outcomes at https://github.com/radialmonster/orf-cleanroom/issues/86#issuecomment-6454077927. Each entry is real completed words / consumed bits; null completed words / consumed bits. Residual bits equal payload bytes times eight minus consumed bits; count per stored site is completed words divided by measured width times height. A zero count is an observed zero, not a completed parse.

For each file, p is the full payload ones count divided by its bit length. One same-length Bernoulli buffer uses one Python Random(20261021).random() draw per bit in MSB-first order, resetting seed per file and sharing the buffer among families. Density is preserved in expectation, not exactly; seed reuse induces dependence. One realization does not establish significance. The full-payload p differs from the earlier prefix-only #577 method.
| Family | 7267 real; null | 7269 real; null | 7801 real; null |
|---|---:|---:|---:|
| rice_stop1_k5 | 96747418 / 683815003; 96071513 / 683815003 | 61335792 / 440653840; 61512501 / 440653839 | 95492254 / 664216082; 94139922 / 664216087 |
| rice_stop1_k4 | 110524010 / 683815007; 111775503 / 683815008 | 70040168 / 440653839; 71492825 / 440653836 | 109845699 / 664216085; 109686026 / 664216088 |
| rice_stop1_k3 | 131875138 / 683815006; 133619438 / 683815005 | 83446718 / 440653838; 85338215 / 440653839 | 131877967 / 664216088; 131384102 / 664216087 |
| rice_stop0_k5 | 99339141 / 683815007; 99180685 / 683815005 | 64246936 / 440653835; 64242078 / 440653838 | 95949164 / 664216087; 95607363 / 664216086 |
| exp_golomb_k2 | 129192944 / 683815008; 130617723 / 683815007 | 80470468 / 440653838; 82719655 / 440653837 | 131674771 / 664216087; 129953490 / 664216086 |
| exp_golomb_k3 | 107951137 / 683815006; 109672251 / 683815004 | 67386014 / 440653838; 69642445 / 440653840 | 109733798 / 664216088; 108691574 / 664216088 |
| elias_gamma_k0 | 211815458 / 683815008; 211369333 / 683815005 | 131254144 / 440653840; 132449878 / 440653840 | 217043810 / 664216086; 213511233 / 664216087 |
| elias_delta_k0 | 0 / 0; 10923605 / 676647994 | 0 / 0; 5808746 / 440115129 | 0 / 0; 20519114 / 664216084 |
| fibonacci_k0 | 103675743 / 683815008; 103572866 / 683815002 | 65334443 / 440653840; 64384618 / 440653840 | 103724161 / 664216086; 105751052 / 664216087 |

| ID | input SHA-256 | width x height | payload bytes | ones count | null SHA-256 |
|---|---|---|---:|---:|---|
| 7267 | 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756 | 10386 x 7792 | 85476876 | 322909592 | 96191c0ebe5e85002a2ed4d8db3c750d9139a5381bbc3caf61a79a3a25173ecf |
| 7269 | dd2a6c1c4ca4d86201207925477e2ea8e50ebd53d7df9117847093f5023540ec | 8172 x 6132 | 55081730 | 203667902 | 871358a3779da4a85c993014727e0cb7746119ef13d3406e37c5a75d1d4b68c9 |
| 7801 | 8832599870d20a96f28897e3e28d9705a4bd05871c9833c7c60a8b59d7d64b82 | 10386 x 7792 | 83027011 | 323134538 | 508b62fcb4250f8528a515b27bcaad8641116dee1c86862826943f87cc9f9f21 |

All three files matched retained verified CC0 identity/hash records, manifest rows and local hashes. Public names: 7267 and 7269 are OM System - OM-1 Mark II - 16bit (4:3).orf; 7801 is OM System - OM-3 - 16bit (4:3).ORF. These selected files are previously studied and are not independent captures. The 7267 pilot matched an independent per-bit parser and bytewise null generator on all 18 cells and null hash; these implementations assist the same human. Remaining initial files are primary tool results and will be freshly independently rerun post-lead as predeclared in https://github.com/radialmonster/orf-cleanroom/issues/86#issuecomment-6454846324.


## Verification
After #581 was posted and its current body scanned clean, a separately implemented per-bit counter and bytewise Bernoulli generator freshly reran all three original files. All 54 original real/null cells, endpoints, residuals, rates, ones counts, null hashes and identities match the published-tool reports exactly. Both implementations assist the same human verifier.

The predeclared additional public 7803, OM System - OM-3 - 16bit (4:3).ORF, SHA-256 `63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0`, was not used in the lead but was studied before this design. Its owner-verified CC0 record, manifest identity and hash matched. The published tool and independent counter agreed exactly in all 18 real/null cells and identity/null fields. It is a separate file, not a blind or independently captured cohort.

7803 geometry is 8172 x 6132, payload 52903737 bytes, ones count 201662218, and null SHA-256 `ac06cc3ef6a0a034971e941640016b10ea75f8e7f5bf0f0da5aff7eb86a36189`. Each table entry is completed words / consumed bits; residual bits equal 423229896 minus the endpoint, and counts per stored site equal count / 50110704. The control uses the same fixed seed and full-payload p, with the limitations above.

| Family | 7803 real count / end; null count / end |
|---|---:|
| rice_stop1_k5 | 60282029 / 423229891; 59620158 / 423229891 |
| rice_stop1_k4 | 69158388 / 423229895; 69395812 / 423229895 |
| rice_stop1_k3 | 82726592 / 423229894; 83005992 / 423229893 |
| rice_stop0_k5 | 61480679 / 423229895; 61249412 / 423229889 |
| exp_golomb_k2 | 81575832 / 423229896; 81432439 / 423229895 |
| exp_golomb_k3 | 68155395 / 423229894; 68290430 / 423229896 |
| elias_gamma_k0 | 133510662 / 423229896; 132376128 / 423229892 |
| elias_delta_k0 | 0 / 0; 6476204 / 235397625 |
| fibonacci_k0 | 64421675 / 423229896; 65085935 / 423229891 |

Real Elias delta completes zero words on all four files, with the entire payload residual. One null realization per file, reset seed dependence and full-payload p do not support significance or identify the actual grammar.

## Reproduce
At commit 8cec39a70a4e550f0890dc138e6f964f13fda548, set FILE to each hash-matched public file above. The tool prints aggregate JSON only; Python 3.14.7 was used.

```sh
python -I -B tools/whole_family_null.py "$FILE" --seed 20261021
```

The elapsed-time field can differ across runs. Peak working set for the 7267 primary pilot was 192946176 bytes; its reported elapsed time was 1402.06 seconds. Resource observations are local, not scientific evidence.

Apply the same command to the hash-matched 7803 file above. Independent verification followed the same declared parse/null method; it is not a different human verifier.
