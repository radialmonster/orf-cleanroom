# Within-token suffix balance in local windows on E-M1 Mark II 1993

Author: @radialmonster
Verified by: @ruedbi
Lead: #757
Variant: unassigned
Builds on: #11, #273
Reproduces: 2026-11-17--radialmonster--local-suffix-balance
Partial: local-window suffix balance on nine verification windows of public E-M1 Mark II id 1993; not exact independence or fairness, physical framing, rows, or decoding.

## Claim

Nine local candidate-token windows (eight consecutive 262144-token windows and one overlapping 524288-token window) on public E-M1 Mark II id 1993 each meet the predeclared descriptive within-token H/L balance tolerance: plug-in MI <= 0.010 bit, and each of the b0 and b1 one proportions within 1/20 of 1/2. This tests a different body and file from the original discovery input.

## Original evidence

Lead #757 measured four consecutive 262144-candidate-token windows on public E-M1 id 1051 using `tools/suffix_balance_windows.py` at commit `15213501fd0346761c96190a0590f871749e203f`, all passing tolerance. Post-lead verification added four subsequent windows and one combined 524288-token window.

## Verification

Independent verification was conducted by @ruedbi on 2026-11-18 using Python standard library (Python 3.8+) and `tools/suffix_balance_windows.py`.

All unit tests in `tools/test_suffix_balance_windows.py` passed.

A fresh rerun was performed with `--mode verification` on public CC0 file raw.pixls.us id 1993 (`Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`):

| Start | Length | Retained | Escapes | b0 ones / retained | b1 ones / retained | MI bits | Pass |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 262144 | 262143 | 1 | 129545/262143 | 126029/262143 | 0.000523 | yes |
| 262144 | 262144 | 262144 | 0 | 129335/262144 | 125733/262144 | 0.000944 | yes |
| 524288 | 262144 | 262144 | 0 | 65335/131072 | 127399/262144 | 0.003707 | yes |
| 786432 | 262144 | 262144 | 0 | 64971/131072 | 1983/4096 | 0.000798 | yes |
| 1048576 | 262144 | 262144 | 0 | 129057/262144 | 125939/262144 | 0.000704 | yes |
| 1310720 | 262144 | 262144 | 0 | 129355/262144 | 126685/262144 | 0.001097 | yes |
| 1572864 | 262144 | 262144 | 0 | 65067/131072 | 127375/262144 | 0.000457 | yes |
| 1835008 | 262144 | 262144 | 0 | 128973/262144 | 125653/262144 | 0.000737 | yes |
| 1048576 | 524288 | 524288 | 0 | 64603/131072 | 15789/32768 | 0.000819 | yes |

All nine windows pass the tolerance: plug-in MI <= 0.010 bit, and b0 and b1 one proportions within 0.05 of 0.50 (`tolerance_pass: True`).

## Reproduce

Using standard library Python and `tools/suffix_balance_windows.py`:

```bash
python -I -B tools/test_suffix_balance_windows.py
python -I -B tools/suffix_balance_windows.py --mode verification --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" <path-to-1993>
```

Verify that all nine windows in the returned JSON report `tolerance_pass: true`.
