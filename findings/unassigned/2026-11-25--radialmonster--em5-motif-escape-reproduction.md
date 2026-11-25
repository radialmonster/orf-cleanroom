# Fixed E-M5 Mark II motif-window test does not favor capped escapes

Author: @radialmonster
Verified by: @radialmonster
Lead: #1007
Variant: unassigned
Builds on: #197, #951, #972, #990

## Claim

The original fixed E-M5 Mark II `P1010019.ORF` window reproduces a single literal-only endpoint-and-count success and no qualifying capped-only success. The six capped escapes reported on its six supported edges do not start at the qualifying flanked runs. Neither outcome establishes the physical grammar.

## Original evidence

Lead #1007 froze the parser-free selection in #197 and used `tools/motif_escape_support.py` at `5fa8781ed98d0bc8e2e78f1efd63e8dfb979b696`. At width 4640, it enumerates every complete six-field literal motif and every forward edge at pitch 27852 ± 278 in the half-open payload interval [17268280,33422440). This is not the token-index rectangle from #972. An edge qualifies only if the interior after its source motif and before its target includes a maximal run of at least twelve zeros and both flanking ones.

From the same start on each qualifying edge, literal and capped k=5 must reach the endpoint and exactly 4634 complete candidate words. Favoring capped under the frozen criterion also requires literal to fail this combined test and a completed capped escape to start at a qualifying run on that same edge. The supported edges can share motifs and runs.

## Verification

The full post-lead discovery aggregate matched the saved report on 2026-11-25 at 18:44:28 UTC. Only after that match did the same pinned tool open reserved public `P1010017.ORF`. Both inputs passed their full CC0 SHA-256 checks.

| Public capture | Motifs | Near-pitch edges | Qualifying runs in window | Supported edges | Exact endpoint, both | Literal only, endpoint and count | Capped only, endpoint and count with qualifying escape |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1010019 | 907 | 1419 | 2 | 6 | 3 | 1 | 0 |
| P1010017 | 906 | 1406 | 0 | 0 | Not scored | Not scored | Not scored |

On P1010019 the paired endpoint masks are `11:3, 00:3`, in literal and capped order. The other three edges overrun at the suffix check in both traversals. With the exact word count also required, the masks are `10:1, 00:5`. The capped traversal completes one escape on each supported edge but none begins at a qualifying run start. Completing a candidate escape somewhere on an edge is not the same as satisfying the tested criterion.

The reserved file has no grammar-result denominator. Neither traversal runs, so the absence of an observed capped-only success there is not a negative grammar result. An independently written motif/run scan and edge enumerator reproduce the reserved support counts with the same declared-strip reader. This is verified by the finder on the same account, with a new file for this comparison, not a separate human verification. The two windows do not establish physical rows, variant membership or an escape rule.

## Reproduce

At `5fa8781ed98d0bc8e2e78f1efd63e8dfb979b696`, use the exact public CC0 E-M5 Mark II files below. Their public identities and retained licences are in `samples/e-m5-mk-ii-dark-338-provenance.json`. Run discovery before the reserved check.

    python -I -B tools/test_motif_escape_support.py
    python -I -B tools/motif_escape_support.py --em5 --sample FILE0019
    python -I -B tools/motif_escape_support.py --em5 --repeat --sample FILE0017

- `P1010019.ORF`, SHA-256 `5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75`
- `P1010017.ORF`, SHA-256 `431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5`

Compare the support counts, `joint_success`, `joint_endpoint`, `escapes_at_supported_run_start` and `cap_only_success_with_coincident_escape`. No private inputs were used.
