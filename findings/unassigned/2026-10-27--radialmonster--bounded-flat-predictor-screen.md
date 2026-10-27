# Bounded flat predictor candidate pass counts reproduce

Author: @radialmonster
Verified by: @radialmonster
Lead: #31
Variant: unassigned
Builds on: #338, #339
Partial: the specific flat-capture same-colour and inter-channel candidate grids reported in comment 6358630767

## Claim
Under the stated candidate raster, numeric mappings, initialization and assumed dark target, the 2640-candidate same-colour screen and 360-candidate inter-channel screen reproduce their reported zero pass counts on the original controlled OM-3 captures. A separate predeclared dark file also has zero passes. Incomplete candidates are reported separately; these bounded results do not rule out general predictor families or establish physical pixels, CFA, framing or an ORF codec.

## Original evidence
@mtakemoto reported in #31 comment 6358630767 that 0/2640 same-colour configurations passed on public CC0 dark PA200010.ORF or its byte-shuffled prefix, and 0/360 inter-channel configurations passed on that dark or white PA210010.ORF. The candidate tests used 16 nominal W-token rows, statistics from rows 4:16 and an assumed dark anchor of 254. The post-hoc 5.7–6.3 bits/site subset is descriptive. The candidate raster and the relationship between the metadata anchor and stored value domain are assumptions; k4 also produces near-site counts on low-noise files and the white stream has startup exceptions.

## Verification
After #31 was posted and its current reproduction section scanned, I ran `tools/flat_predictor_screen.py` at `a2fd30d0ca6980fbb59265367093f7ebe3809a8f`. The complete original dark candidate ledger in the paired run matched the separate real run exactly. Python 3.14.7 ran the real, shuffled, paired and extra screens in 160.7, 165.1, 224.8 and 233.0 seconds respectively; peak memory was not measured. The original dark real search completed 1614 of 2640 configurations, with 1026 stopped at the candidate range limit and zero passes. Its seed-20261022 shuffle of the first 300000 payload bytes completed 1632, with 1008 range stops and zero passes. Thus zero of the requested candidates pass, but range-stopped candidates are not completed negatives. The original paired 200000-byte-prefix inter-channel screen completed all 360 candidates on both dark and white, with zero dark, white or joint passes.

Predeclared additional dark PA200011.ORF is a separate same-body capture, not assumed an independent scene. Its real same-colour screen completed 1730, with 910 range stops and zero passes; its paired screen with the same white file completed all 360 on both, again with zero passes. The post-hoc bits/site subset is not a predeclared success test. The implementation treats a missing-stop cross skip as a failure instead of the historical malformed-input path; no such failure occurred here.

An independently reviewed aggregate checker verified every configuration, completed/failure category and threshold calculation in all four reports. Independent literal synthetic controls covered state updates and nonzero inter-channel cases; these checks assisted the same human verifier. They do not independently validate the candidate physical assumptions.

| Public CC0 input | SHA-256 |
| --- | --- |
| PA200010.ORF, original dark | b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 |
| PA210010.ORF, original white | d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e |
| PA200011.ORF, additional dark | a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3 |

Owner-declared public provenance and source links are in `samples/om3-flat-338-provenance.json`; each input matched its manifest row and local hash. The original contributor's search method is credited to @mtakemoto; the lead finder and verifier are @radialmonster.

## Reproduce
At `a2fd30d0ca6980fbb59265367093f7ebe3809a8f`, substitute the hash-matched paths for DARK, WHITE and EXTRA:

```sh
python -I -B tools/flat_predictor_screen.py --dark DARK --dark-sha256 b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4
python -I -B tools/flat_predictor_screen.py --dark DARK --dark-sha256 b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 --shuffle
python -I -B tools/flat_predictor_screen.py --dark DARK --dark-sha256 b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 --white WHITE --white-sha256 d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e
python -I -B tools/flat_predictor_screen.py --dark EXTRA --dark-sha256 a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3 --white WHITE --white-sha256 d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e
```