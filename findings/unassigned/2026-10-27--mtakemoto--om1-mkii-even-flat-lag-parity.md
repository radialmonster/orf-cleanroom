# One evenly lit OM-1 Mark II flat repeats token-index lag parity

Author: @mtakemoto
Verified by: @mszyndel
Lead: #338
Variant: unassigned
Builds on: 2026-10-27--mtakemoto--om1-mkii-token-index-parity
Partial: parity-dependent lag-match pattern on PA270013 only; the strong site-table suffix pattern and repeatability across the other four new captures are not verified

## Claim
On one of five additional, more evenly lit OM-1 Mark II flat-field captures, PA270013, k=5/stop=1 suffix matches in the token stream show a coherent parity-dependent lag pattern when token indices are laid out with stride W=5220. The four other captures do not show the same coherent pattern. This verifies the lag pattern on one additional file only. It does not verify the lead's strongly dominant 2x2 site-table suffix pairs, identify a physical pixel map, CFA phase or predictor, or establish that the pattern is general across flat-field captures.

## Original evidence
Lead #338 reports a checkerboard-like suffix-match pattern on an OM-3 saturated white frame, using `tools/bayer_grid_probe.py` with a 4,000,000-token prefix and fixed shuffle seed 20261023. Its reported pattern is substantially stronger than the result below. The earlier partial finding `2026-10-27--mtakemoto--om1-mkii-token-index-parity` reproduced related lag parity on two other OM-1 Mark II flat-field files.

## Verification
After #338 was posted, I reran `tools/bayer_grid_probe.py` at commit `931c734` (script SHA-256 `dfb5c15aae8581d42f8d726ca1fb657ee71b9c902f61775f1a6b80ab19ac956e`) on five additional 5220x3912 OM-1 Mark II flat-field captures. All were `own` files and are not publicly downloadable. Each rate below is real / fixed-shuffle over the first 4,000,000 tokens:

| Offset (dy,dx) | PA270013 real / shuffled |
| --- | ---: | ---: |
| (0,1) | 0.042877 | 0.076821 |
| (0,2) | 0.092887 | 0.076938 |
| (1,-2) | 0.043807 | 0.076943 |
| (1,-1) | 0.110244 | 0.077060 |
| (1,0) | 0.043570 | 0.077019 |
| (1,1) | 0.110052 | 0.077065 |
| (1,2) | 0.043565 | 0.076827 |
| (2,-2) | 0.119361 | 0.076860 |
| (2,-1) | 0.044832 | 0.077104 |
| (2,0) | 0.093590 | 0.077101 |
| (2,1) | 0.044151 | 0.077180 |
| (2,2) | 0.117428 | 0.077348 |

On PA270013, even dx at dy=1 are 0.043565-0.043807 while odd dx are 0.110052-0.110546. At dy=2, the even offsets are 0.093590-0.119361 and odd offsets are 0.044151-0.045340. The corresponding shuffled rates remain near 0.077. The other four captures do not show this same alternating pattern; their grid results are generally near the shuffled baselines, with isolated offset differences. Whole-payload token counts for the five files were 20,422,303; 22,163,250; 24,114,708; 21,191,621; and 20,420,697, respectively, compared with W×H=20,420,640. Residual bits were 5, 5, 1, 5 and 4. None of the files had a dominant 2x2 site-table suffix pair; in PA270013, each cell's most common (q,suffix) pair accounts for only 5.4%-7.3% of that cell's 261,000 entries in the first window.

The five input files and SHA-256 values are: PA270004.ORF `b3b13f20d6967c29ef98607cb0f977a93d21bb2f67beaed3cef3443084133e28`; PA270006.ORF `ea1b878b1c6c2dfdb76196cee7e253f1efcd3ee621da36ff51457e90c580f5c2`; PA270007.ORF `f2feafa3e9a6ce39ca23d7471316fde4e4f2ec3f792493bc390239e3e1e125f4`; PA270008.ORF `ed4db668ed5893a9c7d18f6f0efd1a9d745660dca73459690e827b4bccb98974`; PA270013.ORF `06f45eb2a6dd9f6bbccb9654ca0d270f7b5a70bd33bdf4659cf9b516db89ad17`. These are not publicly downloadable, so this result is not yet reproducible by others.

## Reproduce
With the five named files available, substitute their local paths for `FILE1` through `FILE5`:

```sh
python -I -B tools/bayer_grid_probe.py FILE1 FILE2 FILE3 FILE4 FILE5
```

Defaults use the first 4,000,000 tokens, seed 20261023, the fixed within-row shuffled baseline, and site-table windows 2:202 and 565:765.
