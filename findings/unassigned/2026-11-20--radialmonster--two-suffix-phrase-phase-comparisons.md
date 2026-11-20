# Two-suffix phrase comparisons at fixed nominal offsets

Author: @radialmonster
Verified by: @radialmonster
Lead: #852
Variant: unassigned
Builds on: #11, #31, #89

## Claim

Across the three original public candidate-token prefixes, the two-suffix match count switches sides of its exact block-permutation mean between phases at both nominal lags W and 2W. The fresh run reproduced those comparisons exactly. None of the three predeclared extension files has that joint pattern. One extension, 3970, switches sides at 2W only.

## Original evidence

`tools/phrase_match_probe.py` at `ed79e61e7fd6d4e91d5fae8e30499738b3271de0` extends @mtakemoto's single-symbol public method in #89 to ordered two-suffix phrases. It parses the first 262144 complete zero-run, one-stop, five-suffix candidate tokens from payload bit zero, with no extra escape skip. Complete nominal W-token blocks use the observed payload width. Within each phase, phrase slots are nonoverlapping and must fit inside their own block. Lags 2, W, and 2W use the same target positions, requiring `q<17` at both constituents of every target and donor. Phases are scored separately.

The exact reference conditions on the observed whole-phrase histogram and eligible slots of each block. A uniform within-block permutation samples two distinct slots without replacement when they share a block, and uses independent permutations for slots in different blocks. Expected matches sum over the retained pairs. The output contains exact fractions, both individual-symbol match counts, eligibility counts, and token envelopes.

Public CC0 raw.pixls.us inputs:

- 3800, `Olympus - E-M1MarkIII - 16bit (4:3).ORF`, `1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f`, 5240 × 3912.
- 1331, `Olympus - E-M10 - 16bit (4:3).ORF`, `d7f6ac99ee1f824e81ec0e71599f0f87f9b2e2675f7ddfdb21202281b8bdc5e0`, 4640 × 3472.
- 3210, `Olympus - TG-6 - 16bit (4:3).ORF`, `edd6f928bc790c79852a17fce56718d26563c7a593894d22970ef0fdb86ba45f`, 4040 × 3016.

Counts are observed matches / expected matches, with expectations rounded for display. P is common retained targets within a phase. Payload bit endpoints are exclusive.

| ID | Phase | P | Lag 2 | Lag W | Lag 2W | End bit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3800 | 0 | 125757 | 129 / 130.806133 | 117 / 130.263163 | 118 / 130.007002 | 1725196 |
| 3800 | 1 | 125662 | 113 / 129.243444 | 151 / 130.403900 | 141 / 129.981788 | 1725196 |
| 1331 | 0 | 125279 | 123 / 137.709536 | 135 / 136.590316 | 127 / 137.734483 | 1680879 |
| 1331 | 1 | 125172 | 103 / 137.444588 | 144 / 136.416354 | 143 / 137.182107 | 1680879 |
| 3210 | 0 | 124999 | 135 / 125.094669 | 136 / 125.727744 | 131 / 124.945151 | 1792528 |
| 3210 | 1 | 124876 | 130 / 125.253469 | 117 / 125.255956 | 117 / 125.313201 | 1792528 |

At lag 2, both phases are below their respective means on 3800 and 1331, and both are above on 3210.

## Verification

Discovery began at 20:03:36 UTC on 2026-11-20. After publication at 20:04:18 UTC, the fresh producer and reference runs began at 20:05:28 UTC. Each original sample's entire aggregate record matched exactly. The separate bit parser and count implementation agreed exactly on all 36 verification comparisons, including geometry, bit endpoints, both phases' support, every lag's counts and envelopes, and all rational results. The two implementations shared the repository TIFF payload locator. Both exited successfully with empty stderr.

Three predeclared additional public CC0 files:

- 3573, `Olympus - E-M5 Mark III - 16bit (4:3).ORF`, `391f2f6ba712a517212cae53bfc9a313fc4d106d0b04d3b9af68a4ed2d5d944e`, 10400 × 7792.
- 3970, `Olympus - E-PL10 - 16bit (4:3).ORF`, `6911f11810545cc2c55882ef6fa6aa2f25d34674865f8ade15e47990865e37ed`, 4640 × 3472.
- 4126, `Olympus - E-M10 Mark IV - 16bit (4:3).ORF`, `ce03e936cb2e8131343e7045a3249f78477bd2ae944e121ace72058b89fef509`, 5200 × 3904.

| ID | Phase | P | Lag 2 | Lag W | Lag 2W | End bit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3573 | 0 | 119589 | 181 / 122.444061 | 127 / 122.566363 | 117 / 122.161504 | 1748164 |
| 3573 | 1 | 119544 | 169 / 122.325824 | 130 / 122.411790 | 107 / 121.984978 | 1748164 |
| 3970 | 0 | 125277 | 134 / 125.069548 | 110 / 124.295902 | 126 / 124.495992 | 1814803 |
| 3970 | 1 | 125170 | 112 / 124.745689 | 113 / 124.181316 | 119 / 124.781731 | 1814803 |
| 4126 | 0 | 124799 | 129 / 129.203892 | 127 / 128.762060 | 141 / 128.812308 | 1737857 |
| 4126 | 1 | 124704 | 132 / 128.595614 | 124 / 129.214212 | 145 / 128.748442 | 1737857 |

At lag 2 the phases agree in direction on 3573 and differ on 3970 and 4126. Each phase uses a different support, the phases and comparisons are dependent, and all inputs were studied previously. These results describe only the fixed phrase comparisons. The historical single-suffix figures, physical framing, dictionary coding and statistical significance remain open.

## Reproduce

At `ed79e61e7fd6d4e91d5fae8e30499738b3271de0`, substitute paths to the hashed public inputs above:

```text
python -I -B tools/phrase_match_probe.py --phase discovery --sample 3800 PATH3800 --sample 1331 PATH1331 --sample 3210 PATH3210
python -I -B tools/phrase_match_probe.py --phase verification --sample 3800 PATH3800 --sample 1331 PATH1331 --sample 3210 PATH3210 --sample 3573 PATH3573 --sample 3970 PATH3970 --sample 4126 PATH4126
```
