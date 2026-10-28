# Fixed capped-prefix single-block test stops at first escape

Author: @radialmonster
Verified by: @radialmonster
Lead: #603
Variant: unassigned
Builds on: #197, #601, 2026-10-21--radialmonster--four-payloads-start-q47

## Claim

Under the fixed single-block interpretation of the capped-prefix grammar described in public patent US7259698B2, all eight selected public files encounter an invalid escape at the first word after the assumed initial marker. This rejects only the stated no-interior-marker, no-adaptation hypothesis for these inputs; it does not reject the patent generally or identify a camera codec.

## Original evidence

The lead fixed a marker at payload bit zero, ending at its one, then k=5 and maximum prefix 12. D=15 uses the patent example; D=12 was selected after the known 39-zero prefix census and is exploratory. In four previously studied files (7267, 7269, 1993, 1995), the first real word was invalid. A matched control preserved the initial six (D=15) or five (D=12) bytes and shuffled the entire remainder using Random(20261022), reset per file. Both D=15 controls stopped at an invalid escape; both D=12 controls reached the one-million-word ceiling.

## Verification

After the lead, fresh independent runs reproduced all four original 1M records exactly and tested their wider 2M ceilings plus predeclared files 7801, 7803, 1997 and 1998 at both ceilings. All eight real markers matched; every real run stopped before completing a word, on an invalid first escape. The 2M ceiling therefore adds no real-data exposure beyond each early stop; new files are the qualifying extension, not blind captures. All 32 real/control records matched a separately implemented parser and shuffle on every field and control hash; the implementations share the TIFF locator and assisted the same human.

Public CC0 identities and SHA-256:

- 7267: OM System - OM-1 Mark II - 16bit (4:3).orf; SHA-256 `5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756`.
- 7269: OM System - OM-1 Mark II - 16bit (4:3).orf; SHA-256 `dd2a6c1c4ca4d86201207925477e2ea8e50ebd53d7df9117847093f5023540ec`.
- 7801: OM System - OM-3 - 16bit (4:3).ORF; SHA-256 `8832599870d20a96f28897e3e28d9705a4bd05871c9833c7c60a8b59d7d64b82`.
- 7803: OM System - OM-3 - 16bit (4:3).ORF; SHA-256 `63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0`.
- 1993: Olympus - E-M1MarkII - 16bit (4:3).ORF; SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`.
- 1995: Olympus - E-M1MarkII - 16bit (4:3).ORI; SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`.
- 1997: Olympus - E-M1MarkII - 16bit (4:3).ORI; SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`.
- 1998: Olympus - E-M1MarkII - 16bit (4:3).ORF; SHA-256 `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`.

Each real cell is `unconsumed word-start bit / invalid D-bit value`. Each control cell is `accepted words / stop / unconsumed word-start bit / invalid D-bit value`, with `-` when no invalid value was observed. The last column is the hash of the entire marker-preserving shuffled payload. A `limit` stop is not a complete payload parse.

| ID | D | Real bit / value | 1M control | 2M control | Control SHA-256 |
|---|---:|---:|---|---|---|
| 7267 | 15 | 48 / 0 | 28289 / invalid_escape / 203448 / 219 | 28289 / invalid_escape / 203448 / 219 | `8abb2368d54bba189de4458b377e8a8827a499da91eb26b7b6fdc54375f875e6` |
| 7269 | 15 | 48 / 0 | 15516 / invalid_escape / 113020 / 50 | 15516 / invalid_escape / 113020 / 50 | `b8bd87349fdc1c33fa001f993463c5009fb88f253dcceb931c11ae0f6edc5e4f` |
| 7801 | 15 | 48 / 0 | 97152 / invalid_escape / 683856 / 284 | 97152 / invalid_escape / 683856 / 284 | `080acf325557c4704c01f6552d07d7be2f60a8c36987f90ad9b671ddc4f22f44` |
| 7803 | 15 | 48 / 256 | 12239 / invalid_escape / 87051 / 97 | 12239 / invalid_escape / 87051 / 97 | `020a3a1b593da32289c7a478030f1ad649624dffb4318f8eb6b5ee6aeb3eda1a` |
| 1993 | 12 | 40 / 65 | 1000000 / limit / 6921428 / - | 2000000 / limit / 13844402 / - | `b52247567046a9173d4b234481392bd1de1017828ea940300217c55e2217a6b0` |
| 1995 | 12 | 40 / 33 | 1000000 / limit / 6901665 / - | 2000000 / limit / 13803918 / - | `6989449d8e00e1e5781b3c42e72e7474db7a119a82d31a5a721c40d2f700a777` |
| 1997 | 12 | 40 / 65 | 1000000 / limit / 6900672 / - | 2000000 / limit / 13803944 / - | `8e046031643ab75b3ec713ad2fcc2cdce09cc3862e37b092e4e12a04d6d8387b` |
| 1998 | 12 | 40 / 0 | 1000000 / limit / 6903500 / - | 2000000 / limit / 13805833 / - | `01ec20f25f7aa31308400581a8122bbba22aeb63a6b6e23e5f482783963d0004` |

For D=15, k=5 and max-prefix=12 are the patent example and the marker is 47 zeros followed by one. For exploratory D=12, the fixed marker is 39 zeros followed by one. After twelve zero prefix bits, a D-bit escape value whose upper D-5 bits are below 12 violates this particular encoder branch. No interior control marker, reset, adaptation or terminal-fill rule is modeled. A marker-preserving byte shuffle is a descriptive control, not a calibrated grammar null, and a planted-marker random synthetic stream can avoid invalid escapes. Survival to a ceiling is not positive evidence of correctness. The known prefixes, post-hoc D=12 choice and previously studied files are not blind validation; differing marker interpretation or other syntax may explain failure.

## Reproduce

At commit c60c7e598baa85e6fdf454e5d477df4c0360d6ca, obtain each public CC0 file, check its retained provenance and hash, and use its public ID, exact name, hash and local path. For example, for 7267:

```text
python -I -B tools/patent_capped_prefix_probe.py --width 15 --max-words 1000000 --sample 7267 "OM System - OM-1 Mark II - 16bit (4:3).orf" 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756 <local-path>
python -I -B tools/patent_capped_prefix_probe.py --width 15 --max-words 1000000 --tail-shuffle --seed 20261022 --sample 7267 "OM System - OM-1 Mark II - 16bit (4:3).orf" 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756 <local-path>
```

Repeat for all eight identities above, using width 15 for 7267/7269/7801/7803 and width 12 for 1993/1995/1997/1998, and both 1,000,000- and 2,000,000-word ceilings. `stop_at_bits` is the start of the unconsumed word and `invalid_escape_value` is its D-bit branch value. The tool does not infer terminal fill, seek interior markers or adapt parameters.
