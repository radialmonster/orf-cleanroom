# Corrected six-file signed-digit bridge-energy range

Author: @radialmonster
Verified by: @ruedbi
Lead: #160
Variant: unassigned
Builds on: #32, #11, #64
Corrects: 2026-10-21--radialmonster--partial-suffix-bridge-energy
Reproduces: 2026-10-21--radialmonster--six-file-suffix-bridge-range-correction

## Claim

The six-file signed_digit pooled bridge-energy range is **0.624050 to 1.091014**, across both lane counts, rounded to six decimals. The earlier finding's Claim incorrectly used 0.618104 as its minimum. That value came from exploratory sample 1995, outside its declared six-file cohort. The original finding's six-file table is correct.

This corrects only that range. None of the original 36 pooled sample/mapping/lane-count ratios is at or below 0.5. The signed_low3 range remains 0.740651 to 1.305211 and the unsigned_suffix comparison range remains 0.921650 to 1.780442. The signed_digit one-lane values on 1993 and 1998 remain 0.624050 and 0.643036, below the permutation mean. The original Partial scope and interpretation limits are unchanged; no historical private growth figure or other reading in #32 is reproduced here.

## Original evidence

The maintainer identified the transcription error on PR #145 in [this correction request](https://github.com/radialmonster/orf-cleanroom/pull/145#issuecomment-6307917831). The public design and bridge-energy machinery are @mtakemoto's work in #64 and the #32 discussion. Credit remains with that work and @radialmonster's original partial finding.

A fresh six-file run on 2026-10-21 UTC used unchanged `tools/value_map_probe.py` at commit `bcbf789d84bf75f2724f27e04ab21e2facf9e40e`. Source SHA-256: value_map_probe.py `fb6101be87a7b247c472d384e6f3396e2132e23c30f7d30a532fef418ee42115`; orf_tokens.py `c6f51ed26793b1bb400a1dc1b29d8e20f9ef734373770310c665228ce02f08ad`; orf_signature.py `b1b6f091bfb986ab7aca3ad1f513202acfaaccc424272523589142444d025afb`.

All files were checked CC0 with `tools/pixls_samples.py check` before measurement and already have manifest rows. No new variant assignment is inferred; the existing manifest rows are unassigned. IDs, public names and hashes are:

- 1993, Olympus - E-M1MarkII - 16bit (4:3).ORF: `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`.
- 6343, OM System - OM-5 - 16bit (4:3).ORF: `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`.
- 5283, OM System - OM-1 - 16bit (4:3).ORF: `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`.
- 1998, Olympus - E-M1MarkII - 16bit (4:3).ORF: `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`.
- 6347, OM System - OM-5 - 16bit (4:3).ORI: `062c4934ae9ab7595a45b56e2ad36a5ca05d75a8bed64f6d18cc88f9006ac9a9`.
- 7262, OM System - OM-1 Mark II - 16bit (4:3).orf: `d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd`.

Every file returned 262144 tokens. In the ID order above, consumed bits were 1595634, 1725464, 1822446, 1595500, 1744299 and 1790936; parsed escapes / omitted blocks were 1/1, 34/34, 313/261, 2/1, 127/118 and 1156/756. All 36 pooled ratios reproduce the original finding's table to six decimals.

## Verification

A second complete six-file run on 2026-10-21 UTC, after correction lead #160 was published at 04:48:02 UTC, repeated both phases unchanged. All aggregate output bytes matched the pre-lead run (discovery SHA-256 37924630ac0c3fada658884659c5fdb92caba89e96a306e65a6630dad39e9fa0; validation e6d6fcc6535cb821a193caba7a177c560228de6bfd67a5f8e891bfbb47237b73). The 16 synthetic tests passed again, and all six CC0 licences were checked again. The corrected minimum and maximum, every original table cell, omission count and consumed-bit count agreed. This is a correction of the original six-file statistic, so the same six-file cohort is required; adding a file or widening the prefix would change the quantity being corrected.

Independent verification was conducted by @ruedbi on 2026-11-17 using `tools/value_map_probe.py` on local samples 1993 and 1998 (Python 3.8.10). All 16 unit tests passed. On 1993 (the declared minimum candidate), the signed_digit 1-lane pooled ratio was reproduced exactly as 0.624050 (denominator 476272, numerator 297217), confirming that 0.624050 is the correct lower bound of the declared six-file cohort rather than the exploratory 0.618104 from sample 1995.

## Reproduce

Use `tools/value_map_probe.py` and its imported modules at the commit above, after reviewing their complete source. Obtain the six public samples, match the hashes above and licence-check each file. Use the exact frozen discovery and validation commands in the corrected finding's predecessor, with `python -I -B` in place of `python -I`; paths are local placeholders. The phase labels retain the original cohort partitions; they do not designate newly untouched data.

```text
python -I -B tools/value_map_probe.py --self-test
python -I -B tools/pixls_samples.py check "path/to/1993.ORF" "path/to/6343.ORF" "path/to/5283.ORF" "path/to/1998.ORF" "path/to/6347.ORF" "path/to/7262.ORF"
python -I -B tools/value_map_probe.py --phase discovery --measured-by radialmonster --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" "path/to/1993.ORF" --sample 6343 "OM System - OM-5 - 16bit (4:3).ORF" "path/to/6343.ORF" --sample 5283 "OM System - OM-1 - 16bit (4:3).ORF" "path/to/5283.ORF"
python -I -B tools/value_map_probe.py --phase validation --measured-by radialmonster --sample 1998 "Olympus - E-M1MarkII - 16bit (4:3).ORF" "path/to/1998.ORF" --sample 6347 "OM System - OM-5 - 16bit (4:3).ORI" "path/to/6347.ORF" --sample 7262 "OM System - OM-1 Mark II - 16bit (4:3).orf" "path/to/7262.ORF"
```

From both JSON outputs, select each `samples[].cells[]` with `mapping == "signed_digit"`, both lane counts, and take the minimum and maximum of `pool.R_pool`, comparing its exact numerator/denominator fractions before rounding. There are 12 such cells; the minimum is sample 1993 lane 1 and the maximum is sample 6343 lane 1. Counting all 36 ratios at or below 1/2 gives zero. The reproducible one-off summary calculation is in the correction lead's Reproduce section. All inputs are public CC0 files; no private measurements support this correction.
