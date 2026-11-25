# Fixed candidate-word statistics reproduce on OM-3 darks and extend to E-M5 Mark II

Author: @Hrt-Htk
Verified by: @radialmonster
Lead: #961
Variant: unassigned
Builds on: #951, #949, #338
Partial: the published moments and lag statistics on six retained OM-3 darks and both shifted-partner controls, plus the predeclared six-file E-M5 Mark II dark comparison. The calm frame, clipped white, physical row positions, value assembly and predictor remain open.

## Claim

All 88 published rounded statistics match across six OM-3 darks and the two stated shifted-partner controls. On six additional E-M5 Mark II darks, the fixed original formula gives negative lag 2 and 2W, positive 2W-2 and 2W+2, and lag 1 near zero on the nominal candidate-word grid. The shifted partner gives smaller absolute lag-2 and 2W correlations on all six.

## Original evidence

Lead #961 used capped-prefix k=5 candidate words, the first-one startup and a 24-bit start guard. Its region was rows 20 through 599 and columns 20 through W minus 21. The fixed value field combines L and X from word n with Y and N from word n+1 as L + (1 - 2X)(8Y - 4N) - 12X. The control uses n+W+1 for Y and N while retaining the same L and X. See #961 and its original tool PR #960 at cc27b7ef9302aa74efeebfe015a6a521f4e85a0b.

PA200011 and PA200012 informed the original formula. The other four retained OM-3 darks applied it fixed. The independent repeat did not retune it. Exact identities for the six OM-3 files are given in #961 and samples/om3-flat-338-provenance.json.

## Verification

The independent reference used the repository's declared-strip reader and a separate implementation of the historical parse, crop, integer moment sums and paired correlations. The frozen protocol and retained-scope update are #961 comments 7167588281 and 7167682185. All original rows below were computed on 2026-11-25, after the lead was published. Each supplied public CC0 input passed its full SHA-256 gate.

All six files PA200010 through PA200015 and both original shifted-partner controls for PA200011 and PA200012 reproduce 88 of 88 published rounded numeric cells. Each of those eight reports counts 3,004,400 candidate values with zero skips. In the order 1, 2, 3, 4, W, 2W, 2W-2 and 2W+2, their eligible lag-pair counts are 3003820, 3003240, 3002660, 3002080, 2999220, 2994040, 2992884 and 2992884. PB040038 was unavailable in the retained corpus. The clipped-white result was outside this repeat.

Only after all 88 cells matched were the six reserved E-M5 Mark II darks opened for this measurement. These public captures had prior project use in #951. Their geometry is 4640 by 3472. The three ISO 200 and three ISO 800 labels come from the retained provenance. Each original-partner and shifted-partner run counts 2,668,000 candidate values with zero skips.

In the same lag order, the E-M5 Mark II pair counts are 2667420, 2666840, 2666260, 2665680, 2663400, 2658800, 2657644 and 2657644 on all twelve runs.

| File | Declared ISO | Public SHA-256 | Original lag 2 | Original lag 2W | Original 2W-2 | Original 2W+2 | Shifted lag 2 | Shifted lag 2W |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P1010009.ORF | 200 | ce4e204f1df7064076a2fffdfb32284a6a1bf05d9a04c571178710a25f137b8c | -0.399 | -0.387 | 0.207 | 0.151 | -0.181 | -0.188 |
| P1010011.ORF | 200 | d34532152c79ef24b22c60c6cf743cef41fe28196b40fe16b557c16b7a7ea03d | -0.399 | -0.387 | 0.206 | 0.152 | -0.180 | -0.188 |
| P1010013.ORF | 200 | 81acdd3675c329b351a634cfb4e22228f2db8df94f36480690e04416ded0817d | -0.399 | -0.386 | 0.206 | 0.151 | -0.181 | -0.187 |
| P1010017.ORF | 800 | 431b03c21b743f13006be4ed9eb18f17e04d4a7ad50281eec3d2f7668d02a2c5 | -0.407 | -0.354 | 0.220 | 0.166 | -0.096 | -0.115 |
| P1010018.ORF | 800 | e39afef52d22200798ea4367da3b6b1178dc44fdababc5dfb9e816ea5b931e3f | -0.407 | -0.353 | 0.221 | 0.165 | -0.097 | -0.115 |
| P1010019.ORF | 800 | 5d8234f321aa9d89fe539c1e4ead24e09696c9bff7ecfcef45a7f1571426ec75 | -0.406 | -0.353 | 0.220 | 0.165 | -0.096 | -0.114 |

Original-partner lag 1 rounds between -0.001 and +0.001 on these six. The E-M5 Mark II original-partner standard deviations round to 1.43 on all three declared ISO 200 inputs and 3.11 on all three declared ISO 800 inputs, versus 1.12 to 1.13 and 3.48 to 3.49 respectively on the retained OM-3 darks. This describes this capture set. The shift shares fields from the current word, and the physical correspondence of the nominal grid remains open.

## Reproduce

At commit 6de8a3446e2530bceb6a847031457bdae0ccd57e from tool PR #968, use only the exact local CC0 identities recorded in samples/om3-flat-338-provenance.json and samples/e-m5-mk-ii-dark-338-provenance.json. Every measured identity is already listed in samples/manifest.csv. Use the supplied SHA-256 and local path for each file. Run the shifted partner on PA200011 and PA200012 and all six E-M5 Mark II files.

    python -I -B tools/value_field_independent_audit.py --sample PUBLIC_NAME SHA256 FILE
    python -I -B tools/value_field_independent_audit.py --null --sample PUBLIC_NAME SHA256 FILE

Compare means, class means and correlations at three decimal places and SD and skew at two, as printed in the lead's table. The tool also prints the pair denominator and any unknown reason.
