# Literal Rice k4/k5 boundary intersections reproduce on wider prefixes

Author: @radialmonster
Verified by: @radialmonster
Lead: #574
Variant: unassigned
Builds on: #339, 2026-10-27--mtakemoto--controlled-flat-family-counts

## Claim
The six fixed 3 MB literal Rice k=4 versus k=5 positive boundary-intersection counts reproduce. The predeclared wider 6 MB runs on the same three captures are reported separately. These descriptive boundaries do not establish physical framing, synchronized hidden state or the correct code family.

## Original evidence
Each parse starts at bit 0 MSB-first. Bit 0 is the shared anchor but is not counted. A completed shared endpoint closes an interval (previous shared, current shared]. For shuffled cases Python Random(20261022) shuffles the entire payload before taking the prefix, reset for each file. Independent per-bit state-machine and marker arithmetic matched every aggregate field; both implementations share the container locator and shuffle method and assist the same human.

| Public CC0 input | SHA-256 | Order | Positive shared | Last shared bit | Maximum closed span bits | k4 / k5 open-tail words |
|---|---|---|---:|---:|---:|---:|
| PA210010.ORF (white) | d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e | real | 2 | 31529 | 31396 | 3993215 / 3993214 |
| PA210010.ORF (white) | same | shuffled | 1 | 10126565 | 10126565 | 1870630 / 1869336 |
| PA200010.ORF (dark ISO 200) | b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 | real | 5 | 21793383 | 15261360 | 367630 / 367629 |
| PA200010.ORF (dark ISO 200) | same | shuffled | 57878 | 23999801 | 4069 | 30 / 28 |
| PA200012.ORF (dark ISO 800) | c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7 | real | 6266 | 23996530 | 31203 | 578 / 578 |
| PA200012.ORF (dark ISO 800) | same | shuffled | 137097 | 23999851 | 1750 | 23 / 20 |

The unmatched tail is right-censored: a maximum closed span does not describe the remaining window or maximum divergence. Endpoints and tail lengths are bits; the residual is the incomplete suffix after the last completed endpoint.

| Input | Order | k4 / k5 last endpoint | k4 / k5 residual | k4 / k5 open tail |
|---|---|---:|---:|---:|
| PA210010.ORF | real | 24000000 / 23999995 | 0 / 5 | 23968471 / 23968466 |
| PA200010.ORF | real | 23999995 / 23999997 | 5 / 3 | 2206612 / 2206614 |
| PA200010.ORF | shuffle | 24000000 / 23999995 | 0 / 5 | 199 / 194 |
| PA200012.ORF | real | 23999995 / 23999998 | 5 / 2 | 3465 / 3468 |
| PA200012.ORF | shuffle | 23999995 / 23999996 | 5 / 4 | 144 / 145 |
| PA210010.ORF | shuffle | 23999996 / 23999997 | 4 / 3 | 13873431 / 13873432 |

All three file hashes matched retained owner-declared public CC0 records and manifest rows. These are three selected captures, not independent population samples; even a shared boundary does not establish physical resynchronization.


## Verification
After #574 was posted and its current body scanned clean, all six fixed 3 MB runs were repeated. Their full JSON reports matched the original reports exactly except elapsed time. The predeclared wider 6 MB windows are a qualifying wider run on the same captures, not independent captures or blind files:

| Input | Order | Positive shared | Last shared bit | Max closed span | k4 / k5 last endpoint | k4 / k5 residual | k4 / k5 open-tail bits |
|---|---|---:|---:|---:|---:|---:|---:|
| PA210010.ORF | real | 2 | 31529 | 31396 | 48000000 / 47999995 | 0 / 5 | 47968471 / 47968466 |
| PA210010.ORF | shuffle | 5 | 42786507 | 16898376 | 48000000 / 47999993 | 0 / 7 | 5213493 / 5213486 |
| PA200010.ORF | real | 6 | 26444345 | 15261360 | 47999996 / 47999997 | 4 / 3 | 21555651 / 21555652 |
| PA200010.ORF | shuffle | 115427 | 47999823 | 4069 | 47999996 / 47999997 | 4 / 3 | 173 / 174 |
| PA200012.ORF | real | 12662 | 47997361 | 39120 | 47999999 / 47999995 | 1 / 5 | 2638 / 2634 |
| PA200012.ORF | shuffle | 273582 | 47999947 | 1957 | 47999999 / 48000000 | 1 / 0 | 52 / 53 |

The open tails are right-censored. Maximum closed span does not bound the unclosed tail or demonstrate resynchronization. A separate per-bit state-machine and boundary-marker implementation matched all 12 fresh reports on every mathematical field, histogram, endpoint and tail. It shares the container locator and shuffle method, and both implementations assist the same human verifier.

## Reproduce
At commit e8ad4a37b11f7bcffa8cab9d0ef7edc1f84be2bf, set FILE to one of the three locally retained files after matching its SHA-256 above. Each command prints aggregate JSON only:

```sh
python -I -B tools/rice_boundary_compare.py "$FILE" --prefix-bytes 3000000
python -I -B tools/rice_boundary_compare.py "$FILE" --prefix-bytes 3000000 --shuffle --seed 20261022
```

The output includes all fixed interval and word-count histogram bins, sums and maxima, total words, last endpoints, residual bits and unmatched tails. Empty histograms and null gap statistics represent no positive shared endpoint.

For the predeclared wider run use the same commands with `--prefix-bytes 6000000`. The files' public identities and SHA-256 values are above; owner CC0 declarations and source links are retained in `samples/om3-flat-338-provenance.json`.
