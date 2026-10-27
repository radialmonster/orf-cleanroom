# OM-3 flat-field suffix matches reproduce on a wider prefix

Author: @mtakemoto
Verified by: @radialmonster
Lead: #338
Variant: unassigned
Builds on: #11, #31, #302, #144
Partial: the seven original OM-3 flat and dark files' token-index grid and supporting counts

## Claim
The reported white and dark suffix-match patterns reproduce on the seven original public OM-3 files, and persist in an 8,000,000-token prefix. This is a descriptive k=5/stop=1 token-index result at W=5220, not a physical pixel map, CFA phase, or identified predictor.

## Original evidence
Lead #338 reported one saturated white frame and six capped dark frames, using `tools/bayer_grid_probe.py` at `ff015534698e02ad184be694556a1e482aa754dc`, a 4,000,000-token prefix and within-W block shuffle seed 20261023. It reported white lag (0,1)/(0,2) near 0.122/0.989, a parity-dependent grid, and dark offsets below or above their shuffled baselines. It also reported whole-payload counts, q>=6 locations and white site tables.

## Verification
After #338 was posted, I reran the seven files at `3d201e22dd3210e925e184178d3527f0800793a7` with the original 4M prefix and a predeclared wider 8M prefix. These are the original controlled files; a wider prefix qualifies as the extension, not a new capture. The owner declared them CC0 in #338; public names, source links and hashes are recorded in `samples/om3-flat-338-provenance.json`. All hashes matched the records and manifest before analysis.

| File | SHA-256 | Declared capture | 4M (0,1), (0,2), (2,0), (2,-2), (2,2) | 8M same offsets |
| --- | --- | --- | --- | --- |
| PA200010.ORF | b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 | dark ISO 200 | .149478, .115709, .115958, .193813, .177636 | .149609, .115940, .115983, .194010, .177679 |
| PA200011.ORF | a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3 | dark ISO 200 | .149480, .116019, .115991, .193766, .176942 | .149262, .116008, .115932, .193893, .177173 |
| PA200012.ORF | c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7 | dark ISO 800 | .084067, .067444, .064930, .093468, .089222 | .083964, .067186, .064801, .093256, .089139 |
| PA200013.ORF | b714b28697a94081b83d7dd6127ed295f3ffbf6045b098a93381e373f8e3b946 | dark ISO 800 | .084053, .066974, .064729, .093309, .089100 | .083918, .067020, .064730, .093143, .089057 |
| PA200014.ORF | 49d1719d4120da07911488060c35f8d47dd76b9fc03c328d3cea8a190e298fca | dark ISO 800 | .083840, .067044, .064868, .093073, .089109 | .083908, .066934, .064811, .092967, .088992 |
| PA200015.ORF | 84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278 | dark ISO 800 | .083846, .067132, .064667, .092901, .088891 | .083814, .067124, .064762, .092962, .088867 |
| PA210010.ORF | d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e | saturated white ISO 200 | .122205, .989247, .928197, .929542, .926470 | .124530, .989129, .926955, .928313, .925214 |

The 4M shuffle rates for these offsets are approximately .1564-.1571 for ISO 200 dark, .0800-.0807 for ISO 800 dark and .502-.511 for white. White q>=6 occurs at indices 0, 1, 2, 5, 14, 5227, 5230 and 5239; the other six counts range from 133 to 366. Whole token surpluses are +5, +5, +10, +17, +18, +16 and +11 in table order, with 1-4 residual bits. White site-table counts in windows 2:202 and 565:765 match all eight counts stated in #338. These are nominal token coordinates; no physical-row alignment is assumed.

A separately implemented bounded token generator and direct-index arithmetic matched every real and shuffled grid pair and match count, whole-token endpoint and residual, escape and large-q counts, and site table across all 14 reports. The arithmetic implementations share the same human verifier; this is not an additional independent-human verification.

## Reproduce
At commit `3d201e22dd3210e925e184178d3527f0800793a7`, substitute hash-matched local paths for FILE1 through FILE7, in table order:

```sh
python -I -B tools/bayer_grid_probe.py --tokens 4000000 FILE1 FILE2 FILE3 FILE4 FILE5 FILE6 FILE7
python -I -B tools/bayer_grid_probe.py --tokens 8000000 FILE1 FILE2 FILE3 FILE4 FILE5 FILE6 FILE7
```

The defaults retain seed 20261023, the ordinary-suffix within-block shuffle, windows 2:202 and 565:765 and offset zero. The capture and scene provenance comes from the owner's declaration; these are not independent bodies or randomized captures. The result does not identify a physical CFA, pixel map, predictor or escape syntax.