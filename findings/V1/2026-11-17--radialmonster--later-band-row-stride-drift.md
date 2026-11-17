# V1 row-stride candidate moves in later payload bands

Author: @radialmonster
Verified by: @ruedbi
Lead: #144
Variant: V1
Builds on: 2026-10-21--radialmonster--wide-row-stride-new-bodies, #30, #11
Reproduces: 2026-10-22--radialmonster--later-band-row-stride-drift
Partial: the nine-file prefix row-stride table and later-band candidate-peak movement on E-M1 Mark II ids 1995 and 1998 and OM-5 High Res id 6344 only

## Claim

Lead #144 measured a row-start q profile and reported one best candidate
stride S per file from a 300-row prefix. Using the merged
`tools/token_band_profile.py`, which implements the same declared profile,
all nine published prefix S and z values reproduce to the lead's published
two decimals. But the prefix S is not a whole-payload candidate: at later
300-row bands the contrast at the fixed prefix S is often negative, and a
local scan of S-64..S+64 finds a different later-band maximum.

Examples from the fixed-prefix tables below:

- E-M1 Mark II 1995, S=5240: z falls from +39.7654 in the prefix to -3.5920
  at start row 1000 and -22.2917 at start row 2000. The local scan peaks at
  S=5244 (z=+5.6073 and +16.1527) at those starts.
- E-M1 Mark II 1998, S=5240: z falls from +47.6765 to -3.8673 at start row
  1000 and -36.1343 at start row 2000. The local scan peaks at S=5244
  (z=+5.9359) and S=5246 (z=+12.5438).
- OM-5 High Res 6344, S=8365: z is +11.2953 in the prefix and -12.5861 at
  start row 5000. The local scan peaks at S=8353 (z=+7.9237).

The later-band peaks are broad: on 1995 start 2000, S=5244, 5246 and 5251
give z=+16.153, +14.893 and +14.084; on 1998 start 2000, S=5246, 5239 and
5244 give +12.544, +12.352 and +11.789; on 6344 start 5000, S=8353, 8371
and 8376 give +7.924, +7.823 and +6.315. This is a candidate-stride or
phase movement, not a unique physical row boundary.

This confirms the lead's note that the prefix stride may change later in
the file. It shows that a single S measured on the prefix should not be
used as a whole-payload row segmentation without a per-band check.

## Original evidence

Lead #144 (2026-10-21), found by @radialmonster. The lead's nine CC0
inputs, with the SHA-256 values from the lead:

- 1993 Olympus - E-M1MarkII - 16bit (4:3).ORF
  0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8
- 1995 Olympus - E-M1MarkII - 16bit (4:3).ORI
  8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f
- 1997 Olympus - E-M1MarkII - 16bit (4:3).ORI
  89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a
- 1998 Olympus - E-M1MarkII - 16bit (4:3).ORF
  4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71
- 6343 OM System - OM-5 - 16bit (4:3).ORF
  ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7
- 6344 OM System - OM-5 - 16bit (4:3).ORF
  42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512
- 6345 OM System - OM-5 - 16bit (4:3).ORI
  c8277d133c7ac86c7e4af5787fa06515fef8fe044c1b22209c62704537c48e02
- 8549 OM System - OM-5 Mark II - 16bit (4:3).ORF
  c6fe861982ddc18464cf6858d2700f6813cc3a17956bcb12d1179212c999c76a
- 5283 OM System - OM-1 - 16bit (4:3).ORF
  bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b

The existing finding
`2026-10-21--radialmonster--wide-row-stride-new-bodies` covers the
wide-scan best stride on 11 new CC0 files and explicitly leaves later row
bands open. This finding uses the lead's nine files instead, so it does not
repeat that scan.

## Verification

New run on 2026-10-22 UTC, after the lead was posted. All nine local inputs
matched the retained verified-CC0 inventory by SHA-256 and every file
already has a `samples/manifest.csv` row; no catalogue request or manifest
row was added. No new CC0 input was available for the lead's nine-file
comparison in this run; the new coverage is later bands on the same public
files, which `findings/README.md` permits when it is described.

