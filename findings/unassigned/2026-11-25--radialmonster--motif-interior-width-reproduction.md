# Fixed k=5 exact interiors reproduce on OM-3 and extend to E-M5 Mark II darks

Author: @radialmonster
Verified by: @radialmonster
Lead: #976
Variant: unassigned
Builds on: #339, #951, #956, #868

## Claim

The original comparison reproduces: both k=5 candidates finish at the imposed endpoint with exactly W−6 words on 240 of 241 selected OM-3 dark intervals. Neither k=4 candidate reaches an endpoint. The clipped-white capture has zero mutually unique intervals, so its grammar comparison is undefined.

The unchanged rule gives 233/234 exact k=5 results on two reserved OM-3 darks and 719/719 on six reserved E-M5 Mark II darks. Neither k=4 candidate reaches any of these additional endpoints. The capped and literal versions agree throughout this test and the capped grammars complete no escapes.

## Original evidence

Lead #976 froze the all-bit-alignment six-field literal motif, near-pitch distance P = 6W+12 with tolerance max(64, floor(P/100)), and mutual-unique successor/predecessor selection. It excludes the two motifs and starts candidates at the first bit after the left motif. The test cuts before the right motif and requires W−6 full words ending exactly there. Both k values are tested with literal stop-1 and with the fixed 12-zero/12-raw-bit escape alternative. The selector never uses a candidate parse. See #976 and tool PR #975.

## Verification

On 2026-11-25 after the lead was posted and scanned, a fresh run reproduced the complete original aggregate. All selected intervals, per-grammar totals, terminal reasons and paired success masks matched. The saved equality check completed at 17:14:59 UTC, before the two reserved cohorts were opened. All eleven retained public CC0 inputs passed their full hash gates; all three invocations exited zero without stderr.

| Original file | SHA-256 | Motifs | Near-pitch directed edges | Mutually unique | k=5 exact endpoint and count |
| --- | --- | ---: | ---: | ---: | ---: |
| PA210010.ORF | `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e` | 791 | 1568 | 0 | undefined |
| PA200010.ORF | `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4` | 630 | 988 | 129 | 129 |
| PA200012.ORF | `c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7` | 633 | 1009 | 112 | 111 |

The original paired masks, in literal k4, literal k5, capped k4, capped k5 order, are 0101 on 129 PA200010 edges and on 111 PA200012 edges. One PA200012 interval gives 0000, with a stop overrun for both k=5 candidates. Both k=4 versions repeat their original suffix/stop overrun counts on PA200010 (87/42) and PA200012 (76/36).

| Reserved file | SHA-256 | Motifs | Near-pitch directed edges | Mutually unique | k=5 exact endpoint and count |
| --- | --- | ---: | ---: | ---: | ---: |
| PA200011.ORF | `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3` | 641 | 1025 | 119 | 119 |
| PA200015.ORF | `84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278` | 601 | 913 | 115 | 114 |
| P1010009.ORF | `ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c` | 642 | 1035 | 120 | 120 |
| P1010011.ORF | `d34532152c79ef24b22c60c6cf743cef41fe28196b40fe16b557c16b7a7ea03d` | 616 | 966 | 139 | 139 |
| P1010013.ORF | `81acdd3675c329b351a634cfb4e22228f2db8df94f36480690e04416ded0817d` | 645 | 1053 | 120 | 120 |
| P1010017.ORF | `431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5` | 632 | 991 | 105 | 105 |
| P1010018.ORF | `e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f` | 634 | 1021 | 114 | 114 |
| P1010019.ORF | `5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75` | 624 | 976 | 121 | 121 |

All selected reserved edges have mask 0101 except one PA200015 edge with mask 0000; that interval has a suffix overrun under both k=5 candidates. The OM-3 inputs have W=5220 and thus target W−6=5214. For E-M5 Mark II, W=4640, target 4634. The pitch and search window follow the recorded width in each case. The complete k=5 target and endpoint counts agree in every row. These captures had prior project use, but the reserved measurements use new files for this comparison.

A separate implementation of the motif scan, exhaustive edge selection and bit cursor reproduced the reported aggregates using the same declared-strip reader. This is verification under the finder's account, not independent-human verification. The selected intervals are a subset defined by a conditional literal anchor and do not identify physical rows, full bitstream syntax, a value map, or a predictor. The escape rule and white capture remain undecided.

## Reproduce

Use the pinned source at `0b6e1dfa000d59d8fbf08d0c02ef20b7acaed688` and the public input records in `samples/om3-flat-338-provenance.json` and `samples/e-m5-mk-ii-dark-338-provenance.json`. All measured identities already have manifest rows. Use only the recorded matching hashes.

    python -I -B tools/test_motif_interior_probe.py
    python -I -B tools/motif_interior_probe.py --sample PA210010.ORF WHITE --sample PA200010.ORF DARK200 --sample PA200012.ORF DARK800
    python -I -B tools/motif_interior_probe.py --cohort om3-repeat --sample PA200011.ORF FILE011 --sample PA200015.ORF FILE015
    python -I -B tools/motif_interior_probe.py --cohort em5-repeat --sample P1010009.ORF FILE0009 --sample P1010011.ORF FILE0011 --sample P1010013.ORF FILE0013 --sample P1010017.ORF FILE0017 --sample P1010018.ORF FILE0018 --sample P1010019.ORF FILE0019

Compare each edge denominator, paired mask, exact endpoint and words count, and escape totals. A zero selected-edge count is undefined for a grammar comparison, not a rejection. No private inputs were used.
