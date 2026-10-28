# Correct 6343 payload width in nominal-offset findings

Author: @radialmonster
Verified by: @radialmonster
Lead: #684
Variant: unassigned
Builds on: #671, #677, #681
Corrects: 2026-10-28--radialmonster--nominal-row-difference-energy, 2026-10-28--radialmonster--nominal-half-width-energy

## Claim

The width sentence in both corrected findings incorrectly groups public sample 6343 with the 5220-wide 5283. The selected payload width is 5240 for 6343 and 5220 for 5283. The original 6343 numerical offset rows already use W=5240; this corrects the prose and does not change those energy tables.

## Original evidence

Audited 600-row row, half-width and centered-block reports each record 6343 as 5240 x 3912 and 5283 as 5220 x 3912. The manifest also records those dimensions. The 6343 row offsets in the first finding are 5239/5240/5241 and 10479/10480/10481; half-width offsets in the second are 2619/2620/2621, all consistent with W=5240.

## Verification

After this lead was posted, `tools/orf_signature.py` at commit `0634fd5bd2b6aa8c02b7a3f7a8cd5ded60d81fc5` was freshly run on both original files and on additional previously exposed files 1993 and 1995. A separately written TIFF reader walked next-IFD and SubIFD links, selected the largest total strip-byte count, and independently matched identities, dimensions and payload byte counts. Both implementations assisted the same human; the two additional files qualify the fresh check but are not blind captures. The dimensions describe the selected TIFF payload IFD and do not establish physical row framing.

| ID | Selected payload width | Selected payload height | Payload bytes |
|---|---:|---:|---:|
| 5283 | 5220 | 3912 | 20003129 |
| 6343 | 5240 | 3912 | 17772487 |
| 1993 | 5240 | 3912 | 15760125 |
| 1995 | 5240 | 3912 | 15768425 |

## Reproduce

The retained verified public CC0 inputs are:

- 5283: `OM System - OM-1 - 16bit (4:3).ORF`, SHA-256 `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`
- 6343: `OM System - OM-5 - 16bit (4:3).ORF`, SHA-256 `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`
- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`

At commit `0634fd5bd2b6aa8c02b7a3f7a8cd5ded60d81fc5`, verify the identities and hashes, substitute local paths, and run:

```text
python -I -B tools/orf_signature.py FILE5283 FILE6343 FILE1993 FILE1995
```

The tool prints the selected payload dimensions and byte counts. The two original finding files remain unchanged; physical framing and the private historical methods remain open.
