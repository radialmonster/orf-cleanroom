# Candidate stride depends on the selected prefix head and does not consistently transfer

Author: @radialmonster
Verified by: @radialmonster
Lead: #974
Variant: V1
Builds on: #144, #30, 2026-10-22--radialmonster--later-band-row-stride-drift

## Claim

Changing the tested head width changes the winning prefix candidate stride on eight of the nine public captures. All 45 selected prefix scores are positive, but the sign does not consistently persist when the stride is held fixed in later bands. This is sensitivity of one nominal candidate-token fold, not a measurement of physical rows, head length, or variant membership of any sample.

## Original evidence

Lead #974 froze the five heads 8, 16, 32, 64 and 128. Candidate rows use phase zero from payload bit zero and the q-zero/stop/five-bit candidate parser, capped at q=40 with no extra escape bits. It selects the highest descriptive standardized head-versus-rest q contrast from 1,201 strides W through W+1200 over nominal rows 0–299. It evaluates those winners, and each file's single head-32 winner, without refitting in nominal rows 1000–1299. The historical head-32 table matched on all nine inputs at its published precision.

All 45 prefix selections are positive. In the first later band, own-head winners give 23 positive and 22 negative scores. The fixed head-32 winners give 14 positive and 31 negative. The two sets score many of the same tokens, including identical settings, so the totals do not represent independent trials or calibrated p-values.

## Verification

The fresh nine-file run matched the complete discovery JSON at 18:12:09 UTC on 2026-11-25, after #974 was posted. All full SHA-256 hashes matched retained CC0 records. Only after the replay matched did verification score the predeclared wider band, nominal rows 2000–2299. Each input had the same selected single variable strip in both scanners, and the separate band scanner matched the original token count and exact bit endpoint at the original limit. On each file every new scoring interval started beyond both the original prefix and the first later band's scoring intervals, across the tested strides.

All 90 new profiles have 300 complete nominal rows and finite scores. Signs use the unrounded numerator. The five entries per cell correspond to heads 8, 16, 32, 64 and 128.

| Public ID | Rows 2000–2299, own prefix winner | Rows 2000–2299, fixed head-32 winner |
| --- | --- | --- |
| 1993 | + / + / + / + / + | + / + / + / + / + |
| 1995 | + / − / − / − / − | − / − / − / − / − |
| 1997 | + / − / − / − / − | − / − / − / − / − |
| 1998 | + / − / − / − / − | − / − / − / − / − |
| 6343 | + / + / + / + / + | + / + / + / + / + |
| 6344 | − / − / − / − / + | − / − / − / − / − |
| 6345 | − / − / + / + / − | + / + / + / + / + |
| 8549 | − / − / − / + / − | − / − / − / + / − |
| 5283 | + / + / − / + / − | + / + / − / − / − |

The new band has 20 positive and 25 negative own-winner scores, and 18 positive and 27 negative fixed-head-32 scores. Compared with rows 1000–1299, 19/45 and 20/45 signs change, respectively. A separate moment accumulator with the original scanner exactly matched all 20 new profiles on 6344 and 5283, including consumed bits, counts and scores.

This is same-account verification with wider, disjoint bands on previously studied files, not a new cohort. Some head-32 profiles were previously studied. Different heads and strides still share tokens within a band, and multiple files may share body or capture context. No physical row origin, row length or syntax follows.

## Reproduce

At `4b0f9b3750c8fd492cc148762d1c9d926d9fcea2`, supply the public samples below to the original tool, repeating the four arguments for all nine. Then for each sample and head K, run the fixed later profile for its original own winner and its head-32 winner S. The winning strides and both bands' signed standardized means are in the result. No private inputs were used.

    python -I -B tools/stride_head_sensitivity.py --sample ID PUBLIC_NAME SHA256 FILE
    python -I -B tools/token_band_profile.py --sample ID PUBLIC_NAME SHA256 FILE --stride S --head K --start-row 2000 --rows 300

- 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 1995, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 1997, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`
- 1998, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`
- 6343, `OM System - OM-5 - 16bit (4:3).ORF`, `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`
- 6344, `OM System - OM-5 - 16bit (4:3).ORF`, `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512`
- 6345, `OM System - OM-5 - 16bit (4:3).ORI`, `c8277d133c7ac86c7e4af5787fa06515fef8fe044c1b22209c62704537c48e02`
- 8549, `OM System - OM-5 Mark II - 16bit (4:3).ORF`, `c6fe861982ddc18464cf6858d2700f6813cc3a17956bcb12d1179212c999c76a`
- 5283, `OM System - OM-1 - 16bit (4:3).ORF`, `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
