# Wide token row stride on 50 own OM-5 normal-mode files is file-specific and does not hold across payload bands

Author: @radialmonster
Verified by: @Hrt-Htk
Lead: #144
Variant: V1
Builds on: 2026-10-21--radialmonster--wide-row-stride-new-bodies, 2026-10-22--radialmonster--later-band-row-stride-drift, #11, #30
Partial: the prefix row-stride measurement (a stride S is measurable, S is never below the payload width W, the best stride is wider than the image on the denser files, and S is file-specific inside one body, mode and width) and the same measure re-run on later row bands, where the prefix stride does not hold; not the lead's "one sharp peak per file" wording, not the E-M1 Mark II S = W claim, not physical row boundaries, the extra S-W tokens, whole-frame constancy or any value mapping

## Claim

The lead's declared row-start q profile was run unchanged on 50 own OM-5 normal-mode
captures (5240x3912, variable-size payload) that the lead did not use. The measure is
the mean q of the first 32 tokens of a candidate row minus the mean of the rest of that
row, as a one-sample z over 300 folded rows, scanning candidate strides W..W+1200.

- A candidate stride S is measurable on every file and is never below the payload width:
  40 files have S > W, 10 have S = W exactly, none has S < W. S-W has median 28 tokens,
  upper quartile 305.8 and maximum 1048.
- S is file-specific, not fixed by body, mode or width. All 50 files share one body, one
  mode and one payload width, yet S takes 34 distinct values from 5240 to 6288
  (standard deviation 244).
- On the denser files the stride is far above the image width: 19 files exceed W+100 and
  13 exceed W+300, up to W+1048. The 10 files with S = W all have bpp at or below 6.519;
  the S > W files span bpp 6.097 to 8.013.
- The prefix stride is not a whole-payload stride. Re-running the same profile at later
  300-row bands, of the 38 files whose prefix z was at least 5.0, 34 fall below that level
  at candidate row 1000, 36 at row 2000 and 35 at row 3000. Across all files the score at
  the fixed prefix S is below 5.0 on 46, 48 and 46 of them, with medians of 0.58, -0.36
  and -0.20 and 17, 30 and 28 negative values. The best candidate in those bands is a
  different stride on 48 of 50, 50 of 50 and 49 of 49 files with a full band. A moving
  peak can be a stride change, an
  accumulated phase shift or a failure of the candidate unary-plus-five token grammar;
  this run does not separate them.

Not claimed here: that each file has one sharp peak, that S equals W on calm E-M1 Mark II
files, physical row boundaries, whole-frame constancy, what the extra S-W tokens are, or
any value mapping or decode.

## Original evidence

