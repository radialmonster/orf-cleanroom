# Fixed single-period side-peak control reproduces a bounded negative

Author: @mszyndel
Verified by: @mszyndel
Lead: #734
Variant: unassigned
Builds on: #724, #144, #197

## Claim

The frozen nine-case public 7262 table in #734 reproduces in a fresh post-lead
run. Its specified head/rest-resampling control at imposed period 5566 does
not reproduce the real 300-row secondary pair, despite selecting that imposed
primary. A separate extension to two predeclared public files also has no
accepted synthetic secondary at any of the three extents. This excludes only
the specified one-seed surrogate as a sufficient explanation under the frozen
criterion; it does not exclude general estimator artifacts or establish
physical rows, a second period, value recovery or a codec.

## Original evidence

#734 measured raw.pixls.us 7262 at 150/300/600 folded rows, comparing real,
single-period synthetic and whole-prefix shuffle sequences. Real secondary
counts were 1/2/3; synthetic and shuffled counts were zero at every extent.
At 300 rows, real primary 5566 (z 8.15) had secondaries 5614 (6.46) and
5518 (6.16). Synthetic primary 5566 (11.27) had no accepted secondary.

The frozen plan was posted on #724 before discovery. Tool versions:
`tools/stride_harmonics.py` at `090136605d6ac17c2a80927bbe5ea12a0ea49247`,
`tools/token_row_stride.py` at `e38cf378378d11d488835bf87ea5b49eb68950cb`,
and `tools/orf_tokens.py` at `2744ab63601d66855452858eb64d642fdb5db66d`.
Repository run commit: `d50e4739c7ba5c64052da8867eb5ab8ecf9ee9a4`.

## Verification

On 2026-11-13 UTC, after #734 was posted and its unchanged body scanned clean,
@mszyndel freshly reran all nine discovery cases. Every output report was
byte-identical to its discovery report. Then the same procedure was applied to
reserved 7264/7266, at the previously fixed imposed periods 5578/5631.
All 27 post-lead invocations completed successfully, using Python 3.10.17.
The known-period synthetic self-test passed before camera measurement.
This is self-verification by the finder, not a different human or method.

All inputs were downloaded with `tools/pixls_samples.py`, which verified live
CC0 licences and downloaded SHA-256. Local hashes also matched the manifest;
those verified identities were retained and reused without a second catalogue
request. Public names (the ORIs share a catalogue name, so identify them by id
and hash), hashes and predeclared periods are:

| raw.pixls.us id | Public name | SHA-256 | Imposed period |
| ---: | --- | --- | ---: |
| 7262 | OM System - OM-1 Mark II - 16bit (4:3).orf | d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd | 5566 |
| 7264 | OM System - OM-1 Mark II - 16bit (4:3).ori | d7fea34029b9926e7d9cf6ecdfef9de90cbda41ff6eea009cc1a4f5b1813b8df | 5578 |
| 7266 | OM System - OM-1 Mark II - 16bit (4:3).ori | 1c994e4bf5aa4e48d6ec97a1f83558184a866f71bca2b5b1bf914a159927e199 | 5631 |

Each payload is 5220 by 3912. The 150/300/600 extents parse 963000/1926000/
3852000 candidate tokens respectively. In each result cell below, the primary
S (z) precedes the semicolon; every accepted secondary S (z) follows it.
These z scores are descriptive, not calibrated significance.

| id | Rows | Real: primary; secondaries | Synthetic: primary; secondaries | Shuffle: primary; secondaries |
| ---: | ---: | --- | --- | --- |
| 7262 | 150 | 5614 (6.46); 5560 (5.77) | 5566 (7.66); none | 5867 (3.30); none |
| 7262 | 300 | 5566 (8.15); 5614 (6.46), 5518 (6.16) | 5566 (11.27); none | 6295 (2.83); none |
| 7262 | 600 | 5515 (9.13); 5570 (7.00), 5614 (5.63), 5646 (4.40) | 5566 (5.32); none | 6192 (3.44); none |
| 7264 | 150 | 5629 (6.81); 5571 (6.01) | 5578 (8.11); none | 5522 (2.90); none |
| 7264 | 300 | 5578 (7.99); 5620 (6.13), 5529 (5.07) | 5578 (13.63); none | 6347 (3.73); none |
| 7264 | 600 | 5524 (8.41); 5578 (7.33), 5645 (5.42) | 5578 (10.30); none | 6354 (3.03); none |
| 7266 | 150 | 5687 (7.63); 5631 (4.78) | 5631 (7.63); none | 5594 (2.80); none |
| 7266 | 300 | 5631 (8.15); 5694 (5.30), 5586 (5.17) | 5631 (10.89); none | 5250 (3.16); none |
| 7266 | 600 | 5557 (8.66); 5629 (5.70), 5700 (5.57), 5589 (5.44) | 5631 (5.47); none | 6308 (3.80); none |

For the frozen 300-row decision, the synthetic primary must be within 2 tokens
of its imposed period and accepted secondaries within 2 of both published
offsets: (-48,+48), (-49,+42), (-45,+63), respectively. Every synthetic primary
is exactly at its imposed period, but none has a secondary, so all three pairs
fail this criterion. No threshold, period or seed was adjusted after seeing
outcomes. Among the real peaks, only 7266's 300-row S=5694 hits the tool's
rounded W*p/q target window (12/11; exact residual -0.55 tokens); there are no
exact rational hits. All other real peaks and all controls have zero such hits.

The reserved files may be companions and are kept as one possibly related
ORF/ORI group. These public files were already exposed in #724: this is a
procedurally reserved extension, not blind independent-capture validation.
Synthetic head/rest distributions are fitted separately at each extent; prefix
length and fitting support change along with folded-row count. Consequently
this does not isolate a window-length effect. Only one seed is tested, and the
same parser, locator and score are reused. Independent framing and separately
justified nonstationary/phase alternatives remain open. No private inputs.

## Reproduce

At the repository commit above, substitute hash-matched local paths for the
three public input placeholders. Other parameters are frozen defaults: head
32, scan W..W+1200 (5220..6420), z-min 4, suppression 32, min-distance 8,
q-max 12 and tolerance 2. Each invocation independently resets seed 20261112.
These commands read files and print aggregate scores only.

```sh
python -I -B tools/stride_harmonics.py --self-test
for nrows in 150 300 600; do
    python -I -B tools/stride_harmonics.py --rows "$nrows" --seed 20261112 FILE7262
    python -I -B tools/stride_harmonics.py --rows "$nrows" --seed 20261112 --control synthetic --period 5566 FILE7262
    python -I -B tools/stride_harmonics.py --rows "$nrows" --seed 20261112 --control shuffle FILE7262
done
for nrows in 150 300 600; do
    python -I -B tools/stride_harmonics.py --rows "$nrows" --seed 20261112 FILE7264
    python -I -B tools/stride_harmonics.py --rows "$nrows" --seed 20261112 --control synthetic --period 5578 FILE7264
    python -I -B tools/stride_harmonics.py --rows "$nrows" --seed 20261112 --control shuffle FILE7264
done
for nrows in 150 300 600; do
    python -I -B tools/stride_harmonics.py --rows "$nrows" --seed 20261112 FILE7266
    python -I -B tools/stride_harmonics.py --rows "$nrows" --seed 20261112 --control synthetic --period 5631 FILE7266
    python -I -B tools/stride_harmonics.py --rows "$nrows" --seed 20261112 --control shuffle FILE7266
done
```
