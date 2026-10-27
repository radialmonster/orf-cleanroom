# OM-1 and OM-1 Mark II dark captures reproduce the offset pattern

Author: @mtakemoto
Verified by: @mszyndel
Lead: #338
Variant: unassigned
Partial: the dark-frame same-colour offset signature on four lens-cap captures at sensitivity settings 200 and 800

## Claim
On four lens-cap dark captures from the OM-1 and OM-1 Mark II, with one file per body at raw Exif PhotographicSensitivity values 200 and 800, the k=5/stop=1 suffix-match grid reproduces the dark-frame sign pattern in #338. At each body and sensitivity value, rates at (dy,dx)=(0,2) and (2,0) are below the fixed shuffled baseline, rates at (2,-2) and (2,+2) are above it, and dy=1 and dy=3 rows are flat across dx to within 0.001. This verifies only the dark-frame offset pattern; it does not identify a predictor, value map, framing, physical pixel map or CFA phase.

## Original evidence
Lead #338 reports on OM-3 lens-cap frames that (0,2) and (2,0) are below the shuffled baseline, while (2,-2) and (2,+2) are above it. Its ISO 200 real rates are about 0.116, 0.116, 0.194 and 0.177-0.178 against a 0.156-0.157 baseline; its ISO 800 rates are 0.065-0.067, 0.065, 0.093 and 0.089 against a 0.080-0.081 baseline. Odd rows dy=1 and dy=3 are flat within 0.001. The lead uses `tools/bayer_grid_probe.py` with a 4,000,000-token prefix and fixed shuffle seed 20261023.

## Verification
After #338 was posted, I ran `tools/bayer_grid_probe.py` at `40d1660` with its defaults on four additional 5220x3912 lens-cap files. Each pair below is real rate / shuffled rate:

| Body | Raw Exif sensitivity | File | (0,2) | (2,0) | (2,-2) | (2,+2) |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| OM-1 | 200 | P1010001.ORF | 0.114917 / 0.154461 | 0.114793 / 0.154720 | 0.191098 / 0.154597 | 0.174422 / 0.155078 |
| OM-1 | 800 | P1010002.ORF | 0.066037 / 0.079233 | 0.063663 / 0.079104 | 0.091740 / 0.079298 | 0.087620 / 0.078971 |
| OM-1 Mark II | 200 | PA270001.ORF | 0.117144 / 0.158238 | 0.117228 / 0.158384 | 0.197150 / 0.158037 | 0.178173 / 0.158035 |
| OM-1 Mark II | 800 | PA270002.ORF | 0.069780 / 0.083770 | 0.067216 / 0.083660 | 0.096416 / 0.083582 | 0.092355 / 0.083462 |

On all four files, real and shuffled rates across dx at dy=1 and dy=3 vary by less than 0.001. Whole-payload token counts are 20,420,644, 20,420,654, 20,420,643 and 20,420,648, respectively: +4, +14, +3 and +8 versus W x H, with 1, 5, 1 and 3 residual bits.

The own input files and SHA-256 values are: P1010001.ORF `966afc1a0ea8a2c8e9cd78bf86a432f6296f2f0b2eaf89ac12c94a75ee18f516`; P1010002.ORF `6a917fe3b5d41adb026ca1df592f14d3874fd029aedb82da4e66c5d1e95ee64a`; PA270001.ORF `5e3c85c517b8914ad67b5caffd560c2bfb8d77290903cf68f035376622264983`; PA270002.ORF `4d22b06cb79933dd7c5d42ee7596c2de6215e18ce458393f3645fc6f9d8c2ecf`. These files are not publicly downloadable; this result is not yet reproducible by others.

## Reproduce
With the four named files available to the tool, substitute their local paths for `FILE1` through `FILE4`:

```sh
python -I -B tools/bayer_grid_probe.py FILE1 FILE2 FILE3 FILE4
```

Defaults use the first 4,000,000 tokens, seed 20261023, the fixed within-row shuffled baseline and site-table windows 2:202 and 565:765.
