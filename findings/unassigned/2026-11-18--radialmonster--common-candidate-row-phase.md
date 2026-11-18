# Common candidate row phase in fixed public windows

Author: @radialmonster
Verified by: @ruedbi
Lead: #792
Variant: unassigned
Builds on: #31, #777, #788
Reproduces: 2026-11-17--radialmonster--common-candidate-row-phase
Partial: common row-phase rejection on four windows of public E-M1 Mark II id 1995; other bodies and windows not re-run.

## Claim

Under the fixed signed_digit-minus-3, B16, stride-2 candidate and the conditional literal one-token-per-site same-row model, four predeclared 4096-candidate windows on public id 1995 each have a nonempty phase set, but their width-periodic per-file intersection is empty after the fourth window (possible_phase_count = 0). This rejects only that fixed conditional common-phase family on the defined windows.

## Original evidence

Lead #792 used `tools/common_row_phase.py` at `43ea1f54b555990e188fb9b4c931ad00ce40b7e2` on 2026-11-17 UTC on public id 1993 (`Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`) and id 5283. On 1993 the cumulative phase count dropped to 0 after window 3. On 1995, post-lead verification reported 5240, 556, 5240, and 738 phases per window, with cumulative surviving phases dropping to 0 after window 4.

## Verification

Independent verification was conducted by @ruedbi on 2026-11-18 using Python standard library (Python 3.8+) and `tools/common_row_phase.py`.

All unit tests in `tools/test_common_row_phase.py` passed.

A fresh rerun was performed on public CC0 file raw.pixls.us id 1995 (`Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`, payload 5240x3912):

| File | Width | Start Token | Escapes | Status | P0/P1 | S0/S1 | Cut lo/hi | Whole Feasible | Window Phases | Cumulative Phases |
| ---: | ---: | ---: | ---: | :--- | :--- | :--- | :--- | :--- | ---: | ---: |
| 1995 | 5240 | 262144 | 0 | ok | 2048/2048 | 0/0 | 0/4096 | yes | 5240 | 5240 |
| 1995 | 5240 | 524288 | 0 | ok | 1206/1582 | 929/101 | 1857/2412 | no | 556 | 556 |
| 1995 | 5240 | 1048576 | 0 | ok | 2048/2048 | 0/0 | 0/4096 | yes | 5240 | 556 |
| 1995 | 5240 | 1572864 | 0 | ok | 1693/1394 | 599/1026 | 2052/2789 | no | 738 | 0 |

The results match the published finding exactly:
- Window 1 (262144): fully feasible, 5240 phases.
- Window 2 (524288): P0/P1 1206/1582, S0/S1 929/101, cut 1857/2412, 556 phases.
- Window 3 (1048576): fully feasible, 5240 phases (cumulative remains 556).
- Window 4 (1572864): P0/P1 1693/1394, S0/S1 599/1026, cut 2052/2789, 738 phases; cumulative intersection drops to 0 (`conclusion: rejected`, `possible_phase_count: 0`).

## Reproduce

Using standard library Python and `tools/common_row_phase.py`:

```bash
python -I -B tools/test_common_row_phase.py
python -I -B tools/common_row_phase.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" <path-to-1995>
```

Check that the JSON output reports `conclusion: "rejected"` and `possible_phase_count: 0`.
