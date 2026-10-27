# OM-1 Mark II flat files repeat token-index parity in suffix matches

Author: @mtakemoto
Verified by: @mszyndel
Lead: #338
Variant: unassigned
Partial: the checkerboard-like suffix-match pattern in token-index space on two OM-1 Mark II flat-field captures

## Claim
On two OM-1 Mark II flat-field captures with a 5220x3912 payload, suffix matches in the k=5/stop=1 token stream show the same parity-dependent lag pattern reported in #338, when token indices are laid out with stride W=5220. The pattern is less pronounced than on the lead's saturated OM-3 white frame. This verifies only the token-index lag pattern; it does not establish a physical pixel map, CFA phase, or predictor. The lead's dark-frame claim is not tested here.

## Original evidence
The lead reports, on its OM-3 white frame, a suffix-match rate of 0.122 at (dy,dx)=(0,1) and 0.989 at (0,2), with the checkerboard pattern continuing across adjacent rows. Its shuffled rates are 0.502-0.510. The tool was `tools/bayer_grid_probe.py` from PR #340, with seed 20261023 and a 4,000,000-token prefix.

## Verification
After #338 was posted, I ran the current `tools/bayer_grid_probe.py` (last changed at `bff6c7f`) with its defaults on two additional OM-1 Mark II flat-field captures. Both have 5220x3912 payloads. The measured suffix-match rates (real vs fixed shuffle) are:

| Offset (dy,dx) | PA270008 | PA270009 |
| --- | ---: | ---: |
| (0,1) | 0.053273 / 0.286270 | 0.053245 / 0.286138 |
| (0,2) | 0.538273 / 0.285688 | 0.538435 / 0.285667 |
| (1,0) | 0.090405 / 0.118594 | 0.090608 / 0.118603 |
| (1,1) | 0.144832 / 0.118553 | 0.144713 / 0.118537 |
| (2,0) | 0.515977 / 0.284869 | 0.512383 / 0.284728 |
| (2,2) | 0.525170 / 0.284580 | 0.521528 / 0.284769 |

Across the full declared grid, even dx at dy=2 range from 0.512383 to 0.529825, while odd dx range from 0.061919 to 0.066786; shuffled rates for those offsets are 0.284277-0.284892. At dy=1, even dx are about 0.090-0.091 and odd dx about 0.144-0.145, against shuffled rates about 0.118. These repeat the lead's parity-dependent lag structure with smaller one-row contrast.

The files are `own` inputs, not publicly downloadable. Their SHA-256 values are `10459e4bbed86369acaee0ba8ec22fd3e0e4b83b78e6e3cd7af1744bfdeaabc5` (PA270008.ORF) and `2e01d3cef69aec1888b5f52e58dd58d7eb88a6eaa106e883d475cf8945b730e7` (PA270009.ORF). This result is not yet reproducible by others until public inputs are available.

## Reproduce
With the two named input files available, substitute their local paths for `FILE1` and `FILE2`:

```sh
python -I -B tools/bayer_grid_probe.py FILE1 FILE2
```

The defaults use the first 4,000,000 tokens, seed 20261023, the fixed within-row shuffled baseline, and site-table windows 2:202 and 565:765.
