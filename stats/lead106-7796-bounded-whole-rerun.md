# #106 original cohort: bounded 7796 whole-payload rerun

Part of #106. Builds on `stats/lead106-original-cohort-prefix-versus-whole.md` and the separately merged #138 EOF fix. Measured by @radialmonster on 2026-10-27 UTC. This fills the rejected 7796 cell of that descriptive report; it is not a finding, independent-human verification, or a causal body/scene/ISO claim.

## Method and input

After the fix, `tools/orf_tokens.py` at `2663d0a3e6e5675a89e545055b8e1bcfda505cc6` was run on public CC0 id 7796, `OM System - OM-3 - 16bit (4:3).ORF`, SHA-256 `1cee7deb661e45101ab3ca6c4240d24ed949b167ed423703fca15c09dd8ec176`, with a 1,500,000-token prefix and with `--all`. The retained verified CC0 record, manifest identity and local hash match. Geometry is 5220x3912, payload 19,818,873 bytes. Candidate syntax is the earlier report's q zero bits, stop 1 and five suffix bits, with zero extra escape skip; actual escape grammar remains open.

## Results

The prefix gives 1,500,000 candidates, 3,150 escapes, end bit 10,574,018, real/null estimates 1.1014/1.0961 and min(q,8) lag 1/2/3 correlations +0.0374/+0.0067/+0.0118. This agrees with the historical prefix at printed precision.

The corrected whole run gives 23,008,928 complete candidates, 30,616 escapes, end bit 158,550,978, six censored residual bits, real/null estimates 1.1267/1.0984 and lag 1/2/3 +0.0833/+0.0556/+0.0636. An independently bounded generator matched both counts, escape totals and endpoints; the residual is not all ones. The previous fast-path scan accepted one incomplete candidate and ended two bits past the 158,550,984-bit payload; its rejected result remains preserved in the earlier report.

Using the earlier report's printed-ratio definition, 7796 excess is +0.48% prefix and +2.58% whole, a +2.09 percentage-point change. The completed six-file table, with earlier accepted cells unchanged, is:

| ID | Prefix excess | Whole excess | Change, percentage points |
|---:|---:|---:|---:|
| 7262 | +5.92% | +2.01% | -3.91 |
| 7263 | +11.57% | +7.44% | -4.13 |
| 7265 | +11.79% | +8.51% | -3.29 |
| 7796 | +0.48% | +2.58% | +2.09 |
| 7797 | +4.16% | +6.52% | +2.36 |
| 7799 | +5.18% | +7.68% | +2.50 |

These are descriptive selected-file comparisons, not evidence of stationary behaviour, physical rows, one-token-per-pixel correspondence, statistical significance, or causal effects. Residual bits are not interpreted as padding. No image or preview was viewed.

## Reproduce

At `2663d0a3e6e5675a89e545055b8e1bcfda505cc6`, after matching the local file to the public hash above:

```sh
python -I -B tools/test_orf_tokens.py
python -I -B tools/orf_tokens.py FILE7796 --max-tokens 1500000
python -I -B tools/orf_tokens.py FILE7796 --all
```

The [earlier report](lead106-original-cohort-prefix-versus-whole.md) gives the other five cells and its one-off method using `tools/token_tail_distribution_probe.py`'s `scan_tokens` bounded generator. This run passed all 13 current token tests. Full aggregate CLI outputs were retained locally; no raw or decoded data was written.
