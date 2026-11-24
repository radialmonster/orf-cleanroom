# Flat-payload selected-boundary counts reproduce and extend to E-M5 II

Author: @Hrt-Htk
Verified by: @mszyndel
Lead: #951
Variant: unassigned
Builds on: #339, #603, #197, #949
Partial: six-file flat measurements and fixed wider/cross-body extensions; busy-content adaptation and group/active-area interpretation are not verified

## Claim

The six published OM-3 prefix measurements reproduce exactly, including
the two failures on PA200012, equal ends under both readings, white-group
repeat count 386/397 and the reported candidate-word totals. The finder's
later non-six-bit/escape counts also reproduce exactly.
The unchanged 400-row search extends to six public E-M5 II dark inputs:
397/397 selected intervals end exactly on each, with both readings equal.
This is a finite candidate-boundary observation, not physical row framing
or token-to-pixel correspondence. These inputs remain unassigned.

## Original evidence

Lead #951 by @Hrt-Htk, posted 2026-11-24, publishes six public CC0 OM-3
inputs and the first-400 table. Its source is `tools/row_frame_probe.py`
at #950 commit `e962724a368b2352a316d590504f0ce6726dac7a`.
The same-day scope comment reports whole-payload non-six-bit words and
explains why predominantly six-bit data make the endpoint test weak.
Public identities and SHA-256 values are listed below.

## Verification

Fresh 2026-11-24 run by @mszyndel after publication and a clean current
issue scan, with original source/imports reviewed. Before camera testing,
six generated tests at `1a33c1a` covered ordinary prefix lengths 0..11,
every truncated word length, low/high escape values, explicit tail policy
and the length-equivalent group. A generated 40-word sequence with six
`10000000` fields and otherwise six-bit words makes both readings end at
bit 252=6*40+12, without any camera or physical rows. It demonstrates a
length ambiguity, not a null probability for the camera data.

Predeclared plan: repeat the six originals at --rows 400, then use
--rows 400 and --rows 4000 unchanged on those six and six additional
E-M5 II dark captures (three ISO 200, three ISO 800). No per-file retuning
or discarded failures. All 12 full hashes matched retained public CC0
provenance before/after. All have one declared strip, so the original
contiguous extraction agrees with the separate declared-strip reader.
No unavailable private inputs contribute to these results.