Tool: `tools/token_band_profile.py` at upstream main `f418be5`, Python
3.13.15. It is an independent implementation of the declared profile:
absolute candidate rows r*S from payload bit zero; mean q of the first 32
tokens minus the mean of the rest; one-sample z over 300 rows; q capped at
40; escape tokens retained; zero extra escape bits. It is not the lead's
`token_row_stride.py` (PR #143). `python -I -B tools/test_token_band_profile.py`
passes all six tests.

Prefix reproduction, head 32, 300 rows. "Lead z" is the lead's published
value; "this run" is `signed_mean_over_se`:

- 1993 S=5240: lead 10.00; this run +10.0022
- 1995 S=5240: lead 39.77; this run +39.7654
- 1997 S=5240: lead 43.33; this run +43.3286
- 1998 S=5240: lead 47.68; this run +47.6765
- 6343 S=5472: lead 10.59; this run +10.5880
- 6344 S=8365: lead 11.30; this run +11.2953
- 6345 S=5533: lead 14.30; this run +14.2956
- 8549 S=5327: lead 6.21; this run +6.2053
- 5283 S=6010: lead 6.85; this run +6.8495

Fixed-prefix S at later 300-row bands, all starts that fit the token
stream. Values are z; negative values mean the first-32 q mean is below
the rest at that candidate stride:

- 1993 S=5240: 0 +10.0022; 1000 +1.8322; 2000 +3.6486; 3000 +7.4331;
  3612 +5.2988.
- 1995 S=5240: 0 +39.7654; 1000 -3.5920; 2000 -22.2917; 3000 -1.0243;
  3612 +14.0993.
- 1997 S=5240: 0 +43.3286; 1000 -5.3678; 2000 -30.9358; 3000 +15.4742;
  3612 +13.3464.
- 1998 S=5240: 0 +47.6765; 1000 -3.8673; 2000 -36.1343; 3000 +12.7432;
  3612 +13.2572.
- 6343 S=5472: 0 +10.5880; 1000 -1.3771; 2000 +0.2090; 3000 +1.4817;
  3612 +1.0082.
- 6344 S=8365: 0 +11.2953; 1000 +0.1399; 2000 -2.4181; 3000 -0.7908;
  4000 +0.3268; 5000 -12.5861; 5832 -0.1645.
- 6345 S=5533: 0 +14.2956; 1000 -0.5953; 2000 +1.1614; 3000 +0.4443;
  3612 -0.6886.
- 8549 S=5327: 0 +6.2053; 1000 +0.6484; 2000 -0.7267; 3000 +2.1202;
  3612 +0.5194.
- 5283 S=6010: 0 +6.8495; 1000 +0.1360; 2000 -0.2134; 3000 +1.2763.
  Start 3612 is incomplete (the token stream does not supply 300 rows at
  that absolute index) and is excluded from the claim.

Local scan of S-64..S+64 at the same candidate-row starts, top entries:

- 1995 start 1000: fixed S=5240 z=-3.5920; top 5244 +5.6073, 5248 +4.541,
  5235 +3.831, 5263 +3.728, 5239 +3.401.
- 1995 start 2000: fixed S=5240 z=-22.2917; top 5244 +16.153, 5246 +14.893,
  5251 +14.084, 5239 +8.845, 5249 +6.605.
- 1998 start 1000: fixed S=5240 z=-3.8673; top 5244 +5.9359, 5248 +5.288,
  5263 +5.051, 5235 +4.174, 5256 +3.725.
- 1998 start 2000: fixed S=5240 z=-36.1343; top 5246 +12.5438, 5239
  +12.352, 5244 +11.789, 5249 +11.025, 5251 +9.370.
- 6344 start 5000: fixed S=8365 z=-12.5861; top 8353 +7.9237, 8371 +7.823,
  8376 +6.315, 8356 +5.923, 8374 +5.488.

A second run of both scripts produced byte-identical JSON on this host.
The local scan is exploratory: it retains every candidate and uses no
significance threshold. The broad peaks mean it cannot separate a real
stride change from a phase shift, and it is only reported for the three
files above.

Independent verification was conducted by @ruedbi on 2026-11-17 using
`tools/token_band_profile.py` on local samples 1993, 1995, 1997, and 1998
(`Python 3.8.10`). All unit tests in `tools/test_token_band_profile.py` passed.
The probe reproduced the prefix z scores and later-band z scores across all
four tested files to four decimal places (e.g. 1995 prefix +39.7654, start 1000
-3.5920, start 2000 -22.2917; 1998 prefix +47.6765, start 1000 -3.8673,
start 2000 -36.1343). The local scan on 1995 and 1998 confirmed the later-band
candidate peak shifts (1995 start 1000 peak at S=5244 z=+5.6073; start 2000
peak at S=5244 z=+16.1527; 1998 start 1000 peak at S=5244 z=+5.9359; start 2000
peak at S=5246 z=+12.5438).

## Reproduce

Read `tools/token_band_profile.py` and `tools/test_token_band_profile.py`
and check the nine local hashes against the retained CC0 record first.
Then save the script below as `bands.py` in the repository root and run it
with the directory holding the nine raw.pixls.us files (downloaded names
use `_` for `:`).

`bands.py`:

    import json
    import os
    import sys

    sys.path.insert(0, "tools")
    import token_band_profile as P

    D = sys.argv[1]
    SAMPLES = [
        ("1993", "0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8", 5240,
         "1993_Olympus - E-M1MarkII - 16bit (4_3).ORF", [0, 1000, 2000, 3000, 3612]),
        ("1995", "8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f", 5240,
         "1995_Olympus - E-M1MarkII - 16bit (4_3).ORI", [0, 1000, 2000, 3000, 3612]),
        ("1997", "89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a", 5240,
         "1997_Olympus - E-M1MarkII - 16bit (4_3).ORI", [0, 1000, 2000, 3000, 3612]),
        ("1998", "4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71", 5240,
         "1998_Olympus - E-M1MarkII - 16bit (4_3).ORF", [0, 1000, 2000, 3000, 3612]),
        ("6343", "ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7", 5472,
         "6343_OM System - OM-5 - 16bit (4_3).ORF", [0, 1000, 2000, 3000, 3612]),
        ("6344", "42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512", 8365,
         "6344_OM System - OM-5 - 16bit (4_3).ORF", [0, 1000, 2000, 3000, 4000, 5000, 5832]),
        ("6345", "c8277d133c7ac86c7e4af5787fa06515fef8fe044c1b22209c62704537c48e02", 5533,
         "6345_OM System - OM-5 - 16bit (4_3).ORI", [0, 1000, 2000, 3000, 3612]),
        ("8549", "c6fe861982ddc18464cf6858d2700f6813cc3a17956bcb12d1179212c999c76a", 5327,
         "8549_OM System - OM-5 Mark II - 16bit (4_3).ORF", [0, 1000, 2000, 3000, 3612]),
        ("5283", "bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b", 6010,
         "5283_OM System - OM-1 - 16bit (4_3).ORF", [0, 1000, 2000, 3000, 3612]),
    ]
    for sid, sha, stride, name, starts in SAMPLES:
        result = P.measure(os.path.join(D, name), sha, [stride], starts, 300, 32)
        print(json.dumps({
            "pixls_id": sid,
            "stride": stride,
            "token_shortfall": result["token_shortfall"],
            "bands": [{
                "start": band["start_candidate_row"],
                "z": band["signed_mean_over_se"],
                "mean": band["mean_head_minus_rest"],
                "complete": band["complete"],
            } for band in result["bands"]],
        }))

Run:

    python -I -B bands.py /path/to/cc0

For the local scan, save this as `scan.py`:

    import json
    import os
    import sys

    sys.path.insert(0, "tools")
    import token_band_profile as P

    path, digest = sys.argv[1], sys.argv[2]
    stride, start = int(sys.argv[3]), int(sys.argv[4])
    result = P.measure(path, digest,
                       list(range(stride - 64, stride + 65)), [start], 300, 32)
    top = sorted(result["bands"],
                 key=lambda band: band["signed_mean_over_se"], reverse=True)[:8]
    print(json.dumps([{
        "stride": band["stride"],
        "z": band["signed_mean_over_se"],
        "mean": band["mean_head_minus_rest"],
    } for band in top]))

Run it for the five reported cases:

    python -I -B scan.py "/path/to/cc0/1995_Olympus - E-M1MarkII - 16bit (4_3).ORI" 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f 5240 1000
    python -I -B scan.py "/path/to/cc0/1995_Olympus - E-M1MarkII - 16bit (4_3).ORI" 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f 5240 2000
    python -I -B scan.py "/path/to/cc0/1998_Olympus - E-M1MarkII - 16bit (4_3).ORF" 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 5240 1000
    python -I -B scan.py "/path/to/cc0/1998_Olympus - E-M1MarkII - 16bit (4_3).ORF" 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 5240 2000
    python -I -B scan.py "/path/to/cc0/6344_OM System - OM-5 - 16bit (4_3).ORF" 42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512 8365 5000

## Limits

- The profile uses candidate boundaries r*S from payload bit zero; it does
  not establish physical rows, CFA phase, or a unique stride.
- The later-band local maxima are broad. A moving peak can be a real stride
  change or a phase shift; this run does not distinguish them.
- The local scan covers three files and five bands only. The fixed-S run
  covers all nine files, but one 5283 band is incomplete.
- No significance threshold, whole-frame constancy, extra-token meaning,
  predictor, value mapping or decode is claimed.
- The lead's 7267 and 7801 edge cases and the new-file wide scan are not
  retested here; the existing finding covers the latter.
