# Repeated camera-model and capture-second metadata in a frozen cohort

Author: @radialmonster
Verified by: @radialmonster
Lead: #394
Variant: container
Builds on: #318

## Claim
In the 12-file cohort frozen by #318, all files have a make/model and valid second-resolution EXIF DateTimeOriginal. Exact make/model/time matching yields 11 distinct groups, including one repeated group, IDs 1994 and 1995. This is a descriptive metadata coincidence; it establishes neither physical-camera identity, capture independence, common scene or mode, nor a causal relationship. Timezones, subseconds and clock accuracy are not evaluated.

## Original evidence
#394 reports the initial run by @radialmonster on 2026-10-26 using `tools/capture_metadata_audit.py` at commit e05a31b9f337989d6d948b9bce70084690a6163f: 12/12 model and timestamp availability, 11 groups including ten singletons and the repeated 1994/1995 group. Matching hashes reused previously verified CC0 records. Public raw.pixls.us identities:

- 1799; Olympus - C5060WZ - 12bit (4:3).ORF; 3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd
- 1993; Olympus - E-M1MarkII - 16bit (4:3).ORF; 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8
- 1994; Olympus - E-M1MarkII - 16bit (4:3).ORF; f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23
- 1995; Olympus - E-M1MarkII - 16bit (4:3).ORI; 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f
- 1996; Olympus - E-M1MarkII - 16bit (4:3).ORF; eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2
- 2151; Olympus - E-400 - 16bit (4:3).ORF; 1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b
- 5283; OM System - OM-1 - 16bit (4:3).ORF; bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b
- 5284; OM System - OM-1 - 16bit (4:3).ORF; f0301e1b49a4ffbb366ec9800ebe9210f421fb25e75dcdf7d63e4b05bc063caf
- 6343; OM System - OM-5 - 16bit (4:3).ORF; ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7
- 6344; OM System - OM-5 - 16bit (4:3).ORF; 42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512
- 7262; OM System - OM-1 Mark II - 16bit (4:3).orf; d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd
- 7267; OM System - OM-1 Mark II - 16bit (4:3).orf; 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756

## Verification
A separate run after #394 was posted on 2026-10-26, by @radialmonster using the same published tool commit, reproduced the original complete 12-file report: all 12 had model and valid timestamp, with 11 groups and exactly one repeated group, 1994 and 1995. All local hashes matched retained CC0 records before metadata was examined. Both runs represent the same person and are self-verification.

As a separate predeclared extension, held-out IDs 1997 and 1998 were measured only after the lead was posted. Both had model and valid timestamp; the held-out-only report has two distinct groups and no repeated group. The combined 14-file report has model and valid timestamp for all 14, 12 distinct groups, and two repeated groups: 1994/1995 and 1996/1997, both with make OLYMPUS CORPORATION and model E-M1MarkII. This extension describes those files; it does not establish population generalization or capture independence.

The two additional public raw.pixls.us files are:

- 1997; Olympus - E-M1MarkII - 16bit (4:3).ORI; 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a
- 1998; Olympus - E-M1MarkII - 16bit (4:3).ORF; 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71

## Reproduce
At commit e05a31b9f337989d6d948b9bce70084690a6163f, after reviewing the tool and imports, set `RECORDS` to a previously verified CC0 records JSON and `P1799`, `P2151`, etc. to the corresponding local paths for the public IDs above. Quote paths with spaces. The tool checks the local hashes and does not refresh the catalogue; each separate report prints aggregates, not raw timestamps or image data. These commands use POSIX shell variable syntax:

```sh
python -I -B tools/capture_metadata_audit.py --licence-records "$RECORDS" --sample 1799 "$P1799" --sample 2151 "$P2151" --sample 1993 "$P1993" --sample 1994 "$P1994" --sample 1995 "$P1995" --sample 1996 "$P1996" --sample 5283 "$P5283" --sample 5284 "$P5284" --sample 7262 "$P7262" --sample 7267 "$P7267" --sample 6343 "$P6343" --sample 6344 "$P6344"
python -I -B tools/capture_metadata_audit.py --licence-records "$RECORDS" --sample 1997 "$P1997" --sample 1998 "$P1998"
python -I -B tools/capture_metadata_audit.py --licence-records "$RECORDS" --sample 1799 "$P1799" --sample 2151 "$P2151" --sample 1993 "$P1993" --sample 1994 "$P1994" --sample 1995 "$P1995" --sample 1996 "$P1996" --sample 5283 "$P5283" --sample 5284 "$P5284" --sample 7262 "$P7262" --sample 7267 "$P7267" --sample 6343 "$P6343" --sample 6344 "$P6344" --sample 1997 "$P1997" --sample 1998 "$P1998"
```
