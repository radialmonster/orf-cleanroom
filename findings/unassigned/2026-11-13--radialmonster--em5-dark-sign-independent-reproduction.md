# E-M5 Mark II dark-offset signs independently reproduce through 12M tokens

Author: @radialmonster
Verified by: @mszyndel
Lead: #561
Variant: unassigned
Builds on: #338, #558
Reproduces: 2026-10-27--radialmonster--em5-dark-sign-reproduction

## Claim

The four declared real-versus-shuffled suffix-match directions on six public
E-M5 Mark II dark captures reproduce in fresh 4M and 8M candidate-token runs by
a different person. All four directions also hold in the predeclared 12M
extension on every file. This is shared unassigned token-index evidence; it
does not establish physical rows, CFA phase, a predictor or a codec.

## Original evidence

Lead #561 and the reproduced finding used `tools/bayer_grid_probe.py` at
`5086fa574155ea7eb392ea01f4d858a722345138`, candidate k=5/stop=1 parsing from
payload bit zero, payload-width stride, and one within-width ordinary-suffix
shuffle with seed 20261023. The six payloads are 4640 by 3472. Real minus
shuffled match rate is negative at (dy,dx)=(0,2) and (2,0), positive at
(2,-2) and (2,+2). The original finding extends the lead's 4M prefixes to 8M.

The public CC0 inputs were supplied by @mszyndel in #558. Owner declarations
and individual public source links are retained in
`samples/e-m5-mk-ii-dark-338-provenance.json`:

| File | SHA-256 | Declared ISO |
| --- | --- | ---: |
| P1010009.ORF | ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c | 200 |
| P1010011.ORF | d34532152c79ef24b22c60c6cf743cef41fe28196b40fe16b557c16b7a7ea03d | 200 |
| P1010013.ORF | 81acdd3675c329b351a634cfb4e22228f2db8df94f36480690e04416ded0817d | 200 |
| P1010017.ORF | 431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5 | 800 |
| P1010018.ORF | e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f | 800 |
| P1010019.ORF | 5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75 | 800 |

## Verification

On 2026-11-13 UTC, after posting the frozen plan on #561, @mszyndel ran all
six inputs at each of 4M, 8M and 12M tokens using Python 3.10.17 at repository
commit `7a4b1490f720a374298170d627bf092a5bf7a68b`. The measuring tool's last
change is `40d166017c0ffd07e140ab7b753092ddc337ed50`; the tool and its two
repository dependencies are byte-identical to the original pinned commit.
Tool SHA-256: dfb5c15aae8581d42f8d726ca1fb657ee71b9c902f61775f1a6b80ab19ac956e.
Every input hash matched the retained public CC0 provenance before measurement.

All 48 published 4M real/shuffled rates match at the displayed six decimals.
All 24 published 8M contrasts match exactly when subtracting the tool's rounded
six-decimal rates, as in the original finding. All 72 declared signs hold over
the three extents, with no failed reports. Whole-payload endpoint/escape
aggregates, large-q reports and default site tables are identical across the
three extents for each input.

The 12M extension was fixed before inspecting its results. It widens the
original 8M scope on the same captures, rather than adding a body or assuming
capture independence. Its contrasts (rounded real rate minus rounded shuffled
rate) are:

| File | (0,2) | (2,0) | (2,-2) | (2,+2) |
| --- | ---: | ---: | ---: | ---: |
| P1010009.ORF | -0.031880 | -0.032906 | +0.022909 | +0.014525 |
| P1010011.ORF | -0.032234 | -0.032790 | +0.022929 | +0.015190 |
| P1010013.ORF | -0.032264 | -0.032591 | +0.022590 | +0.015030 |
| P1010017.ORF | -0.014576 | -0.017644 | +0.013177 | +0.009393 |
| P1010018.ORF | -0.014863 | -0.017601 | +0.013127 | +0.009485 |
| P1010019.ORF | -0.014586 | -0.017611 | +0.013318 | +0.009462 |

Exact 12M match counts below use offset order (0,2), (2,0), (2,-2), (2,+2).
Each cell is real matches / shuffled matches; pairs are equal for real and
shuffled on these four offsets.

| File | Pairs in offset order | (0,2) matches | (2,0) matches | (2,-2) matches | (2,+2) matches |
| --- | --- | --- | --- | --- | --- |
| P1010009.ORF | 11981440, 11981440, 11981440, 11981440 | 1237149 / 1619114 | 1228306 / 1622567 | 1894401 / 1619917 | 1796732 / 1622707 |
| P1010011.ORF | 11981440, 11981440, 11981440, 11981440 | 1236159 / 1622367 | 1228020 / 1620903 | 1894655 / 1619921 | 1798527 / 1616528 |
| P1010013.ORF | 11981440, 11981440, 11981440, 11981440 | 1231227 / 1617793 | 1227611 / 1618096 | 1889431 / 1618761 | 1797339 / 1617257 |
| P1010017.ORF | 11981432, 11981433, 11981432, 11981432 | 871796 / 1046434 | 835505 / 1046906 | 1206265 / 1048384 | 1161145 / 1048602 |
| P1010018.ORF | 11981432, 11981432, 11981432, 11981432 | 870929 / 1049010 | 835896 / 1046777 | 1203520 / 1046238 | 1160617 / 1046974 |
| P1010019.ORF | 11981428, 11981428, 11981428, 11981428 | 873181 / 1047947 | 836665 / 1047668 | 1206545 / 1046976 | 1161526 / 1048155 |

This upgrades the human verifier, not the independence of inputs or methods:
the same candidate parser, locator and shuffle implementation are reused.
Same-session files may be dependent. One fixed shuffle is descriptive, not
calibrated significance. Physical framing, value recovery, CFA and predictor
alternatives remain open. No private inputs were used.

## Reproduce

At the repository commit above, supply the six hash-matched public file paths
in the table's order. Each command only reads inputs and prints aggregates:

```sh
python -I -B tools/bayer_grid_probe.py --tokens 4000000 FILE1 FILE2 FILE3 FILE4 FILE5 FILE6
python -I -B tools/bayer_grid_probe.py --tokens 8000000 FILE1 FILE2 FILE3 FILE4 FILE5 FILE6
python -I -B tools/bayer_grid_probe.py --tokens 12000000 FILE1 FILE2 FILE3 FILE4 FILE5 FILE6
```

Defaults: seed 20261023, windows 2:202 and 565:765, offset 0 and large-q
threshold 6. Grid pairs start at token 4W and require both tokens to have q<17;
ordinary suffixes are shuffled within W-token blocks and escape positions stay
fixed. Subtract `grid_shuffled.rate` from `grid_real.rate` at the four offsets.
Exact counts are the corresponding `P` and `M` fields.
