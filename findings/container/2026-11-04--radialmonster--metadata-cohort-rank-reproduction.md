# Metadata cohort design remains rank deficient after adding a second ORI

Author: @radialmonster
Verified by: @ruedbi
Lead: #318
Variant: container
Builds on: #299, #307
Reproduces: 2026-10-26--radialmonster--metadata-cohort-rank-reproduction
Partial: categorical metadata design rank, aliases, cells and conditional increments

## Claim

The frozen 12-file public manifest cohort has an additive treatment-coded metadata design with 15 columns, rank 11 and nullity 4. Its 11 observed factor cells are saturated by the design. Adding the preselected public ID 1997 yields 13 files but the same 15 columns, rank 11, nullity 4 and 11 cells. The mode label is a width-derived manifest proxy. These are metadata algebra results, not codec, capture-independence or causal claims.

## Original evidence

Lead #318 measured the 12 inputs below using `tools/cohort_design_audit.py` at commit `0dc8abc988844867ee7dff8fd1172ef505773834` and the manifest with SHA-256 `535d99ace97e3424d561ef1ed35cb8003c3cad3fd827c31ee0ac82d96d66db32`. The conditional rank increments for body, recorded mode, geometry and extension were 2, 0, 3 and 1. The original cohort has 11 cells; IDs 1994 and 1996 share its only repeated cell.

- 1799; Olympus - C5060WZ - 12bit (4:3).ORF; 3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd
- 2151; Olympus - E-400 - 16bit (4:3).ORF; 1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b
- 1993; Olympus - E-M1MarkII - 16bit (4:3).ORF; 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8
- 1994; Olympus - E-M1MarkII - 16bit (4:3).ORF; f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23
- 1995; Olympus - E-M1MarkII - 16bit (4:3).ORI; 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f
- 1996; Olympus - E-M1MarkII - 16bit (4:3).ORF; eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2
- 5283; OM System - OM-1 - 16bit (4:3).ORF; bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b
- 5284; OM System - OM-1 - 16bit (4:3).ORF; f0301e1b49a4ffbb366ec9800ebe9210f421fb25e75dcdf7d63e4b05bc063caf
- 7262; OM System - OM-1 Mark II - 16bit (4:3).orf; d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd
- 7267; OM System - OM-1 Mark II - 16bit (4:3).orf; 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756
- 6343; OM System - OM-5 - 16bit (4:3).ORF; ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7
- 6344; OM System - OM-5 - 16bit (4:3).ORF; 42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512

## Verification

On 2026-11-04 UTC, @ruedbi independently reproduced the metadata design rank and cell structure as a separate run on the current `samples/manifest.csv`.

Running `tools/test_cohort_design_audit.py` passed all 10 tests. Running `tools/cohort_design_audit.py` with the frozen 12 public IDs reproduced: 12 files, 15 columns, rank 11, nullity 4, 11 cells, and conditional rank increments body 2, recorded mode 0, geometry 3, extension 1. The sole repeated cell remains E-M1MarkII, 10400x7792, hires ORF (1994 and 1996).

Adding the preselected public ID 1997 (Olympus E-M1MarkII, SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`, CC0) reproduced: 13 files, 15 columns, rank 11, nullity 4, 11 cells, and identical conditional rank increments (2/0/3/1). IDs 1995 and 1997 share the normal 5240x3912 ORI cell.

An independent exact rational forward-elimination check confirmed rank 11, nullity 4, and independence of all four nullspace vectors, with all four evaluating to zero across every row.

This reproduces finding `2026-10-26--radialmonster--metadata-cohort-rank-reproduction` as an independent verification by a different contributor (@ruedbi).

## Reproduce

```sh
python -I -B tools/test_cohort_design_audit.py
python -I -B tools/cohort_design_audit.py --manifest samples/manifest.csv --ids 1799 2151 1993 1994 1995 1996 5283 5284 7262 7267 6343 6344
python -I -B tools/cohort_design_audit.py --manifest samples/manifest.csv --ids 1799 2151 1993 1994 1995 1996 5283 5284 7262 7267 6343 6344 1997
```
