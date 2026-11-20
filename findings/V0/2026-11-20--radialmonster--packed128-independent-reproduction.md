# packed-12.8 independently reproduced, with explicit stride-control labels

Author: @radialmonster
Verified by: @mszyndel
Lead: #70
Variant: V0
Reproduces: 2026-10-20--radialmonster--packed-12-8-groups-of-ten-values
Corrects: 2026-10-20--radialmonster--packed-12-8-groups-of-ten-values
Builds on: #28, #75

## Claim

The five public packed-12.8 files reproduce the layout and whole-payload claims: rows comprise 16-byte groups containing five LSB-first 3-byte units, each yielding two 12-bit values, with byte 15 zero in every group. The group16-lsb-pad15 family is selected in all five default-window repeats, all five repeats of the original finding's wider command, and all five predeclared larger-window checks. All 17,027,024 whole-payload byte-15 positions are zero, all group tails are empty and all payload byte counts equal width*height*8/5.

The fresh reference-decoder run matches all five full conformance rows, including output hashes and exact payload ends. This uses the repository's reference decoder, not a new implementation or a physical pair-order test. The order within each two-value unit remains unresolved, as do black level and saturation.

The packing claim is reproduced; this finding corrects two reporting details in the original Verification prose. A requested 3200-column window actually reads 3180 columns because the tool rounds down to a multiple of 30. The two bracketed stride correlations labelled as one-byte-off values in that prose are the printed delta -2 and delta -1 entries, not the delta -1 and delta +1 pair. Explicit labels and both actual one-byte controls are reported below. This is not a change to packing or a correction of the whole-payload group counts.

## Original evidence

Lead #70 and the reproduced finding were authored by @radialmonster. The lead measured default 3-band/16-row/1200-column windows; the finding repeated all five files with 8 bands, 32 rows and requested 3200 columns, and checked whole-payload byte-15 counts. The source snapshot is `a4bf2af4b6a9036ae0c90936f4e8080520fb5f77` (`tools/orf_v0_unpack.py` last changed in `1b6c2fc`), whose unpack tool SHA-256 is `1ff0f0cd7c595e0f32d27664fed76b0024f7327ec963bb9aa82b026d80869b50` and `tools/orf_signature.py` SHA-256 is `b1b6f091bfb986ab7aca3ad1f513202acfaaccc424272523589142444d025afb`.

Public raw.pixls.us identities, matched by SHA-256, with CC0 licence records retained from the current catalogue and existing manifest identities checked:

- 2856: `Olympus - E-M5 Mark II - 16bit 16bit "high-res" (4:3).ORF`, SHA-256 `5c42fa75d6b549514b722e2c50726c03e34fac4909ec3640e147ea7fa825fc8d`.
- 2878: `Olympus - E-300 - 16bit (4:3).ORF`, SHA-256 `6d818dbff78b3e2efa4835f568d04733052b9211e6bc65b0a3748a841170e95b`.
- 2977: `Olympus - PEN-F - 16bit (4:3).orf`, SHA-256 `f87a5f3295aeb4d6ab27bb5b41c5e0f3a211ec9b4e3b1d9f105a650bee1a2f13`.
- 3540: `Olympus - E-500 - 16bit (4:3).ORF`, SHA-256 `fa5a4759b2de2b573f59629ad1baf64ad04a85fb8fe1fb3cbf68e08a42fff4f0`.
- 3624: `Olympus - E-330 - 16bit (4:3).ORF`, SHA-256 `ba11eb970ab32e1e9cf3d0176041e4bd11c501d445720c0a344217e785ad65a6`.

## Verification

Fresh runs by @mszyndel on 2026-11-20 UTC followed the prospective plan in #70 comment 7045054157. The current verified-CC0 catalogue has 104 Olympus/OM ORF/ORI files, all with unambiguous measured classes in the manifest; the five listed inputs are its complete recorded packed-12.8 class. The original finding already used all five, so there is no unused applicable CC0 file in this inventory. The extension uses more windows on the same already studied captures, not a new body, scene or blind cohort.

Byte-identical copies of the original source snapshot and import were used for every layout pass. The fixed extension uses 12 bands x 32 rows x requested 3200 columns, after the default and 8-band repeats. Both requested-3200 passes actually read 3180 columns: 814,080 values in the 8-band run and 1,221,120 in the 12-band run per file. All twelve candidate layouts are retained. No parameter was retuned after outcomes, and no input was replaced. Family margins (printed precision) reproduce the original values on both original commands:

| ID | 3x16 margin | 8x32 margin | 12x32 margin | 8x32 pair h1 gap | 12x32 pair h1 gap |
| --- | --- | --- | --- | --- | --- |
| 2856 | 3.97 | 4.03 | 5.86 | 0.6% | 0.2% |
| 2878 | 4.51 | 4.87 | 4.55 | 1.6% | 1.8% |
| 2977 | 5.63 | 5.06 | 5.25 | 0.3% | 0.3% |
| 3540 | 3.83 | 4.76 | 4.62 | 0.6% | 0.7% |
| 3624 | 3.38 | 3.20 | 3.13 | 1.6% | 1.8% |

In the 8-band repeat, the pair-order report is undecided for 2856/2977/3540 and weakly favoured for 2878/3624. The latter gaps print 1.6% in this run; the original prose lists 1.5%. Those auxiliary decimal strings are not asserted identical. In the 12-band extension they print 1.8%; weak smoothness preferences do not establish physical order. The raw candidate-table scores still place both pair orders within the tool's 2% score band.

The complete printed 8-band stride-control results, with delta in bytes added to the nominal row stride, are:

