# Within-token suffix balance holds within a stated tolerance on E-M1 Mark II and OM-1

Author: @radialmonster
Verified by: @ruedbi
Lead: #11
Variant: unassigned
Builds on: 2026-10-21--radialmonster--em1mk2-full-payload-suffix-dependence
Reproduces: 2026-10-21--radialmonster--within-token-suffix-balance-four-bodies
Partial: within-token MI(H;L) and b0/b1 marginals on public E-M1 Mark II files (1993, 1995, 1998) and OM-1 within the stated tolerance; not exact independence or fairness, the b2/b4 special role, physical rows, geometry, or decoding.

## Claim

Under the candidate q-zero, stop-1, five-bit-suffix parse, lead #11 states that within a token the groups `H = b4b3` and `L = b2b1b0` are statistically independent and that `b1` and `b0` behave as fair coins.

This finding reports a predeclared bounded test of that qualitative claim on local public CC0 files from `samples/manifest.csv` (E-M1 Mark II ids 1993, 1995, 1998) and OM-1. Under the established tolerance:
- first 262144 candidate tokens from payload bit zero, q-zero/stop-1/five-suffix parse with no extra escape skip; escapes retained in sequence and excluded from suffix statistics;
- pass if `MI(H;L) <= 0.010` bit and `|P(b1=1) - 0.5| <= 0.05` and `|P(b0=1) - 0.5| <= 0.05` on every file.

All audited files pass that tolerance: `MI(H;L)` is 0.0005 to 0.0025 bit; `P(b1=1)` is 0.4795 to 0.4952 and `P(b0=1)` is 0.4897 to 0.4949. This supports the qualitative statement within the stated tolerance. It does not establish exact independence or exact fair-coin marginals.

## Original evidence

[Lead #11](https://github.com/radialmonster/orf-cleanroom/issues/11), by @radialmonster, reports the H/L split and the within-token independence/fairness statement from private research notes. The merged self-verified finding `2026-10-21--radialmonster--within-token-suffix-balance-four-bodies` measured four public CC0 bodies (ids 241, 5283, 6343, 6946) where MI(H;L) ranged from 0.0008 to 0.0030 bit, P(b1=1) was 0.4688 to 0.4806, and P(b0=1) was 0.4698 to 0.4904, all passing tolerance.

## Verification

Independent verification was conducted by @ruedbi on 2026-11-18 using Python standard library (Python 3.8+) and `tools/orf_tokens.py`.

All unit tests in `tools/test_orf_tokens.py` passed.

A fresh rerun was performed on the first 262,144 candidate tokens of local public CC0 files:

| File ID | File Name / Body | SHA-256 | Escapes (q>=17) | MI(H;L) | Rotated Baseline | P(b4=1) | P(b3=1) | P(b2=1) | P(b1=1) | P(b0=1) | Tolerance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1993 | `Olympus - E-M1MarkII - 16bit (4:3).ORF` | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` | 1 | 0.0005 | 0.0000 | 0.2874 | 0.4087 | 0.3215 | 0.4808 | 0.4942 | pass |
| 1995 | `Olympus - E-M1MarkII - 16bit (4:3).ORI` | `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` | 1 | 0.0006 | 0.0001 | 0.2874 | 0.4069 | 0.3211 | 0.4804 | 0.4949 | pass |
| 1998 | `Olympus - E-M1MarkII - 16bit (4:3).ORF` | `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71` | 2 | 0.0006 | 0.0001 | 0.2873 | 0.4073 | 0.3207 | 0.4795 | 0.4949 | pass |
| - | `Olympus-OM1.ORF` | `1db8b91707e8251d751c8c2db6745133afece89b2931f760defdc1e4577ef11e` | 1 | 0.0025 | 0.0000 | 0.4769 | 0.5030 | 0.4995 | 0.4952 | 0.4897 | pass |

Across all four files, `MI(H;L)` remains below the 0.010 bit bound, and `b1` and `b0` marginals stay within 0.05 of 0.50.

## Reproduce

Using standard library Python and `tools/orf_tokens.py`:

```bash
python -I -B tools/test_orf_tokens.py
python -I -B tools/orf_tokens.py <path-to-file> --max-tokens 262144
```

Inspect the printed `escapes (q>=17)`, `suffix bit balance P(bit=1)` and `within-token MI(H;L)` lines.
