# Common candidate row phase in fixed public windows

Author: @radialmonster
Verified by: @radialmonster
Lead: #792
Variant: unassigned
Builds on: #31, #777, #788

## Claim
Under the fixed signed_digit-minus-3, B16, stride-2 candidate and the conditional literal one-token-per-site same-row model, four predeclared 4096-candidate windows on public id 1993 each have a nonempty phase set, but their width-periodic per-file intersection is empty after the third window. This rejects only that fixed conditional common-phase family on the defined windows. Four 5283 windows contain q>=17 candidates and are unknown, not passes or failures. Both files/windows were previously studied; c=3 was selected from exposed #788 results.

## Original evidence
The finder used `tools/common_row_phase.py` at `43ea1f54b555990e188fb9b4c931ad00ce40b7e2` on 2026-11-17 UTC, following the frozen #31 protocol in comment 6958244755. Inputs were public CC0 raw.pixls.us id 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`, and id 5283, `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`. Original results are the first eight rows below.

## Verification
Fresh post-lead runs on 2026-11-17 UTC reproduced both discovery reports byte-for-byte and measured the same fixed windows on public CC0 id 1995, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`, and id 6344, `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512`. Retained CC0 inventory and manifest match local hashes. All inputs were previously studied; same-account verification is not independent-human verification or evidence of independent captures.

A separately written literal-bit parser and feasibility reference matched the results; it shares the TIFF locator and human account. Its conversion was capped at the primary endpoint, with the parsed count and endpoint independently checked, and it does not reproduce timeout runtimes. Fresh original-file reports matched discovery byte-for-byte; all four verification files received separately run independent reference checks.

All 16 windows returned 4096 candidates without timeout. On 1993 and 1995 the per-file intersection becomes empty; on 6344 it remains nonempty at 268 phases after four defined windows, a necessary-condition survivor only. All four 5283 windows are escape-unknown, leaving all 5220 phases possible and an undefined conclusion, not a pass. P0/P1 are maximal feasible lane-prefix lengths, S0/S1 earliest feasible suffix starts, and inclusive cut bounds are before-token positions. A whole-window feasible result allows every phase. Cumulative counts intersect only defined windows within the same file; they are not shared across files.

File | width | start | escapes | status | P0/P1 | S0/S1 | cut lo/hi | whole feasible | phases | cumulative
---: | ---: | ---: | ---: | :--- | :--- | :--- | :--- | :--- | ---: | ---:
1993 | 5240 | 262144 | 0 | ok | 1652/2048 | 70/0 | 139/3304 | no | 3166 | 3166
1993 | 5240 | 524288 | 0 | ok | 958/2048 | 458/0 | 915/1916 | no | 1002 | 1002
1993 | 5240 | 1048576 | 0 | ok | 1447/1386 | 936/495 | 1871/2773 | no | 903 | 0
1993 | 5240 | 1572864 | 0 | ok | 1114/1561 | 780/910 | 1820/2228 | no | 409 | 0
5283 | 5220 | 262144 | 4 | escape | unknown | unknown | unknown | unknown | unknown | 5220
5283 | 5220 | 524288 | 5 | escape | unknown | unknown | unknown | unknown | unknown | 5220
5283 | 5220 | 1048576 | 9 | escape | unknown | unknown | unknown | unknown | unknown | 5220
5283 | 5220 | 1572864 | 4 | escape | unknown | unknown | unknown | unknown | unknown | 5220
1995 | 5240 | 262144 | 0 | ok | 2048/2048 | 0/0 | 0/4096 | yes | 5240 | 5240
1995 | 5240 | 524288 | 0 | ok | 1206/1582 | 929/101 | 1857/2412 | no | 556 | 556
1995 | 5240 | 1048576 | 0 | ok | 2048/2048 | 0/0 | 0/4096 | yes | 5240 | 556
1995 | 5240 | 1572864 | 0 | ok | 1693/1394 | 599/1026 | 2052/2789 | no | 738 | 0
6344 | 8200 | 262144 | 0 | ok | 1737/1341 | 388/265 | 775/2683 | no | 1909 | 1909
6344 | 8200 | 524288 | 0 | ok | 2048/1135 | 0/338 | 676/2271 | no | 1596 | 1241
6344 | 8200 | 1048576 | 0 | ok | 1383/1185 | 745/1052 | 2104/2371 | no | 268 | 268
6344 | 8200 | 1572864 | 0 | ok | 2048/1829 | 0/905 | 1810/3659 | no | 1850 | 268

The fixed map is `signed_digit(s)=4*(s>>3)+(s&3)-8*((s>>2)&1)`, residual `e=signed_digit(s)-3`. Each lane segment has two unrestricted integer starting values in [0,65535], ignores its first two residuals, and thereafter obeys `x[i]=2*x[i-1]-x[i-2]+e[i]`, without wrap, clamp or adaptation. Candidate parsing is MSB-first q zeros, a stop bit and five suffix bits from payload bit zero, with no added escape skip. The conditional model assumes exactly one candidate per site and rows of even width W>4096. A reset before local token b cuts the two parity lanes after (b+1)//2 and b//2 values; exact integer feasible prefix/suffix limits give the shared cut interval. Phase sets are taken modulo W and intersected separately for each file. Free segment/window anchors need not agree outside the tested window; a survivor remains only a necessary condition. Existing token-count results already challenge the assumed one-token-per-site mapping. No physical framing, row, predictor, value, codec, significance or population claim follows.

## Reproduce
After reading the tool/imports and matching each local input to the retained CC0 record, run from the named commit for each listed sample under an external hard 600-second per-file guard:

    python -I -B tools/common_row_phase.py --sample ID PUBLIC_NAME PATH_TO_CC0_FILE

Cooperative limits are 20 seconds per window and 570 seconds per file. Retain every escape, shortfall, timeout, partial known rejection and failure; do not replace inputs or windows.
