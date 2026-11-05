# b2+b4 local density predicts the embedded preview's low-resolution luma (top band, E-M1 Mark II)

Author: @radialmonster
Verified by: @ruedbi
Lead: #149
Variant: V1
Builds on: #11, #29
Reproduces: 2026-10-21--radialmonster--b2b4-local-luma-proxy
Partial: the fixed b2+b4 top-band low-resolution luma proxy on the four normal E-M1 Mark II files, plus a positive but weaker 1994 High Res run; not the full frame or other bodies.

## Claim

A fixed local density of the suffix bits b2 and b4 predicts the embedded preview's low-resolution luma on E-M1 Mark II files. The mapping is fixed, not fitted: for every token take `v = b2 + b4`, box-average `v` over 63 tokens within each row, block-average to the preview's luma DC grid, and correlate the row-centred token grid with the row-centred preview grid after the preview's luma DC is decoded.

On the top 300 token rows, 20 within-row shuffles:

| file | role | r | shuffle mean +/- sd | z |
|---|---|---|---|---|
| 1993 | discovery | +0.472 | +0.005 +/- 0.018 | +26.12 |
| 1995 | held-out | +0.108 | +0.004 +/- 0.021 | +5.01 |
| 1997 | held-out | +0.122 | -0.007 +/- 0.020 | +6.34 |
| 1998 | held-out | +0.098 | +0.008 +/- 0.024 | +3.69 |

The effect is strong on the 1993 chart and small but significant on the three held-out natural scenes. Only b2 and b4 are used; b0, b1 and b3 are not. This is consistent with the special b2/b4 role in leads #11 and #29, but it does not establish what b2 and b4 mean.

Limits: this is the top 300-row band and a smoothed luma proxy at the preview's DC resolution, not a full pixel decode. A full-frame reshape is not used because the token row stride can drift; the full-frame version of this exact mapping has a negative correlation and is not claimed.

## Original evidence

Lead #149. Tools (standard library only) at PR #148, commit f802395 (the preview finder was corrected after the lead to reject an implausible 54882x11566 candidate in the OM-5 container; the E-M1 Mark II numbers are unchanged):

- `tools/token_luma_probe.py` builds the fixed map and the shuffle null.
- `tools/jpeg_dc.py` decodes the embedded baseline preview's luma DC. It was checked locally against the decoded preview BMP: the 400x300 DC grid has r=0.99999 with 8x8 block means of the preview.

Files are CC0 raw.pixls.us copies. SHA-256:

- 1993 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 1995 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 1997 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`
- 1998 `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`

## Verification

On 2026-11-05 UTC, @ruedbi independently verified the fixed b2+b4 top-band low-resolution luma proxy on all five public CC0 E-M1 Mark II files using `tools/token_luma_probe.py` (`--rows 300 --window 63 --perms 20`):

- 1993 (5240x3912): r = +0.47214, shuffle = +0.00547 +/- 0.01787, z = +26.12, escapes = 1
- 1995 (5240x3912 ORI): r = +0.10846, shuffle = +0.00353 +/- 0.02093, z = +5.01, escapes = 1
- 1997 (5240x3912 ORI): r = +0.12245, shuffle = -0.00663 +/- 0.02037, z = +6.34, escapes = 1
- 1998 (5240x3912): r = +0.09793, shuffle = +0.00809 +/- 0.02434, z = +3.69, escapes = 2
- 1994 (10400x7792 High Res): r = +0.05856, shuffle = -0.00142 +/- 0.02204, z = +2.72, escapes = 443

All 20 tests in `tools/test_token_luma_probe.py` passed, and `tools/token_luma_probe.py --self-test` passed. All local sample hashes matched retained CC0 records in `samples/manifest.csv`.

This reproduces and upgrades finding `2026-10-21--radialmonster--b2b4-local-luma-proxy` to verified.

## Reproduce

```sh
python -I -B tools/test_token_luma_probe.py
python -I -B tools/token_luma_probe.py --self-test
python -I -B tools/token_luma_probe.py FILE1993 --rows 300 --window 63 --perms 20
python -I -B tools/token_luma_probe.py FILE1995 --rows 300 --window 63 --perms 20
python -I -B tools/token_luma_probe.py FILE1997 --rows 300 --window 63 --perms 20
python -I -B tools/token_luma_probe.py FILE1998 --rows 300 --window 63 --perms 20
python -I -B tools/token_luma_probe.py FILE1994 --rows 300 --window 63 --perms 20
```
