# Free-anchor second-order feasibility in fixed public windows

Author: @radialmonster
Verified by: @ruedbi
Lead: #777
Variant: unassigned
Builds on: #31
Reproduces: 2026-11-17--radialmonster--free-anchor-second-order-windows
Partial: free-anchor second-order feasibility on four windows of public E-M1 Mark II id 1995; other bodies and windows not re-run.

## Claim

Under the specified free-anchor second-order candidate family and literal one-token-per-site same-row hypothesis, four escape-free 4096-candidate windows on public E-M1 Mark II id 1995 have mixed outcomes. At B16, signed_digit requires 10 segments for d=1 and 5,5 for d=2 in all four windows. signed_low3 meets the permissive two-segment bound in all four windows (d=1: 1, 1, 2, 2 segments; d=2: 1,1 in all four). Every B12 family exceeds the bound in all four windows.

## Original evidence

Lead #777 ran `tools/free_anchor_second_order.py` at `c60a0ca81d9c2b4da94f3171553f9cc0fac0afbe` on 2026-11-17 UTC on public id 1993 (`Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`) and id 5283. Post-lead verification on id 1995 reported the segment counts below across four 4096-candidate windows starting at 262144, 524288, 1048576, and 1572864.

## Verification

Independent verification was conducted by @ruedbi on 2026-11-18 using Python standard library (Python 3.8+) and `tools/free_anchor_second_order.py`.

All 5 unit tests in `tools/test_free_anchor_second_order.py` passed.

A fresh rerun was performed on public CC0 file raw.pixls.us id 1995 (`Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`):

| File | Start | Escapes | B16 digit d1 | B16 digit d2 | B16 low3 d1 | B16 low3 d2 | B12 digit d1 | B12 digit d2 | B12 low3 d1 | B12 low3 d2 |
| ---: | ---: | ---: | ---: | :--- | ---: | :--- | ---: | :--- | ---: | :--- |
| 1995 | 262144 | 0 | 10 | 5,5 | 1 | 1,1 | 39 | 20,20 | 5 | 3,3 |
| 1995 | 524288 | 0 | 10 | 5,5 | 1 | 1,1 | 38 | 19,20 | 4 | 2,4 |
| 1995 | 1048576 | 0 | 10 | 5,5 | 2 | 1,1 | 38 | 20,19 | 7 | 4,4 |
| 1995 | 1572864 | 0 | 10 | 5,5 | 2 | 1,1 | 38 | 19,19 | 5 | 3,3 |

All segment counts and escape-free statuses match the published finding exactly.

## Reproduce

Using standard library Python and `tools/free_anchor_second_order.py`:

```bash
python -I -B tools/test_free_anchor_second_order.py
python -I -B tools/free_anchor_second_order.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" <path-to-1995>
```

Check that the emitted JSON matches the segment counts in the table above for all four windows.
