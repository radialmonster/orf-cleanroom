# OM-5 phase comparison across two bands reproduces

Author: @radialmonster
Verified by: @radialmonster
Lead: #356
Variant: unassigned
Builds on: #144, #149, #351
Partial: 6343 top versus later candidate-band phase comparison and predeclared 6344 extension; other original files, null claims and physical-row interpretation not verified

## Claim

The selected phase for the fixed b2+b4 preview-luma score on OM-5 file 6343 differs between candidate start rows 0 and 1000 under the declared search. This is a bounded descriptive comparison on unassigned files, not a V1 signature, physical row origin, phase law, value or decode.

## Original evidence

Lead #356 reported that public CC0 id 6343, `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`, selects phase 716 with r about +0.409 at start row 0, but phase 3981 with r about +0.055 at start row 1000; the later band at phase 716 gives about +0.003. Its method used candidate stride 5472, 300 rows, a 63-token window, b2+b4 sum mapping, coarse step 16 and refinement +/-16. Phase may overlap the next candidate row; the preview DC is a numeric camera-rendering reference, not ground truth. The search covers its coarse and refined family, not every possible phase.

## Verification

After the lead was posted, the same human reran 6343 using `tools/token_luma_phase_probe.py` at `76ec53213cb442aae270294a0e91055b78fadb2a`: start 0 had phase 0 r=+0.07506 and selected phase 716 r=+0.40894; start 1000 had phase 0 r=-0.01786 and selected phase 3981 r=+0.05492. An auxiliary scan included phase 716 at start 1000, r=+0.00258. Only this point is used from the auxiliary scan, whose coarse step differs from the full search. These reproduce the lead's rounded band comparison. This is self-verification; agents assisting the same human are not independent human verifiers.

The predeclared additional public CC0 file 6344, `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512`, has 8200x6132 payload geometry and uses its previously reported candidate stride 8365. At start 0 phase 0 gave +0.06531 and the search selected phase 1015 at +0.34505; at start 1000 phase 0 gave +0.01909 and the search selected phase 8226 at +0.03173. Both runs used 300 rows, window 63, step 16 and refine 16 without a shuffle. These previously studied files and regions are not blind or independent-capture tests. Both hashes were matched to retained verified CC0 records and existing manifest entries.

The two full 6343 searches evaluate 343 coarse phases and 33 refinement phases; the 6344 searches evaluate 524 coarse and 33 refinement phases. The selected phase is the best in the evaluated family, not necessarily the global maximum. Nine reported phase-point scores were independently checked against scalar arithmetic at printed precision; this point check does not independently establish the full search maximum. No shuffle null, phase law, physical rows, population generality or codec is established here; the other original files and null claims remain open.

## Reproduce

At `76ec53213cb442aae270294a0e91055b78fadb2a`, use local files matching the two public hashes above:

```sh
python -I -B tools/token_luma_phase_probe.py "$FILE6343" --stride 5472 --rows 300 --start-row 0 --window 63 --map sum --step 16 --refine 16 --perms 0 --seed 1
python -I -B tools/token_luma_phase_probe.py "$FILE6343" --stride 5472 --rows 300 --start-row 1000 --window 63 --map sum --step 16 --refine 16 --perms 0 --seed 1
python -I -B tools/token_luma_phase_probe.py "$FILE6343" --stride 5472 --rows 300 --start-row 1000 --window 63 --map sum --step 716 --refine 0 --perms 0 --seed 1
python -I -B tools/token_luma_phase_probe.py "$FILE6344" --stride 8365 --rows 300 --start-row 0 --window 63 --map sum --step 16 --refine 16 --perms 0 --seed 1
python -I -B tools/token_luma_phase_probe.py "$FILE6344" --stride 8365 --rows 300 --start-row 1000 --window 63 --map sum --step 16 --refine 16 --perms 0 --seed 1
```
