# Selected largest-strip IFDs are single-strip in six public variable-size files

Author: @radialmonster
Verified by: @ruedbi
Lead: #591
Variant: container
Builds on: #11, #359
Reproduces: 2026-10-28--radialmonster--single-strip-selected-ifds
Partial: the single-strip structure on six public CC0 variable-size E-M1 Mark II files (1993, 1994, 1995, 1996, 1997, 1998); not the full 100-file cohort or independent TIFF parser agreement.

## Claim

The uniquely selected largest-strip-byte-total TIFF IFD has one strip in six public CC0 variable-size files from an E-M1 Mark II camera (ids 1993, 1994, 1995, 1996, 1997, 1998). These single-strip observations do not test adjacency between multiple strips.

## Original evidence

The lead used `tools/strip_contiguity_audit.py` at `cf3e74928434b9e8cd18bf3a9962a0ac6e2f0e13` on 81 primary files from the frozen 100-file cohort. All 81 hashes matched and all selected IFDs had one strip; no cases failed. An independently written TIFF parser agreed on the aggregate records. In a follow-up run, all 100 audits (81 primary + 19 reserved) succeeded with single strips.

## Verification

Independent verification was conducted by @ruedbi on 2026-11-18 using `tools/strip_contiguity_audit.py` at commit `aaf77e5d04c8f54b23f84b87269a476095dbfc8d` with Python standard library (Python 3.8+).

All 7 unit tests in `tools/test_strip_contiguity_audit.py` passed.

A fresh rerun was performed on 6 public CC0 variable-size files from `samples/manifest.csv` (Olympus E-M1 Mark II):
- id 1993: `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` (5240x3912, payload 15760125 bytes)
- id 1994: `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23` (10400x7792, payload 60993898 bytes)
- id 1995: `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` (5240x3912, payload 15768425 bytes)
- id 1996: `eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2` (10400x7792, payload 60996963 bytes)
- id 1997: `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a` (5240x3912, payload 15767553 bytes)
- id 1998: `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71` (5240x3912, payload 15772675 bytes)

All 6 SHA-256 hashes matched the retained manifest. For every file, `strip_contiguity_audit.py` selected the unique largest-strip IFD and confirmed:
- `strip_count: 1`
- `single_strip: true`
- `table_adjacent: true`
- `forward_gaps: 0`
- `negative_table_deltas: 0`
- `nonascending_transitions: 0`
- `physical_overlap: false`
- `failures: 0`
- `status: "ok"`

Total files audited: 6; total failures: 0.

## Reproduce

Using `tools/strip_contiguity_audit.py` with standard library Python:

```text
python -I -B tools/strip_contiguity_audit.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 <local-path-to-1993>
python -I -B tools/strip_contiguity_audit.py --sample 1994 "Olympus - E-M1MarkII - 16bit (4:3).ORF" f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23 <local-path-to-1994>
python -I -B tools/strip_contiguity_audit.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f <local-path-to-1995>
python -I -B tools/strip_contiguity_audit.py --sample 1996 "Olympus - E-M1MarkII - 16bit (4:3).ORF" eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2 <local-path-to-1996>
python -I -B tools/strip_contiguity_audit.py --sample 1997 "Olympus - E-M1MarkII - 16bit (4:3).ORI" 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a <local-path-to-1997>
python -I -B tools/strip_contiguity_audit.py --sample 1998 "Olympus - E-M1MarkII - 16bit (4:3).ORF" 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 <local-path-to-1998>
```

Check retained CC0 provenance and local hashes before running. The tool reports explicit JSON and zero exit code on success.
