# Token cross-field dependence reproduces on two new bodies, at lower mutual information

Author: @radialmonster
Verified by: @ruedbi
Lead: #11
Variant: V1
Builds on: 2026-10-20--radialmonster--em1mk2-b4-next-b2-share-provenance
Reproduces: 2026-10-21--radialmonster--token-dependence-new-bodies
Partial: the cross-field/same-field structure, H/L independence and b1/b0 fairness on whole E-M1 Mark III 3800/3802 and E-M5 Mark III 3588 payloads; not the lead's about 0.12/0.07 MI magnitudes, the strict "cross-field only" equality at lag 1, the one-token-per-pixel row stride, or preview geometry.

## Claim

Lead #11's k=5 token stream has a reproducible neighbour-dependence structure on the E-M1 Mark II: at token distance 1 and 3 the cross-field pairs H(t-1)->L(t) and L(t-1)->H(t) carry more mutual information than the same-field pairs, and at distance 2 the same-field pair L-L (and H-H) carries more than the cross-field pairs. H and L are independent within a token, b1 and b0 are near fair, and about 97% of the H->L information is carried by b4(t-1)->b2(t).

On whole payloads of two bodies not used for that measurement, the dominant cross-field directions and the lag-2 same-field structure are present: H->L at lag 1 and L->H at lag 3 are the largest pairs, and L-L (plus H-H) dominates at lag 2. H/L within-token MI is 0.0013 to 0.0015 bit, and b4(t-1)->b2(t) carries 0.95 to 0.96 of the H->L information. The absolute MI values are lower than the lead's ~0.12/0.07: 0.0103 to 0.0166 bit for H->L and 0.0043 to 0.0065 for L->H. The strict "cross-field only" equality at lag 1 is not reproduced: L->H is close to or slightly below H-H on the E-M1 Mark III files. This verifies the structure, not the magnitudes.

## Original evidence

Lead #11 (found by @radialmonster, 2026-10-18) reported, from private research notes: H and L independent within a token; b1 and b0 fair coins; cross-field dependence at token lags 1 and 3 (H->L about 0.12 bit, L->H about 0.07) with same-field about 0; same-field dependence at lag 2 (L-L about 0.04, H-H about 0.02); and about 97% of the H->L information carried by b4(t-1)->b2(t).

The lead's 2026-10-20 note says the 0.12 figure does not hold for the 5240-wide body. Finding `2026-10-20--radialmonster--em1mk2-b4-next-b2-share-provenance` reports about 0.05 bit H->L on id 1993 and 0.09 to 0.11 bit on id 1994, with the b4->b2 share 0.95 to 0.98.

Tool: `tools/orf_tokens.py`, standard library only, merged on main. It parses q zero bits, a 1 stop bit and a 5-bit suffix, and prints the suffix-bit balance, within-token MI(H;L), the neighbour MI table at lags 1 to 3, and the b4->b2 share. The lead had no public script when posted.

Files, all public CC0 raw.pixls.us (id, name, SHA-256):

