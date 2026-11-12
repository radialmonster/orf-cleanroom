# 4 of 4 OM-5 High Res ORF/ORI companion pairs pass the preview-DC 0.98 screen

Author: @G6bill
Verified by: @Hrt-Htk
Lead: #347
Variant: unassigned
Builds on: #313
Partial: the companion-separation claim at the fixed r >= 0.98 cut, on 4 new own OM-5 High Res ORF/ORI pairs; not the lead's 23-pair count, not its AUC, not the held-out threshold, not the same-session rate, and not the different-day claim, which this run contradicts

## Claim

Lead #347 reported that on 23 companion pairs of one OM-5 body, every pair of a
High Res ORF and its same-name, same-second ORI scores at or above the frozen
r >= 0.98 preview-DC cutoff. This verification covers that companion-separation
claim only, at the unchanged cutoff, on a disjoint cohort of another owner's
OM-5 files.

All 4 companion pairs in the new cohort score r >= 0.98, with minimum
0.999360, median 0.999998 and maximum 0.999999. All 4 sit above every
different-day pair in the cohort, whose maximum is 0.983887. They do not sit
above every same-day pair: the maximum same-day score is 0.999951 and 51
of 1722 same-day pairs reach 0.98, so the cutoff separates companion pairs from
different recorded days here, not from every frame of the same session.

Not verified here: the 23-pair count, the AUC figures, the held-out threshold
and its rates, and the same-session rate. The lead's different-day claim (0 of
132709) is contradicted by this cohort, 2 of 112388 pairs reaching 0.98, so it
is outside this finding; those numbers are on the lead's issue.

## Original evidence

