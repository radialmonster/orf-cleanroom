# Row period equals W where a row-start profile is sharp; busy bodies carry more than W tokens per row

Author: @radialmonster
Verified by: @ruedbi
Lead: #30
Variant: unassigned
Builds on: #11
Reproduces: 2026-10-19--radialmonster--row-period-is-w-where-sharp-and-busy-bodies-exceed-w
Partial: row period and row-start profile on public CC0 E-M1 Mark II files and OM-1; other bodies and ruled-out claims of #30 not re-run.

## Claim

Part of lead #30 (the row-layout claims only; the other negatives in that lead were not re-run):

- Parsing the payload with the k=5 token model of #11 (q zero bits, stop bit, 5-bit suffix) consumes the whole payload to within 4 bits on every file tested in full.
- Where the start of a row shows a sharp profile (the first 24 tokens cost more bits than later ones, z >= 10), the row period equals the payload width W: 5240x3912 files 1995, 1997, 1998 all peak sharply at best P = 5240 (W+0).
- Calm file 1993 shows moderate elevation at W (z = 5.6) with best P = 5240 (W+0).
- On busy 5220x3912 bodies (OM-1), the elevation profile is flat (z <= 1.0 at every candidate period W-4..W+4), confirming that the row period is not established by a sharp profile there.

## Original evidence

Lead #30 (private notes, 2026-10-14..18): period equal to W on 5240x3912 (6 of 6), 4640x3472 (7 of 9, the others +1 or +3) and 8200x6132 (1 of 1); average 6025 tokens per row on a busy 5220x3912 body.

The merged finding `2026-10-19--radialmonster--row-period-is-w-where-sharp-and-busy-bodies-exceed-w` reported:
- Sharp (z >= 10): 5240x3912 ids 8af91836 (z 18.5), 89138ccc (z 27.5), 4bc52d99 (z 30.4), all with best P = 5240.
- Moderate (5 <= z < 10): 0b433019 (5240, z 5.6 at W).
- 5220x3912: best z at any P is 3.2 or less.
- Whole payload parse on 89138ccc: 126140420 of 126140424 bits used (4 residual bits), 5243.7 tokens/row (W 5240).

## Verification

Independent verification was conducted by @ruedbi on 2026-11-18 using Python standard library (Python 3.8+) and `tools/orf_tokens.py`.

All unit tests in `tools/test_orf_tokens.py` passed.

A fresh rerun was performed on local public CC0 files from `samples/manifest.csv` across the first 300 rows (300 x W candidate tokens, K=24 header tokens compared against the row remainder across candidate periods P in [W-4, W+4]):

| File ID | File Name / Camera | SHA-256 | Dimensions | Tokens | Best P | Best z | W elevation | W z | Status |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1993 | `Olympus - E-M1MarkII - 16bit (4:3).ORF` | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` | 5240x3912 | 1572000 | 5240 (W+0) | 5.6 | 0.087 | 5.6 | Moderate |
| 1995 | `Olympus - E-M1MarkII - 16bit (4:3).ORI` | `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` | 5240x3912 | 1572000 | 5240 (W+0) | 18.5 | 0.286 | 18.5 | Sharp |
| 1997 | `Olympus - E-M1MarkII - 16bit (4:3).ORI` | `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a` | 5240x3912 | 1572000 | 5240 (W+0) | 27.5 | 0.333 | 27.5 | Sharp |
| 1998 | `Olympus - E-M1MarkII - 16bit (4:3).ORF` | `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71` | 5240x3912 | 1572000 | 5240 (W+0) | 30.4 | 0.351 | 30.4 | Sharp |
| - | `Olympus-OM1.ORF` | `1db8b91707e8251d751c8c2db6745133afece89b2931f760defdc1e4577ef11e` | 5220x3912 | 1566000 | 5219 (W-1) | 1.0 | 0.001 | 0.1 | Flat |

The z-scores and elevation statistics match the historical findings exactly to printed precision:
- 1993 (0b433019): elev = 0.087, z = 5.6 at best P = 5240 (W+0).
- 1995 (8af91836): elev = 0.286, z = 18.5 at best P = 5240 (W+0).
- 1997 (89138ccc): elev = 0.333, z = 27.5 at best P = 5240 (W+0).
- 1998 (4bc52d99): elev = 0.351, z = 30.4 at best P = 5240 (W+0).
- OM-1 (1db8b917): flat profile, max z = 1.0 across all tested candidate periods W-4..W+4 (z = 0.1 at P = W = 5220).

Whole-payload parse on 1997 (`89138ccc`):
- Total tokens parsed: 20513308
- Tokens per image row: 5243.7 (W = 5240)
- Bits consumed: 126140420 of 126140424 payload bits (4 leftover bits).

All numbers match the reported evidence exactly.

## Reproduce

With standard library Python:

```bash
python -I -B tools/test_orf_tokens.py
```

Run the row period probe on matching files:

```python
import sys, math, hashlib
sys.path.insert(0, "tools")
import orf_tokens as T

K = 24
for path in sys.argv[1:]:
    w, h, buf = T.locate(path)
    n = 300 * w
    qs, ss, marks, pos = T.parse(buf, n, w)
    l = [q + 6 for q in qs]
    res = {}
    for P in range(w - 4, w + 5):
        m = len(l) // P
        d = []
        for row_idx in range(m):
            row = l[row_idx * P : (row_idx + 1) * P]
            head = sum(row[:K]) / K
            rest = sum(row[K:]) / (P - K)
            d.append(head - rest)
        mean_d = sum(d) / m
        var_d = sum((x - mean_d) ** 2 for x in d) / (m - 1)
        sd_d = math.sqrt(var_d)
        z = mean_d / (sd_d / math.sqrt(m))
        res[P] = (mean_d, z)
    bp = max(res, key=lambda p: res[p][1])
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()[:8]
    print(f"{sha} {w}x{h} tokens={len(l)} W: elev={res[w][0]:.3f} z={res[w][1]:.1f} | best P={bp} (W{bp-w:+d}) elev={res[bp][0]:.3f} z={res[bp][1]:.1f}")
```
