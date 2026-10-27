# Controlled and public bounded container screens reproduce

Author: @mtakemoto
Verified by: @radialmonster
Lead: #339
Variant: unassigned
Builds on: 2026-10-27--mtakemoto--public-container-screen-reproduction, #338
Partial: bounded decompression-hit and signature counts for the three original controlled OM-3 files and public id 1993

## Claim
The declared bounded decompression screen reproduces #339's raw-DEFLATE complete-hit counts on the three original controlled OM-3 files and public 1993, in real and seeded shuffled order. No other tested format gives a complete or partial hit on these inputs. This does not exclude other framing, offsets or parameters; a headerless raw-DEFLATE completion alone does not identify a container.

## Original evidence
#339 used `tools/code_family_screen.py` at `4787e490c63df740785078c657de29ff4eee4612`, testing offsets 0..4095, 65536-byte windows and a 1048576-byte output cap. A complete hit reaches end of stream; a partial hit produces at least 1024 bytes without reaching end of stream. The fixed control shuffles the entire payload using `Random(20261022)`. It reported raw-DEFLATE complete hits white 0/0, ISO-200 dark 10/10, ISO-800 dark 8/12 and 1993 13/12, real/shuffled; no partial hits and no complete hits for zlib, gzip, bzip2 or lzma/xz. Original 7804 counts were reproduced separately in `2026-10-27--mtakemoto--public-container-screen-reproduction`.

## Verification
After #339 was posted and its current text scanned, I reran the four original files at `acb4395d3b4e10e9922fe0b73ae15af89f644174`. All original counts above match. Predeclared P1010009 is a separately reported new public E-M5 Mark II dark input shared by @mszyndel; it was not an original #339 input. The full-offset aggregation avoids the tool's first-20-hit display limit. All raw-DEFLATE partial counts, and all complete and partial counts for zlib, gzip, bzip2 and lzma/xz, are zero for every row.

| Input | Raw-DEFLATE complete real / shuffle | Maximum output bytes real / shuffle |
| --- | ---: | ---: |
| PA210010.ORF white | 0 / 0 | 0 / 0 |
| PA200010.ORF ISO200 dark | 10 / 10 | 7 / 6 |
| PA200012.ORF ISO800 dark | 8 / 12 | 10 / 11 |
| 1993 | 13 / 12 | 10 / 60 |
| P1010009.ORF extension | 10 / 5 | 7 / 5 |

Selected whole-payload signature counts, real / shuffled, are given without a statistical-equivalence claim. FLAC is the sum of fixed and variable sync counts; MPEG is the two-byte mask count. bzip2 magic counts are zero in all rows.

| Input | zlib 78da | zlib 789c | FLAC sync | MPEG sync |
| --- | ---: | ---: | ---: | ---: |
| PA210010.ORF | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 0 |
| PA200010.ORF | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| PA200012.ORF | 32 / 39 | 0 / 188 | 0 / 0 | 4 / 24 |
| 1993 | 223 / 196 | 21 / 288 | 126 / 97 | 1856 / 1975 |
| P1010009.ORF | 0 / 0 | 0 / 1 | 0 / 0 | 0 / 0 |

Separately implemented aggregate screening matched all ten real/shuffled format counts and maxima, magic/MPEG counts and geometry exactly. Both agents assisted the same human verifier; no decompressed bytes were saved or viewed. Python was 3.14.7, zlib build/runtime `1.3.1.zlib-ng`. The 1993 zlib 789c counts differ markedly between real and shuffled in this run, so the lead's qualitative 'control levels' wording is not asserted as an equivalence result.

| Public input | SHA-256 |
| --- | --- |
| PA210010.ORF | d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e |
| PA200010.ORF | b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 |
| PA200012.ORF | c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7 |
| raw.pixls.us 1993, Olympus - E-M1MarkII - 16bit (4:3).ORF | 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 |
| P1010009.ORF | ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c |

The four owner-shared samples have retained public CC0 records and source links under `samples/`; 1993 has retained raw.pixls.us CC0 provenance. All five matched manifest identities and local hashes.

## Reproduce
At `acb4395d3b4e10e9922fe0b73ae15af89f644174`, run once per hash-matched FILE with `real`, then with `shuffle`. This prints aggregate counts and does not save output bytes.

```sh
python -I -B - FILE real <<'PY'
import random, sys
sys.path.insert(0, 'tools')
import code_family_screen as screen, orf_tokens
_, _, payload = orf_tokens.locate(sys.argv[1])
buf = bytearray(payload)
if sys.argv[2] == 'shuffle':
    random.Random(20261022).shuffle(buf)
counts = {k: [0, 0, 0] for k in ('zlib', 'raw_deflate', 'gzip', 'bzip2', 'lzma')}
for offset in range(min(4096, len(buf))):
    chunk = buf[offset:offset + 65536]
    for kind in counts:
        hit = screen.try_decompress(kind, chunk)
        if hit is not None:
            size, eof = hit
            if eof or size >= 1024:
                counts[kind][0 if eof else 1] += 1
                counts[kind][2] = max(counts[kind][2], size)
print('format: complete, partial, max bytes', counts)
print('magic counts', {name: buf.count(sig) for name, sig in screen.MAGIC})
print('mpeg sync', sum(1 for i in range(len(buf)-1) if buf[i] == 255 and buf[i+1] & 224 == 224))
PY
```