# Fixed A15 capped-prefix contract on public E-M1 Mark II files

Author: @radialmonster
Verified by: @ruedbi
Lead: #807
Variant: unassigned
Builds on: #197, #603, 2026-10-28--radialmonster--fixed-capped-prefix-first-escape
Reproduces: 2026-11-17--radialmonster--fixed-a15-capped-prefix-contract
Partial: the verification phase on public CC0 E-M1 Mark II files 1993, 1995, and 1997; other bodies or contracts not tested.

## Claim

Under the declared fixed A15/D12/k5 whole-strip contract, public id 1993 stops at an invalid capped word after 3,746,386 complete words. The previously known id 1995 negative control stops at its first word (0 complete words). Predeclared id 1997 stops at an invalid capped word after 7,829,398 complete words. These failures reject the declared full contract for these files.

## Original evidence

Lead #807 used `tools/capped15_contract_probe.py` at commit `220388329665742b337796fdc555837232940d43`. On public CC0 id 1993 (`Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`), it gave invalid value 50 after 3,746,386 words. On id 1995 (`Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`), it stopped at word 0 with invalid value 271. On id 1997 (`Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`), it stopped after 7,829,398 words with invalid value 58.

## Verification

Independent verification was conducted by @ruedbi on 2026-11-18 using Python standard library (Python 3.8+) and `tools/capped15_contract_probe.py`.

All 5 unit tests in `tools/test_capped15_contract_probe.py` passed.

A fresh rerun was performed with `--phase verification` on the three public CC0 files:

| ID | Strip bits | Completed | Ordinary | Capped | Ordinary q sum | Complete endpoint | Unread bits | Word start | Examined position | Invalid value | Status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1993 | 126081000 | 3746386 | 3746385 | 1 | 447997 | 22926374 | 103154626 | 22926374 | 22926401 | 50 | invalid_escape |
| 1995 | 126147400 | 0 | 0 | 0 | 0 | 40 | 126147360 | 40 | 67 | 271 | invalid_escape |
| 1997 | 126140424 | 7829398 | 7829395 | 3 | 922781 | 47899272 | 78241152 | 47899272 | 47899299 | 58 | invalid_escape |

All numbers, endpoints, and invalid escape values reproduce the published finding exactly.

## Reproduce

Using standard library Python and `tools/capped15_contract_probe.py`:

```bash
python -I -B tools/test_capped15_contract_probe.py
python -I -B tools/capped15_contract_probe.py --phase verification --sample 1993 <path-to-1993> --sample 1995 <path-to-1995> --sample 1997 <path-to-1997>
```

Check that the emitted JSON matches the completed word counts, endpoints and invalid escape values above.
