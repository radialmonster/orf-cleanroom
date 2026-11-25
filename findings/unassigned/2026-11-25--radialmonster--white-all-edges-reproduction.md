# Fixed k=5 white motif-interior advantage reproduces in an adjacent band

Author: @radialmonster
Verified by: @radialmonster
Lead: #988
Variant: unassigned
Builds on: #197, #339, #951, #868, #976

## Claim

Both fixed k=5 variants reproduce the exact endpoints and W−6 word counts on 397 of 1568 directed near-pitch motif edges in the original clipped-white PA210010 band. In the fixed adjacent band, both give 399 of 1596. Neither k=4 variant reaches any endpoint in either band. Choosing a suffix width in this comparison does not resolve which candidate edges are physical rows.

## Original evidence

Lead #988 fixed PA210010.ORF and the all-edge motif comparison from #987. It removes the literal six-field motifs, parses the same bounded interior for each candidate, and reports successes only if the exact end and target count agree. It does not select a best path or impose mutual uniqueness.

The retained public CC0 PA210010.ORF SHA-256 is `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`. The filename and source are recorded in `samples/om3-flat-338-provenance.json` and `samples/manifest.csv`. Its declared width is 5220, with pitch 31332, tolerance 313, and target W−6=5214 words.

## Verification

On 2026-11-25 after the lead was posted and scanned, the default invocation matched the complete saved discovery aggregate, including all parts of the joint masks, endpoint/overrun totals and source/target strata. This exact match was checked at 17:40:45 UTC before the adjacent band was measured. Both invocations passed the full public hash gate and exited zero with no stderr.

| Fixed band (bit index, half-open) | Motifs | Directed edges | k=5 exact endpoint | k=5 endpoint and target | k=4 exact endpoint | All candidates' completed words (per candidate) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [40,12532840) | 791 | 1568 | 789 | 397 | 0 | 8174773 |
| [12532840,25065640) | 800 | 1596 | 798 | 399 | 0 | 8320746 |

Mask order is literal k4, literal k5, capped k4, capped k5. Discovery repeats 0101 on 397 edges and 0000 on 1171. Adjacent masks are 0101 on 399 and 0000 on 1197. In the adjacent band the k=4 variants overrun every edge at the stop check, and the k=5 variants have 798 exact endpoints and 798 stop overruns. Both capped candidates complete zero escapes in each band.

| Band | Sources with an outgoing edge | k=5 all / some / none | k=4 all / some / none | Sources without an outgoing edge |
| --- | ---: | --- | --- | ---: |
| Discovery | 789 | 5 / 392 / 392 | 0 / 0 / 789 | 2 |
| Adjacent | 798 | 2 / 397 / 399 | 0 / 0 / 798 | 2 |

In the adjacent band the successful edges all have gap residue zero modulo six. The residue-zero stratum also has 395 failures, and residues two and four each have 401 failures. This does not identify the correct edge among same-residue candidates.

An independently written bit scan, exhaustive edge enumeration and bounded cursor recomputed and matched the adjacent aggregate with the shared strip locator. This is same-account verification, and an additional window on the same file, not a new capture. No edges cross the band boundary, but many edges within a band share motifs. The result does not establish frame boundaries, physical rows, variant membership, values, or an escape rule.

## Reproduce

At `d1d533d4549a35681eecd7f2f74167ac12a41adf` use the pinned public CC0 PA210010 file. The tool matches its full hash before processing. Do not infer a grammar outcome on zero edge support.

    python -I -B tools/test_white_motif_all_edges.py
    python -I -B tools/white_motif_all_edges.py --sample WHITE
    python -I -B tools/white_motif_all_edges.py --repeat --sample WHITE

Compare `joint_success_masks`, grammar endpoints and overruns, `source_outcomes` and the gap/degree strata. No private inputs were used.
