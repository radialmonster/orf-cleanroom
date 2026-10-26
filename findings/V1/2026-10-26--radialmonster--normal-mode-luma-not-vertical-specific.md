# Normal-mode E-M1 II top-band b2+b4 score is not specific to preview vertical alignment

Author: @radialmonster
Verified by: @radialmonster
Lead: #351
Variant: V1
Builds on: 2026-10-21--radialmonster--b2b4-local-luma-proxy, #149
Partial: the four normal E-M1 Mark II top-band files and the High Res 1994 and 1996 boundary only

## Claim

On the four normal E-M1 Mark II top-band files, the fixed b2+b4 preview-DC grid score is not specific to the declared preview row alignment. Scoring every circular shift of the preview's 23 luma DC rows, the observed score is rank 2 or 3 of 22, and a one-row-up preview scores higher on 1993, 1995 and 1997. The within-row shuffle null permutes suffix tokens inside each row, so it tests horizontal structure only; the original top-band z does not establish row-registered luma.

The effect is mode-dependent. On the two High Res E-M1 Mark II files the observed score is rank 1 of 11, but the margin over the best shifted preview is only 0.00068 (1994) and 0.00322 (1996), so rank 1 does not establish strong vertical specificity either. The supported statement is that the normal-mode top-band score is a coarse spatial correlation, not a precise low-resolution luma map.

## Original evidence

Lead #351. The measurement is the fixed map of `2026-10-21--radialmonster--b2b4-local-luma-proxy`: `v = b2 + b4` per token, box mean over 63 tokens within each row, block mean to the preview's luma DC grid, row-centred correlation. The new tool is `tools/token_luma_probe.py --shift-null` in PR #350, merged as `5e7f595`. It scores the declared target and every circular shift of its rows with the same map and prints the observed rank, best shift and shift mean, sd and maximum.

The lead's four normal-mode public CC0 inputs:

| id | observed r | best shift | best r | observed rank |
| ---: | ---: | ---: | ---: | ---: |
| 1993 | +0.47214 | 22 (one row up) | +0.53012 | 2 / 22 |
| 1995 | +0.10846 | 22 (one row up) | +0.11123 | 3 / 22 |
| 1997 | +0.12245 | 22 (one row up) | +0.12382 | 2 / 22 |
| 1998 | +0.09793 | 3 | +0.09936 | 3 / 22 |

SHA-256: 1993 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`; 1995 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`; 1997 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`; 1998 `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`.

## Verification

A new run was made on 2026-10-26 UTC, after lead #351 was posted, at main `5e7f595` (the tool PR merged). It reran the four normal-mode files and added the two High Res E-M1 Mark II files, which the lead did not use. All six local hashes matched their retained verified-CC0 records; each already has a `samples/manifest.csv` row. No catalogue request, download or manifest edit was made.

| id | mode | observed r | best shift | best r | observed rank | margin |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1993 | normal | +0.47214 | 22 | +0.53012 | 2 / 22 | -0.05798 |
| 1995 | normal | +0.10846 | 22 | +0.11123 | 3 / 22 | -0.00277 |
| 1997 | normal | +0.12245 | 22 | +0.12382 | 2 / 22 | -0.00137 |
| 1998 | normal | +0.09793 | 3 | +0.09936 | 3 / 22 | -0.00143 |
| 1994 | High Res | +0.05856 | 1 | +0.05788 | 1 / 11 | +0.00068 |
| 1996 | High Res | +0.09649 | 1 | +0.09327 | 1 / 11 | +0.00322 |

The four normal-mode rows reproduce the lead's numbers. The two High Res rows are the new boundary: the observed score is the best of the 11 shifts, but only by about 0.001 to 0.003. The shift distributions are narrow (normal-mode sd 0.003 to 0.154; High Res sd about 0.003), so the rank is the useful summary and the High Res rank 1 is not a large effect.

The High Res inputs: 1994 `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23`; 1996 `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2`.

## Reproduce

Read `tools/token_luma_probe.py` and `tools/test_token_luma_probe.py` first, then match each local file to the SHA-256 above:

    python -I -B tools/test_token_luma_probe.py
    python -I -B tools/token_luma_probe.py "<dir>/1993_Olympus - E-M1MarkII - 16bit (4_3).ORF" --rows 300 --window 63 --perms 20 --shift-null
    python -I -B tools/token_luma_probe.py "<dir>/1995_Olympus - E-M1MarkII - 16bit (4_3).ORI" --rows 300 --window 63 --perms 20 --shift-null
    python -I -B tools/token_luma_probe.py "<dir>/1997_Olympus - E-M1MarkII - 16bit (4_3).ORI" --rows 300 --window 63 --perms 20 --shift-null
    python -I -B tools/token_luma_probe.py "<dir>/1998_Olympus - E-M1MarkII - 16bit (4_3).ORF" --rows 300 --window 63 --perms 20 --shift-null
    python -I -B tools/token_luma_probe.py "<dir>/1994_Olympus - E-M1MarkII - 16bit (4_3).ORF" --rows 300 --window 63 --perms 20 --shift-null
    python -I -B tools/token_luma_probe.py "<dir>/1996_Olympus - E-M1MarkII - 16bit (4_3).ORF" --rows 300 --window 63 --perms 20 --shift-null

## Limits

- The shift null is a sensitivity diagnostic, not a calibrated p-value. It has only 22 normal-mode shifts and 11 High Res shifts; the rank is coarse, and no exact significance is claimed.
- The High Res rank 1 margin is tiny; it is reported as a boundary, not as evidence of strong vertical registration.
- The top 300 rows only. Later bands, other bodies, other window or DC scales, a phase-randomized null, values and a decode are not tested.
- The finder and verifier are the same human account, so this is self-verified, not independent human verification.
