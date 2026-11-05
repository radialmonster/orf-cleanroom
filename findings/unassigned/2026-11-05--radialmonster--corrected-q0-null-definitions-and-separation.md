# Corrected q0 null definitions and fixed-prefix separation

Author: @radialmonster
Verified by: @ruedbi
Lead: #231
Variant: unassigned
Builds on: #197, #214
Reproduces: 2026-10-21--radialmonster--corrected-q0-null-definitions-and-separation
Partial: corrected null definitions and fixed-prefix q0 comparison only; follow-up documentation and the broader framing questions remain open

## Claim

The corrected default q0 comparison uses independent Bernoulli bits with p equal to the measured prefix ones fraction, preserving density in expectation only. Byte shuffle preserves the exact byte histogram. Independently shuffling zero-run and one-run lengths while retaining alternating run values preserves the exact per-value maximal-run-length multisets and first/last bit values. Neither implemented null preserves every local statistic.

On the six selected public CC0 E-M1MarkII payload prefixes below, 131072 bytes from bit zero and seed 20261021, the real bounded candidate k=5 parser has a higher q0 share than each corrected implemented control. This is descriptive separation for this fixed cohort and seed. It does not establish significance, generic parser-artifact exclusion, actual entropy-code boundaries, an alphabet, physical rows, values, a predictor or decoding.

This corrects the earlier finding's advertised random/run preservation definitions and supersedes its broad framing inference. Its original random/run figures came from different generators; the corrected figures below are new measurements. The original finding remains unchanged. The byte-shuffle and real counts need not be discarded.

## Original evidence

Lead #231, posted 2026-10-21 at 16:50:01 UTC, fixes the corrected method and five-file evidence before verification. Source: [tools/token_framing_probe.py](https://github.com/radialmonster/orf-cleanroom/blob/9f731ea9614d790c3d95f0e594b085b8116502bb/tools/token_framing_probe.py), its imported `orf_signature.py`, and `tools/test_token_framing_probe.py` at commit `9f731ea9614d790c3d95f0e594b085b8116502bb`. It counts a candidate only when all q zeros, stop and five suffix bits fit. q>=17 receives no extra skip. Every model restarts Python random.Random(seed). No Markov option is used here.

Exact q0_count / complete_tokens (real; Bernoulli; byte shuffle; alternating run shuffle):

- 1993: 157927/172214; 73358/149059; 78394/151830; 75864/151702.
- 1994: 173761/174485; 66721/145902; 74023/150147; 71844/150019.
- 1995: 158426/172294; 73353/149055; 78260/151766; 75831/151570.
- 1996: 173744/174445; 66515/145797; 74541/150210; 71830/149878.
- 1997: 158184/172259; 73390/149074; 78330/151897; 75953/151605.

Public identities, all CC0 raw.pixls.us content, already present by id/name/hash in samples/manifest.csv:

- 1993, Olympus - E-M1MarkII - 16bit (4:3).ORF, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`.
- 1994, Olympus - E-M1MarkII - 16bit (4:3).ORF, SHA-256 `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23`.
- 1995, Olympus - E-M1MarkII - 16bit (4:3).ORI, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`.
- 1996, Olympus - E-M1MarkII - 16bit (4:3).ORF, SHA-256 `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2`.
- 1997, Olympus - E-M1MarkII - 16bit (4:3).ORI, SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`.
- Verification file 1998, Olympus - E-M1MarkII - 16bit (4:3).ORF, SHA-256 `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`.

Measured signatures remain unassigned: compression tag 1 and variable-size payloads, 5240x3912 on 1993/1995/1997/1998 and 10400x7792 on 1994/1996. The original finding's V1 folder does not classify these files by model alone.

## Verification

On 2026-11-05 UTC, @ruedbi independently verified the corrected q0 null measurements on all six public CC0 E-M1 Mark II samples using `tools/token_framing_probe.py` at 131072-byte prefix and seed 20261021. All 33 synthetic unit tests in `tools/test_token_framing_probe.py` passed.

All model counts, consumed bits, token counts, and residual bits exactly reproduced across all six samples:
- 1993: real 157927/172214; Bernoulli 73358/149059; byte shuffle 78394/151830; alternating run shuffle 75864/151702.
- 1994: real 173761/174485; Bernoulli 66721/145902; byte shuffle 74023/150147; alternating run shuffle 71844/150019.
- 1995: real 158426/172294; Bernoulli 73353/149055; byte shuffle 78260/151766; alternating run shuffle 75831/151570.
- 1996: real 173744/174445; Bernoulli 66515/145797; byte shuffle 74541/150210; alternating run shuffle 71830/149878.
- 1997: real 158184/172259; Bernoulli 73390/149074; byte shuffle 78330/151897; alternating run shuffle 75953/151605.
- 1998: real 158189/172256 (0.918337); Bernoulli 73354/149055 (0.492127); byte shuffle 78212/151740 (0.515434); alternating run shuffle 75513/151541 (0.498301).

On every tested sample, real q0 share exceeds all three null controls. All local sample SHA-256 hashes matched retained CC0 manifest records.

This reproduces and upgrades finding `2026-10-21--radialmonster--corrected-q0-null-definitions-and-separation` to verified.

## Reproduce

```sh
python -I -B tools/test_token_framing_probe.py
python -I -B tools/token_framing_probe.py --bytes 131072 --seed 20261021 --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1993 --sample 1994 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1994 --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1995 --sample 1996 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1996 --sample 1997 "Olympus - E-M1MarkII - 16bit (4:3).ORI" FILE1997 --sample 1998 "Olympus - E-M1MarkII - 16bit (4:3).ORF" FILE1998
```
