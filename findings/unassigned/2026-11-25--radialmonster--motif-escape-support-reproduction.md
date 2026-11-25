# Neither fixed E-M1 Mark II motif window supplies an escape-support edge

Author: @radialmonster
Verified by: @radialmonster
Lead: #990
Variant: unassigned
Builds on: #197, #951, #976, #988

## Claim

The original fixed E-M1 Mark II 1993 window again has 443 literal motifs and 147 directed near-pitch edges, with no qualifying zero run. The predeclared 1997 window has 459 motifs and 33 directed near-pitch edges, also with no qualifying run. Neither window supplies an interior on which to compare the two candidate escape rules.

## Original evidence

Lead #990 used the method frozen on #197 and `tools/motif_escape_support.py` at `cc1894a9509bf07ad4e52d201aed1035e5f7c448`. The selector enumerates every complete literal six-field motif, then every forward edge within the inclusive pitch tolerance, without choosing a path. A support run is a maximal run of at least twelve zero bits with a one on each side, both inside the tested interval. An edge is eligible for traversal only if its interior, after removing the source motif and before the target motif, contains that entire context.

The input was public raw.pixls.us CC0 ID 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`. The original aggregate was 443 motifs, 147 edges, zero flanked runs in the full window and zero edges with a supported interior.

## Verification

After #990 was posted on 2026-11-25, a fresh 1993 invocation matched the complete saved discovery aggregate at 18:03:51 UTC. Only after that check did the unchanged protocol use reserved public raw.pixls.us CC0 ID 1997, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`. Both files passed the full hash gate. The declared width is 5240 for each. The half-open window is [40,12580840), the pitch is 31452, the tolerance is 314 and the unexercised target is W−6 = 5234 candidate words.

| Public ID | Literal motifs | Directed near-pitch edges | Flanked runs in window | Edges with a flanked run |
| --- | ---: | ---: | ---: | ---: |
| 1993 | 443 | 147 | 0 | 0 |
| 1997 | 459 | 33 | 0 | 0 |

An independently written bit scan and exhaustive edge enumeration recomputed the 1997 counts, sharing the declared-strip reader. This checks the selector and support counts without providing a second human verifier.

Both return `no_run_bearing_edge`; the literal, capped and joint traversal results are empty. There is no grammar-result denominator, not a pair of zero success rates. In particular the #603 startup example has its preceding marker outside this window. No result here establishes physical rows, word boundaries, variant membership, absence of escapes in the encoding, or which candidate rule applies. This is self-verification on the same account, with an additional public file.

## Reproduce

At `cc1894a9509bf07ad4e52d201aed1035e5f7c448` use the two exact public CC0 inputs above. Check the original result before doing the extension. No private inputs were used.

    python -I -B tools/test_motif_escape_support.py
    python -I -B tools/motif_escape_support.py --sample FILE1993
    python -I -B tools/motif_escape_support.py --repeat --sample FILE1997

Compare `motifs`, `eligible_edges`, `window_flanked_runs`, `run_bearing_edges`, the empty traversal results and the explicit no-support status.
