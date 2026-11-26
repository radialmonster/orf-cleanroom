# Independent reproduction of the fixed E-M5 II escape comparison

Author: @radialmonster
Verified by: @mszyndel
Lead: #1007
Variant: unassigned
Reproduces: 2026-11-25--radialmonster--em5-motif-escape-reproduction
Builds on: #197, #951, #972, #990

## Claim

The published fixed-window P1010019 aggregate reproduces exactly: six
run-bearing edges, six completed capped escapes, no escape at a qualifying
run start, one literal-only endpoint-and-word-count success and no capped-only
success meeting the coincident-escape criterion. P1010017 reproduces zero
run-bearing edges. Additional P1010018 also has no qualifying edges, so it
supplies no grammar-comparison denominator. These results do not identify
physical rows, an escape rule or the camera's grammar.

## Original evidence

Lead #1007 and the reproduced finding by @radialmonster use
`tools/motif_escape_support.py` at
`5fa8781ed98d0bc8e2e78f1efd63e8dfb979b696`. For width 4640, use payload
bits [17268280,33422440), pitch 27852 and tolerance 278. Enumerate all
complete six-field literal motifs and all directed near-pitch edges. An
interior qualifies only if it contains a maximal run of at least twelve
zeros and both flanking ones, after the source's 48 motif bits and before
the target motif. From that fixed start, require exact endpoint and 4634
complete words under literal or capped k=5. Capped-only support additionally
requires a completed escape at a qualifying run start on that same edge.

Input identity qualification: the issue's P1010019 SHA-256 ends
`d7a4a808dd0a`, which differs from the merged finding, pinned tool and
retained public provenance. This run uses the latter's correct full hash
below. The erroneous identity as written is not reproduced; the original
finding's identity and measured counts are reproduced. No existing finding
is corrected or edited.

## Verification

New independent-person run by @mszyndel on 2026-11-26 after checking the
current issue safety scan and reading the complete executable source/imports.
The original measurement and import chain are unchanged from the pinned
source. Six generated tests pass before camera measurement: independent
run census, maximality/flanks, unaligned runs, aligned and truncated escapes,
a known capped-only same-edge positive, and no-support parser exclusion.

Both original invocations run freshly in source order. All reported counts
match the published finding. On P1010019, paired endpoint masks are
11:3/00:3, and endpoint-plus-count masks are 10:1/00:5 (literal/capped
order). Both traversals overrun at the suffix on the remaining three edges.
Each of the six supported edges completes one capped escape, but none starts
at a qualifying run. Thus completing an escape somewhere on an edge does
not satisfy the criterion.

Before its outcomes, predeclare new-to-finding public P1010018 under the
identical raw-bit window and rule. A minimal explicit identity selector in
`tools/motif_escape_support.py` at `5c24325` (#1044) adds that hash-pinned
input; the measurement function is unchanged. Complete original reports
also repeat exactly under the extended CLI. This uses the original camera
measurement algorithm; it is a different-person reproduction, not independent
software. All three inputs had earlier research exposure, so the extension
is procedural rather than blind or independent-session validation.

| Public E-M5 II capture | SHA-256 | Motifs | Near-pitch edges | Qualifying window runs | Run-bearing edges | Both exact endpoint | Literal-only endpoint and count | Capped-only success with qualifying escape |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| P1010019.ORF | `5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75` | 907 | 1419 | 2 | 6 | 3 | 1 | 0 |
| P1010017.ORF | `431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5` | 906 | 1406 | 0 | 0 | Not scored | Not scored | Not scored |
| P1010018.ORF | `e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f` | 931 | 1501 | 0 | 0 | Not scored | Not scored | Not scored |

On P1010017 and P1010018 neither grammar runs; all grammar-result maps are
empty. Their zero supported edges are measured support outcomes, not negative
grammar results. Edges can share motifs and runs. The nominal pitch and raw
motif do not establish physical row boundaries or an independently anchored
escape interval. The original finite comparison does not favor capped,
without proving literal k=5 or rejecting capped elsewhere.

All full hashes matched retained CC0 provenance before/after. Public owner
declarations and source URLs are in
`samples/e-m5-mk-ii-dark-338-provenance.json`. Existing personal manifest rows
cover all three; no new rows, raw files, images, pixel data or private inputs
are included.

## Reproduce

Original source at `5fa8781ed98d0bc8e2e78f1efd63e8dfb979b696`, using only
the exact public hashes above:

```
python -I -B tools/test_motif_escape_support.py
python -I -B tools/motif_escape_support.py --em5 --sample FILE0019
python -I -B tools/motif_escape_support.py --em5 --repeat --sample FILE0017
```

At `5c24325`, repeat both original commands and add:

```
python -I -B tools/motif_escape_support.py --em5 --em5-file P1010018.ORF --sample FILE0018
```

Compare the complete JSON reports, including run-bearing-edge denominators,
joint endpoint/count masks, completed escapes, supported-run coincidence and
the capped-only criterion. Independent physical anchors and camera syntax
remain open on #197; no compressed decode step follows from this reproduction.
