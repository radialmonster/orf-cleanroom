# Independent reproduction of packed-12 layouts and conformance

Author: @radialmonster
Verified by: @mszyndel
Lead: #69
Variant: V0
Reproduces: 2026-10-19--radialmonster--packed-12-msb-two-values-per-three-bytes
Corrects: 2026-10-19--radialmonster--packed-12-msb-two-values-per-three-bytes
Builds on: #28, #75, #77

## Claim

The nine public packed-12 files reproduce the declared byte-layout families: two MSB-first 12-bit values per three bytes, plain on six inputs and with bytes reversed inside each four-byte word on 1432/2431/792. All original default/wider family margins, wider true-stride and one-byte-offset values and the three stated low-two-bit shares reproduce at printed precision. The predeclared larger window retains the same families on all nine. Full reference conformance rows/hashes and exact ends match on all nine, preserving declared strip gaps and the six known two-field layouts.

This also corrects only the original finding's approximate window-coverage multiplier: 8*32*2400 = 614,400 values per file, versus 3*16*1200 = 57,600, a ratio of 32/3 (about 10.67), not about five. The original numerical comparison results and packing claims reproduce; no algorithm or pair order is changed.

Physical pair order, CFA interpretation, the cause of XZ-2's low-two-bit pattern and general body/firmware/layout selectors remain unresolved. A reference hash pins the emitted order, not its physical correctness.

## Original evidence

Lead #69 and the reproduced finding were authored by @radialmonster. The exact original snapshot is abe5c10fefe9952950fa0ec4f2a357d62c8a2ada, with tools/orf_v0_unpack.py last changed in 0785fcb. The unpack tool SHA-256 is `13cf4592ca512510fe7ef20cbd1798b5b69cc343db808e6e6763336fe4fc2ca1`; its tools/orf_signature.py import is `b02e3caab8b3a735e7cb58613d4941de7f834c096bebc830680d308457a6ce71`. The lead used the default 3-band/16-row/1200-column window and the finding used 8 bands, 32 rows, 2400 columns.

Public raw.pixls.us identities matched retained verified CC0 records and existing manifest hashes:

- 1432: `Olympus - XZ-2 - 12bit (4:3).orf`, SHA-256 `675fefe7c9e99281783b987889d723b5f46692f5c20e19fed5e422c7c6d2636b`.
- 1799: `Olympus - C5060WZ - 12bit (4:3).ORF`, SHA-256 `3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd`.
- 2420: `Olympus - SP510UZ - 12bit (4:3).ORF`, SHA-256 `f0737d78bb2e588963a3d5038fab493cdff1c9c48475704de96d797bbb81e62a`.
- 2431: `Olympus - XZ-10 - 12bit (4:3).ORF`, SHA-256 `a25383acad9b5bb0bb404715e0957f2eb80aa1aaad6c448a71025c03cfa631be`.
- 3438: `Olympus - SP565UZ - 12bit (4:3).ORF`, SHA-256 `5088771f83ce08a001b44672e1dd9f013e603933c37ce1bfb7030a02abbe801c`.
- 5491: `Olympus - SP570UZ - 12bit (4:3).ORF`, SHA-256 `baab92391834076b427e406e98da79aaba48fb87243d6ccae60e08e299cfccf7`.
- 780: `Olympus - C7070WZ - 12bit (4:3).ORF`, SHA-256 `9d55506f9d6ee31d2d4c4b6df0dcd1d016d358b3e5eb4ed31edd7227dfefd5f8`.
- 792: `Olympus - SH-2 - 12bit (4:3).ORF`, SHA-256 `6e6b9b7dd9ded7c4b364b83116c817ca2d6daac15f2e9ef7796159b08c3288a1`.
- 8609: `Olympus - SP550UZ - 12bit (4:3).ORF`, SHA-256 `05f49918e1b1894c3abd2b5451b356f7a00adb1c8568abc5babff33fcade1bb2`.

## Verification

Fresh runs by @mszyndel on 2026-11-20 UTC followed the fixed plan in #69 comment 7046935312. The retained complete 104-file CC0 inventory contains exactly these nine recorded packed-12 inputs; the original finding used them all, so no unused applicable public file exists in that inventory. This is another contributor's reproduction with the same tools/captures, not a new-body, blind-cohort or independently implemented decoder test.

Byte-identical copies of the original source snapshot/import repeated both original commands, then applied the predeclared 12-band/32-row/2400-column extension (921,600 values per file). Pair-order output is retained literally; a family comparison removes only the printed -swap component. In particular, 5491 selects 12-msb-swap in the larger run, within the same plain MSB byte-layout family. It is not forced back to an unswapped order.

