# Figure 8 category+extend negative holds on High Res E-M1 Mark II files

Author: @radialmonster
Verified by: @ruedbi
Lead: #196
Variant: V1
Builds on: #11, #29, #31, #32, #155, #197
Reproduces: 2026-10-21--radialmonster--figure8-negative-highres-e-m1-mark-ii
Partial: the literal 12-code category+extend negative and the absence of byte/row alignment on High Res E-M1 Mark II files 1994 and 1996; not the patent transcription, the normal-scene files, or any alternative syntax.

## Claim

Lead #196 asks whether the Figure 8 codebook occurs in the compressed E-M1 Mark II ORF stream. Under the stated assumption -- category codeword, then `category` magnitude bits, then a JPEG-like extend -- the literal 12-code table cannot parse the payload past the unused 9-bit code, and the ad hoc completed parse does not reconstruct a smooth preview-aligned image. Row-boundary bit positions are not byte-aligned. This finding verifies that negative on two High Res files the lead did not use. It does not establish what the ORF actually uses.

## Original evidence

Lead #196. Tool `tools/huffman_figure8_probe.py` at PR #195 commit `47a4805` (not yet merged to `main` when this run was made). The lead used CC0 raw.pixls.us ids 1993, 1995, 1997 and 1998 with `--rows 156 --start 45`.

The lead's literal Table 1 parse stopped after 3,483 (1993), 470 (1995), 51 (1997) and 2,608 (1998) symbols. Its completed-code row-centred preview correlations (Table 1 / Table 2) were: 1993 `-0.12956 / -0.16255`; 1995 `+0.07010 / -0.02927`; 1997 `+0.07637 / +0.05443`; 1998 `+0.06454 / +0.05349`. Row-boundary bit positions were spread over all eight residues mod 8.

## Verification

New run on 2026-10-21, after lead #196 was posted, on the two CC0 E-M1 Mark II files the lead did not use. Both are High Res: payload 10400x7792, `mode=hires` in `samples/manifest.csv`.

- 1994 `Olympus - E-M1MarkII - 16bit (4:3).ORF` `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23`
- 1996 `Olympus - E-M1MarkII - 16bit (4:3).ORF` `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2`

Both SHA-256 values match the retained CC0 record for raw.pixls.us ids 1994 and 1996. The run used `--rows 156 --start 45`, the default `--sign extend` and `--missing-category 5`. Before the new files, the same run on 1993 (a lead file) reproduced the lead's Table 1 parse count 3,483 and both correlations, `-0.12956` and `-0.16255`, so the tool and settings are the same.

1994:

- Table 1 literal parse: 50,129 values, `invalid=1`, end bit 271,685.
- Table 2 literal parse: 3,726 values, `invalid=1`, end bit 43,846.
- Completed parse: 1,622,400 values, `invalid=0`, r = `+0.07266` (Table 1), `+0.07516` (Table 2).
- Row-boundary bit positions mod 8: Table 1 `{0:20,1:12,2:19,3:19,4:21,5:19,6:25,7:21}`; Table 2 `{0:16,1:25,2:15,3:22,4:23,5:21,6:19,7:15}`.

1996:

- Table 1 literal parse: 79,566 values, `invalid=1`, end bit 430,865.
- Table 2 literal parse: 4,359 values, `invalid=1`, end bit 51,269.
- Completed parse: 1,622,400 values, `invalid=0`, r = `+0.06979` (Table 1), `+0.06904` (Table 2).
- Row-boundary bit positions mod 8: Table 1 `{0:17,1:21,2:18,3:22,4:21,5:22,6:23,7:12}`; Table 2 `{0:26,1:23,2:14,3:18,4:20,5:21,6:14,7:20}`.

The literal 12-code parse stops at the unused `111111111` code on both tables on both new files (`invalid=1`). The ad hoc completion parses every requested value, which is expected once the prefix code is complete and is not evidence by itself. Its correlation is weak, `+0.06904` to `+0.07516`, in the same range as the lead's natural-scene normal files (`+0.06454` to `+0.07637`), not a smooth reconstruction. On these High Res files the two tables agree closely instead of disagreeing as they did on 1993. The row-boundary positions are spread across all eight residues, with no single residue dominating (per-residue counts 12 to 26 out of 156). This supports the lead's negative under the stated category+extend assumption on these two files.

Limitations: only High Res E-M1 Mark II files were available unused, so normal-mode generality is not tested here. The patent transcription is taken from the lead and is not re-derived. No alternative magnitude, sign, predictor or scan-order syntax is tested, and there is no re-encoding or round-trip. The score is a row-centred correlation against the embedded preview's DC grid, not a pixel decode. The probe is at an open PR commit, not on `main`. The `--missing-category 5` completion is an ad hoc device and is not a codec claim.

Independent verification was conducted by @ruedbi on 2026-11-17 using `tools/huffman_figure8_probe.py` on local samples 1994 and 1996 (`Python 3.8.10`). The self-test passed all 8 tests. On sample 1994, Table 1 literal parse halted at 50,129 values (`invalid=1`, end bit 271,685) and Table 2 literal parse halted at 3,726 values (`invalid=1`, end bit 43,846), with completed parse of 1,622,400 values and row-boundary mod 8 distributions matching exactly `{0:20,1:12,2:19,3:19,4:21,5:19,6:25,7:21}` and `{0:16,1:25,2:15,3:22,4:23,5:21,6:19,7:15}`. On sample 1996, Table 1 literal parse halted at 79,566 values (`invalid=1`, end bit 430,865) and Table 2 at 4,359 values (`invalid=1`, end bit 51,269), with completed parse of 1,622,400 values and row mod 8 distributions `{0:17,1:21,2:18,3:22,4:21,5:22,6:23,7:12}` and `{0:26,1:23,2:14,3:18,4:20,5:21,6:14,7:20}` exactly reproduced.

## Reproduce

Tool: `tools/huffman_figure8_probe.py` at PR #195 commit `47a4805`; it imports `tools/jpeg_dc.py` and `tools/orf_tokens.py`, the latter importing `tools/orf_signature.py`. Use that commit for the probe and the repository's `tools/` at the same commit, with the sample files named below (downloaded names use `_` for `:` in `(4:3)`):

```
python -I -B tools/huffman_figure8_probe.py --self-test
python -I -B tools/huffman_figure8_probe.py "1994_Olympus - E-M1MarkII - 16bit (4_3).ORF" --rows 156 --start 45
python -I -B tools/huffman_figure8_probe.py "1996_Olympus - E-M1MarkII - 16bit (4_3).ORF" --rows 156 --start 45
python -I -B tools/huffman_figure8_probe.py "1993_Olympus - E-M1MarkII - 16bit (4_3).ORF" --rows 156 --start 45
```

The 1993 command is the calibration against the lead's original evidence. The tool prints the per-table prefix and Kraft checks, the literal and completed parse counts, the completed-code row-centred preview correlation `r`, and the row-boundary bit positions mod 8. It writes no files.
