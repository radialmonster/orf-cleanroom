# Selected largest-strip IFDs are single-strip in a frozen public cohort

Author: @radialmonster
Verified by: @radialmonster
Lead: #591
Variant: container
Builds on: #11, #359

## Claim

The uniquely selected largest-strip-byte-total TIFF IFD has one strip in each of 100 selected public CC0, variable-size files. These single-strip observations do not test adjacency between multiple strips.

## Original evidence

The lead used `tools/strip_contiguity_audit.py` at `cf3e74928434b9e8cd18bf3a9962a0ac6e2f0e13` on 81 primary files from the frozen cohort described below. All 81 hashes matched and all selected IFDs had one strip; no cases failed. An independently written TIFF parser agreed on the aggregate records. Both implementations assisted the same human.

## Verification

After the lead was posted, a fresh run reproduced all 81 primary records exactly and added the 19 predeclared reserved files. All 100 audits succeeded and all 100 selected IFDs had one strip; the independent TIFF parser agreed on every aggregate record. Zero gaps, negative table deltas, nonascending transitions and physical overlaps were reported, but each adjacency result is vacuous: none of the selected IFDs had a second strip.

The cohort is the 100 distinct SHA-256 values in CC0, `variable` rows of `samples/manifest.csv` at `22877907b6f25863d46ee7c2b50f7b672c48ce04`. The split was frozen before measurement: interpreting the first eight hexadecimal hash digits as an integer, residue zero modulo five is reserved (19 files), all other residues primary (81). This is a fixed manifest snapshot, not a claim about every present or future CC0 file.

The tool selects the unique IFD with the largest sum of strip byte counts; tied maxima and invalid candidate strip counts fail. Its conservative failure behavior is not unconditional equivalence to a first-winner selector. No noncontiguous selected case triggered a correction review for earlier measurements. This result does not validate their other assumptions, establish multi-strip contiguity, or identify codec framing or physical rows.

## Reproduce

At source commit `cf3e74928434b9e8cd18bf3a9962a0ac6e2f0e13`, run the following example after obtaining the retained verified CC0 sample and substituting its local path:

```text
python -I -B tools/strip_contiguity_audit.py --sample 1776 "Olympus - E-PL5 - 16bit (4:3).ORF" 08e90f890283f4af3c05b14c67851dd2d52c5fcaf24522634d0d9ef734213427 <local-sample-path>
```

Repeat for each deduplicated cohort entry in the frozen manifest, with its public identity, name, expected hash and local path. Check retained CC0 provenance and local hashes. The modulo-five rule above recovers the primary and reserved subsets; the command reports failures explicitly and emits aggregate strip metadata only.