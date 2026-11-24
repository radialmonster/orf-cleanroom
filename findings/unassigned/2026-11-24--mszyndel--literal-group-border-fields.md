# Literal two-value IP fields do not directly specify candidate group columns

Author: @mszyndel
Verified by: @mszyndel
Lead: #958
Variant: unassigned
Builds on: #951, #949

## Claim

On the six discovery and six predeclared additional public OM-3/E-M5 II
files, literal ImageProcessing 0x0612 and 0x0613 are SHORT/count 2.
Both are [12,0] on all six OM-3 files and [8,0] on all six E-M5 II files.
Candidate six-field group columns vary within each group of identical
vectors. The declared direct scalar comparison is therefore undefined;
no component, offset, scale or coordinate convention is silently selected.
This neither identifies these tags nor decides syntax versus border data,
physical rows or value assembly. Inputs remain unassigned.

## Original evidence

Lead #958 reports six discovery rows after the frozen protocol on #951.
Tool `tools/row_group_border_inventory.py` and the optional requested-path
extension to `tools/makernote_prefix_audit.py` are at 7163279 (#957).
The #950 first-400-row pattern/longest-chain rule and fixed candidate
parse are shared, not independent physical framing. The tool counts all
selected heads that are reached at a candidate boundary, including the
last selected head; #951 counts adjacent intervals instead.

## Verification

Fresh post-publication run on 2026-11-24 after the lead's current clean
scan. The six discovery records repeat exactly and six reserved records
were added: PA200011, PB040038, PA200015, P1010011, P1010018, P1010019.
All 12 full hashes match retained public CC0 records. These files had
previous research exposure; this split is procedural, not blind or
independent-capture validation. Four generated controls and seven reader
tests pass. Source code and imports were reviewed before use.
The metadata reader copies the declared MakerNote envelope before
excluding its identified scalar preview interval from subsequent scoped
field parsing. It does not decode preview pixels. Unsupported shapes
and unaligned heads are retained. No private inputs contribute.

| Public file | SHA-256 | 0612=0613 | Candidate columns: parsed heads | Selected / unaligned |
|---|---|---|---|---|
| PA210010.ORF | `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e` | [12, 0] | 8:398 | 398 / 0 |
| PA200010.ORF | `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4` | [12, 0] | 2:398 | 398 / 0 |
| PA200011.ORF | `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3` | [12, 0] | 1:398 | 398 / 0 |
| PB040038.ORF | `6f1c8b303ab79f451b77794680d06c3fcb3fde8c4e653152e1e9383259cfdbdb` | [12, 0] | 2:398 | 398 / 0 |
| PA200012.ORF | `c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7` | [12, 0] | 2:307 | 309 / 2 |
| PA200015.ORF | `84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278` | [12, 0] | 2:249 | 249 / 0 |
| P1010009.ORF | `ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c` | [8, 0] | 3:398 | 398 / 0 |
| P1010011.ORF | `d34532152c79ef24b22c60c6cf743cef41fe28196b40fe16b557c16b7a7ea03d` | [8, 0] | 3:398 | 398 / 0 |
| P1010013.ORF | `81acdd3675c329b351a634cfb4e22228f2db8df94f36480690e04416ded0817d` | [8, 0] | 2:398 | 398 / 0 |
| P1010017.ORF | `431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5` | [8, 0] | 3:398 | 398 / 0 |
| P1010018.ORF | `e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f` | [8, 0] | 2:398 | 398 / 0 |
| P1010019.ORF | `5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75` | [8, 0] | 3:398 | 398 / 0 |

Only PA200012 has unaligned selected heads (two); they are not assigned
a column. Literal IP 0x0611 is [12,0] on all 12. 0x0614/0x0615 are
LONG/count 1 with values 5184/3888 on OM-3 and 4608/3456 on E-M5 II;
these are literal declarations, not an established physical crop model.

## Reproduce

At 7163279, use the public identities/hashes above and their retained
provenance in `samples/om3-flat-338-provenance.json`,
`samples/e-m5-mk-ii-dark-338-provenance.json`, and the Zenodo OM-3
record in `samples/om-system-pen-om-3-om-5-mark-ii-zenodo-provenance.json`
for PB040038. Personal manifest rows for all 12 already exist.

```
python -I -B tools/test_row_group_border_inventory.py
python -I -B tools/test_makernote_prefix_audit.py
python -I -B tools/row_group_border_inventory.py --records PROVENANCE_JSON --sample NAME FILE
```

Repeat the last command per file or repeat `--sample NAME FILE` for
files sharing a provenance JSON. The full JSON retains type/count/value,
every selected/parsed/unaligned denominator and not_scalar comparison.
Independent coordinate evidence, the group's origin and busy-content
adaptation remain open on #951 and in V1 G3; they do not follow from
the differing literal vectors and candidate columns.