Lead #347, found by @G6bill. Tools: `tools/preview_pair_screen.py` at commit
`a1ee5d9` with `tools/jpeg_dc.py` at `5a0c2bf`, run at repo commit `787bd65`;
labels from `tools/capture_pair_calibration.py` at `285b797` (#346 branch);
DateTimeOriginal read through `tools/orf_signature.py` at `fe85f79`.

The finder screened 593 of 596 distinct ORF/ORI from one OM-5 body over 15
shooting days: 549 normal ORF, 24 High Res ORF, 23 ORI, all previews
3200x2400. 23 companion pairs, all at r >= 0.98 (min 0.997589). Same-session
pairs (|dt| <= 600 s, not companions) 65 of 7494 at 0.98. Different recorded
days 0 of 132709, maximum 0.949723. Three files were removed because the screen
version then in use aborted on them. The files are the finder's own and are not
shared, so the lead is `not yet reproducible`.

## Verification

New run on 2026-11-12 UTC, after the lead was posted, by a different person
(@Hrt-Htk), on a disjoint cohort of own OM-5 files: 528 ORF/ORI listed, 507
distinct by SHA-256 (21 duplicate paths across folders), 42 recorded days, all
previews 3200x2400. No file lacks DateTimeOriginal, no pair is excluded for
missing metadata, all 507 previews decode (`status ok`), none is
low-information, and 128271 pairs were scored. Tools at current `main`:
`tools/preview_pair_screen.py` `cde85b7`, `tools/jpeg_dc.py` `3d70fa8`,
`tools/capture_pair_calibration.py` `bf18366`, `tools/orf_signature.py`
`9f748fd`. The screen version used here records an undecodable preview as
`unsupported` and continues (#348), so no file had to be removed. Fixed
settings unchanged: 12x12 identity-aligned grid of quantized DC means, unit
norm, r >= 0.98, grid SD >= 1, `--threshold 0.98 --hard-seconds 600`. The
protocol was written and hashed before any score existed (local sha256
`5da56bd8fa774a9a153e18b35ecb347a62e3c5cd21252dfdba1c1790d60cad9b`), including
the file set, the block order and the pass criteria. All files went to the
screen in one call; the run took 974 s in a single CPU process.

Class census, as `capture_pair_calibration.py` printed it (n, count >= 0.98,
min / median / max):

| class | n | >= 0.98 | min | median | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| P companion | 4 | 4 | 0.999360 | 0.999998 | 0.999999 |
| B same second, not companion | 1 | 1 | 0.998984 | 0.998984 | 0.998984 |
| H same day, <= 600 s | 1722 | 51 | -0.890945 | 0.173660 | 0.999951 |
| S same day, > 600 s | 14156 | 0 | -0.899650 | 0.068780 | 0.964333 |
| E different days | 112388 | 2 | -0.955446 | 0.035918 | 0.983887 |

AUC from the same output: P (n=4) vs H (n=1722) 0.9991; P (n=4) vs E (n=112388)
1.0000. `calibration: unsupported (P=0 H=178)` and `validation: unsupported
(P=4 H=1544)`: the tool's own descriptive minimum is 10 P and 10 H pairs per
split and this cohort has 4 P pairs in total, so no threshold is calibrated or
applied here and the split numbers carry no weight.

The companion claim holds in this cohort: 4 of 4 pairs reach 0.98, minimum
0.999360.

The different-day claim does not hold in this cohort: 2 of 112388 pairs reach
0.98, at 0.982892 and 0.983887, one file pairing with two files from two other
recorded days (45 and 55 days later). The rest of the upper tail is 60 pairs at
r >= 0.95, 33 at >= 0.96 and 10 at >= 0.97. The three files involved are not
low-information: their grid SD is 274.892, 208.938 and 383.056, ranks 9, 28 and
3 of the 507 samples. Their 12x12 grids are dominated by one direction: row
means explain 0.9768 to 0.9967 of the grid variance and a least-squares plane
0.8106 to 0.8618, against a 39-file subsample median of 0.5276 (row means) and
0.5048 (plane) and a companion-pair median of 0.0769 and 0.3104. They correlate
with 20 to 26 of the other 506 files at r >= 0.90 and 7 to 12 at r >= 0.95, and
the two later files score 0.975869 against each other. These are broad-gradient
frames, not flat or dark ones, which is the structure two different captures
can share closely; that is a property of the frames, not evidence of one scene,
and it does not rescue the lead's 0.98 cutoff as a different-day negative.

The 4 companion pairs, `own`, SHA-256 from `samples/manifest.csv` (High Res ORF
/ its ORI):

- `5ac7fcceb96af9d85b42fde1784bb4ebfb743f4c0b651469ec3c5ae10450d6cb` /
  `b8333393e3ecb9676922a821f4ce409b507c1045e7b9dca4b7d9c66e202bc223`
- `3d29fb93fafdde858c5ef696ca832c027ef702ba6086677fb9efc59da12dcbbd` /
  `7fd9f52539300775b93bd9efb8933b466d3a32bcf5cba8f5932c394933b95662`
- `deb13b819636aa39758c08ac736d6d92b5a55ae990607ea4f82e46979aa4b70f` /
  `ab377a0c76d8a22b8c1132aa6dbd90acd1ee01846601d3822d4b8c95905cda2f`
- `68cc5234b19886d11262d381e5d3705a97bc7120a816016ff4e1c7f25395859e` /
  `3474921a0a269e2a91e6a5b3b78a60273f917fe4c6d9e1e6fa92dbb3976dedba`

The rest of the cohort is described by counts only. All files are the
verifier's own and are not shared, so this result is `not yet reproducible`.

## Reproduce

On any set of ORF/ORI files you may use, with High Res ORF + ORI companions
among them, count the pairs as follows (one screen call, because pairs are
formed within a run; ORF/ORI only, never `.xmp` sidecars):

    python -I -B tools/preview_pair_screen.py HIGH_RES_1.ORF HIGH_RES_1.ORI HIGH_RES_2.ORF HIGH_RES_2.ORI HIGH_RES_3.ORF HIGH_RES_3.ORI HIGH_RES_4.ORF HIGH_RES_4.ORI > screen.jsonl
    python -I -B tools/capture_pair_calibration.py --screen screen.jsonl --threshold 0.98 --hard-seconds 600 HIGH_RES_1.ORF HIGH_RES_1.ORI HIGH_RES_2.ORF HIGH_RES_2.ORI HIGH_RES_3.ORF HIGH_RES_3.ORI HIGH_RES_4.ORF HIGH_RES_4.ORI

On the 8 companion files of this cohort that run prints 8 samples, 28 pairs,
4 positives, and `P n=4 >=0.98: 4 (1.0000) min 0.999360 median 0.999998
max 0.999999`. A companion pair is labelled P only when both files carry the
same base name, the same DateTimeOriginal second, and one member has payload
width > 6000; a renamed copy of the same content is not a companion. Read-only,
standard library only, no image or preview is rendered.
