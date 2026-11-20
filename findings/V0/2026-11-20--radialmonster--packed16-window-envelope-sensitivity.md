# Nested packed-16 windows retain identity rejections under the fixed toy envelope

Author: @radialmonster
Verified by: @radialmonster
Lead: #872
Variant: V0
Builds on: #301, #310, #325, #797, 2026-10-26--radialmonster--packed16-toy-envelope-reproduction

## Claim

On three public packed-16 files, increasing the nested windows from 32x24 to 64x48 and 128x96 preserves both original identity rejections under the fixed toy envelope. At 128x96 it adds a third and still accepts 13 of 36 constructed nonidentity controls.

## Original evidence

The discovery run started on 2026-11-20 at 21:20:51 UTC. `tools/v0_window_envelope_probe.py` at `3f38049abe978d1edd35efa60588d2be427b945c` uses center-column windows anchored at the top, middle and bottom. It compares the same five maps as #325 on floor(stored word / 16) with strict binary64 upper-envelope comparisons, and reports stored-word features separately. It classifies each trial with the original 32x24 limits and, separately, with size-specific limits refitted on the same synthetic scene/noise/seed design.

Public raw.pixls.us CC0 files, matched to the manifest by SHA-256:

- 1800, `Olympus - E-1 - 16bit (4:3).ORF`, `042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c`
- 2151, `Olympus - E-400 - 16bit (4:3).ORF`, `1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b`
- 5424, `Olympus - E-10 - 16bit (4:3).ORF`, `2bfdade72439017a60a47aad1e5bbcb1aca36f2be7a21e94a4257a678fb6f4da`

| Size | Identity accepted / 9 | Complement / 9 | XOR high / 9 | Affine permutation / 9 | Offset / 9 | All nonidentity accepted / 36 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 32x24 | 7 | 7 | 7 | 2 | 0 | 16 |
| 64x48 | 7 | 7 | 7 | 3 | 0 | 17 |
| 128x96 | 6 | 6 | 5 | 2 | 0 | 13 |

The two rules gave identical rejection reasons in all 135 discovery trials. The nine stored-word summaries and 45 mapping records at 32x24 exactly match a fresh run of the original #325 tool. At all three sizes, E-1 middle and E-400 top are rejected for `lag2_mean_abs` alone. E-10 middle also fails on lag2 at 128x96. There were no other identity rejections in discovery. The fixed lag2 limit is 33.37921348314607. At 128x96, 1,274 of 73,728 textured training cells hit 4095.

## Verification

After #872 was posted, a new run started on 2026-11-20 at 21:22:46 UTC. It repeated all 135 discovery mapping records and 27 stored-word summaries with an exact match. The discovery cohort used all three current public CC0 packed-16 files. The new run therefore also widened the same nine anchored windows to the predeclared 256x192 extent.

| 256x192 rule | Identity accepted / 9 | Complement / 9 | XOR high / 9 | Affine permutation / 9 | Offset / 9 | All nonidentity accepted / 36 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Fixed | 5 | 5 | 5 | 2 | 0 | 12 |
| Refitted | 3 | 3 | 3 | 0 | 0 | 6 |

With fixed limits the two original rejections, E-10 middle and E-10 bottom fail lag2. The refit additionally rejects E-400 middle and bottom on lag2. The refitted lag2 limit is 16.84399638633377, while 145,408 of 294,912 smooth training cells and 83,405 of 294,912 textured training cells hit 4095. Training extent and limits change together, so the refit does not isolate a window-size effect. A separate read-only implementation matched all 180 mapping records and 36 stored-word summaries in the fresh run. Both implementations were run for the same contributor.

Windows overlap on the same three captures. All acceptance and rejection labels describe constructed controls for this toy envelope. Physical mapping, effective precision, black level, CFA, held-out transport and compressed decoding remain open.

## Reproduce

At the pinned tool commit, use the exact three CC0 files above for the local file arguments. The tool verifies their SHA-256.

```text
python -I -B tools/test_v0_window_envelope_probe.py
python -I -B tools/v0_window_envelope_probe.py --phase discovery --sample 1800 E1_FILE --sample 2151 E400_FILE --sample 5424 E10_FILE
python -I -B tools/v0_window_envelope_probe.py --phase verification --sample 1800 E1_FILE --sample 2151 E400_FILE --sample 5424 E10_FILE
```
