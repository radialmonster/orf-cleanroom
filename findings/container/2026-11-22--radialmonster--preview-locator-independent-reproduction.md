# Independent reproduction of the fixed Olympus preview locator

Author: @radialmonster
Verified by: @mszyndel
Lead: #920
Variant: container
Reproduces: 2026-11-21--radialmonster--metadata-first-jpeg-locator
Builds on: #155, #916, #924

## Claim

A different contributor reproduces every offset, length, dimension and exact scanner agreement in the six-file #920 finding. A separately written TIFF/MakerNote reader and JPEG marker checker agrees on all six, then on predeclared public E-M5 Mark II High Res 2856. These are bounded container-location observations, not official tag semantics, JPEG entropy conformance or physical raw-to-preview registration.

## Original evidence

The finding used `tools/preview_metadata_locator.py` at `e29899abda73da78cff723794c989ca47a9f07c7`: leading OLYMPUS MakerNote header, directory at relative 12, scalar type-13 0x2020 relative link, then LONG/count-one 0x0101 and 0x0102 for MakerNote-relative start and length. Bounds, consulted metadata spans and exact JPEG markers precede the scanner comparison. Four original inputs and the two self-verification additions gave the six rows repeated below.

## Verification

On 2026-11-22 UTC, @mszyndel re-ran the original discovery and verification commands after checking their current issue text and clean scan. The verification replayed all four fresh discovery records before opening 1051 and 3588. The published source and its dependencies are byte-identical to those at the checked-out main used for this run.

The separate reader `tools/preview_locator_independent.py` at `00ad489ee0134c4e30396d3804d82f40dc54b979` (tool PR #941) imports only the standard library, with its own bounded directory reader and JPEG marker walk. It uses the fixed declared rule and no JPEG/header scan. Eight synthetic controls passed before sample use, including all outer/inner endian combinations, changing pointer origins, a larger decoy, wrong bases, displaced header, endpoint/envelope errors and duplicate directories.

| ID | Original candidate and scanner | Separate implementation | JPEG offset | JPEG length | Dimensions |
| --- | --- | --- | ---: | ---: | --- |
| 1994 | exact match | agrees | 52224 | 1174738 | 3200x2400 |
| 1995 | exact match | agrees | 52224 | 1054035 | 3200x2400 |
| 3800 | exact match | agrees | 52224 | 970691 | 3200x2400 |
| 3802 | exact match | agrees | 52224 | 958486 | 3200x2400 |
| 1051 | exact match | agrees | 52224 | 922386 | 3200x2400 |
| 3588 | exact match | agrees | 52224 | 978222 | 3200x2400 |
| 2856, predeclared addition | exact match | agrees | 52224 | 1101713 | 3200x2400 |

All seven full content hashes were matched to retained CC0 catalogue records before and after measurement. The 2856 addition was fixed in #920 comment 7077188126 before sample runs; no rule changed for it. It extends the original finding's bodies but was already used elsewhere in the project, not a blind new capture. A later call to the unchanged original measure independently selected and compared its preview, after the separate reader had derived its interval.

The literal fresh discovery stdout SHA-256 is `408d890b3dbbcbb3966a71aac54867507a5105235992c141b31683bf46e517de`. It differs from the historical saved-report hash `d7bc9e1d2ad67be92475b3cbb1b8037527a99612432347a72c228bc6a1348bea` printed in #920. That historical report's bytes are unavailable here; its byte hash was not reproduced and no cause is established. All published interval/dimension results reproduce, and this run's four-record discovery replay is exact. This finding verifies the measured locator claim, not the historical saved-report checksum.

Public raw.pixls.us CC0 identities:

- 1994; Olympus - E-M1MarkII - 16bit (4:3).ORF; f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23
- 1995; Olympus - E-M1MarkII - 16bit (4:3).ORI; 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f
- 3800; Olympus - E-M1MarkIII - 16bit (4:3).ORF; 1e7a256eff14df75055dd7fe7a68aabefb4d8ed475317e80ebf7ff77d5bcfd3f
- 3802; Olympus - E-M1MarkIII - 16bit (4:3).ORI; 83932e61123a90a423a81f87d08c9ed66bca5feb0d900d7d1d0924845dfa9f46
- 1051; Olympus - E-M1 - 16bit (4:3).orf; 19ba17e778ae802d4039f0e88bb1cd68825780788b8058c479067e32b9a63eda
- 3588; OLYMPUS - E-M5 Mark III - 16bit (4:3).ORF; 24de6ac3bd5e668ee22fd0dbf2e344608949eb85f7342f28470ce709c9d51226
- 2856; Olympus - E-M5 Mark II - 16bit 16bit "high-res" (4:3).ORF; 5c42fa75d6b549514b722e2c50726c03e34fac4909ec3640e147ea7fa825fc8d

The scanner comparison still uses the existing scanner for reference, while the new metadata/marker implementation is separate. Both implementations share the declared header, pointer convention and test inputs; agreement does not prove generality, official meanings, a crop origin or pixel mapping. Other layouts and varying starts remain in V1 G3/G4 and #924. No private inputs or image/pixel outputs are involved.

## Reproduce

Read the scripts and imports first. Use the exact public identities above, retained verified CC0 records containing id/name/sha256/licence, the original tool commit and the separate reader commit from #941.

    python -I -B tools/preview_metadata_locator.py --phase discovery --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802
    python -I -B tools/preview_metadata_locator.py --phase verification --frozen DISCOVERY_JSON --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802 --sample 1051 FILE1051 --sample 3588 FILE3588

Retain the first command's unchanged stdout as DISCOVERY_JSON in scratch. The second requires exact replay of those four records.

    python -I -B tools/preview_locator_independent.py --records RECORDS_JSON --sample 1994 FILE1994 --sample 1995 FILE1995 --sample 3800 FILE3800 --sample 3802 FILE3802 --sample 1051 FILE1051 --sample 3588 FILE3588 --sample 2856 FILE2856

Each separate-reader candidate has the same status/offset/length/width/height as the original candidate and scanner. For the 2856 scanner check using the unchanged original measure, the following one-off call reads the named public input and prints aggregate results:

    python -I -B -c "import sys; sys.path.insert(0, 'tools'); import preview_metadata_locator as p; print(p.measure(open(sys.argv[1], 'rb').read()))" FILE2856
