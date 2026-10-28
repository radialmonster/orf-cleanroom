# Prefix and whole candidate Rice statistics on OM-3 dark files

Author: @radialmonster
Verified by: @radialmonster
Lead: #624
Variant: unassigned
Builds on: #106, #338, #594

## Claim

For two public OM-3 dark files, compare fixed 1,500,000-word prefix projections and capped-q lag correlations with the whole candidate parse. This is descriptive and does not establish equivalence, ISO causality, pixel framing or the camera codec.

## Original evidence

The lead reported PA200010 and PA200012. Their null projections both rounded to 0.8179 and 0.8308 respectively in prefix and whole results; lag 1 and lag 2 differed between extents. All inputs had been exposed previously, including whole candidate counts and endpoints.

## Verification

After the lead, fresh runs exactly reproduced both original records and evaluated the four predeclared additional files. All six independent parser and integer-moment reports matched all primary aggregate fields; both implementations share the TIFF locator and assisted the same human. All 12 guarded runs exited 0 with empty stderr. All six displayed null projections agree between extents to four decimal places, while their exact rational projections differ. The prefix residual is the remaining payload, not a malformed-word assertion.

| File | Extent | Words | Endpoint bits | Residual bits | Escapes | Complete-byte bits | Ones | Real | Null | Lag 1 | Lag 2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 200010 | prefix | 1500000 | 9003519 | 113567449 | 2 | 9003512 | 3850471 | 1.0000 | 0.8179 | 0.4042695932 | 0.3926050138 |
| 200010 | whole | 20420645 | 122570967 | 1 | 4 | 122570960 | 52415023 | 1.0000 | 0.8179 | 0.4028892866 | 0.3885149851 |
| 200011 | prefix | 1500000 | 9003521 | 113567439 | 1 | 9003520 | 3850976 | 1.0000 | 0.8180 | 0.4015551586 | 0.3801298326 |
| 200011 | whole | 20420645 | 122570956 | 4 | 3 | 122570952 | 52422458 | 1.0000 | 0.8180 | 0.4106004051 | 0.3956241459 |
| 200012 | prefix | 1500000 | 9008576 | 113631728 | 1 | 9008576 | 4041655 | 1.0000 | 0.8308 | 0.2418362196 | 0.2399966839 |
| 200012 | whole | 20420650 | 122640301 | 3 | 5 | 122640296 | 55024583 | 1.0000 | 0.8308 | 0.2428631263 | 0.2368892601 |
| 200013 | prefix | 1500000 | 9008812 | 113632988 | 2 | 9008808 | 4041532 | 1.0000 | 0.8308 | 0.2461461118 | 0.2327387870 |
| 200013 | whole | 20420657 | 122641798 | 2 | 6 | 122641792 | 55030807 | 1.0000 | 0.8308 | 0.2422159307 | 0.2334665159 |
| 200014 | prefix | 1500000 | 9008766 | 113632210 | 1 | 9008760 | 4042217 | 1.0000 | 0.8308 | 0.2369900707 | 0.2392670815 |
| 200014 | whole | 20420658 | 122640974 | 2 | 5 | 122640968 | 55029296 | 1.0000 | 0.8308 | 0.2384835894 | 0.2357249766 |
| 200015 | prefix | 1500000 | 9008518 | 113632530 | 1 | 9008512 | 4042541 | 1.0000 | 0.8309 | 0.2562772177 | 0.2406844999 |
| 200015 | whole | 20420656 | 122641047 | 1 | 5 | 122641040 | 55035354 | 1.0000 | 0.8309 | 0.2453993997 | 0.2345904353 |

## Reproduce

At commit 5743f30d7d946c716ff5c1d55b3847b17c805e40, obtain the six owner-declared CC0 files and verify their published SHA-256 values and retained provenance. Run `python -I -B tools/prefix_whole_null_probe.py --sample <public-name> <sha256> <local-path>` for each. The tool reads a hash-checked snapshot and prints aggregate data only.

| Public name | SHA-256 |
|---|---|
| PA200010.ORF | b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 |
| PA200011.ORF | a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3 |
| PA200012.ORF | c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7 |
| PA200013.ORF | b714b28697a94081b83d7dd6127ed295f3ffbf6045b098a93381e373f8e3b946 |
| PA200014.ORF | 49d1719d4120da07911488060c35f8d47dd76b9fc03c328d3cea8a190e298fca |
| PA200015.ORF | 84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278 |

## Limitations

The candidate grammar starts at bit zero, takes stop 1 plus five suffix bits without an escape skip and retains all words, capping q at 8 for pair-centered Pearson lags. Null density uses complete bytes before each endpoint; the projected count is not a decoded raster. Previously studied same-session captures do not establish matching shutter, temperature or processing. Independent checks share the TIFF locator and assisted the same human.
