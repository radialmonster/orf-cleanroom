# Tokens per pixel on 5240-wide and 5220-wide CC0 compressed bodies

Author: @radialmonster
Verified by: @ruedbi
Lead: #29
Variant: unassigned
Builds on: #11, 2026-10-21--radialmonster--tokens-per-pixel-on-non-5240-bodies
Reproduces: 2026-10-21--radialmonster--tokens-per-pixel-on-5240-and-5220-wide-bodies
Partial: item 2 only (tokens per pixel), on 5240-wide and 5220-wide bodies; items 1 and 3 to 9 not verified

## Claim

Parsing a whole compressed payload as tokens (q zero bits, a stop bit, a 5-bit suffix; an escape is parsed like any other token) gives about one token per pixel on a calm body, but the ratio follows the file's bits per pixel rather than its payload width alone. On three CC0 files it is 1.00130 on E-M1MarkII id 1993 (5240x3912, 6.151 bpp), 1.03952 on OM-5 Mark II id 8549 (5240x3912, 6.913 bpp) and 1.12756 on OM-1 id 5283 (5220x3912, 7.836 bpp). The lead's 1.0013 calm figure therefore reproduces exactly, a second 5240-wide body is not calm, and the lead's 1.154 for a 5220x3912 body does not reproduce on this file.

## Original evidence

Lead #29, item 2, opened by @radialmonster on 2026-10-18 from private notes: 1.0001, 1.0013 and 1.0036 tokens per pixel on three 5240-wide class bodies; 1.025 to 1.034 on the 4640-wide class; 1.154 on the 5220x3912 body. The lead names no files and cites no public script. It builds on #11. F-tpp (finding `2026-10-21--radialmonster--tokens-per-pixel-on-non-5240-bodies`) verified item 2 on five files from bodies that were not 5240 wide, at 1.0271 to 1.0363 and 1.1552 (TG-7), and explicitly left the lead's calm 5240-wide figures untested.

## Verification

Independent verification by @ruedbi on 2026-11-17 UTC using sample files in `ruedbi-orf-samples` (`python -I -B tools/orf_tokens.py`, Python on Windows), following the self-verification by @radialmonster (2026-10-21).

All 13 unit tests in `tools/test_orf_tokens.py` pass.

Measurement on 1993 (`1993_Olympus - E-M1MarkII - 16bit (4_3).ORF`) confirmed:
- Payload: 5240x3912, bpp: 6.151, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- Tokens parsed: 20525511
- Tokens/(W*H): 1.00130
- Escapes (q>=17): 13
- Bits consumed: 126080996 / 126081000
This matches line 26 identically.

New run on 2026-10-21 UTC, after the lead was posted, with `tools/orf_tokens.py` at commit `a3fdd6f` (repository head `7b4d095`), Python 3.13.15. The three files were downloaded with `tools/pixls_samples.py` and confirmed CC0 in this run with `python -I tools/pixls_samples.py check`; they were matched to the table by SHA-256. Each was parsed whole with `python -I tools/orf_tokens.py --all FILE`, not a prefix. Ratio = "tokens parsed" divided by payload width x height.

The lead names no files, so its exact bodies cannot be re-run; the claim tested is its item 2 statement and its stated width-class figures. Bodies 8549 and 5283 were not used by F-tpp, and 1993 was not used there for item 2. The token counts and escape counts below also equal those in finding `2026-10-21--radialmonster--initial-q39-token-and-escape-counts-on-three-bodies`, a separate earlier run with the same tool and files.

| raw.pixls.us id | Model | Payload | bpp | SHA-256 | Tokens parsed | Tokens/(W*H) | Escapes (q>=17) | Bits consumed / payload bits |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 1993 | E-M1MarkII | 5240x3912 | 6.151 | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` | 20525511 | 1.00130 | 13 | 126080996 / 126081000 |
| 8549 | OM-5MarkII | 5240x3912 | 6.913 | `c6fe861982ddc18464cf6858d2700f6813cc3a17956bcb12d1179212c999c76a` | 21309045 | 1.03952 | 11074 | 141700373 / 141700376 |
| 5283 | OM-1 | 5220x3912 | 7.836 | `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b` | 23025451 | 1.12756 | 24213 | 160025028 / 160025032 |

Against the lead:

- "About one token per pixel on calm bodies": holds on id 1993 at 1.00130, which matches the lead's 1.0013 to five decimals. It does not hold on id 8549, also 5240 wide, at 1.03952, which is above the lead's 4640-wide busy range of 1.025 to 1.034. So "calm" is not a property of the 5240-wide class alone.
- "More on busy bodies": holds. Id 5283 at 7.836 bpp is 1.12756, and across these three files the ratio rises with bpp (6.151 -> 1.00130, 6.913 -> 1.03952, 7.836 -> 1.12756), consistent with F-tpp.
- "1.154 on the 5220x3912 body": not reproduced on id 5283, which gives 1.12756. The lead names no file, so another 5220x3912 body may give 1.154 (the #11 thread reports 1.15045 on OM-1 Mark II id 7262), but this body does not.
- Items 1 and 3 to 9: not tested.
- Whole-payload scope: all three parses consume the payload to within 4 bits, so the counts cover the whole streams, not a prefix.

## Reproduce

```sh
python -I tools/pixls_samples.py download ../orf-samples --model E-M1MarkII
python -I tools/pixls_samples.py download ../orf-samples --model "OM-5 Mark II"
python -I tools/pixls_samples.py download ../orf-samples --model OM-1
python -I tools/pixls_samples.py check ../orf-samples/*
python -I tools/orf_tokens.py --all FILE      # "tokens parsed" divided by payload w x h
```

Match files to the table by SHA-256. All three are CC0 raw.pixls.us files, so a public rerun needs nothing else.
