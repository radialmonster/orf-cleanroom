# Public whole-payload candidate family counts reproduce

Author: @mtakemoto
Verified by: @radialmonster
Lead: #339
Variant: unassigned
Builds on: 2026-10-27--mtakemoto--rice-counts-public-files
Partial: eight remaining candidate-family whole-payload count rows for public ids 1993 and 7804

## Claim

The eight remaining public-file candidate-family count rows in #339 reproduce on 1993 and 7804, in real order and after the fixed whole-payload byte shuffle. These counts are bounded candidate parses; they do not identify or exclude an ORF codec or establish a codeword-to-pixel mapping.

## Original evidence

Lead #339 used `tools/code_family_screen.py` at `4787e490c63df740785078c657de29ff4eee4612` and reported whole-payload completed codewords minus width times height. Its shuffled control permutes the entire payload with seed 20261022. The Rice stop-1 k=5 public counts are covered separately by `2026-10-27--mtakemoto--rice-counts-public-files`.

## Verification

After the lead, @radialmonster reran the eight declared families at `6578d28d738b1fba1be8f4a93b1f932b224dc19e`. All 32 original real/shuffled entries match the lead exactly. Predeclared 6344 was not an original lead input, but was previously studied; its values are a separate descriptive extension. An independently implemented bounded counter agrees with the whole counts and endpoints. Both agents assisted the same human, not an independent human verifier.

| Candidate family | 1993 real / shuffled | 7804 real / shuffled | 6344 real / shuffled |
|---|---:|---:|---:|
| Rice stop 1 k=4 | +674403 / +537055 | +6174157 / +6238058 | +4345301 / +4280926 |
| Rice stop 1 k=3 | +4452081 / +4732860 | +11518331 / +11521047 | +14500401 / +15129956 |
| Rice stop 0 k=5 | -1670492 / -2037879 | +3052372 / +2991474 | -1468652 / -2657533 |
| Exp-Golomb k=2 | +4840542 / +4580696 | +11294416 / +11144706 | +16039742 / +15105147 |
| Exp-Golomb k=3 | +747652 / +654715 | +6045753 / +5988915 | +4861321 / +4617633 |
| Elias gamma | +20351582 / +20251112 | +31539290 / +31214437 | +57399636 / +56497552 |
| Elias delta | -20498880 / -4698764 | -20420640 / -18191025 | -50282400 / -12839431 |
| Fibonacci | -2251762 / -1885005 | +4314037 / +4427068 | -1865804 / -1121922 |

Each cell is completed codewords minus width times height. Elias delta on the real payload stops before completing its first word on all three files, so the negative value there is exactly minus the number of stored positions; this is an incomplete candidate parse, not a count of negative words. Shuffled delta also leaves unconsumed suffixes; all residuals are bounded by the payload and have no asserted padding meaning. No flat frames, compression ratios, container screens or other families are verified here.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` |
| 7804 | OM System - OM-3 - 16bit (4:3).ORI | `bcc05bd57e78cbbb308a596f97987975f7167b17768d8c2d536c87e0c34298e0` |
| 6344 | OM System - OM-5 - 16bit (4:3).ORF | `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512` |

All inputs matched retained verified CC0 records, manifest identities and local hashes.

## Reproduce

At `6578d28d738b1fba1be8f4a93b1f932b224dc19e`, run once per hash-matched file, first with `real` and then with `shuffle`. This reads the sample and prints aggregate counts only.

```sh
python -I -B - FILE real <<'PY'
import random, sys
sys.path.insert(0, 'tools')
import code_family_screen as screen, orf_tokens
w, h, payload = orf_tokens.locate(sys.argv[1])
buf = bytearray(payload)
if sys.argv[2] == 'shuffle':
    random.Random(20261022).shuffle(buf)
bits = bin(int.from_bytes(buf, 'big'))[2:].zfill(len(buf) * 8)
families = [('rice_stop1', 4), ('rice_stop1', 3), ('rice_stop0', 5),
            ('exp_golomb', 2), ('exp_golomb', 3), ('elias_gamma', 0),
            ('elias_delta', 0), ('fibonacci', 0)]
for family, k in families:
    _, (end, count) = screen.count_family(bits, family, k, len(bits))
    print(family, k, 'words', count, 'consumed', end,
          'residual', len(bits) - end, 'minus_sites', count - w*h)
PY
```
