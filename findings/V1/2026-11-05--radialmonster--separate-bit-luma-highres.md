# b2 alone and b4 alone each predict top-band luma on two High Res E-M1 Mark II files

Author: @radialmonster
Verified by: @ruedbi
Lead: #149
Variant: V1
Builds on: 2026-10-21--radialmonster--b2b4-local-luma-proxy, #11, #29
Reproduces: 2026-10-21--radialmonster--separate-bit-luma-highres
Partial: the separate b2-only and b4-only top-band luma maps on the High Res E-M1 Mark II files 1994 and 1996; not the original b2+b4 sum claim (already covered by 2026-10-21--radialmonster--b2b4-local-luma-proxy), other bodies, the full frame, or any pixel decode.

## Claim

The fixed b2+b4 top-band luma proxy of lead #149 is not the only positive combination of its two bits. On two High Res E-M1 Mark II files not used for the separate-bit run, each bit alone has a positive correlation with the embedded preview's luma DC and exceeds its own within-row shuffle:

| file | map | r | shuffle mean +/- sd | z |
|---|---|---|---|---|
| 1994 | sum = b2+b4 | +0.05856 | -0.00142 +/- 0.02204 | +2.72 |
| 1994 | b2 alone | +0.07343 | +0.00272 +/- 0.01977 | +3.58 |
| 1994 | b4 alone | +0.03834 | -0.00508 +/- 0.02127 | +2.04 |
| 1996 | sum = b2+b4 | +0.09649 | -0.00546 +/- 0.01732 | +5.89 |
| 1996 | b2 alone | +0.11598 | -0.00720 +/- 0.02210 | +5.57 |
| 1996 | b4 alone | +0.06844 | -0.00042 +/- 0.02015 | +3.42 |

On both files b2 alone has the largest real correlation, the sum is second and b4 alone is third. That ranking differs from the separate-bit result on the normal E-M1 Mark II files 1995, 1997 and 1998, where the sum was larger than either bit on 3 of 3. The sum-dominance ranking is therefore file/scope-dependent, while the positive separate-bit direction holds on all five files tested with this measure.

The measure is unchanged: `v = b2`, `v = b4` or `v = b2 + b4` for every token, a 63-token centred box mean within each candidate row, block averaging to the preview's luma DC grid, and Pearson correlation after subtracting each row's mean. The null permutes the suffix bytes within each row. The same 20 within-row shuffles with `--seed 1` are used for every map of a file.

Limits: this is a top-300-candidate-row, low-resolution luma proxy, not a pixel decode. The nominal token rows use the payload width, not established physical rows; the token row stride of these High Res files is reported as W+5 and W+8 in lead #144. The embedded preview is the camera's numeric rendering, not sensor ground truth. Positive marginal correlations do not show that b2 and b4 carry independent information after conditioning on each other, nor what either bit means. The shuffle z values are descriptive, not calibrated significance. No full-frame or other-body claim is made.

## Original evidence

Lead #149 and its merged finding `2026-10-21--radialmonster--b2b4-local-luma-proxy` established the fixed sum map on four normal E-M1 Mark II files and the 1994 High Res sum control. The separate-bit run on 1995, 1997 and 1998 is in [issue comment 6322833923](https://github.com/radialmonster/orf-cleanroom/issues/149#issuecomment-6322833923); it reported both single-bit maps positive above their own shuffle and the sum larger than either bit on all three files.

Tools (standard library only): `tools/token_luma_probe.py` and `tools/jpeg_dc.py`. The separate-bit option was added in PR #243 (`tools/token_luma_probe.py` commit `1d85520`); the scoring code is unchanged at main commit `2cfdf7c` / tool commit `3e306f1`, source SHA-256 `2a8be22d988c0b00d5fe316e13b905a3feba8d9b915c28e85e1d7a9740f307ea`. `tools/jpeg_dc.py` source SHA-256 is `d86e5a4d0b4e3bc1481b40dff070d73f5c311611545cee46ae8ac602287ce381`.

The two new inputs are public CC0 raw.pixls.us copies:

- 1994 `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23`
- 1996 `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2`

Both are 10400x7792 variable-size payloads with a 400x300 preview DC grid; the run uses 12x400 of that grid. 1994 has 443 candidate escapes and 1996 has 607, all treated as 0 in the b2/b4 maps without removing token positions.

## Verification

On 2026-11-05 UTC, @ruedbi independently verified the separate-bit luma probe results on High Res samples 1994 and 1996 using `tools/token_luma_probe.py`. All 20 synthetic unit tests in `tools/test_token_luma_probe.py` passed, as did `tools/token_luma_probe.py --self-test`.

The independent run exactly reproduced all six cells down to the fifth decimal place:
- 1994 sum: r = +0.05856, shuffle = -0.00142 +/- 0.02204, z = +2.72, escapes = 443
- 1994 b2 alone: r = +0.07343, shuffle = +0.00272 +/- 0.01977, z = +3.58, escapes = 443
- 1994 b4 alone: r = +0.03834, shuffle = -0.00508 +/- 0.02127, z = +2.04, escapes = 443
- 1996 sum: r = +0.09649, shuffle = -0.00546 +/- 0.01732, z = +5.89, escapes = 607
- 1996 b2 alone: r = +0.11598, shuffle = -0.00720 +/- 0.02210, z = +5.57, escapes = 607
- 1996 b4 alone: r = +0.06844, shuffle = -0.00042 +/- 0.02015, z = +3.42, escapes = 607

All sample hashes matched retained CC0 manifest records.

This reproduces and upgrades finding `2026-10-21--radialmonster--separate-bit-luma-highres` to verified.

## Reproduce

```sh
python -I -B tools/test_token_luma_probe.py
python -I -B tools/token_luma_probe.py --self-test
python -I -B tools/token_luma_probe.py FILE1994 --rows 300 --window 63 --perms 20 --seed 1 --map sum
python -I -B tools/token_luma_probe.py FILE1994 --rows 300 --window 63 --perms 20 --seed 1 --map b2
python -I -B tools/token_luma_probe.py FILE1994 --rows 300 --window 63 --perms 20 --seed 1 --map b4
python -I -B tools/token_luma_probe.py FILE1996 --rows 300 --window 63 --perms 20 --seed 1 --map sum
python -I -B tools/token_luma_probe.py FILE1996 --rows 300 --window 63 --perms 20 --seed 1 --map b2
python -I -B tools/token_luma_probe.py FILE1996 --rows 300 --window 63 --perms 20 --seed 1 --map b4
```
