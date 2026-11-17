# Lead #32 partial: no suffix bridge-energy ratio at or below 0.5 on six CC0 files

Author: @radialmonster
Verified by: @ruedbi
Lead: #32
Variant: unassigned
Builds on: #11, #64
Reproduces: 2026-10-21--radialmonster--partial-suffix-bridge-energy
Partial: signed_digit and signed_low3 readings (with unsigned_suffix as a comparison), bridge-energy metric only; no pooled ratio at or below 0.5 on the six predeclared CC0 files, and signed_digit below the permutation mean on the two E-M1 Mark II files

## Claim

Lead #32 rules out many ways of turning the token fields into a value. This finding verifies one bounded part of that negative under one metric.

With the bridge-energy metric fixed in the lead #32 discussion (128-token blocks from index 0, complete blocks containing q >= 17 omitted whole, 262144-token prefix, three suffix-only mappings, lane counts 1 and 2 by absolute token parity), none of the 36 pooled sample/mapping/lane-count cells is at or below 0.5 on six CC0 files. Pooled R = sum(E)/sum(N) ranges over 0.618104 to 1.091014 for signed_digit, 0.740651 to 1.305211 for signed_low3, and 0.921650 to 1.780442 for unsigned_suffix. This supports the lead's negative for these three readings on these files.

One part of the lead's wording does not hold under this metric. The lead says the signed low digit reading was "worse than null (growth about 15 vs 5)". On the two E-M1 Mark II files 1993 and 1998 the signed_digit one-lane reading is 0.624050 and 0.643036, below the permutation mean (R = 1), while unsigned_suffix is 1.000789 and 1.031150 there. A growth test and a detrended bridge-energy test are different measures, so this does not refute the historical figure; it means "worse than null" is not a statement about this metric.

The exact historical figures could not be reproduced: the lead gives neither a method nor named files. This is a different, public operationalization of the same negative, not the historical experiment. It does not establish a bounded undetrended reconstruction, a value map, an image, or a decoder. Detrending removes mean drift, and a ratio below 1 is only smoother than a permutation of the same increments.

## Original evidence

The lead's evidence is private research notes dated 2026-10-14 to 2026-10-18; it names bodies A-E by size class and gives aggregate figures only. It states that no public script exists for those figures and that a reproduction should parse the stream with the token model from #11 and compare candidate values against a within-row shuffle.

The public bridge-energy design used here was fixed by @mtakemoto in the lead #32 discussion on 2026-10-19 before any target measurement, and implemented in `tools/value_map_probe.py` (PR #64, merged). The finder's claim is the negative result in the lead; the metric is an independent operationalization, not the finder's historical method. The tool's design and first run are @mtakemoto's work; this finding is a self-verification of the finder's lead, using that merged tool unchanged.

## Verification

A new run was made on 2026-10-21 UTC, after the lead was posted and after the earlier public run, with `tools/value_map_probe.py` at commit `fa3ed83` and source SHA-256 `value_map_probe.py` `fb6101be87a7b247c472d384e6f3396e2132e23c30f7d30a532fef418ee42115`, `orf_tokens.py` `c6f51ed26793b1bb400a1dc1b29d8e20f9ef734373770310c665228ce02f08ad`, `orf_signature.py` `b1b6f091bfb986ab7aca3ad1f513202acfaaccc424272523589142444d025afb`.

All six files were downloaded from raw.pixls.us and checked `CC0` with `python -I tools/pixls_samples.py check` immediately before the run. The lead names no files or bodies, so the six CC0 files below are the public cohort; none is identified as one of the lead's bodies A-E. The settings were unchanged from the frozen design: MSB-first original parser, `escape_extra=0`, 128-token blocks from index 0, complete blocks containing q >= 17 omitted whole, 262144-token prefix, lane counts 1 and 2 selected by absolute token parity. The run reproduced the earlier public pooled ratios to all six decimals.

