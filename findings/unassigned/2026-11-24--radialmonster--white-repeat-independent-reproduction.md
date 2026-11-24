# Independent reproduction of the charged white literal-repeat description

Author: @radialmonster
Verified by: @mszyndel
Lead: #864
Variant: unassigned
Reproduces: 2026-11-20--radialmonster--white-payload-literal-repeat-description
Builds on: #338, #339

## Claim

All 14 published verification records reproduce exactly under the fixed
literal-repeat description, including exceptions, gamma-gap costs, starts
and padded charges. The six-bit template selected on the original white
window costs 272592 training bits. Whole-white charge is 63273928 for
122570968 input bits; the original whole-dark comparator costs 135629920
for the same input length. All four original white windows save bits and
one of the original four dark windows does.

Two predeclared larger white windows also save bits without refitting.
An additional public dark capture costs 135343056 bits for 122570960
input bits overall, with one of four windows saving bits. These are
finite literal-description costs, not the camera's syntax, physical
framing, values or a decoder.

## Original evidence

Lead #864 and the reproduced finding by @radialmonster specify a fit
only on 65536 white bytes starting at byte 65536. Try periods 1..256,
majority at absolute residue with ties zero, minimum padded charged
size with smaller-period tie break. Each description charges 136 fixed
header bits, its template, positive Elias-gamma exception gaps from
index minus one, and byte padding. The tool computes costs and does
not emit encoded camera data.

Source `tools/literal_repeat_probe.py` and its complete repository import
chain are byte-identical to 39c04060234bb1510cd2355881bd04f8672e6899.
The original two public CC0 OM-3 files have retained provenance in
`samples/om3-flat-338-provenance.json`:

- PA210010.ORF (saturated white), SHA-256 `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`.
- PA200010.ORF (capped dark), SHA-256 `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4`.

Both are 5220x3912, with 15321371 selected payload bytes.

## Verification

New run by @mszyndel on 2026-11-24, after publication and the current
clean issue scan. Original source/imports and three generated tests
were read first. Tests exercise all periods/phases against a literal
synthetic oracle, ties/bounds and the full CLI; all pass. Both original
CLI phases run freshly. All 256 fit costs and template identity match
between phases and the extension; all five discovery white records
match their verification counterparts. Every integer in the reproduced
finding's 14-row table matches, including whole-stream coverage.

This is a different-human reproduction of the original code; the camera
cost algorithm is shared, not a second independent implementation.
The selected template's ASCII-bit SHA-256 is
`740b504574f2bc5d27b06c79a4477194c40990c8f066d5df34faa285c30c23ba`.
No template bits or encoded camera streams are published.

Before new outcomes, freeze two 131072-byte white windows at 1/2 MiB
and one new-to-finding public dark input PA200011.ORF, SHA-256
`a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3`.
Its geometry is 5220x3912 with 15321370 payload bytes, and its CC0
provenance is in the same JSON. `tools/literal_repeat_heldout.py` at
16e9909 (#966) reuses the frozen white template and original description
functions. The new dark is extracted with the independent declared-strip
reader, never fitted. All three full input hashes match retained verified
records before/after; existing personal manifest rows are reused.
These previously studied captures are not blind or independent scenes;
larger windows overlap the previously measured whole stream. No result
uses unavailable private files.

Original records (all non-whole intervals contain 524288 input bits):

| File | Interval | Start bit | Exceptions | Gamma gap bits | Charged bits |
|---|---|---:|---:|---:|---:|
| PA210010.ORF | 1 MiB | 8388608 | 39375 | 273763 | 273912 |
| PA210010.ORF | 2 MiB | 16777216 | 38607 | 268547 | 268696 |
| PA210010.ORF | 3 MiB | 25165824 | 40854 | 283802 | 283944 |
| PA210010.ORF | 4 MiB | 33554432 | 40408 | 280888 | 281032 |
| PA210010.ORF | Whole | 0 | 9108946 | 63273786 | 63273928 |
| PA210010.ORF | Startup | 0 | 50096 | 301226 | 301368 |
| PA210010.ORF | Tail | 122046680 | 39225 | 272781 | 272928 |
| PA200010.ORF | 1 MiB | 8388608 | 245417 | 674907 | 675056 |
| PA200010.ORF | 2 MiB | 16777216 | 245851 | 675429 | 675576 |
| PA200010.ORF | 3 MiB | 25165824 | 190786 | 583230 | 583376 |
| PA200010.ORF | 4 MiB | 33554432 | 136955 | 497757 | 497904 |
| PA200010.ORF | Whole | 0 | 45713227 | 135629773 | 135629920 |
| PA200010.ORF | Startup | 0 | 241858 | 668940 | 669088 |
| PA200010.ORF | Tail | 122046680 | 245849 | 675013 | 675160 |

Predeclared extension (larger white intervals contain 1048576 input
bits; new dark windows/startup/tail contain 524288):

| File | Interval | Start bit | Exceptions | Gamma gap bits | Charged bits |
|---|---|---:|---:|---:|---:|
| PA210010.ORF | 128 KiB | 8388608 | 77200 | 536614 | 536760 |
| PA210010.ORF | 128 KiB | 16777216 | 78730 | 547740 | 547888 |
| PA200011.ORF | 1 MiB | 8388608 | 191850 | 584086 | 584232 |
| PA200011.ORF | 2 MiB | 16777216 | 155656 | 527106 | 527248 |
| PA200011.ORF | 3 MiB | 25165824 | 137009 | 497969 | 498112 |
| PA200011.ORF | 4 MiB | 33554432 | 245380 | 674660 | 674808 |
| PA200011.ORF | Whole | 0 | 45603957 | 135342907 | 135343056 |
| PA200011.ORF | Startup | 0 | 245763 | 675305 | 675448 |
| PA200011.ORF | Tail | 122046672 | 311104 | 618626 | 618768 |

Whole records include every payload bit. Startup/tail are overlapping
diagnostics with separately charged headers; the rows must not be added
as independent compression savings or independent camera captures.

## Reproduce

Original source and imports at 39c04060234bb1510cd2355881bd04f8672e6899:

```
python -I -B tools/test_literal_repeat_probe.py
python -I -B tools/literal_repeat_probe.py --phase discovery --sample PA210010.ORF PATH_WHITE
python -I -B tools/literal_repeat_probe.py --phase verification --sample PA210010.ORF PATH_WHITE --sample PA200010.ORF PATH_DARK
```

Additional-input wrapper at 16e9909:

```
python -I -B tools/literal_repeat_heldout.py --white PATH_WHITE --dark PATH_PA200011
```

Use only exact public hashes above, with retained CC0 verification. Compare
the 256 training costs, selected period/template hash and every integer in
the tables. The extension uses the same white fit and absolute phase on
all records. Independently justified camera syntax explaining repetition,
startup, exceptions and tail remains open on #339; no compressed decode
step follows from this independent reproduction.
