# Token-parity mean contribution to q lag differences reproduces

Author: @radialmonster
Verified by: @radialmonster
Lead: #585
Variant: unassigned
Builds on: #86, 2026-10-20--radialmonster--large-sensor-k5-parse-near-bernoulli-null

## Claim
For the two original OM-1 Mark II q47-prefix files, the fixed token-index parity between-group mean component contributes far less than half the positive lag-2 minus lag-1 Pearson difference on the 1M-token prefix. The predeclared wider 2M-token prefixes show the same outcome on these two files. For the two OM-3 files the difference is nonpositive, so the criterion is not applicable. This tests only the specified between-group mean contribution; it does not rule out other parity structure or establish physical rows, CFA, a mechanism or a codec.

## Original evidence
The fixed protocol was posted before outcomes at https://github.com/radialmonster/orf-cleanroom/issues/86#issuecomment-6456152287. Each file's first 1000000 complete q+stop+5 candidate tokens starts at bit 0; all tokens including escapes and initial q47 are retained, and q is capped at 8. The old bounded-prefix scanner reaches exactly the requested 1000000 complete tokens for every file. For each lag, partition pairs by original source-token index parity. Exact integer moments and rational within/between centered covariance numerators use the same pooled Pearson denominator. The table gives the Pearson correlations, between-parity components, and (between2 - between1)/(r2 - r1) only for a positive difference; the 0.5 comparison is a predeclared descriptive threshold.

| Public ID | r1 | r2 | between1 | between2 | share | >= 0.5 |
|---|---:|---:|---:|---:|---:|---|
| 7267 | 0.086010584603 | 0.115710063669 | -0.000000028364 | 0.000000029196 | 0.000001938071 | false |
| 7269 | 0.076278736579 | 0.146467692931 | -0.000000187911 | 0.000000190121 | 0.000005385922 | false |
| 7801 | 0.027549707530 | 0.015588614423 | -0.000005449150 | 0.000005437646 | not applicable | not applicable |
| 7803 | 0.035322375910 | 0.027012072224 | -0.000000273099 | 0.000000270444 | not applicable | not applicable |

Public identity / SHA-256: 7267 OM System - OM-1 Mark II - 16bit (4:3).orf `5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756`; 7269 same public name `dd2a6c1c4ca4d86201207925477e2ea8e50ebd53d7df9117847093f5023540ec`; 7801 OM System - OM-3 - 16bit (4:3).ORF `8832599870d20a96f28897e3e28d9705a4bd05871c9833c7c60a8b59d7d64b82`; 7803 same public name `63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0`. All snapshots matched retained verified CC0 records and manifest identity/hash rows. Independent bounded bit parsing and Fraction covariance matched full JSON for all four; both implementations assist the same human. These selected files are not independent captures.


## Verification
After #585 was posted and its current body scanned clean, all four 1M-token reports were rerun and exactly match the full discovery JSON. The predeclared wider 2M-token prefixes below use the same four captures, not new or blind captures. Each requested prefix completed; all tokens including escapes were retained and q was capped at 8.

| Public ID | r1 | r2 | between1 | between2 | share | >= 0.5 |
|---|---:|---:|---:|---:|---:|---|
| 7267 | 0.088748422565 | 0.122335466604 | -0.000000359141 | 0.000000359145 | 0.000021385830 | false |
| 7269 | 0.081053788224 | 0.148531188802 | -0.000000213724 | 0.000000214917 | 0.000006352369 | false |
| 7801 | 0.028266162011 | 0.016892259198 | -0.000001004046 | 0.000001001566 | not applicable | not applicable |
| 7803 | 0.033683887237 | 0.027852642449 | -0.000000682081 | 0.000000679995 | not applicable | not applicable |

A separately implemented bounded bit parser and Fraction covariance calculation matched all eight fresh 1M/2M JSON reports exactly, including group moments, rational numerators, correlations and endpoints. Both implementations assist the same human verifier. The threshold and decomposition are descriptive, not a causal or significance test.

## Reproduce
At commit df652cabe9ede38faed68e3acdc6758b28abadbf set FILE to one of the four retained public files and check its SHA-256 above. Output includes all integer group moments, exact fraction numerators, correlations, criterion and endpoint; no pixel data is written.

```sh
python -I -B tools/q_parity_covariance.py "$FILE" --tokens 1000000
```

For the predeclared wider run use the same command with `--tokens 2000000`. The output retains exact group moments and fractions; the table rounds floating values to 12 decimals.
