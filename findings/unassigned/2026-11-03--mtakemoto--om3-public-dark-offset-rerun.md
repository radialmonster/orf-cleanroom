# Two additional public OM-3 dark captures reproduce the grid offset signs

Author: @mtakemoto
Verified by: @mszyndel
Lead: #338
Variant: unassigned
Builds on: 2026-10-27--mtakemoto--om3-flat-grid-reproduction
Partial: the dark-frame same-colour offset signs on two additional public OM-3 captures

## Claim
On two additional public OM-3 capped-dark ORFs with payload width 5220, a fresh 4,000,000-token k=5/stop=1 suffix grid has rates below the fixed shuffled baseline at (dy,dx)=(0,2) and (2,0), and above baseline at (2,-2) and (2,+2). The dy=1 and dy=3 rows vary across dx by less than 0.001. One file records Exif PhotographicSensitivity 200 and the other 800. This verifies only the dark-frame token-index offset signs; it does not identify physical pixel rows, a CFA phase or a predictor.

## Original evidence
Lead #338 reports the same dark-frame sign pattern on six OM-3 capped-dark captures using `tools/bayer_grid_probe.py`, a 4,000,000-token prefix and fixed within-width shuffle seed 20261023. For ISO 200, real rates at (0,2), (2,0), (2,-2), (2,+2) were about 0.116, 0.116, 0.194 and 0.177-0.178 against a 0.156-0.157 shuffled baseline. For ISO 800, rates were 0.065-0.067, 0.065, 0.093 and 0.089 against a 0.080-0.081 baseline. The original seven-file rerun is recorded in `2026-10-27--mtakemoto--om3-flat-grid-reproduction`.

## Verification
After #338 was posted, I ran `tools/bayer_grid_probe.py` at commit `40d166017c0ffd07e140ab7b753092ddc337ed50` with its defaults on two additional ORFs from the public CC0 [Zenodo OM-3 test-capture record](https://zenodo.org/records/23923547). The run used a 4,000,000-token prefix, seed 20261023, payload-width stride and the default site-table windows. SHA-256 values matched the retained public provenance before analysis.

Each grid entry is real rate / shuffled rate:

| File | SHA-256 | Exif sensitivity | (0,2) | (2,0) | (2,-2) | (2,+2) | Whole tokens minus W×H; residual bits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PB040038.ORF | `6f1c8b303ab79f451b77794680d06c3fcb3fde8c4e653152e1e9383259cfdbdb` | 200 | 0.112216 / 0.151250 | 0.112278 / 0.151844 | 0.184833 / 0.151698 | 0.172915 / 0.151969 | +3; 5 |
| PB040039.ORF | `48775195def2ce068e5446ef7304a889c696eb51b7de49104848e9ee8f475aa3` | 800 | 0.063171 / 0.076248 | 0.061336 / 0.076504 | 0.088656 / 0.076286 | 0.084675 / 0.076354 | +11; 1 |

Across dx, the real rates in both dy=1 and dy=3 rows vary by less than 0.001 on each file. Both inputs are publicly downloadable; these numbers do not depend on private files. The recorded sensitivity values are standard Exif tag 0x8827, not calibrated ISO or a causal explanation.

## Reproduce
Download the two named files from [Zenodo record 23923547](https://zenodo.org/records/23923547), verify their SHA-256 values above, then at commit `40d166017c0ffd07e140ab7b753092ddc337ed50` run:

```sh
python -I -B tools/bayer_grid_probe.py FILE200 FILE800
```

Defaults use the first 4,000,000 complete candidate tokens, seed 20261023, the within-width shuffle and site-table windows 2:202 and 565:765.
