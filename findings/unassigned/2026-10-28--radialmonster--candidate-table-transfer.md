# Cross-file held-out candidate table transfer

Author: @radialmonster
Verified by: @radialmonster
Lead: #662
Variant: unassigned
Builds on: #29, #658

## Claim

For this fixed 2 by 2 cross-file candidate-token comparison, transferring the other file's training tables changes held-out KT losses relative to each target's own training tables. Both q>0 order-3 transfer losses are higher than the recipient-trained losses. These descriptive differences do not establish body causation or a physical codec.

## Original evidence

The lead reduced previously generated and independently audited #658 band-0 training and band-1 test reports using `tools/token_lag3_transfer_probe.py` at commit `790a4381b7ddeaafe50ff74e7bce9456a04a928e`. The two direct report byte SHA-256 values were `6033ceb82338a9f7314f09f51493a22c62b8aa3c07ea1d9503763df8ee28e6cc` (1993) and `47ba53f9f9c07d3a0efaf23fe85f01239abf13026ced903341826e030067f3cc` (5283). Fresh results for that matrix are included below.

## Verification

After the lead was posted, six fresh producer reports reproduced the original two band-1 cases and supplied the predeclared band-2 tests for 1993, 5283, 1995 and 6343. Each fresh report matched its previously independently audited #658 report exactly. The wider band and additional files qualify verification, but all inputs had been previously exposed and the verifier is the finder. A separate implementation independently recalculated all transfer cells from these shared aggregate reports: tables and context counts matched exactly and losses, gains and differences agreed within 1e-12. No new independent raw parser was run after this lead.

For each trainer and target, use the trainer's band-0 order-0, order-2 and order-3 KT half-count models on the target's test-band tables, separately for q>0 and suffix b0. Context uses preceding same-field bits at lags 1..order; no test updates. Compare each transfer loss to the same target's loss under its own band-0 training. Gain is order-2 loss minus order-3 loss; values are bits per target. The table retains all fixed cells and both fields. Diagonal differences are zero by construction. A positive gain can coexist with a higher absolute loss than the recipient-trained model: that happens for q>0 in both off-diagonal band-1 cells. For q>0 in band 2 the 1993-to-1995 order-0 loss is slightly lower while its order-2 and order-3 losses are higher than the recipient baseline.