| ID | Family | Default margin | 8-band margin | 12-band margin | 8-band stride -1 / 0 / +1 |
|---|---|---|---|---|---|
| 1432 | w4-12-msb | 6.26 | 5.30 | 5.87 | 0.160 / 0.985 / 0.157 |
| 1799 | 12-msb | 2.81 | 3.19 | 2.91 | -0.003 / 0.891 / -0.001 |
| 2420 | 12-msb | 1.29 | 2.33 | 2.39 | 0.071 / 0.914 / 0.069 |
| 2431 | w4-12-msb | 10.95 | 11.61 | 11.54 | 0.110 / 0.994 / 0.109 |
| 3438 | 12-msb | 1.60 | 1.88 | 1.71 | 0.043 / 0.781 / 0.045 |
| 5491 | 12-msb | 1.26 | 1.68 | 1.70 | 0.029 / 0.588 / 0.028 |
| 780 | 12-msb | 1.66 | 1.96 | 1.93 | 0.048 / 0.918 / 0.049 |
| 792 | w4-12-msb | 6.49 | 5.02 | 5.03 | 0.100 / 0.941 / 0.090 |
| 8609 | 12-msb | 2.84 | 2.57 | 2.53 | 0.004 / 0.857 / -0.000 |

On the 8-band repeat, low-two-bits-zero shares reproduce 1.0000 on XZ-2 1432, 0.7068 on XZ-10 2431 and 0.2596 on SH-2 792. These are the stated windows, not a causal or whole-frame precision claim. The pair-order alternatives/weak preferences remain descriptive and do not settle physical order.

The historic window probe reads its file-offset windows from the first declared payload offset; it does not independently join strips across gaps or identify physical rows. Its values above reproduce that original measure. Whole-frame conformance instead uses the reference decoder's declared-strip reader and established two-field mapping, excluding physical gap bytes. At  f79157e (source code unchanged from 46345de1b93f6384616a362485f2e2b76bf9732e), every field of the nine corresponding samples/conformance-V0.csv rows matches, including exact ends, order, row layout, ranges and output hashes. Output SHA-256 uses the emitted uint16 values little-endian, row-major and unshifted:

- 1432: `a8cedb760320786303436515140aba5406a36598e9df841ac706c7b8ecf38a4d` (natural).
- 1799: `1e6a220bfa5fbdced0bc9acf6c62cecc3cf287ad3df527e3fe980f154534ab37` (two-field).
- 2420: `cfca8bfd4489355e98a9acd3ca40ba83e89b60267d5ef6197e9f14e758cd9f3d` (two-field).
- 2431: `96e57e497f18092664831bb4d9d11d1bdbc1d97f841d4c1e5be91fff464fe697` (natural).
- 3438: `8efdaba481cd470cde37b2db535a9d4439faa14db13f2e332363395d62b4efff` (two-field).
- 5491: `3ade5df7552bafd57992e27d06d98484de2e7866eb4de30e2286fcbc28dde77c` (two-field).
- 780: `3b0807cf04a79b9740e912702eb043dd738e442f39098f9e3584f712e05c51f5` (two-field).
- 792: `21fe65f6975d951b83aba92818339d915c9b76d927810d35b7f7f05fc5b89752` (natural).
- 8609: `75f2379b923a8df7a2ee8c60f75270aa820c5fb074cb91e7df3b328619fa2d45` (two-field).

All 36 per-input jobs exited zero, with no 300-second timeout. Layout stderr was empty and conformance emitted its normal zero-error summary. Input hashes matched before/after the runs. No decoded values, images or previews were saved. The window-coverage correction is arithmetic over the printed window sizes; the actual measured row/column dimensions are unchanged.

## Reproduce

Read the tool and import at abe5c10fefe9952950fa0ec4f2a357d62c8a2ada. Obtain the nine exact CC0 inputs through tools/pixls_samples.py, retaining licence records and matching by SHA-256. Replace FILES below with IDs 1432,1799,2420,2431,3438,5491,780,792,8609 in that order:

    python -I -B tools/orf_v0_unpack.py FILES
    python -I -B tools/orf_v0_unpack.py --bands 8 --rows 32 --cols 2400 FILES
    python -I -B tools/orf_v0_unpack.py --bands 12 --rows 32 --cols 2400 FILES

Read the candidate tables, literal chosen/pair-alternative lines, low2=0 shares and explicit stride-delta lines. For the coverage multiplier, a one-off arithmetic check is:

    python -I -B -c "print(8*32*2400,3*16*1200,(8*32*2400)/(3*16*1200))"

At 46345de1b93f6384616a362485f2e2b76bf9732e (the same reference code/conformance table used in this run):

    python -I -B tools/conformance.py --csv FILES

The local run used separate per-file invocations with 300-second budgets and retained stdout/stderr/exits. Match full conformance rows by input hash, without adding gap bytes, fitting a window or forcing a pair order. Preserve failures/timeouts as unknown with no replacement input. All numbers depend only on public CC0 inputs; no private result contributes. The original lead's CFA/body-firmware/low-bit-cause/pair-order/new-body questions remain open in the V0 gaps and docs follow-up.
