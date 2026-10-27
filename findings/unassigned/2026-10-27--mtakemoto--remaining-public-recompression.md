# Remaining public prefix recompression ratios reproduce

Author: @mtakemoto
Verified by: @radialmonster
Lead: #339
Variant: unassigned
Builds on: 2026-10-27--mtakemoto--zlib-public-prefix-reproduction, 2026-10-27--mtakemoto--controlled-flat-recompression
Partial: public 1993 bzip2/LZMA and 7804 zlib/bzip2/LZMA first-4MB ratios

## Claim
The remaining reported first-4,000,000-byte public-file recompression ratios reproduce for 1993 and 7804, real and after the fixed whole-payload shuffle. These sizes do not identify a codec or establish a general efficient-coder claim.

## Original evidence
#339 used `tools/code_family_screen.py` at `4787e490c63df740785078c657de29ff4eee4612`, with 4,000,000-byte prefixes and whole-payload `Random(20261022)` shuffle reset per file. Its 1993 bzip2/LZMA ratios are .9391/.9543 real and 1.0002/.9866 shuffled; 7804 zlib/bzip2/LZMA ratios are 1.0003/1.0035/1.0001 real and 1.0003/1.0050/1.0001 shuffled. Its 1993 zlib result was previously reproduced in `2026-10-27--mtakemoto--zlib-public-prefix-reproduction`; the three controlled flat files are covered by `2026-10-27--mtakemoto--controlled-flat-recompression`.

## Verification
After #339 was posted and its current text scanned, I reran the two original public files at `cedefaaa50568a9d4d074ec8cd3892337401308a`. All ten real/shuffled ratios in this Partial scope match at the reported precision. Predeclared 6344 is a separate, previously studied public OM-5 file, not an original #339 input. Each table cell is exact compressed bytes, real / shuffled, from 4,000,000 input bytes:

| ID | zlib-9 | bzip2-9 | LZMA-6 |
| --- | ---: | ---: | ---: |
| 1993 | 3916500 / 3926377 | 3756504 / 4000633 | 3817024 / 3946308 |
| 7804 | 4001216 / 4001226 | 4014003 / 4019890 | 4000260 / 4000260 |
| 6344 extension | 3894127 / 3961711 | 3735838 / 4012764 | 3782920 / 3984856 |

6344 ratios are .9735/.9904, .9340/1.0032 and .9457/.9962 in the same algorithm order. Ratios are Python `round(length/4000000, 4)`; exact lengths avoid decimal tie ambiguity. Python was 3.14.7, zlib build/runtime `1.3.1.zlib-ng`. Separately implemented incremental compressor calls matched all 18 exact lengths and ratios; the agents assisted the same human verifier. The 1993 zlib lengths also match the retained earlier result; the earlier environment-specific discrepancy remains unexplained.

| ID | Public raw.pixls.us name | SHA-256 |
| ---: | --- | --- |
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 |
| 7804 | OM System - OM-3 - 16bit (4:3).ORI | bcc05bd57e78cbbb308a596f97987975f7167b17768d8c2d536c87e0c34298e0 |
| 6344 | OM System - OM-5 - 16bit (4:3).ORF | 42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512 |

All inputs matched retained verified CC0 records, manifest identities and local hashes. The shuffle is descriptive; these files are not assumed independent scenes.

## Reproduce
At `cedefaaa50568a9d4d074ec8cd3892337401308a`, for each hash-matched FILE run once as `real`, then as `shuffle`:

```sh
python -I -B - FILE real <<'PY'
import bz2, lzma, random, sys, zlib
sys.path.insert(0, 'tools')
import code_family_screen as screen, orf_tokens
_, _, payload = orf_tokens.locate(sys.argv[1])
buf = bytearray(payload)
if sys.argv[2] == 'shuffle':
    random.Random(20261022).shuffle(buf)
prefix = bytes(buf[:4000000])
print('lengths', len(zlib.compress(prefix, 9)), len(bz2.compress(prefix, 9)),
      len(lzma.compress(prefix, preset=6)))
print('ratios', screen.compressibility(prefix))
PY
```