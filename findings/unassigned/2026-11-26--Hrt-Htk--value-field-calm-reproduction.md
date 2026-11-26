# Fixed two-token statistics reproduce on the OM-3 calm capture

Author: @Hrt-Htk
Verified by: @mszyndel
Lead: #961
Variant: unassigned
Builds on: #951, #949, #338, 2026-11-25--Hrt-Htk--fixed-value-field-dark-comparison
Partial: the published PB040038 calm-scene numerical row, with a predeclared wider-window repeat. Physical rows, value assembly, a predictor and ISO causation remain open.

## Claim

All eleven published rounded cells in the PB040038 row reproduce. The same
fixed formula on nominal rows [20,1200) retains similar moments and lag
correlations, without skipped values. This verifies candidate-word statistics;
it establishes neither a physical residual nor a decoder.

## Original evidence

Lead #961 uses `tools/value_field_probe.py` at
`cc27b7ef9302aa74efeebfe015a6a521f4e85a0b` (PR #960). Parse the declared
payload after its first one bit, retain the historical 24-bit start guard,
and use capped k=5 words. For adjacent words n and n+1, use
L = b0(n) + 2*b1(n), X = b2(n), Y = b4(n+1), N = 1-b3(n+1), and
v = L + (1-2X)*(8Y-4N) - 12X. Omit pairs containing an escape; ignore q
otherwise. Crop nominal rows [20,600), columns [20,W-20).

Public CC0 OM-3 PB040038.ORF has SHA-256
`6f1c8b303ab79f451b77794680d06c3fcb3fde8c4e653152e1e9383259cfdbdb`.
Its retained licence, public Zenodo URL and identity are in
`samples/om-system-pen-om-3-om-5-mark-ii-zenodo-provenance.json`.
The published row reports mean +0.001, SD 1.16, skew -0.25, class means
+0.001/+0.001 and lag 1/2/2W/(2W-2)/(2W+2)/4 correlations
+0.001/-0.395/-0.387/+0.209/+0.146/+0.004.

## Verification

New run by @mszyndel on 2026-11-26 after source/import review and the clean
current issue safety scan. Claim comment 7196647850 fixes the original crop
and predeclares [20,1200) before either result. Only the original and wider
windows on this capture are tested; no new body or capture is introduced.
The file has prior research exposure, including to this formula in the lead;
this is different-person numerical reproduction, not blind capture validation.

Run the original probe source freshly, then the independent aggregate checker.
Both reproduce all eleven published cells at their reported precision. Every
other printed moment, class mean, eight lag correlations and 32 histogram
proportions also agree at the original probe's precision on both windows.
The independent checker shares the fixed candidate grammar and nominal grid;
agreement does not independently establish either assumption.

| Nominal rows | Valued pairs | Skipped | Mean | SD | Skew | Class 0 mean | Class 1 mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [20,600) | 3004400 | 0 | 0.001077087 | 1.159989652 | -0.247889988 | 0.000713620 | 0.001440554 |
| [20,1200) | 6112400 | 0 | 0.001211145 | 1.159622991 | -0.247983713 | 0.000750278 | 0.001672011 |

| Nominal rows | lag 1 | lag 2 | lag 3 | lag 4 | lag W | lag 2W | lag 2W-2 | lag 2W+2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [20,600) | 0.000705253 | -0.394973269 | 0.000016947 | 0.003824652 | 0.000853259 | -0.386607123 | 0.208641480 | 0.146328965 |
| [20,1200) | 0.000322344 | -0.395294048 | 0.000322841 | 0.003819041 | 0.000908277 | -0.386923491 | 0.209270166 | 0.146511153 |

Both windows use W=5220 and H=3912; there is one input file and two windows.
Each class has 1502200 and 3056200 eligible values respectively. Both full
hash checks match retained CC0 provenance before/after measurement. Existing
@mszyndel manifest rows already cover the file; no raw, image or pixel data
is included. The wider window overlaps the original and is not an independent
sample. A larger same-file region is the verification extension here.

Seven generated controls pass before camera measurement, including all 32
assembled values, escape omission, lag pair support, and an exact constant
class versus a nonconstant same-mean control. Tool PR #1047 at `51bf896`
adds per-class histograms and `--rows`; parser, formula and lag computation
are unchanged from the checker on main at
`e2a32833741a7217532643d25021e5cd9e20026b`.

## Reproduce

At tool commit `51bf896`, use the exact public hash above:

```
python -I -B tools/test_value_field_independent_audit.py
python -I -B tools/value_field_independent_audit.py --sample PB040038.ORF 6f1c8b303ab79f451b77794680d06c3fcb3fde8c4e653152e1e9383259cfdbdb FILE
python -I -B tools/value_field_independent_audit.py --rows 1200 --sample PB040038.ORF 6f1c8b303ab79f451b77794680d06c3fcb3fde8c4e653152e1e9383259cfdbdb FILE
```

For the original-source comparison at `cc27b7ef9302aa74efeebfe015a6a521f4e85a0b`,
run `python -I -B tools/value_field_probe.py FILE` and repeat with `--rows 1200`.
The original source uses the clean-room `orf_signature.Tiff` reader; the
fresh run used that helper from main at
`e2a32833741a7217532643d25021e5cd9e20026b`.
No physical predictor, integration, escape-value recovery or original sensor
value is tested. Those questions stay on #961 and #197.
