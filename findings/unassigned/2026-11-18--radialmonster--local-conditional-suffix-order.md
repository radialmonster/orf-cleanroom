# Local conditional suffix ordering on public E-M1 Mark II 1993

Author: @radialmonster
Verified by: @ruedbi
Lead: #765
Variant: unassigned
Builds on: #29, #757
Reproduces: 2026-11-17--radialmonster--local-conditional-suffix-order
Partial: local conditional suffix ordering on nine verification windows of public E-M1 Mark II id 1993; not statistical significance, physical framing, or a decoder.

## Claim

In each of nine candidate-token windows (eight consecutive 262144-token windows and one overlapping 524288-token window) on public E-M1 Mark II id 1993, the conditional proportions P(b2=1 | b1b0=j) in the fixed order j=00,01,10,11 follow the adjacent comparison pattern `<`, `<`, `<`. Thus, unlike public E-M1 id 1051 (pattern `>`, `>`, `<`) and OM-5 id 6343 (pattern `>`, `<`, `<`), the conditional proportions on 1993 are strictly increasing across all nine windows.

## Original evidence

Lead #765 reported that on public E-M1 id 1051, four consecutive 262144-token windows had the adjacent comparison pattern `>`, `>`, `<`. Post-lead verification added five further windows on 1051 (all `>`, `>`, `<`) and nine windows on OM-5 id 6343 (eight `>`, `<`, `<` and one `>`, `>`, `<`).

## Verification

Independent verification was conducted by @ruedbi on 2026-11-18 using Python standard library (Python 3.8+), `tools/suffix_balance_windows.py` and `tools/suffix_conditional_order.py`.

All unit tests in `tools/test_suffix_conditional_order.py` passed.

A fresh run was performed on public CC0 file raw.pixls.us id 1993 (`Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`):

| File | Start | Length | Retained | Escapes | 00 | 01 | 10 | 11 | Adjacent | Strictly Increasing |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| 1993 | 0 | 262144 | 262143 | 1 | 9117/34979 | 20249/66156 | 4217/12528 | 24719/63389 | <, <, < | true |
| 1993 | 262144 | 262144 | 262144 | 0 | 17072/70447 | 19157/65964 | 20531/62362 | 23669/63371 | <, <, < | true |
| 1993 | 524288 | 262144 | 262144 | 0 | 12045/68653 | 3506/16523 | 15496/62821 | 9397/32289 | <, <, < | true |
| 1993 | 786432 | 262144 | 262144 | 0 | 7186/34611 | 8048/33005 | 17721/62980 | 5298/15983 | <, <, < | true |
| 1993 | 1048576 | 262144 | 262144 | 0 | 16448/70307 | 9011/32949 | 19601/62780 | 23011/63159 | <, <, < | true |
| 1993 | 1310720 | 262144 | 262144 | 0 | 6179/23081 | 835/2759 | 10646/31773 | 23815/63139 | <, <, < | true |
| 1993 | 1572864 | 262144 | 262144 | 0 | 15599/68642 | 17846/66127 | 2428/7921 | 22871/64007 | <, <, < | true |
| 1993 | 1835008 | 262144 | 262144 | 0 | 17414/70203 | 19129/66288 | 10037/31484 | 22999/62685 | <, <, < | true |
| 1993 | 1048576 | 524288 | 524288 | 0 | 6997/27910 | 19031/66057 | 40893/126326 | 23413/63149 | <, <, < | true |

All nine windows satisfy the adjacent pattern `<`, `<`, `<` with `strictly_increasing: true` and `nondecreasing: true`.

## Reproduce

Using standard library Python:

```bash
python -I -B tools/test_suffix_conditional_order.py
python -I -B tools/suffix_balance_windows.py --mode verification --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" <path-to-1993> > scratch/1993_balance.json
python -I -B tools/suffix_conditional_order.py scratch/1993_balance.json
```

Check that the emitted JSON reports `adjacent: ["<", "<", "<"]` and `strictly_increasing: true` for all windows.
