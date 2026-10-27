# E-M5 Mark II dark-token offset signs reproduce on wider prefixes

Author: @radialmonster
Verified by: @radialmonster
Lead: #561
Variant: unassigned
Builds on: #338, #558

## Claim
Six public E-M5 Mark II capped-dark captures show the four declared suffix-match directions against a fixed block shuffle in both the 4M and wider 8M candidate-token prefixes. This describes these nominal token-index offsets only; it does not establish a physical CFA, predictor, variant or population effect.

## Original evidence
#561 used `tools/bayer_grid_probe.py` at `5086fa574155ea7eb392ea01f4d858a722345138` on six owner-shared public CC0 E-M5 Mark II captures, 4640×3472 payloads. Public identities, SHA-256 hashes, declared ISO settings and source links are in `samples/e-m5-mk-ii-dark-338-provenance.json`; @mszyndel provided the captures in #558. The frozen candidate k=5/stop=1 grid used the first 4M tokens, W from the container, and one ordinary-suffix within-W shuffle with seed 20261023. For all six, real minus shuffle was negative at (0,2) and (2,0), positive at (2,-2) and (2,+2).

## Verification
After #561 was posted and its current text scanned, I reran all six 4M reports and obtained identical full JSON to the original reports. The predeclared wider 8M prefixes on the same files retain all 24 signs. Values below subtract the tool's six-decimal shuffled rate from its six-decimal real rate; 4M evidence values and all public hashes are listed in #561 and the retained provenance record.

| File | 8M (0,2) | 8M (2,0) | 8M (2,-2) | 8M (2,+2) |
| --- | ---: | ---: | ---: | ---: |
| P1010009.ORF | -0.031878 | -0.032956 | +0.022895 | +0.014443 |
| P1010011.ORF | -0.032091 | -0.032851 | +0.022871 | +0.015078 |
| P1010013.ORF | -0.032517 | -0.032640 | +0.022488 | +0.014977 |
| P1010017.ORF | -0.014862 | -0.017590 | +0.013140 | +0.009386 |
| P1010018.ORF | -0.014845 | -0.017679 | +0.013154 | +0.009508 |
| P1010019.ORF | -0.014528 | -0.017616 | +0.013210 | +0.009361 |

A separately implemented bounded-token generator and direct-index arithmetic matched every real and shuffled pair/match count, whole-payload endpoint and residual, escape and large-q count, and site table across all twelve post-lead reports. The shuffle helper was shared; the agents assisted the same human verifier.

The 8M prefix is a wider run on the same captures, not a new body or independently sampled scene. Same-session files may be dependent. The shuffle is a descriptive control, not calibrated significance; no token-to-pixel correspondence, physical row or predictor follows.

## Reproduce
At `5086fa574155ea7eb392ea01f4d858a722345138`, substitute the six hash-matched public file paths in table order:

```sh
python -I -B tools/bayer_grid_probe.py --tokens 4000000 FILE1 FILE2 FILE3 FILE4 FILE5 FILE6
python -I -B tools/bayer_grid_probe.py --tokens 8000000 FILE1 FILE2 FILE3 FILE4 FILE5 FILE6
```

Default seed is 20261023; ordinary suffixes are shuffled within W-token blocks, escape positions fixed.