| raw.pixls.us id | public name | SHA-256 | escapes / omitted blocks | signed_digit 1 / 2 | signed_low3 1 / 2 | unsigned 1 / 2 |
|---|---|---:|---:|---:|---:|---:|
| 1993 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` | 1 / 1 | 0.624050 / 0.763920 | 0.794635 / 0.740651 | 1.000789 / 0.921650 |
| 6343 | OM System - OM-5 - 16bit (4:3).ORF | `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7` | 34 / 34 | 1.091014 / 1.036478 | 1.278014 / 1.094736 | 1.719142 / 1.304408 |
| 5283 | OM System - OM-1 - 16bit (4:3).ORF | `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b` | 313 / 261 | 1.014033 / 0.999012 | 1.116065 / 1.034395 | 1.163499 / 1.081964 |
| 1998 | Olympus - E-M1MarkII - 16bit (4:3).ORF | `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71` | 2 / 1 | 0.643036 / 0.786777 | 0.796512 / 0.743915 | 1.031150 / 0.956672 |
| 6347 | OM System - OM-5 - 16bit (4:3).ORI | `062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9` | 127 / 118 | 1.077995 / 1.034338 | 1.305211 / 1.108097 | 1.632536 / 1.267303 |
| 7262 | OM System - OM-1 Mark II - 16bit (4:3).orf | `d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd` | 1156 / 756 | 1.030985 / 1.025915 | 1.297901 / 1.103036 | 1.780442 / 1.351005 |

All six runs reached the 262144-token prefix. There was no incomplete tail and no zero-variance lane or block. Block selection is by whole block, not by deleting individual escape tokens, so the omitted-block counts above also describe the selection size; the 7262 run retains 1292 of 2048 complete blocks. These selection and framing limits are the same as in the frozen design.

Independent verification was conducted by @ruedbi on 2026-11-17 using `tools/value_map_probe.py` on local samples 1993 and 1998 with Python 3.8.10. All 16 unit tests in `test_value_map_probe.py` passed. The runs reproduced the exact pooled ratios to all six decimals on both files:
- 1993: escapes/omitted 1/1; signed_digit 0.624050 / 0.763920; signed_low3 0.794635 / 0.740651; unsigned 1.000789 / 0.921650.
- 1998: escapes/omitted 2/1; signed_digit 0.643036 / 0.786777; signed_low3 0.796512 / 0.743915; unsigned 1.031150 / 0.956672.

## Reproduce

Obtain the six samples with `tools/pixls_samples.py download` and check each is CC0 first. Paths below are placeholders; the downloaded names replace `:` with `_`.

```
python -I tools/value_map_probe.py --self-test
python -I tools/pixls_samples.py check \
  '/path/to/cc0-samples/1993_Olympus - E-M1MarkII - 16bit (4_3).ORF' \
  '/path/to/cc0-samples/6343_OM System - OM-5 - 16bit (4_3).ORF' \
  '/path/to/cc0-samples/5283_OM System - OM-1 - 16bit (4_3).ORF' \
  '/path/to/cc0-samples/1998_Olympus - E-M1MarkII - 16bit (4_3).ORF' \
  '/path/to/cc0-samples/6347_OM System - OM-5 - 16bit (4_3).ORI' \
  '/path/to/cc0-samples/7262_OM System - OM-1 Mark II - 16bit (4_3).orf'

python -I tools/value_map_probe.py --phase discovery --measured-by radialmonster \
  --sample 1993 'Olympus - E-M1MarkII - 16bit (4:3).ORF' '/path/to/cc0-samples/1993_Olympus - E-M1MarkII - 16bit (4_3).ORF' \
  --sample 6343 'OM System - OM-5 - 16bit (4:3).ORF' '/path/to/cc0-samples/6343_OM System - OM-5 - 16bit (4_3).ORF' \
  --sample 5283 'OM System - OM-1 - 16bit (4:3).ORF' '/path/to/cc0-samples/5283_OM System - OM-1 - 16bit (4_3).ORF' \
  > discovery.json

python -I tools/value_map_probe.py --phase validation --measured-by radialmonster \
  --sample 1998 'Olympus - E-M1MarkII - 16bit (4:3).ORF' '/path/to/cc0-samples/1998_Olympus - E-M1MarkII - 16bit (4_3).ORF' \
  --sample 6347 'OM System - OM-5 - 16bit (4:3).ORI' '/path/to/cc0-samples/6347_OM System - OM-5 - 16bit (4_3).ORI' \
  --sample 7262 'OM System - OM-1 Mark II - 16bit (4:3).orf' '/path/to/cc0-samples/7262_OM System - OM-1 Mark II - 16bit (4_3).orf' \
  > validation.json
```

The table's numbers are the `cells[].pool.R_pool.approx` fields of the two JSON outputs; `signed_digit`, `signed_low3` and `unsigned_suffix` are the three `cells[].mapping` values, and lane count 1 or 2 is `cells[].lane_count`. `cells[].pool.R_pool` is null only when the null energy is zero; there were no such cells here.
