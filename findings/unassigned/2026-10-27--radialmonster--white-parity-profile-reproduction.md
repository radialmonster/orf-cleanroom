# Nominal white-token parity stability reproduces on a wider profile

Author: @radialmonster
Verified by: @radialmonster
Lead: #555
Variant: unassigned
Builds on: #338, 2026-10-27--mtakemoto--om3-flat-grid-reproduction

## Claim
On the original public OM-3 white capture, the fixed 8M-token nominal-block parity profile has zero opposing blocks among the eligible evaluation blocks. The same conditional result holds on a wider whole-payload profile. This is token-index evidence only; it does not establish physical rows, CFA phase or token insertion locations.

## Original evidence
#555 used `tools/flat_parity_profile.py` at `bd838f979260dc44a3d26bdd6969876092503df2` on PA210010.ORF, SHA-256 `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`, publicly shared under CC0 by its owner; source and declaration are retained in `samples/om3-flat-338-provenance.json`. With candidate k=5/stop=1 tokens, width W=5220, blocks 2:202 fit an orientation using q=0/suffix 0 and 8 parity contrast. Evaluation requires >=0.9 W qualifying tokens and absolute contrast >=0.1; these are uncalibrated practical thresholds. The 8M prefix has 1532 complete blocks plus 2960 tokens, training numerator -895670 and orientation -1; all 1330 later blocks are eligible, with zero opposing, low-information or ties. The fixed within-W ordinary-suffix shuffle seed 20261023 retains q at original positions and uses the real fitted orientation; it has zero eligible blocks and an undefined verdict.

## Verification
After #555 was posted and its current text scanned, @radialmonster reran the 8M profile and obtained an identical full JSON report. The predeclared wider profile covers the whole candidate parse of 20420651 tokens, with 3912 complete nominal blocks and 11 trailing tokens. Of its 3710 evaluation blocks, 3709 are eligible and none opposes the fitted orientation; one is low-information, with no ties. Block 2958 has numerator -451 and denominator 5203: coverage passes but absolute contrast 451/5203 is below 0.1. No claim of constancy is made for this excluded block. The shuffled whole-profile control has zero eligible blocks, 3710 low-information blocks, 25 ties and an undefined verdict. The 11 trailing tokens have no asserted physical interpretation.

A separately implemented bounded token parser and block arithmetic matched every real and shuffled block field and all summary fields in the fresh 1532-block prefix and 3912-block whole profile; the shuffle helper was shared. These implementations assist the same human verifier. Even-token shifts can alter block boundary counts but are not uniquely located by parity, and other causes can change a nominal contrast. These results do not establish physical row boundaries, CFA phase, a predictor, or statistical significance.

## Reproduce
At commit `bd838f979260dc44a3d26bdd6969876092503df2`, substitute the hash-matched public file for FILE:

```sh
python -I -B tools/flat_parity_profile.py --sha256 d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e --tokens 8000000 FILE
python -I -B tools/flat_parity_profile.py --sha256 d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e FILE
```

A null `zero_opposing` is undefined, including for a complete input with exit status zero. Both runs retain the fixed 2:202 template, thresholds and shuffle seed.