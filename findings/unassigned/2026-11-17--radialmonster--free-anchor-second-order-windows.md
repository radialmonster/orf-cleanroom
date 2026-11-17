# Free-anchor second-order feasibility in fixed public windows

Author: @radialmonster
Verified by: @radialmonster
Lead: #777
Variant: unassigned
Builds on: #31

## Claim
Under the specified free-anchor second-order candidate family and literal one-token-per-site same-row hypothesis, four escape-free 4096-candidate windows on public E-M1 Mark II id 1993 have mixed outcomes. At B16, signed_digit requires more than two segments for d=1 and d=2 in all four; signed_low3 meets the permissive two-segment bound in one d=1 window and three d=2 windows. Every B12 family exceeds the bound in all four. Four predeclared windows on OM-1 id 5283 contain q>=17 candidates, so all 32 family outcomes are undefined; they are neither failures nor survivors. These are bounded conditional observations, not a general exclusion of predictors or identification of a codec.

## Original evidence
The finder ran `tools/free_anchor_second_order.py` at `c60a0ca81d9c2b4da94f3171553f9cc0fac0afbe` on 2026-11-17 UTC after the protocol in #31 comment 6955575141. The public CC0 inputs were raw.pixls.us id 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`, and id 5283, `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`. Their results are the first eight rows below.

## Verification
Fresh post-lead runs on 2026-11-17 UTC exactly reproduced both discovery reports and added the predeclared public CC0 id 1995, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`, and id 6344, `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512`. Retained CC0 inventory and manifest rows match the local hashes. All four files were previously studied; same-account verification is not independent-human verification or evidence of independent captures. A separately written literal-bit parser and binary-search feasibility reference matched every window and family; it shared the TIFF locator and human account.

All 16 windows returned 4096 candidates without timeout. Each cell gives the minimum feasible segment count for d=1 or independent parity-lane counts for d=2. `undefined` means the window contains an escape; every family in that window is undefined and is not a failure or survival. The first four family columns are B16 primary; the last four are B12 secondary. In a defined cell, the permissive bound passes exactly when every lane count is at most two.

File | Start | Escapes | B16 digit d1 | B16 digit d2 | B16 low3 d1 | B16 low3 d2 | B12 digit d1 | B12 digit d2 | B12 low3 d1 | B12 low3 d2
---: | ---: | ---: | ---: | :--- | ---: | :--- | ---: | :--- | ---: | :---
1993 | 262144 | 0 | 10 | 5,5 | 2 | 1,1 | 39 | 19,19 | 7 | 4,4
1993 | 524288 | 0 | 10 | 6,5 | 5 | 3,3 | 40 | 21,20 | 15 | 9,8
1993 | 1048576 | 0 | 10 | 5,5 | 3 | 2,2 | 38 | 19,19 | 9 | 5,5
1993 | 1572864 | 0 | 10 | 5,5 | 3 | 2,2 | 38 | 19,20 | 12 | 6,7
5283 | 262144 | 4 | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined
5283 | 524288 | 5 | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined
5283 | 1048576 | 9 | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined
5283 | 1572864 | 4 | undefined | undefined | undefined | undefined | undefined | undefined | undefined | undefined
1995 | 262144 | 0 | 10 | 5,5 | 1 | 1,1 | 39 | 20,20 | 5 | 3,3
1995 | 524288 | 0 | 10 | 5,5 | 1 | 1,1 | 38 | 19,20 | 4 | 2,4
1995 | 1048576 | 0 | 10 | 5,5 | 2 | 1,1 | 38 | 20,19 | 7 | 4,4
1995 | 1572864 | 0 | 10 | 5,5 | 2 | 1,1 | 38 | 19,19 | 5 | 3,3
6344 | 262144 | 0 | 10 | 6,5 | 3 | 2,2 | 40 | 21,20 | 13 | 6,6
6344 | 524288 | 0 | 10 | 6,6 | 4 | 2,1 | 40 | 20,20 | 13 | 6,6
6344 | 1048576 | 0 | 11 | 6,6 | 4 | 2,2 | 41 | 21,21 | 14 | 7,7
6344 | 1572864 | 0 | 10 | 5,5 | 4 | 2,2 | 39 | 20,20 | 16 | 8,8

The parse starts at payload bit zero, MSB-first: q zeros, a stop bit and five suffix bits, without extra escape skip. The signed_digit mapping is `4*(s>>3)+(s&3)-8*((s>>2)&1)`; signed_low3 is `(s&7)-8` if `s&4`, otherwise `s&7`. For each lane segment, two free integer starting values lie in [0,2**B-1], its first two residuals are ignored, and subsequent values obey `x[i]=2*x[i-1]-x[i-2]+e[i]`, without wrap, clamp or adaptation. Exact integer slope intervals and greedy maximal feasible prefixes yield the minimum count. d=2 lanes choose breaks independently, possibly incompatibly; a passing cell is only a permissive necessary condition. Under a literal one-token-per-site same-row model and width greater than 4096, at most one row reset crosses a window. Existing token-count evidence already challenges that model. No physical framing, row, value, predictor or codec is established; other predictor/mapping families and significance remain open.

## Reproduce
After reading the tool and imports and matching local input hashes to retained CC0 records, run at the named source commit for each listed sample, under a hard 600-second per-file guard:

    python -I -B tools/free_anchor_second_order.py --sample ID PUBLIC_NAME PATH_TO_CC0_FILE

The tool checks a cooperative 120-second family deadline; report escaped, short, timed-out and failed cases rather than replacing windows or files.
