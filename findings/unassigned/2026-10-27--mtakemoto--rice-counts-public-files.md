# Rice k=5 counts on three public files

Author: @mtakemoto
Verified by: @radialmonster
Lead: #339
Variant: unassigned
Partial: Rice stop-1 k=5 prefix and whole-payload counts on the two public controls

## Claim

For the two public controls, the lead's Rice stop-1 k=5 parse produces the counts below. These are counts under a candidate parse, not evidence that the payload uses Rice coding or that codewords correspond to image sites.

## Original evidence

Lead #339 used `tools/code_family_screen.py` at `4787e490c63df740785078c657de29ff4eee4612`, with a 3,000,000-byte prefix and a byte shuffle seeded 20261022. For 1993 it reported 3,918,435 prefix codewords in 23,999,997 bits and 20,525,511 whole-payload codewords in 126,080,996 bits, four residual bits, and +26,631 versus width times height; the shuffled whole count was -2,282,418 versus sites. For 7804 the corresponding real prefix and whole counts were 3,379,365 in 23,999,997 bits and 23,323,882 in 161,653,856 bits, zero residual bits, and +2,903,242 versus sites; the shuffled whole count was +2,497,188 versus sites.

## Verification

After the lead, @radialmonster reran the candidate at `6578d28d738b1fba1be8f4a93b1f932b224dc19e`, and predeclared 7803 as an additional file before measurement. Each retained CC0 record and manifest identity matched the local SHA-256. An independently written bit-by-bit counter agreed with each prefix and whole count and consumed-bit total. Each shuffle starts anew with `random.Random(20261022)` on the entire payload. The prefix is then the first 3,000,000 bytes of that payload, including for the shuffle.

| ID | Public name | SHA-256 |
|---|---|---|
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` |
| 7804 | OM System - OM-3 - 16bit (4:3).ORI | `bcc05bd57e78cbbb308a596f97987975f7167b17768d8c2d536c87e0c34298e0` |
| 7803 | OM System - OM-3 - 16bit (4:3).ORF | `63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0` |

| ID | Order | Prefix words / consumed bits | Whole words / consumed bits | Residual bits | Whole words minus sites |
|---|---|---:|---:|---:|---:|
| 1993 | real | 3,918,435 / 23,999,997 | 20,525,511 / 126,080,996 | 4 | +26,631 |
| 1993 | shuffled | 3,467,730 / 23,999,999 | 18,216,462 / 126,080,998 | 2 | -2,282,418 |
| 7804 | real | 3,379,365 / 23,999,997 | 23,323,882 / 161,653,856 | 0 | +2,903,242 |
| 7804 | shuffled | 3,402,537 / 23,999,993 | 22,917,828 / 161,653,852 | 4 | +2,497,188 |
| 7803 | real | 3,351,900 / 23,999,995 | 60,282,029 / 423,229,891 | 5 | +10,171,325 |
| 7803 | shuffled | 3,379,030 / 23,999,998 | 59,583,800 / 423,229,896 | 0 | +9,473,096 |

The two original public-file results match the stated scope; the extra file is descriptive, not a general claim about a camera or variant. Flat frames, other candidate families, recompression and container screens were not tested here. The previously reported zlib ratio discrepancy remains open and is not reproduced by this count-only run.

## Reproduce

At `6578d28d738b1fba1be8f4a93b1f932b224dc19e`, run the following from the repository root once for each hash-matched public file, replacing `FILE` with its path. This reads the sample and prints aggregate counts only; run it once with `real` and once with `shuffle` for each file.

```sh
python -I -B - FILE real <<'PY'
import random, sys
sys.path.insert(0, 'tools')
import orf_tokens, code_family_screen
width, height, payload = orf_tokens.locate(sys.argv[1])
data = bytearray(payload)
if sys.argv[2] == 'shuffle':
    random.Random(20261022).shuffle(data)
bits = bin(int.from_bytes(data, 'big'))[2:].zfill(len(data) * 8)
prefix, whole = code_family_screen.count_family(bits, 'rice_stop1', 5, min(3000000, len(data)) * 8)
print('width height payload_bits', width, height, len(bits))
print('prefix consumed_bits words', *prefix)
print('whole consumed_bits words', *whole)
print('residual_bits minus_sites', len(bits) - whole[0], whole[1] - width * height)
PY
```
