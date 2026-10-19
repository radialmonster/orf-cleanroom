# Row period equals W where a row-start profile is sharp; busy bodies carry more than W tokens per row

Author: @radialmonster
Verified by: @radialmonster
Lead: #30
Variant: unassigned
Builds on: #11
Partial: row period and row-start profile only; the other ruled-out claims of #30 are not re-run

## Claim
Part of lead #30 (the row-layout claims only; the other negatives in that lead were not re-run):
- Parsing the payload with the k=5 token model of #11 (q zero bits, stop bit, 5-bit suffix) consumes the whole payload to within 4 bits on every file tested in full (6 of 6).
- Where the start of a row shows a sharp profile (the first 24 tokens cost more bits than later ones, z >= 10), the row period equals the payload width W: 5240x3912 (4 of 4 sharp files), 8200x6132 (1 of 1). One 4640x3472 file has its sharp peak at W+2, not W (the lead says the same kind of offset occurs: others +1 or +3).
- Most files have no sharp profile (z < 10 at every period W-4..W+4), so the period is undetermined there, not different from W.
- On the busy 5220x3912 bodies the whole-payload average is 5886 and 6015 tokens per row (W = 5220), and no period W-4..W+4 reaches z 3.5 on any of 13 such files, so tokens per row should not be assumed equal to W. On the calm 5240 and 4640 files the average is also above W (5244, 5281; 4818, 4808).

## Original evidence
Lead #30 (private notes, 2026-10-14..18): period equal to W on 5240x3912 (6 of 6), 4640x3472 (7 of 9, the others +1 or +3) and 8200x6132 (1 of 1); average 6025 tokens per row on a busy 5220x3912 body. The lead states no method or file list, so this run defines its own measure (below) and does not reproduce the lead's numbers like "9.5-14 vs 13.0".

## Verification
New run on 2026-10-19, after the lead was posted. Files: the 87 compressed (`size_class` variable) CC0 files of the Olympus/OM set (checked with `pixls_samples.py check`, all CC0). None of the lead's files are named, so I cannot say which overlap; the 5220x3912 files, 8200x6132 files from three bodies and the E-M5 Mark III 5240 file were not in the manifest before this PR.

Measure (inline script `rowperiod.py` below): parse the first 300 x W tokens with `orf_tokens.parse`, cost of a token = q + 6 bits, fold into rows of P tokens for each P in W-4..W+4, difference d = mean cost of the first 24 tokens of a row minus the mean of the rest, per row; z = mean(d) / (sd(d) / sqrt(rows)). Called "sharp" if z >= 10 at the best P (threshold fixed before looking at all files).

Numbers (87 files, tools/orf_tokens.py and tools/orf_signature.py at commit 62c368a):
- Sharp (z >= 10): 6 files. 5240x3912: 8af91836 (z 18.5), 89138ccc (27.5), 4bc52d99 (30.4), 24de6ac3 (33.2), all best P = 5240. 8200x6132: e9a21175 (41.5), best P = 8200. 4640x3472: 1a952245 (15.7), best P = 4642 (W+2; at P = W z is -2.9).
- Moderate (5 <= z < 10): 7 files; four of them have the best P at the edge of the scanned window (W+4), so the period is not established there. At W: a1345ebe (4640, z 6.2), 0b433019 (5240, z 5.6).
- 5220x3912 (OM-1, OM-1 Mark II, OM-3; 13 files): best z at any P is 3.2 or less.
- Whole payload parse (`tokrow.py`): bits used vs payload bits: bf2eef6b 160025028 / 160025032, d7fea340 165541509 / 165541512, 89138ccc 126140420 / 126140424, 24de6ac3 130236368 / 130236368, 1a952245 110295437 / 110295440, 19ba17e7 111353149 / 111353152. Tokens per row: 5885.9 and 6015.1 (W 5220), 5243.7 and 5281.0 (W 5240), 4818.0 and 4808.4 (W 4640).

Limits: only P within W-4..W+4 was scanned; 300 rows per file; the sharpness measure is mine; the lead's other negatives (headers, adaptive parameter, serpentine order, column phase) are not tested here.

## Reproduce
Clone, then (paths are examples; `pixls_samples.py check` on each file first):

    python tools/pixls_samples.py check FILE
    python rowperiod.py . 300 FILE        # row period / row-start profile
    python tokrow.py . FILE               # whole-payload tokens per row

`rowperiod.py`:

    """Inline script for lead #30 reproduction: row period and row-start block over orf_tokens.parse output.
    usage: python rowperiod.py REPO_DIR ROWS FILE..."""
    import sys, os, math, hashlib
    repo, rows = sys.argv[1], int(sys.argv[2])
    sys.path.insert(0, os.path.join(repo, "tools"))
    import orf_tokens as T
    import numpy as np
    K = 24
    for f in sys.argv[3:]:
        w, h, buf = T.locate(f)
        n = rows * w
        qs, ss, marks, pos = T.parse(buf, n, w)
        # (a) total bits consumed vs payload
        l = np.array(qs, dtype=np.float64) + 6
        best = None
        res = {}
        for P in range(w - 4, w + 5):
            m = len(l) // P
            a = l[:m * P].reshape(m, P)
            head = a[:, :K].mean(axis=1)       # first K tokens of each row
            rest = a[:, K:].mean(axis=1)
            d = head - rest
            z = d.mean() / (d.std(ddof=1) / math.sqrt(m))
            res[P] = (d.mean(), z)
        bp = max(res, key=lambda p: res[p][1])
        sha = hashlib.sha256(open(f, "rb").read()).hexdigest()[:8]
        print("%s %dx%d tokens=%d W: elev=%.3f z=%.1f | best P=%d (W%+d) elev=%.3f z=%.1f | esc=%d" % (
            sha, w, h, len(l), res[w][0], res[w][1], bp, bp - w, res[bp][0], res[bp][1], sum(1 for q in qs if q >= 17)))

`tokrow.py`:

    """Inline script for lead #30: whole-payload token count per image row. usage: tokrow.py REPO FILE.."""
    import sys, os
    sys.path.insert(0, os.path.join(sys.argv[1], "tools"))
    import orf_tokens as T
    for f in sys.argv[2:]:
        w, h, buf = T.locate(f)
        qs, ss, marks, pos = T.parse(buf, 10**9, w)
        print("%s %dx%d tokens=%d tokens/row=%.1f (W=%d) bits_used=%d of %d" % (os.path.basename(f)[:4], w, h, len(qs), len(qs)/h, w, pos, len(buf)*8))
