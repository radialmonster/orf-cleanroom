# Exact OM-3 motif lattices miss initial starts and can fill an adjacent window

Author: @radialmonster
Verified by: @radialmonster
Lead: #1023
Variant: unassigned
Builds on: #30, #197, #951, #988

## Claim

The bounded public OM-3 white and dark traces reproduce the original parser-free lattice result. No pitch–phase lattice in the frozen range is full in the first window. On each file the best first-window pair at pitch 31332 matches 398 of 400 expected motif starts, then 400 of 400 in the adjacent window without refitting. This does not establish physical row labels.

## Original evidence

Lead #1023 used `tools/literal_motif_lattice.py` at `d7a4e08e616d8f1500c67cf88064c5242b0122ac` after freezing the scope on #30. It scans all alignments of six repetitions of `100xxxxx` using only the declared payload bits. The x bits may differ, and unrelated extra motifs are allowed. The windows are [40,12532840) and [12532840,25065640), measured from payload bit zero. All 627 integer pitches from 31019 through 31645 and every phase relative to bit 40 are considered. A predicted start is admissible only if its entire 48-bit motif would fit in its window.

The best first-window pair maximizes exact coverage fraction with ties broken by matched count, smaller pitch and smaller phase. The same pitch and phase are scored in the second window. Full-lattice counts, including the intersection, are computed separately from that best pair. No token parser is used in selecting or scoring a lattice.

## Verification

The full discovery JSON repeated after the lead was posted, at 19:41:13 UTC on 2026-11-25. Only then did the unchanged protocol use the two reserved dark captures. All four files passed the retained CC0 identity and full hash gates. The screens ran at declared W=5220, with the same windows and search bounds in every case.

| Capture | First / adjacent motifs | Full first / adjacent / both | Best first pitch, phase | First matches | Same pair adjacent matches |
| --- | ---: | ---: | --- | ---: | ---: |
| PA210010 white | 791 / 800 | 0 / 1 / 0 | 31332, 147 | 398/400 | 400/400 |
| PA200010 dark | 630 / 637 | 0 / 1 / 0 | 31332, 41 | 398/400 | 400/400 |
| PA200011 dark, reserved | 641 / 637 | 0 / 0 / 0 | 31332, 43 | 242/400 | 142/400 |
| PA200012 dark, reserved | 633 / 630 | 0 / 0 / 0 | 31349, 233 | 11/400 | 7/400 |

An independent bit scan and lattice evaluator, with the same declared-strip reader, agree with the complete reserved summaries. The exact adjacent-window coverage is confined to the two discovery captures. In particular, similar motif totals do not guarantee the same lattice coverage. These are measured bit-position constraints, not a physical row assignment, a claim about why any marker is absent, or a rejection of variable row lengths. This is verified by the finder using two new inputs for this comparison, not an independent human verification.

## Reproduce

At `d7a4e08e616d8f1500c67cf88064c5242b0122ac` use the following exact public CC0 names and hashes. Their retained source records are pinned in `samples/om3-flat-338-provenance.json` and the manifest. Run discovery before the reserved extension.

    python -I -B tools/test_literal_motif_lattice.py
    python -I -B tools/literal_motif_lattice.py --sample PA210010.ORF WHITE --sample PA200010.ORF DARK
    python -I -B tools/literal_motif_lattice.py --cohort repeat --sample PA200011.ORF DARK200 --sample PA200012.ORF DARK800

- `PA210010.ORF` `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`
- `PA200010.ORF` `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4`
- `PA200011.ORF` `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3`
- `PA200012.ORF` `c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7`

Compare all motif counts, full-window counts, intersections and first-to-adjacent fixed-pair counts. No private files were used.
