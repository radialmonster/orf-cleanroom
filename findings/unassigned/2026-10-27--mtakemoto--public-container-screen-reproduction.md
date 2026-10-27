# Public bounded container screen reproduces

Author: @mtakemoto
Verified by: @radialmonster
Lead: #339
Variant: unassigned
Partial: bounded container decompression-hit counts for public id 7804

## Claim

The lead's bounded decompression screen on public id 7804 reproduces 25 real and 22 shuffled complete raw-DEFLATE hits, with no complete hits for the other four tested formats and no partial hits. This screen does not rule out other framing, offsets or parameters, and headerless raw-DEFLATE completion alone is not evidence of a container.

## Original evidence

Lead #339 used `tools/code_family_screen.py` at `4787e490c63df740785078c657de29ff4eee4612`: offsets 0 through 4095, 65536-byte windows and a 1048576-byte output cap. A hit is complete when the decompressor reaches its end of stream, or partial when at least 1024 output bytes are produced without an end of stream. The control shuffles the entire payload using seed 20261022. The lead's body reports 25 / 22 complete raw-DEFLATE hits for 7804, no partial hits and at most 79 output bytes across its screened inputs; a subsequent author comment reported a maximum of 50 bytes. The 7804 real run below supports 79 for this input.

## Verification

After the lead, @radialmonster reran the bounded screen at `6578d28d738b1fba1be8f4a93b1f932b224dc19e` under Python 3.14.7, zlib build/runtime 1.3.1.zlib-ng. Counting every hit by format avoids the existing tool's first-20-hit display limit. An independently written aggregate screen agreed on all counts and maximum sizes; this is a computational cross-check, not independent-human verification.

| ID | Order | Complete raw-DEFLATE hits | Maximum raw-DEFLATE output bytes | Other complete or partial hits |
|---:|---|---:|---:|---:|
| 7804 | real | 25 | 79 | 0 |
| 7804 | shuffled | 22 | 17 | 0 |
| 6344 | real | 13 | 145 | 0 |
| 6344 | shuffled | 18 | 249 | 0 |

All raw-DEFLATE partial counts are also zero. Other formats are zlib, gzip, bzip2 and lzma/xz. Predeclared 6344 was not an original lead input but was previously studied; its result is separate descriptive evidence. The two files do not establish general absence of a container, a codec or physical framing. No decompressed bytes were saved or viewed.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 7804 | OM System - OM-3 - 16bit (4:3).ORI | `bcc05bd57e78cbbb308a596f97987975f7167b17768d8c2d536c87e0c34298e0` |
| 6344 | OM System - OM-5 - 16bit (4:3).ORF | `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512` |

Both local hashes matched retained verified CC0 records, public identities and existing manifest rows.

## Reproduce

At `6578d28d738b1fba1be8f4a93b1f932b224dc19e`, run once per hash-matched file, first with `real` and then with `shuffle`. This counts all hits from the existing tool's bounded decompressor and prints aggregates only.

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
print('format: complete, partial, max output bytes', counts)
PY
```
