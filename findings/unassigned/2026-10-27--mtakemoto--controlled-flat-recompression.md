# Controlled OM-3 prefix recompression ratios reproduce

Author: @mtakemoto
Verified by: @radialmonster
Lead: #339
Variant: unassigned
Builds on: 2026-10-27--mtakemoto--zlib-public-prefix-reproduction, #338
Partial: the three original controlled OM-3 files' 4MB zlib, bzip2 and LZMA recompression ratios

## Claim
The reported first-4,000,000-byte zlib-9, bzip2-9 and LZMA-6 recompression ratios reproduce for the original white and two capped-dark OM-3 files, in real order and after the fixed whole-payload byte shuffle. These empirical compressed sizes do not identify the ORF coder or establish a general claim about efficient coders.

## Original evidence
#339 used `tools/code_family_screen.py` at `4787e490c63df740785078c657de29ff4eee4612`, with the first 4,000,000 payload bytes and a control shuffled over the entire payload using `random.Random(20261022)`, reset per file. Its owner-shared public CC0 inputs and declarations are retained in `samples/om3-flat-338-provenance.json`. It reported all 18 ratios below rounded to four decimals.

## Verification
After #339 was posted and its current text scanned, I reran the three original files at `03ad26bd2016212fa9069369fe0636c4e61abf93`; all 18 rounded ratios match. Predeclared P1010009 is a separate public E-M5 Mark II dark capture shared by @mszyndel, not an original #339 input; its CC0 provenance is in `samples/e-m5-mk-ii-dark-338-provenance.json`. All inputs passed record, manifest and local SHA-256 gates. Each cell is exact compressed bytes, real / shuffled, from a 4,000,000-byte input:

| File | SHA-256 | zlib-9 | bzip2-9 | LZMA-6 |
| --- | --- | ---: | ---: | ---: |
| PA210010.ORF white | d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e | 40749 / 1607958 | 36468 / 1508373 | 53444 / 1509572 |
| PA200010.ORF ISO 200 dark | b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 | 1900566 / 2844143 | 1583795 / 2795237 | 1675724 / 2614200 |
| PA200012.ORF ISO 800 dark | c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7 | 3364358 / 3646659 | 2732703 / 3795330 | 3014140 / 3637612 |
| P1010009.ORF ISO 200 dark | ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c | 2180703 / 3143995 | 1816391 / 3169007 | 1948164 / 3039452 |

The first three rows' ratios are respectively .0102/.4020, .0091/.3771, .0134/.3774; .4751/.7110, .3959/.6988, .4189/.6535; and .8411/.9117, .6832/.9488, .7535/.9094. The extension ratios are .5452/.7860, .4541/.7923 and .4870/.7599. Ratios use Python `round(length/4000000, 4)`; exact lengths avoid decimal tie ambiguity. Python was 3.14.7, with zlib build and runtime `1.3.1.zlib-ng`. Separately implemented incremental compressor calls matched all 24 exact lengths and ratios; both agents assisted the same human verifier. This does not resolve a prior environment-specific 1993 zlib discrepancy discussed in `2026-10-27--mtakemoto--zlib-public-prefix-reproduction`.

## Reproduce
At `03ad26bd2016212fa9069369fe0636c4e61abf93`, for each hash-matched public FILE run once as `real` and once with `shuffle`. This reads the file and prints aggregate lengths and the existing tool's ratios only:

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

The fixed shuffle is descriptive, and the different-body file is not assumed to be an independent scene. Other #339 claims and the broader coder-efficiency interpretation remain outside this Partial result.