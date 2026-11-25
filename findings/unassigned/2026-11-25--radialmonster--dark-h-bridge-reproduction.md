# Fixed dark-field H bridges do not consistently exceed block controls

Author: @radialmonster
Verified by: @radialmonster
Lead: #1019
Variant: unassigned
Builds on: #31, #961, #972, #1015

## Claim

The fixed OM-3 H bridge comparison reproduces its file-specific split. Both recorded-ISO-200 darks score below both block shuffles, while all four recorded-ISO-800 darks score above both. The predeclared all-six criterion fails. This is a comparison under the fixed candidate field and coordinates, not evidence for a physical predictor or ISO causation.

## Original evidence

Lead #1019 froze the procedure on #31 and used `tools/value_field_order_bridge.py` at `836299f4a465bd121ba956940c3fa5305520c77f`. The #972 candidate field, adjacent partner, both-word omission rule, parser and nominal rectangle are unchanged. For each complete H chain at lag two, let P_j be the jth residual prefix sum and n the chain length. Bridge values z_j=n·P_j−j·P_n remove uniform drift, and u_j=n·z_j−sum(z) centers the bridge exactly. No initial reconstruction seed enters. Compare r and r+2 in the same column parity at fixed zero horizontal shift, pooling the exact cross sum and both energies before normalization. The two controls shuffle intact 32-residual blocks within each chain, keeping the short terminal remainder unchanged and using seeds 1 and 2 reset per file.

There are 1156 complete row-parity pairs and 2994040 paired values in every original lane. Per capture the 3004400 eligible values, no omissions, and exact sum match #972. Both ISO-200 originals are in [−0.165072,−0.158755] at six decimals, and all four ISO-800 originals in [+0.031348,+0.039397]. All exact ranking comparisons are recorded in #1019.

## Verification

The complete discovery aggregate matched a new post-lead run at 19:27:52 UTC on 2026-11-25, before the six reserved E-M5 Mark II darks were opened for this measurement. All twelve public captures passed the retained CC0 record and whole-file hash gates. The second body is new to this test, not unseen by the project. It cannot rescue the original failed all-six criterion.

| E-M5 Mark II capture | Declared ISO | Original r | Block seed 1 | Block seed 2 | Original above both |
| --- | ---: | ---: | ---: | ---: | --- |
| P1010009.ORF | 200 | -0.164334021 | -0.009379143 | +0.011267344 | No |
| P1010011.ORF | 200 | -0.183506591 | -0.028898001 | -0.008256164 | No |
| P1010013.ORF | 200 | -0.143053751 | -0.006084907 | -0.024057172 | No |
| P1010017.ORF | 800 | +0.024195696 | -0.001568437 | -0.001294855 | Yes |
| P1010018.ORF | 800 | +0.002478012 | +0.007518936 | +0.000305325 | No |
| P1010019.ORF | 800 | +0.011837316 | +0.002169583 | +0.014622854 | No |

Only one of six reserved originals exceeds both controls. Each of the three ISO-200 originals is below both, but the four-of-four ISO-800 result on OM-3 does not extend to the E-M5 Mark II ISO-800 group. Every reserved file has 2668000 eligible values, with no omissions and field support and exact sums matching #972. All lanes score 1156 complete row-parity pairs and 2658800 paired values. A separate bridge and block-shuffle implementation, sharing the field parser and strip selector, exactly matches all 18 reserved lane cross sums, energies and support counts.

This is self-verification by the finder. The paired nominal rows overlap and the two control permutations do not calibrate significance. The test assigns no physical correspondence, predictor, bit depth or value map. V was not scored.

## Reproduce

At `836299f4a465bd121ba956940c3fa5305520c77f` use the public CC0 names and full hashes from #972 and the pinned `samples/om3-flat-338-provenance.json` and `samples/e-m5-mk-ii-dark-338-provenance.json` records. Supply matching paths in the frozen order. The tool checks the full hash before parsing.

    python -I -B tools/test_value_field_order_bridge.py
    python -I -B tools/value_field_order_bridge.py --sample PA200010.ORF FILE0010 --sample PA200011.ORF FILE0011 --sample PA200012.ORF FILE0012 --sample PA200013.ORF FILE0013 --sample PA200014.ORF FILE0014 --sample PA200015.ORF FILE0015
    python -I -B tools/value_field_order_bridge.py --cohort repeat --sample P1010009.ORF FILE0009 --sample P1010011.ORF FILE0011 --sample P1010013.ORF FILE0013 --sample P1010017.ORF FILE0017 --sample P1010018.ORF FILE0018 --sample P1010019.ORF FILE0019

Compare `result.lanes` and `result.decision`, retaining exact moments for ordering and using rounded r only for display. No private files were used.
