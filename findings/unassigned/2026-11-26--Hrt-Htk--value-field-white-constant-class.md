# The fixed OM-3 white-field formula has an exact constant class

Author: @Hrt-Htk
Verified by: @mszyndel
Lead: #961
Variant: unassigned
Builds on: #951, #949, #338, 2026-11-25--Hrt-Htk--fixed-value-field-dark-comparison
Partial: the PA210010 constant -4 candidate-class observation in the original and predeclared wider windows. Its cause, physical pixel registration, a predictor and a decoder remain open.

## Claim

The fixed #961 formula returns exactly -4 at every eligible class-0 candidate
position on PA210010 in the original nominal rows [20,600) and wider
[20,1200). Class 1 is nonconstant. These exact histograms verify the lead's
constant-class observation, without explaining it or identifying a physical
colour channel or residual.

## Original evidence

Lead #961 states that clipped white PA210010 gives a constant -4 in one
checkerboard class. Its original measurement is
`tools/value_field_probe.py` at `cc27b7ef9302aa74efeebfe015a6a521f4e85a0b`
(PR #960). The issue gives no class histogram or exact denominator for this
white statement, so this verification predeclares that measure before reading
the results rather than claiming to reproduce an unpublished numeric table.

Public CC0 OM-3 PA210010.ORF has SHA-256
`d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`.
The licence, public URL and declared saturated-white ISO 200 condition are in
`samples/om3-flat-338-provenance.json`. No independent physical flatness or
constant-sensor-input measurement is assumed.

## Verification

New different-person run by @mszyndel on 2026-11-26, after source/import
review and checking the clean current issue safety scan. Claim comment
7196647850 fixes the original formula/crop, exact per-class histograms and
wider window before outcomes. First reproduce the PB040038 published row,
then open PA210010 with no retuning. This capture and candidate grammar have
prior project exposure. The wider same-file region is the verification
extension, not a new capture or body.

Use the declared payload, W=5220, H=3912, first-one startup, historical
24-bit guard and capped k=5 candidate words. From n and n+1, use
L=b0(n)+2*b1(n), X=b2(n), Y=b4(n+1), N=1-b3(n+1), and
v=L+(1-2X)*(8Y-4N)-12X. Omit escape-bearing pairs, otherwise ignore q.
Class is (nominal row + nominal column) modulo 2; columns are [20,W-20).

| Nominal rows | All valued pairs | Skipped | Class-0 count | Class-0 exact histogram | Class-1 mean |
| --- | ---: | ---: | ---: | --- | ---: |
| [20,600) | 3004400 | 0 | 1502200 | -4:1502200, all other bins zero | -0.484653175 |
| [20,1200) | 6112400 | 0 | 3056200 | -4:3056200, all other bins zero | -0.496285911 |

Class 1 has the same denominator as class 0 in each window. Its exact nonzero
histogram bins, with all other values in [-20,11] absent, are:

| Value | [20,600) count | [20,1200) count |
| ---: | ---: | ---: |
| -5 | 562 | 1152 |
| -4 | 182068 | 379270 |
| -3 | 540 | 1129 |
| -1 | 4063 | 8299 |
| 0 | 1306248 | 2648573 |
| 1 | 8719 | 17777 |

Original-probe and independent-checker moments, class means, all eight printed
lag correlations and all 32 printed histogram proportions agree at the
original precision in both windows. The exact class histograms are additional
outputs of the checker in tool PR #1047, commit `51bf896`; the original tool
reports class means only. Seven generated controls pass before measurement,
including an exact -4 class and a nonconstant -5/-3 control whose mean remains
-4. Thus this constancy test does not rely on the mean alone.

Both full-hash checks match retained CC0 provenance before/after. Existing personal
manifest rows cover the input. No private inputs, images, pixel data or raw
files are included. These overlapping windows are not independent samples.

The result challenges interpreting the formula as a universally zero-centred
physical prediction residual without further assumptions. It does not prove
which assumption fails. Flat-area mode, bias correction, channel offset,
physical registration and the predictor are not tested. In particular, the
lead's statement about what a predictor can produce on constant input is not
verified by the candidate-class counts: a physically constant input and
predictor initialization have not been independently established.

## Reproduce

At tool commit `51bf896`, using the exact public hash above:

```
python -I -B tools/test_value_field_independent_audit.py
python -I -B tools/value_field_independent_audit.py --sample PA210010.ORF d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e FILE
python -I -B tools/value_field_independent_audit.py --rows 1200 --sample PA210010.ORF d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e FILE
```

Check exact class histograms, class counts and skipped count. The original
comparison uses `python -I -B tools/value_field_probe.py FILE` at
`cc27b7ef9302aa74efeebfe015a6a521f4e85a0b`, repeated with `--rows 1200`.
The clipped-white mechanism and physical interpretation remain on #961/#197;
no compressed decoding step follows from this measurement.
