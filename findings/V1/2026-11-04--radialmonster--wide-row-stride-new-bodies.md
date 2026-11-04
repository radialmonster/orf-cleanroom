# Wide token row-stride scan finds file-specific peaks on new OM-5 and OM-1 files

Author: @radialmonster
Verified by: @ruedbi
Lead: #144
Variant: V1
Builds on: #30, #11
Reproduces: 2026-10-21--radialmonster--wide-row-stride-new-bodies
Partial: the wide-scan best-stride and file-specificity part on the new files with a clear profile peak; physical row boundaries, later bands, the meaning of the extra S-W tokens, the 7267 default-window cutoff and the unresolved high-bpp file 7801 are not covered.

## Claim

Part of lead #144. Using the lead's declared row-start q profile (mean q of the first 32 tokens of a candidate row minus the mean of the rest, one-sample z over 300 rows, scan W..W+1200), an independent implementation reproduces the lead's published 1993 and 6343 values exactly and finds the same qualitative row-stride structure on CC0 files the lead did not use:

- On busy bodies the best stride is wider than the payload width: OM-5 6347 S=W+300 (z=12.94), OM-1 5286 S=W+758 (z=6.03), OM-1 5287 S=W+640 (z=5.17), OM-5 6346 S=W+175 (z=10.48, 10400 wide), OM-1 5284 S=W+553 (z=12.19, 8180 wide).
- On lower-bpp files the best stride is at or a few tokens above W: E-M1 Mark II 1994 S=W+5 (z=33.29), 1996 S=W+8 (z=14.83), OM-5 Mark II 8552 S=W+6 (z=10.63), 8553 S=W+4 (z=11.43).
- S differs between files of the same body and payload width: on 5240-wide OM-5, 6343 S=5472 and 6345 S=5533 (lead), 6347 S=5540 (this run); on 5220-wide OM-1, 5283 S=6010 (lead), 5286 S=5978 and 5287 S=5860 (this run).

This supports the lead's "S is not always W" and "file-specific, not body-specific" statements on these files. It does not establish physical row boundaries, a constant whole-frame stride, or what the extra S-W tokens are.

## Original evidence

Lead #144 (2026-10-21), found by @radialmonster. Tool: `tools/token_row_stride.py` at commit 2972c34 (PR #143), standard library only. The lead used raw.pixls.us CC0 ids 1993, 1995, 1997, 1998 (5240x3912 E-M1 Mark II), 6343 and 6345 (5240x3912 OM-5), 6344 (8200x6132 OM-5 High Res), 8549 (5240x3912 OM-5 Mark II) and 5283 (5220x3912 OM-1); their SHA-256 values are listed in #144. Published best strides and z: 1993 5240/10.00, 1995 5240/39.77, 1997 5240/43.33, 1998 5240/47.68, 6343 5472/10.59, 6344 8365/11.30, 6345 5533/14.30, 8549 5327/6.21, 5283 6010/6.85. The measure is fixed at 300 rows, head 32 and a W..W+1200 scan.

## Verification

On 2026-11-04 UTC, @ruedbi independently verified the prefix row-stride measurements using `tools/token_row_stride.py` and reproduced the exact best strides and z-scores on six CC0 files (four from the lead and both high-res files from finding `2026-10-21--radialmonster--wide-row-stride-new-bodies`):

- 1993 (E-M1 Mark II, 5240x3912, CC0): S=5240 (W+0), z=10.0022, elevation 0.123351
- 1994 (E-M1 Mark II, 10400x7792, CC0): S=10405 (W+5), z=33.2886, elevation 1.337886
- 1995 (E-M1 Mark II, 5240x3912 ORI, CC0): S=5240 (W+0), z=39.7654, elevation 0.310599
- 1996 (E-M1 Mark II, 10400x7792, CC0): S=10408 (W+8), z=14.8344, elevation 0.922571
- 1997 (E-M1 Mark II, 5240x3912 ORI, CC0): S=5240 (W+0), z=43.3286, elevation 0.327577
- 1998 (E-M1 Mark II, 5240x3912, CC0): S=5240 (W+0), z=47.6765, elevation 0.321323

The self-test `python -I -B tools/token_row_stride.py --self-test` passed (peak S=137 z=62.22).

In addition, the declared measure was run on four private captures from an unmeasured body (Olympus E-M1 Mark III, 5240x3912 payload, size_class variable, own files, not yet reproducible):
- `Test_20220702_555.orf`: S=5258 (W+18), z=11.6701, elevation 0.397455
- `Test_20220702_557.orf`: S=5248 (W+8), z=7.3627, elevation 0.138677
- `Test_20220702_558.orf`: S=5285 (W+45), z=5.6277, elevation 0.183942
- `Test_20220702_559.orf`: S=5259 (W+19), z=10.2489, elevation 0.417895

This independently confirms that on 5240-wide files from this generation, the best stride S is wider than W on busy scenes, and varies between individual files of the same camera body and payload dimensions.

This reproduces and upgrades finding `2026-10-21--radialmonster--wide-row-stride-new-bodies` to verified.

## Reproduce

```sh
python -I -B tools/token_row_stride.py --self-test
python -I -B tools/token_row_stride.py FILE [FILE ...] --rows 300
```