| ID | delta -16 | delta -2 | delta -1 | delta 0 | delta +1 | delta +2 | delta +16 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2856 | 0.750 | -0.012 | -0.006 | 0.947 | -0.014 | -0.008 | 0.736 |
| 2878 | 0.815 | -0.038 | -0.018 | 0.960 | -0.019 | -0.042 | 0.810 |
| 2977 | 0.848 | -0.023 | -0.002 | 0.991 | -0.008 | -0.016 | 0.836 |
| 3540 | 0.861 | -0.066 | -0.026 | 0.977 | -0.022 | -0.073 | 0.865 |
| 3624 | 0.668 | 0.055 | 0.062 | 0.970 | 0.060 | 0.041 | 0.672 |

The true-stride and one-group-off results and the original bracketed numerical values reproduce; the bracketed values correspond specifically to delta -2/-1. The original finding's label is corrected here rather than silently reinterpreting either control as delta +1. Both actual one-byte controls remain far below the true-stride correlation on these inputs. The lead's similarly worded default-window examples should also be read from the explicit tool delta labels.

Before the whole-payload direct-slice count, `tools/strip_contiguity_audit.py`'s reviewed audit confirmed one in-bounds strip with no physical overlap for each file. The original inline byte-15 count then yields exactly the published whole-payload totals:

| ID | Dimensions | Payload bytes | 16-byte groups | Nonzero byte 15 |
| --- | --- | --- | --- | --- |
| 2856 | 9280x6932 | 102926336 | 6432896 | 0 |
| 2878 | 3360x2504 | 13461504 | 841344 | 0 |
| 2977 | 10400x7796 | 129725440 | 8107840 | 0 |
| 3540 | 3360x2504 | 13461504 | 841344 | 0 |
| 3624 | 3280x2450 | 12857600 | 803600 | 0 |

At source snapshot `a22366c4db7c58c90d4b2686a95d453333758388`, `tools/conformance.py --csv` with the existing reference decoder reproduces every field of the five matching rows in `samples/conformance-V0.csv`, keyed by input hash. All five are packed-12.8/lsb, natural row order, exact end, and zero out-of-range values. Output SHA-256 is over the emitted values as little-endian uint16, row-major, unshifted:

| ID | Output SHA-256 |
| --- | --- |
| 2856 | `79aa165b0c74e88ff6c3e3e027e86aad30a6957d9b7d3d8990668aafbb393ef4` |
| 2878 | `09736a0cc45c4834a89b3b606e58d80caa3772549e2dabe3bb1a8a6304b04315` |
| 2977 | `32c3bc92092bc11e7d854d08dc9c151bd5525262072a3dc32f88b4b941ad80c6` |
| 3540 | `bd231fd8c50e85f774fe142e9633c64f6844ae4b8758889f2befedf2ffc944f6` |
| 3624 | `36f8e058e2b1c6da64746254b7e9af8d5574d33867035382546a4764b54a548b` |

All 25 per-file jobs (15 layout passes, five pad scans and five conformance runs) exited zero, with no 300-second timeout. Layout/pad jobs had empty stderr; conformance stderr contained its normal zero-error summary. Input hashes matched retained CC0 records before and after each file's runs. No decoded/preview values or images were written. This is reproduction by a contributor other than the finder using shared published tools; the conformance check is not a blind second implementation or independent proof of physical row/pair order.

## Reproduce

Read the named sources and their repository imports first. Obtain the exact five CC0 inputs using `tools/pixls_samples.py`, retain licence verification and check local hashes. Match input IDs 2856, 2878, 2977, 3540, 3624 in that order. At `a4bf2af4b6a9036ae0c90936f4e8080520fb5f77`, run the default, original wider and predeclared extension commands:

    python -I -B tools/orf_v0_unpack.py FILE2856 FILE2878 FILE2977 FILE3540 FILE3624
    python -I -B tools/orf_v0_unpack.py --bands 8 --rows 32 --cols 3200 FILE2856 FILE2878 FILE2977 FILE3540 FILE3624
    python -I -B tools/orf_v0_unpack.py --bands 12 --rows 32 --cols 3200 FILE2856 FILE2878 FILE2977 FILE3540 FILE3624

Preserve each report's printed window, candidate table, chosen line, pair-order alternatives and explicit stride-delta line. Enforce 300 seconds per input per pass (the local run used separate per-file invocations). Keep timeouts or read/identity failures as unknowns rather than replacing an input or changing a window.

For whole-payload geometry/padding and reference conformance, use source snapshot `a22366c4db7c58c90d4b2686a95d453333758388`. The pad check below is the original finding's read-only inline count with a declared-strip geometry guard:

    python -I -B -c "import sys; sys.path.insert(0,'tools'); import orf_signature as s; from strip_contiguity_audit import audit
    for p in sys.argv[1:]:
        data=open(p,'rb').read(); a=audit(data)
        assert a['table_adjacent'] and not a['physical_overlap']
        g=s.signature(p); o=int(g['payload_offset']); n=int(g['payload_bytes'])
        d=data[o:o+n]; pads=d[15:n//16*16:16]
        print(g['sha256'],n,n%16,len(pads),sum(1 for b in pads if b))" FILE2856 FILE2878 FILE2977 FILE3540 FILE3624
    python -I -B tools/conformance.py --csv FILE2856 FILE2878 FILE2977 FILE3540 FILE3624

Compare complete conformance rows by input SHA-256 with the committed table at that snapshot. Only aggregates and hashes are printed; no pixel arrays are saved. The original #70 follow-ups on pair order, black level/saturation and new applicable bodies remain in V0 G4/G7.
