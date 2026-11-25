# Consecutive exact OM-3 motif anchors expose a minimum-length k5 interior budget

Author: @radialmonster
Verified by: @radialmonster
Lead: #1027
Variant: unassigned
Builds on: #30, #197, #951, #988, #1023

## Claim

On the two original OM-3 captures, both k5 readings reach the fixed endpoint and 5214 words on all 399 tested lattice intervals per file. The raw stride-six stop predicate holds throughout. Neither k4 reading reaches those endpoints. The exact bit budget makes the two k5 successes equivalent to the raw predicate, not a discriminator between the escape rules.

## Original evidence

Lead #1027 froze per-file phases before parsing. At declared W=5220 it tests only consecutive predicted motif positions 40+phase+j·31332 for j=400..799. The 48-bit source motif is removed and the next motif excluded. Both complete literal motifs must be present. Missing anchors are not bridged and their edges are not counted as failures.

The exact interior length 31284 is 6×5214 bits. The literal k5 word consumes at least six bits, and the capped k5 word also consumes at least six. Thus the exact 5214-word endpoint count requires every word to have the minimum length. It is equivalent to a one at each stride-six stop site, with no constraint on the five following bits for that check. This does not exercise an escape. A separate direct bit test checks the same condition without a candidate parse.

The original white phase 147 and dark phase 41 each give 400 anchors and 399 available intervals in [12532840,25065640), payload-bit coordinates. The original endpoint-only and endpoint-plus-count masks are both `0101:399` per file in literal k4, literal k5, capped k4, capped k5 order.

## Verification

The full discovery JSON matched a fresh post-lead replay at 19:53:27 UTC on 2026-11-25. Only after this equality did the unchanged protocol use reserved public PA200011.ORF, phase 43. All three files passed the retained CC0 record and complete hash gates.

PA200011 has 142 of 400 predicted anchors present and 141 of 399 available adjacent intervals. Because only consecutive present anchors make an interval, the 142 present positions form one contiguous run on the tested lattice. The other 258 intervals are unavailable, not grammar failures. On all 141 available edges, the raw predicate holds and both k5 readings reach the exact endpoint and 5214 words. Both masks are `0101:141`. Neither k4 variant reaches any endpoint, with 66 stop overruns and 75 suffix overruns per reading. No capped escape completes in any of the three files' scored interiors.

A separate scanner and bounded cursor using the shared declared-strip reader match the reserved counts, masks and overrun reasons. This is verification by the finder, not by another human. It extends the tested fixed bit pattern to a sparse lattice. It does not establish camera row boundaries, the semantics of the six-field motif, or syntax in the missing intervals.

## Reproduce

At `a834dee4ad142a96cbc89d7f8776061b4c560c46` use the exact public CC0 inputs below. The pinned `samples/om3-flat-338-provenance.json` and manifest supply the retained records. The tool checks full input hashes before parsing.

    python -I -B tools/test_fixed_motif_edge_budget.py
    python -I -B tools/fixed_motif_edge_budget.py --sample PA210010.ORF WHITE --sample PA200010.ORF DARK
    python -I -B tools/fixed_motif_edge_budget.py --cohort repeat --sample PA200011.ORF DARK200

- `PA210010.ORF`, SHA-256 `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`
- `PA200010.ORF`, SHA-256 `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4`
- `PA200011.ORF`, SHA-256 `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3`

Compare masks, `predicate`, `predicate_agreement`, grammar totals, and available and unavailable edges. No private files were used.