The 4000-row search limit reaches EOF on all 12 inputs, but the tool
retains only one longest chain of group matches at assumed pitch
6W+12 with tolerance max(64,pitch//100). It does not test all physical
rows or all matches; reported denominators are selected intervals.
Equal endpoints can coexist with misses and changing group columns.
The two readings have zero different endpoints in both runs on all 12.

| Input / declared condition | SHA-256 | W x H | 400: exact / selected | 4000: exact / selected | Group columns at 400 / 4000 |
|---|---|---|---|---|---|
| PA210010.ORF (saturated white ISO 200) | `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e` | 5220x3912 | 397/397 | 3909/3909 | 8 / 8 |
| PA200010.ORF (dark ISO 200) | `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4` | 5220x3912 | 397/397 | 3906/3909 | 2 / 2,3,4 |
| PA200011.ORF (dark ISO 200) | `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3` | 5220x3912 | 397/397 | 3905/3909 | 1 / 1,2,3 |
| PB040038.ORF (calm Zenodo scene) | `6f1c8b303ab79f451b77794680d06c3fcb3fde8c4e653152e1e9383259cfdbdb` | 5220x3912 | 397/397 | 3909/3909 | 2 / 2 |
| PA200012.ORF (dark ISO 800) | `c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7` | 5220x3912 | 306/308 | 750/754 | 2 / 2 |
| PA200015.ORF (dark ISO 800) | `84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278` | 5220x3912 | 248/248 | 660/663 | 2 / 10 |
| P1010009.ORF (dark ISO 200) | `ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c` | 4640x3472 | 397/397 | 3469/3469 | 3 / 3 |
| P1010011.ORF (dark ISO 200) | `d34532152c79ef24b22c60c6cf743cef41fe28196b40fe16b557c16b7a7ea03d` | 4640x3472 | 397/397 | 3469/3469 | 3 / 3 |
| P1010013.ORF (dark ISO 200) | `81acdd3675c329b351a634cfb4e22228f2db8df94f36480690e04416ded0817d` | 4640x3472 | 397/397 | 3469/3469 | 2 / 2 |
| P1010017.ORF (dark ISO 800) | `431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5` | 4640x3472 | 397/397 | 2426/2429 | 3 / 3,4,5 |
| P1010018.ORF (dark ISO 800) | `e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f` | 4640x3472 | 397/397 | 2916/2924 | 2 / 2,4,5,6,7,9,10 |
| P1010019.ORF (dark ISO 800) | `5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75` | 4640x3472 | 397/397 | 3458/3469 | 3 / 3,4,5,6,7,8,9,10,11 |

The wider search is an extension, not a reproduction of an asserted
whole-frame rule. In particular, the first-400 fixed-column wording must
not be extrapolated to all the wider-run candidates.

Independent candidate-word counter `tools/capped_prefix_counts.py` at
`1a33c1a` uses independently extracted declared strips. The fixed grammar
is q<12, a one and five suffix bits, or 12 zeros and any 12 raw bits.
All 12 begin with a literal 40-bit zero-run-plus-one prefix. The original
tool counts only while 24 bits remain. Counting every bounded complete
word adds exactly three words on each input, leaving the residual below;
this qualifies the published phrase "whole-payload token count". It is
not proof that these final candidate words are actual camera tokens.
Delta is guarded count minus W*H; complete delta is delta+3.

| Input | Guarded delta | Guarded non-six-bit words | Per nominal row | Guarded escapes | Complete low-raw escapes (<384) | Complete residual bits |
|---|---:|---:|---:|---:|---:|---:|
| PA210010.ORF | +4 | 23461 | 5.997 | 5 | 2 | 3 |
| PA200010.ORF | +1 | 21310 | 5.447 | 3 | 3 | 1 |
| PA200011.ORF | +0 | 21342 | 5.456 | 3 | 3 | 4 |
| PB040038.ORF | -2 | 21248 | 5.431 | 1 | 1 | 5 |
| PA200012.ORF | +7 | 88746 | 22.686 | 5 | 5 | 3 |
| PA200015.ORF | +13 | 89445 | 22.864 | 5 | 5 | 1 |
| P1010009.ORF | +0 | 19122 | 5.507 | 1 | 1 | 4 |
| P1010011.ORF | +0 | 18941 | 5.455 | 1 | 1 | 1 |
| P1010013.ORF | -1 | 18996 | 5.471 | 1 | 1 | 0 |
| P1010017.ORF | +6 | 20768 | 5.982 | 7 | 7 | 5 |
| P1010018.ORF | +7 | 20660 | 5.950 | 7 | 7 | 4 |
| P1010019.ORF | +8 | 20884 | 6.015 | 9 | 9 | 1 |

The E-M5 II ISO 800 captures still average only about six non-six-bit
words per nominal row, near the six-field group itself. They are not an
equally strong variable-length test as the two OM-3 ISO 800 captures
(about 22.7/22.9 per nominal row). Equal ISO settings do not imply equal
noise or equivalent evidence. A low-valued escape is observed under this
candidate parse; it does not establish an official escape syntax.

Open: group syntax versus border data, comparison to 0x2040/0x0612,
busy-content adaptation, independent row origins and value assembly.
The prefix table and these extensions establish none of them. The
busy-file over-count examples and the claim about changing code length
were not tested here. #951 remains open under this Partial finding.

## Reproduce

Use the reviewed #950 source at the exact original commit above:

```
python -I -B tools/row_frame_probe.py --rows 400 FILE [FILE ...]
python -I -B tools/row_frame_probe.py --rows 4000 FILE [FILE ...]
```

Supply all 12 files above, preserving their hash identities. Retained
CC0/source links are in `samples/om3-flat-338-provenance.json`,
`samples/om-system-pen-om-3-om-5-mark-ii-zenodo-provenance.json` and
`samples/e-m5-mk-ii-dark-338-provenance.json`. Existing personal manifest
rows cover these inputs (the PA200015 row is submitted in #954).
Use the separate counter source at `1a33c1a`:

```
python -I -B tools/test_capped_prefix_counts.py
python -I -B tools/capped_prefix_counts.py --controls
python -I -B tools/capped_prefix_counts.py --records samples/om3-flat-338-provenance.json --sample PA200012.ORF FILE
python -I -B tools/capped_prefix_counts.py --records samples/e-m5-mk-ii-dark-338-provenance.json --sample P1010017.ORF FILE
```

Repeat `--sample NAME FILE` for every input belonging to each retained
provenance file. Use the Zenodo OM-3 provenance file for PB040038.
The JSON contains guarded/complete counts and exact residual lengths;
compare with the tables. No image or preview rendering is used.

For the declared-strip cross-check, use the existing tool function on
each file/hash pair (no writes or network):

```
python -I -B -c "import sys,json; sys.path.insert(0,'tools'); from strip_start_audit import measure; print(json.dumps(measure(sys.argv[1],sys.argv[2])))" FILE SHA256
```

All 12 report strip_count=1 and status=agree, including complete payload
byte equality between the independent reader and existing locator.
