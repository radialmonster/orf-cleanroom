# Scoped declaration non-overlap repeats and extends to the E-500 exterior

Author: @radialmonster
Verified by: @radialmonster
Lead: #984
Variant: container
Builds on: #949, #964, #978, #982

## Claim

The fixed 36-byte E-1 and E-300 intervals from #984 reproduce with no overlap against the reached outer declarations. The unchanged audit finds no overlap on the predeclared E-500 interval [3982,4018) either. It does not establish whether those bytes are unused or who owns them.

## Original evidence

Lead #984 fixed exterior intervals using the #982 absolute candidate end and the independently declared MakerNote end. The audit considers TIFF header and reached IFD0/next/SubIFD and standard Exif declarations, typed out-of-line values except the MakerNote envelope, declared strips and explicit JPEG interchange pairs. It does not read through the target to traverse a directory or inspect its contents. Private, MakerNote, GPS and interoperability directories remain out of scope.

## Verification

On 2026-11-25 after #984 was posted and scanned, the complete original aggregate for E-1 1800 and E-300 2878 matched before the E-500 run. The equality gate was recorded at 17:52:57 UTC. The [extension scope](https://github.com/radialmonster/orf-cleanroom/issues/984#issuecomment-7170120886) was fixed publicly before opening the third file for declaration analysis. Its exact interval comes from #993. The E-500 previously informed that separate top-directory and candidate extent check.

| Public identity | SHA-256 | Fixed half-open interval | Reached IFDs | Overlap declarations | Unique overlap bytes |
| --- | --- | --- | ---: | ---: | ---: |
| 1800 Olympus E-1 | `042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c` | [3826,3862) | 3 | 0 | 0/36 |
| 2878 Olympus E-300 | `6d818dbff78b3e2efa4835f568d04733052b9211e6bc65b0a3748a841170e95b` | [4078,4114) | 3 | 0 | 0/36 |
| 3540 Olympus E-500 | `fa5a4759b2de2b573f59629ad1baf64ad04a85fb8fe1fb3cbf68e08a42fff4f0` | [3982,4018) | 3 | 0 | 0/36 |

All three inputs passed full retained public CC0 hash checks. No branch issue was reported in either original audit or the extension. A separate bounded declaration reader agreed on the E-500 scope, IFD count and zero union result. This is same-account verification. No inference follows about unvisited or undeclared data, private structure, or offset semantics.

## Reproduce

Use `tools/legacy_exterior_declarations.py` at `5bef0e9f6cc8cfd81b47a2746d419734bdbb9982`. The original tool and traversal rules are unchanged from `36ccb595c283b0359647d6e3e21daa257d267ed9`. The added option permits only the fixed E-500 identity and target. Do the discovery equality check before opening the extension file; the CLI keeps the cohorts separate but does not track replay order.

    python -I -B tools/test_legacy_exterior_declarations.py
    python -I -B tools/legacy_exterior_declarations.py --sample 1800 FILE1800 --sample 2878 FILE2878
    python -I -B tools/legacy_exterior_declarations.py --extension --sample 3540 FILE3540

Compare the exact targets, reached count, reported issues, intersections and total coverage. All samples are listed in the manifest. No result uses private inputs.
