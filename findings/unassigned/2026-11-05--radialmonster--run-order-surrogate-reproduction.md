# Run-order surrogate measurement reproduces on public E-M1 Mark II files

Author: @radialmonster
Verified by: @ruedbi
Lead: #322
Variant: unassigned
Builds on: #297, #231, #308
Reproduces: 2026-10-23--radialmonster--run-order-surrogate-reproduction

## Claim

On the lead's public `id1993` development slice, the frozen 154-candidate periodic bit-density search has maximum `99.05161517759645` (`11,520,000/116,303`), above all 127 declared run-order surrogate maxima: `0/127` exceedances, plus-one rank `1/128 = 0.0078125`, two exact ties. The winner is the second window, width 2, phase 0, with 378 of 1024 selected ones against 603 of 1024 others. This is a narrow surrogate-model diagnostic; it does not establish camera exchangeability, a p-value, framing, codec syntax or pixel values.

The same frozen search on two further public High Res E-M1 Mark II files not used by the lead also gives `0/127` exceedances. Those two files are additional development controls, not untouched validation.

## Original evidence

@radialmonster opened lead #322 on 2026-10-22. The original tool was `tools/run_reorder_search.py` at commit `427d8f84fc0a69f2b6bc7b719bd6995ecb8623cd` (PR #321). Its predeclared design is a 512-byte logical strip window `[4096,4608)`, two non-overlapping 2048-bit windows, widths 2-12 and every phase (154 candidates), and 127 run-order surrogates from Python `random.Random` MT19937 seed `20261022`. The surrogate preserves each symbol's global maximal-run-length multiset, endpoints, density and all four adjacent-transition counts; it does not preserve local window density, byte histograms or run positions.

The lead's public input is raw.pixls.us id 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`, measured 5240x3912, variable-size payload.

## Verification

Independent verification by @ruedbi on 2026-11-05 UTC using sample files in `ruedbi-orf-samples` (`python -I -B tools/run_reorder_search.py`, Python 3.13 on Windows 11), following the self-verification by @radialmonster (2026-10-23).

`python -I -B tools/test_run_reorder_search.py` passes all 8 tests.

The lead's id1993 figures reproduce exactly:
- winner: window 1, width 2, phase 0, `selected_n=1024`, `selected_ones=378`, `other_n=1024`, `other_ones=603`;
- exact score `11,520,000/116,303 = 99.05161517759645`, two exact ties;
- exceedances `0/127`, plus-one rank `1/128`, Wilson 95% interval `[0, 0.029359645293763368]`.

The three synthetic development controls also reproduce: constant zero maximum `0` with `127/127`; uniform seed 611 maximum `9.043628441897434` with `42/127`; forced-byte-LSB maximum `229.8228920164404` with `0/127`.

The same frozen search applied to the two public High Res files reproduced all metrics exactly:
- id 1994, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23`, 10400x7792: winner window 1, width 2, phase 0, 284/1024 versus 668/1024, score `289.430902287922`, `0/127`, two ties.
- id 1996, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2`, 10400x7792: winner window 1, width 6, phase 3, 341/341 versus 639/1707, score `445.857408270865`, `0/127`, one tie.

## Reproduce

```sh
python -I -B tools/test_run_reorder_search.py
python -I -B tools/run_reorder_search.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 FILE1993
python -I -B tools/run_reorder_search.py --sample 1994 "Olympus - E-M1MarkII - 16bit (4:3).ORF" f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 FILE1994
python -I -B tools/run_reorder_search.py --sample 1996 "Olympus - E-M1MarkII - 16bit (4:3).ORF" eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2 FILE1996
```

## Public input identities

- raw.pixls.us id 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`, 5240x3912.
- raw.pixls.us id 1994, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23`, 10400x7792.
- raw.pixls.us id 1996, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2`, 10400x7792.