Lead #144 (2026-10-21), found by @radialmonster. Tool `tools/token_row_stride.py` at
commit 2972c34 (PR #143), standard library only, checked with
`python -I tools/token_row_stride.py --self-test`. The measure is fixed at 300 rows, head
32 tokens and a W..W+1200 stride scan; the lead names no peak threshold. Its nine public
CC0 inputs and published best strides:

| id | body | W x H | best S | S-W | z |
| ---: | --- | --- | ---: | ---: | ---: |
| 1993 | E-M1 Mark II | 5240x3912 | 5240 | 0 | 10.00 |
| 1995 | E-M1 Mark II | 5240x3912 | 5240 | 0 | 39.77 |
| 1997 | E-M1 Mark II | 5240x3912 | 5240 | 0 | 43.33 |
| 1998 | E-M1 Mark II | 5240x3912 | 5240 | 0 | 47.68 |
| 6343 | OM-5 | 5240x3912 | 5472 | +232 | 10.59 |
| 6344 | OM-5 High Res | 8200x6132 | 8365 | +165 | 11.30 |
| 6345 | OM-5 ORI | 5240x3912 | 5533 | +293 | 14.30 |
| 8549 | OM-5 Mark II | 5240x3912 | 5327 | +87 | 6.21 |
| 5283 | OM-1 | 5220x3912 | 6010 | +790 | 6.85 |

The lead also states that S is file-specific rather than body-specific (OM-5 6343 and
6345 differ by 61 tokens), that S = W on the calm E-M1 Mark II files, and that the prefix
stride may change later in the payload (untested in the lead).

## Verification

New run on 2026-11-12 UTC, after the lead was posted, by @Hrt-Htk: `tools/` scripts only,
`python -I -B`, standard library only. No file the lead used is in this cohort; the lead's
OM-5 files (6343, 6345) are different captures from a different source.

Inputs: 50 `own` captures, all OM Digital Solutions OM-5 in normal mode, payload
5240x3912, size_class variable, compression tag 1, bpp 6.027 to 8.013 (median 6.519).
They are the 50 rows appended to `samples/manifest.csv` in #721; identities by SHA-256
below, index 1..50 in that append order. The files are not shared, so **this result is
not yet reproducible by others** (RULES.md, "Data"); the method and the tool commits are.

Tools: `tools/token_row_stride.py` at e38cf37 (the diff from the lead's 2972c34 touches
only a degenerate-variance sign, an off-by-one in the header comment, a `--head` guard and
the error exit status; the score is unchanged), `tools/token_band_profile.py` at f3ab6f0
(same declared profile, integer moments, absolute candidate rows r*S from payload bit
zero, independent bit reader) and `tools/orf_tokens.py` at 2744ab6.

`python -I -B tools/token_row_stride.py --self-test` passed (peak S=137, z=62.22).
The scan ran as `--rows 300 --top 2000`, so every candidate of every scan was retained;
the 50 scans took 16.8 s. As a cross-check, `token_band_profile.py` at start row 0
reproduces the same best S and the same z to 2 decimals on all 50 files.

| measure over the 50 files | value |
| --- | --- |
| S range / distinct values | 5240 to 6288 / 34 (sd 243.9) |
| S-W min / Q1 / median / Q3 / max | 0 / 1.0 / 28.0 / 305.8 / 1048 (mean 164.9) |
| S = W / S > W / S < W | 10 / 40 / 0 |
| S-W > 100 / S-W > 300 / 0 < S-W <= 8 | 19 / 13 / 7 |
| z min / Q1 / median / Q3 / max | 2.86 / 5.09 / 7.53 / 13.24 / 72.48 |
| z >= 5.0 / z < 5.0 | 38 / 12 |
| Pearson r(S-W, bpp) / Spearman rho | +0.4147 / +0.6228 |
| Pearson r(S-W, bpp) without the 10 S = W files | +0.3172 (n=40) |
| mean bpp, S = W group / S > W group | 6.246 / 6.825 |

Later bands: 300 rows per band at candidate row starts 0, 1000, 2000 and 3000, head 32,
re-scanning prefix S-64..S+64 clipped to W..W+1200 (start row 0 is the same window and
reproduces the prefix exactly). The window's lower edge is clipped at W for 30 of the 50
files, which biases the shifts below upward.

| start row | full bands | band-best S = prefix S | band S - prefix S (min/Q1/median/Q3/max) | band-best z (min/median/max) | z at prefix S (min/median/max) | z at prefix S < 5.0 | z at prefix S < 0 |
| ---: | ---: | ---: | --- | --- | --- | ---: | ---: |
| 0 | 50 | 50 | 0 / 0 / 0 / 0 / 0 | 2.86 / 7.58 / 72.48 | 2.86 / 7.58 / 72.48 | 12/50 | 0/50 |
| 1000 | 50 | 2 | -63 / -5 / +5 / +30 / +63 | 0.50 / 6.39 / 28.73 | -10.40 / 0.58 / 28.73 | 46/50 | 17/50 |
| 2000 | 50 | 0 | -64 / +2 / +9 / +37 / +62 | 0.89 / 5.95 / 25.77 | -19.57 / -0.36 / 25.55 | 48/50 | 30/50 |
| 3000 | 49 | 0 | -63 / -13 / +4 / +45 / +64 | 1.44 / 6.56 / 37.92 | -126.22 / -0.20 / 7.63 | 46/49 | 28/49 |

The band-best candidate moves by more than 32 tokens from the prefix stride on 33 of the
50 files at one of the three later bands. Index 8 cannot supply 300 rows at start row
3000 (269 rows, band z 2.80 at S=6271) and is excluded from that row. Pearson r between
the band-best S and bpp is +0.4147, +0.4127, +0.4058 and +0.5942 at the four starts.

Limitations. (1) The lead's "one sharp peak per file" wording is **not** part of this
finding. The lead gives no peak threshold, so two criteria were fixed before the 50 files
were measured: P1, the maximum z over the scan is at least 5.0; P2, every candidate at
least 8 tokens away from the best has z at most half of it. On this cohort 38 of 50 files
pass P1 and 22 of 50 pass P1 and P2; 12 of 50 have no peak at all (z 2.86 to 4.90, indices
1, 2, 4, 5, 8, 10, 14, 36, 37, 38, 41, 49). The lead's nine public files span z 6.21 to
47.68. (2) The lead's calm-body statement is about E-M1 Mark II files and is not tested
here: this cohort has no E-M1 Mark II file, only OM-5. (3) Candidate strides are not
physical rows, the maximum is not a unique physical boundary, and the later-band peaks are
broad. (4) All 50 inputs are `own`, so no number here is reproducible by others yet.

Per-file results (index, bpp, S, S-W, z; z as the tool prints it):

| # | bpp | S | S-W | z |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 7.124 | 5572 | 332 | 4.90 |
| 2 | 7.811 | 5944 | 704 | 4.30 |
| 3 | 6.691 | 5274 | 34 | 6.80 |
| 4 | 8.013 | 5655 | 415 | 3.77 |
| 5 | 7.821 | 5814 | 574 | 4.33 |
| 6 | 6.267 | 5240 | 0 | 6.23 |
| 7 | 6.785 | 5295 | 55 | 5.22 |
| 8 | 6.165 | 6288 | 1048 | 2.86 |
| 9 | 6.393 | 5282 | 42 | 9.47 |
| 10 | 6.460 | 5254 | 14 | 4.67 |
| 11 | 7.435 | 5598 | 358 | 12.09 |
| 12 | 6.142 | 5240 | 0 | 58.47 |
| 13 | 7.525 | 5242 | 2 | 9.83 |
| 14 | 7.315 | 5602 | 362 | 3.66 |
| 15 | 6.143 | 5240 | 0 | 30.69 |
| 16 | 6.411 | 5240 | 0 | 6.67 |
| 17 | 6.684 | 5242 | 2 | 15.56 |
| 18 | 6.246 | 5241 | 1 | 11.82 |
| 19 | 7.022 | 5644 | 404 | 6.65 |
| 20 | 7.022 | 5396 | 156 | 5.11 |
| 21 | 6.155 | 5240 | 0 | 46.66 |
| 22 | 6.027 | 5240 | 0 | 65.35 |
| 23 | 6.188 | 5241 | 1 | 26.79 |
| 24 | 6.206 | 6118 | 878 | 5.68 |
| 25 | 6.340 | 5241 | 1 | 16.33 |
| 26 | 6.253 | 5240 | 0 | 11.75 |
| 27 | 7.128 | 5561 | 321 | 9.91 |
| 28 | 6.315 | 5281 | 41 | 9.42 |
| 29 | 7.504 | 5402 | 162 | 8.39 |
| 30 | 6.547 | 5253 | 13 | 23.33 |
| 31 | 6.904 | 5429 | 189 | 13.62 |
| 32 | 6.753 | 5242 | 2 | 14.43 |
| 33 | 6.576 | 5313 | 73 | 7.48 |
| 34 | 6.418 | 5241 | 1 | 10.42 |
| 35 | 6.530 | 5500 | 260 | 7.58 |
| 36 | 7.904 | 5781 | 541 | 3.23 |
| 37 | 7.199 | 5593 | 353 | 4.05 |
| 38 | 6.499 | 5261 | 21 | 3.46 |
| 39 | 6.485 | 5302 | 62 | 27.24 |
| 40 | 6.860 | 5388 | 148 | 6.46 |
| 41 | 6.520 | 5690 | 450 | 2.88 |
| 42 | 6.097 | 5259 | 19 | 5.37 |
| 43 | 6.177 | 5240 | 0 | 43.17 |
| 44 | 6.851 | 5262 | 22 | 8.28 |
| 45 | 6.475 | 5260 | 20 | 5.72 |
| 46 | 6.367 | 5240 | 0 | 72.48 |
| 47 | 6.499 | 5370 | 130 | 5.08 |
| 48 | 6.519 | 5240 | 0 | 7.23 |
| 49 | 6.362 | 5254 | 14 | 4.81 |
| 50 | 7.333 | 5261 | 21 | 9.91 |

Input identities (`own`, SHA-256), index as in the table above:

```text
 1 21be55ff67d4fff6576507102fe2eb8ac462e356dc6d7cde22b2a23f86bb98e1
 2 2a691f772ed5e29d6597566b29ad2288ff11a6786a3c9aca5f754cdfa83ec4bf
 3 4854cf60ef25bbd7c39b138e37be182683430de1fc70f34cbc63af6051e911de
 4 7c16cbf60483f3b8ba289765452e416aa2015c40017673090c64a72f5c7303e0
 5 269afc4e65b97db6fb7035d9c1f8b18deb77bafdf472af945223ff0c4712ff15
 6 81d679194870a0e48b17313578a279ca643b02ec41eafd8e37fb4f4974f5886b
 7 06a757cc1dca362bddfcbb1c34e840c65116eb4f21c9c1ce28b454a4c4987726
 8 b49f2e008b755cd0c001ef02641102e8934c0bc7bf9078f99108cd606bce275f
 9 53837f7de9b8ec95c73c20a8379d1782e85e2bf2aabe2e2b04a4ce69983a8bb9
10 68aa72046690deb3307afbb91ea25efe7f290344bc5504e3b1744b6cdc17f726
11 a536ef5679f60e81eb86d1ab6af694e3883fddc8b335d2e6b66f4a2edb8ba1ce
12 2d5bc7c77f4dc393f2eac898bb7596f0e5dabd982d3d3b2debe9b44427da2b80
13 9bc10af8fbed81ca50580df3f0d70e699bc5251fe3ef5fb4b0b9dfe7e13a74cf
14 2fd27e6c427d539871efdedbffc7cf9aa0e28e9e49ff9936e6be5971217fd608
15 63a1ca7664af6fde92383acf948b1fb6bc1a359a1b8ead2dac7f367b2b2b0273
16 076e3f6b304c0b9c7252925ba9c9ff013bcea54a84ea8de6165d64446adaaa3b
17 a3bb40253726ad080a6a382cac8ad901e78d5e72649e6c7085e80fb7fc101ceb
18 6faed66024f46bb4d7227bc9f01c4b8b4505fc8381832b7455b70018bece6e2a
19 f40abd5ecd165cd6345435c7dee60eb8b27142cd5500be7e08eac392c60046f7
20 cc19b0764b2af9d23e78a658132ae8d636c33c7e66cb089ee861ebcfb2282813
21 7ffa6f6d18c771cb89868b05c20f9a278bc168d7db617662f52173a5897b147b
22 39d2b2cf739997b222751f5e1efd26f07a539ca58f5c0da04da5d0b0b3f4137e
23 9328e18dcef8105b846c4b0c86f2f9a3556fe040b08137f22fd29fa0dcdaa44d
24 e29574ef723a0f3451cb56fad22ac19ba0cd97f85fdcd0f17c584521fa811806
25 f80949b4edad8a875759dfdeb4d4e550436e4b84219ed0fd416e6dfc41f255f7
26 79aad359ff8388b087ef4fa610b5294aeb6f106f091a6dc9bc56762381393247
27 45c0862d280960a922924849a2f5618dabe255a2a370a46a671504aaf8ed5791
28 ec9a5874181631d32fd276dc8bcb332958d34e1b79196287ee5a53f115c8cf74
29 bf306404cdec3c2123e8bf1ea517cdad0bf7bd6ba1cbf23d21d584ba997af5a9
30 69fb9c023923b0320fca15f407b684f0968521fd81ec13fb8fa1fd6913d7c957
31 cd3e6c4f2fd3bf6a96c7986a3ee82ac691a8ea3b658a50b6ff46f481b3b55f0c
32 82ba9563d994d7d71cb1aa2fb1680c068bdd37c1a6b280836bf030bfc6c51db0
33 d1d1058461b5a165a48a031299815356f98365c8ae3c1870ec6c574864527f99
34 aba0d34a65dc2bd6ca223d2e1eca1583d7964f8d15c7376e04ae48b12d4f2745
35 1e7ddba5f494c1fe2b600234cacfb083a812c052667cc0f4e11aefe273c02fad
36 26863e2f4a98d37d379d56ef1661ece2f63ffd1ba27a5a194b61620baecea3ae
37 0e1171aadf47a98b89d01868bd57147aabe0192532b60d961e233c708fa4056f
38 2b4102cb43b313c58a841d6c8f4df2524249f0e0fd0e12ee8b8fa8a5a02b79af
39 c53c8815574d45cf2fd7813d36f83c14da6129595e0f21c0e55bce5e98d177a4
40 146ef6ca8cfb9e46bd47b2ba74cf8e6dc3082c4a92b1bcf4749cd78687d5c9bc
41 532f6d2043b859806a8ba214573a59b5d8cc706e8069bee2aa3a9b3d3ce05ee9
42 4aa8fdaa6c7c6a80f21619d7b8d41c8001083e498c9d6c98d0f07e1c3a8e579c
43 ae4e4c35cb962bda0f79c84a55d2e3d7a0c056ab14b00199d31e36522b68481b
44 81666a0264563b53a03c5a81eab7306ae8cd85db1c17c6110f70d3e9ce56418e
45 38876a1895edee9991b29dd2bf2712f8141b7cfbd9031fc0241d145ad019b167
46 b12e8fcab9760b69d507d00b6fd1a9eb4737f432de17db98a3a00761a5e5388c
47 4e369761c2d5c7df9dc465505e7d1c1a13cf22f59eddfb2f11f79f9e75f2198d
48 5ffa457130fa75f6aed3c24c55d69545b2f67f80dc84a085a48142d0c6b3966c
49 93ae1d0fed02cdee3c555fd71d0a51f83fbf34441734e2e0c20d942f062684d8
50 01eb9471a624ff4f6cdf20d52006ca48e746f99395dcafaf8ee8a635c2fc4573
```

## Reproduce

Run from the repository root with local copies of the files named on the command line;
these steps only read files and print numbers.

    python -I -B tools/token_row_stride.py --self-test
    python -I -B tools/token_row_stride.py FILE [FILE ...] --rows 300 --top 2000
    python -I -B tools/orf_signature.py FILE [FILE ...]

Save the scan output as `scan.txt` and the signature CSV as `sig.csv`, then save the
script below as `summary.py` and run `python -I -B summary.py scan.txt sig.csv`. It keeps
the tool's first (best) candidate line per file, joins bpp by file name and prints the
aggregates above (S-W quartiles, counts, distinct S, z distribution, Pearson and Spearman
against bpp).

```python
import csv
import math
import re
import statistics
import sys

SCAN = re.compile(r"^== (\S.*)$")
ROW = re.compile(r"^\s+S=(\d+)\s+S-W=([+-]\d+)\s+rows=(\d+)\s+z=(-?[\d.]+)\s+elevation=(-?[\d.]+)$")


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def q(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


scan = []
name = None
for line in open(sys.argv[1]):
    m = SCAN.match(line.rstrip("\n"))
    if m:
        name = m.group(1)
        continue
    m = ROW.match(line.rstrip("\n"))
    if m and name:
        scan.append((name, int(m.group(1)), int(m.group(2)), float(m.group(4))))
        name = None  # keep only the tool's first (best) line per file
bpp = {r["file"]: float(r["bpp"]) for r in csv.DictReader(open(sys.argv[2]))}
S = [s for _, s, _, _ in scan]
d = [dw for _, _, dw, _ in scan]
z = [zz for _, _, _, zz in scan]
b = [bpp[n] for n, _, _, _ in scan]
print("files %d" % len(scan))
print("bpp: min %.3f median %.3f max %.3f" % (min(b), statistics.median(b), max(b)))
print("S: range %d..%d  distinct %d  sd %.1f"
      % (min(S), max(S), len(set(S)), statistics.pstdev(S)))
print("S-W: min %d Q1 %.1f median %.1f Q3 %.1f max %d mean %.2f"
      % (min(d), q(d, .25), q(d, .5), q(d, .75), max(d), sum(d) / len(d)))
print("S=W %d  S>W %d  S<W %d  distinct S %d" % (d.count(0), sum(1 for v in d if v > 0),
                                                 sum(1 for v in d if v < 0), len(set(S))))
print("S-W > 100: %d  S-W > 300: %d  0 < S-W <= 8: %d"
      % (sum(1 for v in d if v > 100), sum(1 for v in d if v > 300),
         sum(1 for v in d if 0 < v <= 8)))
print("z: min %.2f Q1 %.2f median %.2f Q3 %.2f max %.2f"
      % (min(z), q(z, .25), q(z, .5), q(z, .75), max(z)))
print("z >= 5.0: %d  z < 5.0: %d" % (sum(1 for v in z if v >= 5.0), sum(1 for v in z if v < 5.0)))
print("Pearson r(S-W, bpp) %.4f  Spearman %.4f  n=%d"
      % (pearson(b, d), pearson(ranks(b), ranks(d)), len(b)))
```

Later bands, with W and S0 the payload width and the prefix best stride of a file. The
`--sample` arguments are the public identity of an input; for an `own` file use its own
index and SHA-256:

    python -I -B tools/token_band_profile.py --sample ID NAME SHA256 FILE \
        --stride 5240 --stride S0 --start-row 0 --rows 300
    python -I -B tools/token_band_profile.py --sample ID NAME SHA256 FILE \
        --stride S0-64 ... --stride S0+64 \
        --start-row 0 --start-row 1000 --start-row 2000 --start-row 3000 --rows 300

The tool prints one JSON document per sample: `signed_mean_over_se` is the z of this
profile, `complete_rows` and `token_shortfall` report bands the token stream cannot fill,
and `bands` is ordered by stride then start row.
