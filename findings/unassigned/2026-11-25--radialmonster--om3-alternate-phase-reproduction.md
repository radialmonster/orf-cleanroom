# Fit-selected four-bit shift partly recovers literal OM-3 dark motifs

Author: @radialmonster
Verified by: @radialmonster
Lead: #1035
Variant: unassigned
Builds on: #30, #1031, #1023, #338

## Claim

At the fixed 31332-bit pitch, the independently selected alternative is four bits later than the frozen starting phase on each of two public OM-3 dark captures. The alternative hits all 200 positions in the first held-out band of both darks. It is incomplete in the fit and farther bands and does not meet the full-recovery criterion on either capture. These are literal motif positions, not physical rows or evidence that the same motif instance moved.

## Original evidence

Lead #1035 used `tools/alternate_motif_phase.py` at `605284c660fae72dbf9592c234ed9ad85a53106b` on PA200010 dark and PA210010 white. The tool requires four previous fixed-phase counts from #1031 before searching alternatives. Origin is bit 40. Every literal occurrence of six `100xxxxx` fields belongs to the tile containing its start, with all 48 bits required to fit in the declared strip, even across tile edges. No candidate words are parsed. Among alternative phases with positive counts in [800,1000), the highest fit count wins, choosing the lower phase on a tie. The same fixed phase is scored on [1000,1200) and [1200,1600). Full recovery requires 200, 200 and 400 matches, respectively.

## Verification

The full discovery aggregates were reproduced in a new run on 2026-11-25 at 20:18:07 UTC after the lead was posted at 20:17:09 UTC. Reserved public CC0 PA200011 was run separately at 20:18:17 UTC using the same procedure, not the discovery phase. All files passed the exact hash and retained CC0 identity checks. Five generated controls passed. Separate literal scanning and aggregation with the same strip reader agreed on the reserved result. The verifier is the finder, not a separate human verifier.

| Capture | Original / selected phase | Original fit, score, farther | Selected fit, score, farther | All motif starts | Occupied tiles |
| --- | --- | --- | --- | --- | --- |
| PA200010 dark | 41 / 45 (+4) | 2, 0, 0 | 154, 200, 190 | 331, 328, 639 | 200, 200, 400 |
| PA210010 white | 147 / 155 (+8) | 200, 200, 400 | 200, 200, 399 | 404, 401, 802 | 200, 200, 400 |
| PA200011 dark, reserved | 43 / 47 (+4) | 0, 0, 0 | 173, 200, 5 | 328, 329, 649 | 200, 200, 400 |

Each alternative is the unique fit winner and none passes full recovery. All target tiles have at least one motif on every file. This distinguishes missing matches at the original phase from absence of the motif in the affected tile. It does not distinguish drift, variable row lengths, or replacement of one motif instance by another. The white comparator retains full coverage at its original phase while nearly matching at a second phase, which limits the use of high phase coverage alone to identify a physical boundary. Nothing here specifies a word grammar.

## Reproduce

At `605284c660fae72dbf9592c234ed9ad85a53106b`, substitute local paths for DARK, WHITE and RESERVED, using these exact public CC0 sources recorded in `samples/om3-flat-338-provenance.json` and `samples/manifest.csv`.

    python -I -B tools/test_alternate_motif_phase.py
    python -I -B tools/alternate_motif_phase.py --sample PA200010.ORF DARK --sample PA210010.ORF WHITE
    python -I -B tools/alternate_motif_phase.py --cohort repeat --sample PA200011.ORF RESERVED

- `PA200010.ORF` `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4`
- `PA210010.ORF` `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`
- `PA200011.ORF` `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3`

Compare the prior counts, fit-only choice, tie count, two unchanged scores and exact window totals. No private files were used.
