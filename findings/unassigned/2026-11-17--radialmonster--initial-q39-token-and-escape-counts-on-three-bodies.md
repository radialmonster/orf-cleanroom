# A q=39 token starts three more compressed payloads and appears nowhere else

Author: @radialmonster
Verified by: @ruedbi
Lead: #37
Variant: unassigned
Builds on: #11
Reproduces: 2026-10-21--radialmonster--initial-q39-token-and-escape-counts-on-three-bodies

## Claim

On three CC0 compressed payloads from bodies lead #37 did not use (E-M1MarkII, OM-1 and OM-5MarkII), the first five payload bytes are `00 00 00 00 01`, which parse as a q=39 token. Exactly one q=39 token occurs in each whole payload, so it is only the initial token. No q=30 token occurs. Non-initial escapes lie at q 17 to 28 and their rate rises with bits per pixel; on the two escape-rich files the mode is q=21. This reproduces the lead's initial-token and escape-distribution claims on new bodies.

## Original evidence

Lead #37, opened by @radialmonster on 2026-10-19, parsed 11 CC0 files with `tools/orf_tokens.py` (commit 8e5dc0e). It reported that all 11 payloads begin `00 00 00 00 01` (first token q=39), that q=39 occurs only at the start, that no q=30 token occurs, and that other escapes lie at q 17 to 29 with a peak at q=21 on escape-rich files. Its escape counts included 7 non-initial escapes on E-M1MarkIII (3800) and 124364 on OM-1MarkII (7262).

The lead's bodies were OM-5, E-M1MarkIII, E-M10, E-3, TG-6, E-M5MarkIII, E-PL10, E-M10MarkIV and OM-1MarkII. None of the three bodies below is among them.

## Verification

Independent verification by @ruedbi on 2026-11-17 UTC using sample files in `ruedbi-orf-samples` (`python -I -B tools/orf_tokens.py` and `tools/orf_signature.py`, Python on Windows), following the self-verification by @radialmonster (2026-10-21).

All 13 unit tests in `tools/test_orf_tokens.py` pass.

Measurement on 1993 (`1993_Olympus - E-M1MarkII - 16bit (4_3).ORF`) confirmed:
- Payload: 5240x3912, bytes: 15760125, bpp: 6.151, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- First 5 bytes: `0000000001` (initial token q=39)
- Total parsed tokens: 20525511 (whole payload, 126080996 bits consumed, 4 residual bits)
- Exact q=39 count: 1 (only the initial token)
- Escapes (q>=17): 13 (0.00006% of tokens), distribution: `17:1 18:1 21:8 22:2 39:1`
- Non-initial max q: 22, q=21 count: 8
This matches line 25 and 31 identically.

A new run on 2026-10-21 UTC, after the lead was posted, with `tools/orf_tokens.py` at `a3fdd6f` (the repository head), Python 3.13.15. The three files were downloaded with `tools/pixls_samples.py`, checked CC0 in this run, and matched to the table by SHA-256. Each was parsed whole with `python -I tools/orf_tokens.py --all FILE`, not a prefix. The lead's exact bodies and exact figures were not re-measured; this is a separate run on three new bodies.

| raw.pixls.us id | Model | Payload | bpp | SHA-256 | First 5 bytes | q=39 count | Escapes (q>=17) | Non-initial max q | q=21 count |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 1993 | E-M1MarkII | 5240x3912 | 6.151 | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` | `0000000001` | 1 | 13 | 22 | 8 |
| 5283 | OM-1 | 5220x3912 | 7.836 | `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b` | `0000000001` | 1 | 24213 | 28 | 5128 |
| 8549 | OM-5MarkII | 5240x3912 | 6.913 | `c6fe861982ddc18464cf6858d2700f6813cc3a17956bcb12d1179212c999c76a` | `0000000001` | 1 | 11074 | 28 | 3759 |

Escape q counts (the q=39 entry is the initial token; the other entries are non-initial):

- 1993 E-M1MarkII: `17:1 18:1 21:8 22:2 39:1`; 12 non-initial escapes, 0.00006% of 20525511 tokens.
- 5283 OM-1: `17:4179 18:3244 19:3749 20:4794 21:5128 22:1606 23:973 24:300 25:159 26:60 27:14 28:6 39:1`; 24212 non-initial escapes, 0.10516% of 23025451 tokens.
- 8549 OM-5MarkII: `17:1191 18:1020 19:1205 20:2866 21:3759 22:549 23:291 24:116 25:47 26:24 27:2 28:3 39:1`; 11073 non-initial escapes, 0.05197% of 21309045 tokens.

Against the lead:

- Initial token: holds on 3 of 3 new payloads (first five bytes `0000000001`, q=39).
- q=39 only at the start: holds on 3 of 3 (exact q=39 count is one in each whole payload).
- No q=30: holds on 3 of 3; none of the q values is 29 to 38 either, and the only q above 28 is the initial q=39.
- Escape rate rises with bpp: holds across these three (6.151 bpp, 13 escapes; 6.913 bpp, 11074; 7.836 bpp, 24213). The two escape-rich files peak at q=21, as in the lead; the calm E-M1MarkII file has 8 of its 12 non-initial escapes at q=21 but too few escapes to call a mode.
- Whole-payload parse: all three payloads were consumed to within 4 bits (1993: 126080996 of 126081000 bits; 5283: 160025028 of 160025032; 8549: 141700373 of 141700376), so the counts above cover the whole stream rather than a prefix.

## Reproduce

```sh
python -I tools/pixls_samples.py download ../orf-samples --model E-M1MarkII --max 1
python -I tools/pixls_samples.py download ../orf-samples --model OM-1 --max 1
python -I tools/pixls_samples.py download ../orf-samples --model "OM-5 Mark II" --max 1
python -I tools/pixls_samples.py check ../orf-samples/*        # confirm CC0
python -I tools/orf_tokens.py --all FILE                        # escape q values and token count
python -I tools/orf_signature.py FILE                           # payload size, bpp and SHA-256
```

First five payload bytes and the initial q, using the same payload locator as the token tool:

```sh
python -I -c "import sys; sys.path.insert(0,'tools'); from orf_tokens import locate; [(lambda w,h,b,p: print(p, w, h, b[:5].hex(), 48-int.from_bytes(b[:6],'big').bit_length()))(*locate(p), p) for p in sys.argv[1:]]" FILE...
```

The last number is q for the first token: 48 minus the bit length of the first six payload bytes. A first token with q=39 has 39 zero bits, the stop bit, and the suffix starting in byte six.