| Test band | Trainer | Target | Field | Train targets | Test targets | Unseen order-3 targets | Transfer losses 0,2,3 | Transfer gain | Transfer minus recipient losses 0,2,3 | Transfer minus recipient gain |
|---:|---|---|---|---:|---:|---:|---|---:|---|---:|
| 1 | 1993 | 1993 | q_positive | 255875 | 256000 | 0 | 0.387667853, 0.388820659, 0.361135789 | 0.0276848692 | 0, 0, 0 | 0 |
| 1 | 1993 | 1993 | suffix_b0 | 255875 | 256000 | 0 | 0.999874755, 0.999884262, 0.999920012 | -3.5749644e-05 | 0, 0, 0 | 0 |
| 1 | 5283 | 1993 | q_positive | 223375 | 256000 | 0 | 0.915439657, 0.861455169, 0.788549579 | 0.0729055897 | 0.527771804, 0.47263451, 0.42741379 | 0.0452207205 |
| 1 | 5283 | 1993 | suffix_b0 | 223375 | 256000 | 0 | 1.00040079, 1.00048398, 1.0005181 | -3.4128483e-05 | 0.000526032059, 0.000599713611, 0.00059809245 | 1.621161e-06 |
| 1 | 1993 | 5283 | q_positive | 255875 | 225250 | 0 | 1.7447044, 1.78383418, 1.5478861 | 0.235948085 | 0.748503483, 0.78838479, 0.554894501 | 0.233490289 |
| 1 | 1993 | 5283 | suffix_b0 | 255875 | 225250 | 0 | 0.999443848, 0.999456407, 0.999480981 | -2.4574635e-05 | 0.000560976654, 0.00060302852, 0.000614964525 | -1.19360043e-05 |
| 1 | 5283 | 5283 | q_positive | 223375 | 225250 | 0 | 0.996200912, 0.995449394, 0.992991599 | 0.00245779568 | 0, 0, 0 | 0 |
| 1 | 5283 | 5283 | suffix_b0 | 223375 | 225250 | 0 | 0.998882871, 0.998853378, 0.998866017 | -1.26386307e-05 | 0, 0, 0 | 0 |
| 2 | 1993 | 1993 | q_positive | 255875 | 256000 | 0 | 0.280646682, 0.282609517, 0.254757247 | 0.0278522705 | 0, 0, 0 | 0 |
| 2 | 1993 | 1993 | suffix_b0 | 255875 | 256000 | 0 | 1.00003949, 1.00003063, 1.00007951 | -4.88801685e-05 | 0, 0, 0 | 0 |
| 2 | 5283 | 1993 | q_positive | 223375 | 256000 | 0 | 0.909070511, 0.845244791, 0.761009877 | 0.0842349145 | 0.628423829, 0.562635274, 0.50625263 | 0.056382644 |
| 2 | 5283 | 1993 | suffix_b0 | 223375 | 256000 | 0 | 1.00098107, 1.00104325, 1.00106576 | -2.25136114e-05 | 0.000941583808, 0.00101261794, 0.000986251381 | 2.63665571e-05 |
| 2 | 1993 | 5283 | q_positive | 255875 | 220000 | 0 | 1.74441144, 1.78181803, 1.54169426 | 0.240123768 | 0.748227963, 0.787016945, 0.550235689 | 0.236781257 |
| 2 | 1993 | 5283 | suffix_b0 | 255875 | 220000 | 0 | 0.999421999, 0.999448898, 0.999469759 | -2.0860502e-05 | 0.000616090812, 0.000745686623, 0.000748513921 | -2.82729749e-06 |
| 2 | 5283 | 5283 | q_positive | 223375 | 220000 | 0 | 0.996183477, 0.994801088, 0.991458576 | 0.00334251145 | 0, 0, 0 | 0 |
| 2 | 5283 | 5283 | suffix_b0 | 223375 | 220000 | 0 | 0.998805909, 0.998703212, 0.998721245 | -1.80332045e-05 | 0, 0, 0 | 0 |
| 2 | 1993 | 1995 | q_positive | 255875 | 256000 | 0 | 0.405406772, 0.404591768, 0.380805649 | 0.0237861192 | -9.46989288e-06, 2.75857405e-07, 1.52645783e-05 | -1.49887209e-05 |
| 2 | 1993 | 1995 | suffix_b0 | 255875 | 256000 | 0 | 0.999894135, 0.999885724, 0.99992338 | -3.76557618e-05 | -3.05161814e-06, -1.57315626e-05, 3.33178365e-05 | -4.9049399e-05 |
| 2 | 5283 | 1995 | q_positive | 223375 | 256000 | 0 | 0.916495353, 0.86535662, 0.795743567 | 0.0696130527 | 0.51107911, 0.460765128, 0.414953183 | 0.0458119448 |
| 2 | 5283 | 1995 | suffix_b0 | 223375 | 256000 | 0 | 1.00046906, 1.0006049, 1.00062305 | -1.8156254e-05 | 0.000571868882, 0.000703442069, 0.00073299196 | -2.95498912e-05 |
| 2 | 1993 | 6343 | q_positive | 255875 | 252375 | 0 | 1.27821732, 1.3031898, 1.15450906 | 0.148680737 | 0.362437904, 0.409692505, 0.28482993 | 0.124862576 |
| 2 | 1993 | 6343 | suffix_b0 | 255875 | 252375 | 0 | 0.99976249, 0.999786918, 0.999761779 | 2.51393985e-05 | 5.34184965e-05, 0.000196024006, 0.000213790574 | -1.7766568e-05 |
| 2 | 5283 | 6343 | q_positive | 223375 | 252375 | 0 | 0.968438887, 0.953154065, 0.930906175 | 0.0222478899 | 0.0526594752, 0.0596567684, 0.0612270402 | -0.00157027181 |
| 2 | 5283 | 6343 | suffix_b0 | 223375 | 252375 | 0 | 1.00000532, 0.999892673, 0.99985753 | 3.51431017e-05 | 0.000296249995, 0.000301779458, 0.000309542323 | -7.76286482e-06 |

The stop-1/five-suffix parse starts at payload bit zero without extra escape skipping; band b contains candidate-token indices b*262144 through (b+1)*262144-1. Whole original-index 128-token blocks containing q>=17 are omitted; each retained block contributes 125 targets. All runs reached their requested extent. Marginal and context differences can confound transfer. This fixed descriptive comparison is not a significance test or physical framing evidence.

## Reproduce

The retained verified public CC0 inputs are:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`

At commit `790a4381b7ddeaafe50ff74e7bce9456a04a928e`, verify identities and hashes and substitute local paths. Generate the two band-1 reports and all four band-2 reports, then extract each CLI envelope's `sample` object as a JSON report. For example:

```text
python -I -B tools/token_lag3_heldout_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --test-band 1 > ENVELOPE1993.json
python -I -B tools/token_lag3_heldout_probe.py --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" FILE5283 --test-band 1 > ENVELOPE5283.json
python -I -B -c "import json,pathlib; print(json.dumps(json.loads(pathlib.Path('ENVELOPE1993.json').read_bytes())['sample']))" > REPORT1993.json
python -I -B -c "import json,pathlib; print(json.dumps(json.loads(pathlib.Path('ENVELOPE5283.json').read_bytes())['sample']))" > REPORT5283.json
python -I -B tools/token_lag3_transfer_probe.py REPORT1993.json REPORT5283.json
```

Repeat report generation with `--test-band 2` for all four identities, then pass those four extracted reports to the same reducer. The reducer emits all training/test and recipient-training tables plus report/source hashes; serialization can change report byte hashes without changing values. Separately justified contexts and framing remain open on the existing corpus.