- 1993 `Olympus - E-M1MarkII - 16bit (4:3).ORF` `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 3800 `Olympus - E-M1MarkIII - 16bit (4:3).ORF` `1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f`
- 3802 `Olympus - E-M1MarkIII - 16bit (4:3).ORI` `83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46`
- 3588 `OLYMPUS - E-M5 Mark III - 16bit (4:3).ORF` `24de6ac3bd5e668ee22fd0dbf2e344608949eb85f7342f28470ce709c9d51226`

## Verification

An independent verification run was performed on 2026-11-18 UTC by @ruedbi using `tools/orf_tokens.py --all` on the four public CC0 files above, plus an additional CC0 extension file (id 3804, `Olympus - E-M1MarkIII - 16bit (4:3).ORI`, SHA-256 `d831692b608471ad64667eb2485bab553de0ddb9366d384c4ecb731092b5dc42`). All 13 unit tests in `tools/test_orf_tokens.py` passed.

All four original files reproduce the exact reported values:

| id | body | bpp | q=0 share | within-token MI(H;L) | b4->b2 | b4->b2 share | b1 | b0 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1993 | E-M1 Mark II (control) | 6.151 | 0.8889 | 0.0027 | 0.0495 | 0.98 | 0.4815 | 0.4939 |
| 3800 | E-M1 Mark III | 6.425 | 0.7301 | 0.0014 | 0.0097 | 0.95 | 0.4753 | 0.4892 |
| 3802 | E-M1 Mark III | 6.395 | 0.7434 | 0.0015 | 0.0120 | 0.96 | 0.4769 | 0.4900 |
| 3588 | E-M5 Mark III | 6.353 | 0.7834 | 0.0013 | 0.0157 | 0.95 | 0.4778 | 0.4940 |
| 3804 | E-M1 Mark III (extension) | 6.712 | 0.6515 | 0.0017 | 0.0055 | 0.91 | 0.4809 | 0.4863 |

Neighbour MI in bits, in the order H->L, L->H, L-L, H-H:

| id | lag 1 | lag 2 | lag 3 |
| ---: | --- | --- | --- |
| 1993 | 0.0507, 0.0245, 0.0034, 0.0068 | 0.0024, 0.0040, 0.0121, 0.0092 | 0.0062, 0.0198, 0.0016, 0.0032 |
| 3800 | 0.0103, 0.0043, 0.0033, 0.0053 | 0.0013, 0.0016, 0.0047, 0.0032 | 0.0017, 0.0054, 0.0008, 0.0019 |
| 3802 | 0.0125, 0.0046, 0.0029, 0.0051 | 0.0015, 0.0019, 0.0073, 0.0031 | 0.0018, 0.0065, 0.0006, 0.0018 |
| 3588 | 0.0166, 0.0065, 0.0031, 0.0051 | 0.0015, 0.0014, 0.0111, 0.0025 | 0.0017, 0.0067, 0.0002, 0.0010 |
| 3804 | 0.0061, 0.0017, 0.0030, 0.0033 | 0.0014, 0.0011, 0.0024, 0.0020 | 0.0012, 0.0028, 0.0004, 0.0011 |

Against the lead:

- **Holds on all four files:** H/L are independent within a token (0.0013 to 0.0017 bit, against a 0.0000 to 0.0001 rotated-pair baseline); b1 and b0 are near fair (0.475 to 0.494); at lag 1 H->L exceeds all three other pairs; at lag 2 L-L and H-H dominate over cross-field pairs; at lag 3 L->H exceeds H->L and both same-field pairs; b4->b2 carries 0.91 to 0.96 of the H->L information.
- **The control reproduces the corrected 5240-wide figure:** whole-payload 1993 gives H->L 0.0507 bit and a b4->b2 share of 0.98, consistent with the lead's 2026-10-20 note and the earlier finding on ids 1993 and 1994. The 1993 lag-3 pattern is L->H 0.0198 against H->L 0.0062.
- **Does not reproduce the magnitudes:** H->L is 0.0061 to 0.0166 bit, not ~0.12; L->H is 0.0017 to 0.0065, not ~0.07.
- **The strict "cross-field only" wording at lag 1 is not reproduced on the E-M1 Mark III files:** L->H (0.0043, 0.0046, 0.0017) is slightly below H-H (0.0053, 0.0051, 0.0033), although H->L is clearly the largest pair. On E-M5 Mark III 3588, L->H (0.0065) exceeds H-H (0.0051).
- **Prefix sensitivity:** a 400-row prefix of 3802 did not show the lag-1/lag-3 pattern (H->L 0.0005, L->H 0.0005, L-L 0.0009, H-H 0.0012); the whole payload does. The whole-payload result is reported for every file; the prefix is shown only to document this sensitivity, and the scope is whole payloads only.
- **Not tested:** the one-token-per-pixel row stride and preview geometry (both need a different measurement), other bodies, pixel values, a predictor, scan order, round-trip or any decode. The lead's claim is a token-stream statistic, not a decode. Whether these files meet the full V1 signature, including row stride, is not established here; this finding measures the token-statistic part of lead #11 on them.

This independent run reproduces and upgrades finding `2026-10-21--radialmonster--token-dependence-new-bodies` to verified.

## Reproduce

```sh
python -I -B tools/test_orf_tokens.py
python -I -B tools/orf_tokens.py "<dir>/1993_Olympus - E-M1MarkII - 16bit (4_3).ORF" --all
python -I -B tools/orf_tokens.py "<dir>/3800_Olympus - E-M1MarkIII - 16bit (4_3).ORF" --all
python -I -B tools/orf_tokens.py "<dir>/3802_Olympus - E-M1MarkIII - 16bit (4_3).ORI" --all
python -I -B tools/orf_tokens.py "<dir>/3588_OLYMPUS - E-M5 Mark III - 16bit (4_3).ORF" --all
python -I -B tools/orf_tokens.py "<dir>/3804_Olympus - E-M1MarkIII - 16bit (4_3).ORI" --all
```

Read the lines `within-token MI(H;L)`, `lag 1:`, `lag 2:`, `lag 3:`, `b4(t-1)->b2(t):` and `suffix bit balance P(bit=1)`. Match files to the table by SHA-256, not by name. All five are public CC0 raw.pixls.us files; no number here depends on a private file.
