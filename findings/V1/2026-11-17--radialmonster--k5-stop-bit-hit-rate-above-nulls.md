# The k=5 stop-bit hit rate is far above local-statistic nulls on E-M1 Mark II

Author: @radialmonster
Verified by: @ruedbi
Lead: #197
Variant: V1
Builds on: #11, #29, #196, 2026-10-21--radialmonster--suffix-luma-table-weak-transfer
Reproduces: 2026-10-21--radialmonster--k5-stop-bit-hit-rate-above-nulls
Partial: the q=0 null test only; not the entropy-code alphabet, value mapping, or decode

## Claim

On E-M1 Mark II files, the k=5 unary parser's **q=0 share** (the stop bit is the first bit of the token) is far above null streams that preserve the prefix's relevant local bit statistics.

Over a 131072-byte payload prefix:

| file | ones | real q0 | random | byte shuffle | run shuffle |
|---|---|---|---|---|---|
| 1993 | 0.4917 | **0.9170** | 0.5019 | 0.5163 | 0.4938 |
| 1995 | 0.4916 | **0.9195** | 0.5019 | 0.5157 | 0.4936 |
| 1997 | 0.4918 | **0.9183** | 0.5019 | 0.5157 | 0.4924 |
| 1994 High-Res | 0.4571 | **0.9959** | 0.5019 | 0.4930 | 0.4565 |

Across five seeds on 1995, the nulls stay in a narrow band: random 0.4985–0.5002, byte shuffle 0.5138–0.5181, run shuffle 0.4920–0.4954, while the real value is 0.9195.

The token framing therefore carries a real delimiter signal and is **not a generic parser artifact** under these nulls. The 0–7 residual-bit observation is still not evidence by itself, as lead #197 says. This finding does not establish the entropy-code alphabet, the token-to-value mapping, or a decode.

## Original evidence

Lead #197. Tool: `tools/token_framing_probe.py`, PR #198, commit `4f140d3`. The bounded local parser counts a token only when its q+6 bits fit, so it does not inherit the known `orf_tokens.scan` overread (#138).

Files are CC0 raw.pixls.us copies:

- 1993 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 1994 `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23`
- 1995 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 1997 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`

## Verification

Independent verification by @ruedbi on 2026-11-17 UTC using sample files in `ruedbi-orf-samples` (`python -I -B tools/token_framing_probe.py`, Python on Windows), following the self-verification by @radialmonster (2026-10-21).

All 33 unit tests in `tools/test_token_framing_probe.py` pass.

Measurement on 1993 (`1993_Olympus - E-M1MarkII - 16bit (4_3).ORF`) and 1995 (`1995_Olympus - E-M1MarkII - 16bit (4_3).ORI`) at 131072-byte payload prefix with seed 20261021 confirmed:
- 1993: ones fraction 0.4917, real q0=0.9170, byte shuffle=0.5163, matching line 18 identically.
- 1995: ones fraction 0.4916, real q0=0.9195, byte shuffle=0.5157, matching line 19 identically.

New run on 2026-10-21, after lead #197 was posted, on **1994 High-Res**, which the lead's motivation table did not use (it used 1993, 1995, 1996, 1997 and 1998):

- 1994: real q0=0.9959; nulls 0.5019 (random), 0.4930 (byte shuffle), 0.4565 (run shuffle).

The 1993/1995/1997 rows are the lead's original evidence; the re-run reproduces them, and the five-seed 1995 null range is new here. Self-verified by the finder.

## Reproduce

With the tool from PR #198:

    python -I -B tools/token_framing_probe.py --sample 1994 "Olympus - E-M1MarkII - 16bit (4:3).ORF" "1994_Olympus - E-M1MarkII - 16bit (4_3).ORF" --bytes 131072 --seed 20261021
    python -I -B tools/token_framing_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" "1993_Olympus - E-M1MarkII - 16bit (4_3).ORF" --bytes 131072 --seed 20261021
    python -I -B tools/token_framing_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" "1995_Olympus - E-M1MarkII - 16bit (4_3).ORI" --bytes 131072 --seed 20261021
    python -I -B tools/token_framing_probe.py --sample 1997 "Olympus - E-M1MarkII - 16bit (4:3).ORI" "1997_Olympus - E-M1MarkII - 16bit (4_3).ORI" --bytes 131072 --seed 20261021

Change `--seed` to vary the nulls; the real value is fixed.
