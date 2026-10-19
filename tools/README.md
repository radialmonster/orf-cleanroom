# tools

Analysis scripts, all original code (see RULES.md).

Each script should:
- take raw.pixls.us file paths as arguments and not download anything itself (`pixls_samples.py` is the one exception);
- print or write aggregate statistics only, with no images or pixel dumps;
- run on CPU, with GPU acceleration optional;
- state at the top which finding (an ID from `findings/`), lead issue (`#n`) or spec Gap (`specs/V<n>.md`) it supports.

## Example tools

**`suffix_match_probe.py`** supports lead #31 with exact suffix-equality counts
against independent within-block permutations that preserve escape positions.
It prints aggregate JSON, with every declared lag and explicit sample failures.
The frozen discovery and validation cohorts are in `tools/cohorts/`; later files
use a separate `replication` cohort with the same design metadata. Local paths
are supplied separately and never appear in output. This bounded descriptive
measure cannot establish or exclude dictionary coding. Synthetic exhaustive
permutation tests run with `python -I tools/suffix_match_probe.py --self-test`.

    python -I tools/suffix_match_probe.py --cohort PUBLIC_COHORT.json --measured-by @yourhandle --sample ID path/to/file.ORF

**`pixls_samples.py`** lists, checks and downloads raw.pixls.us Olympus/OM samples using the site's licence listing. It downloads CC0 files only and verifies SHA-256. See the top-level README.

**`manifest_rows.py`** turns local CC0 files into ready-made `samples/manifest.csv` rows, combining the licence listing with `orf_signature.py`.

**`orf_signature.py`** prints one CSV row per file with its measured container and payload facts: SHA-256, magic, make, model, payload size, bits per sample, compression tag, payload offset and bytes, and bits per pixel. It reads the TIFF structure only and decodes nothing.

    python tools/orf_signature.py path/to/* > rows.csv

**`conformance.py`** runs the reference decoder (`decoder/orf_decode.py`) on files and prints per file the input SHA-256, packing, size, bytes consumed vs payload size, min/max, out-of-range count (for packed-16: words with a non-zero low nibble), smoothness and the output hash, then a summary. `--csv` gives the `samples/conformance-V0.csv` format. Supports ROADMAP.md.

    python -I tools/conformance.py path/to/*

**`test_orf_decode.py`** round-trip tests of the decoder on synthetic bytes: `python -I tools/test_orf_decode.py`.

**`bit_runs.py`** gives a histogram of zero-bit runs in the payload (MSB-first), as aggregate numbers. It's a starting point for bitstream work (the F1 lead, #11).

    python tools/bit_runs.py path/to/file.ORF --mb 1

Example output on raw.pixls.us `8549_OM System - OM-5 Mark II - 16bit (4_3).ORF` (CC0), first 1 MB:

    q= 0  share=0.48036
    q= 1  share=0.27349
    q= 2  share=0.13019
    q= 3  share=0.06272

**`orf_tokens.py`** parses the token stream described in lead #11 (q zero bits, stop bit, 5-bit suffix; escape at q >= 17) and prints aggregate statistics per file: tokens against width x height, bit alignment at multiples of the width, q histogram and escapes, suffix bit balance, H/L bit-group shares, the ones-density with the tokens per pixel a Bernoulli (independent-bits) null predicts next to the measured value, correlation of min(q,8) at token lags 1, 2, 3, 6 and the row stride, and mutual information at token lags 1-3 (H->L, L->H, L->L, H->H), the b2 context gain and vertical lag 2, each with a baseline that shows the estimator bias. Numbers are printed as measured, whether or not they match that lead. It parses a prefix by default (`--max-tokens`, `--rows`); `--all` parses the whole payload. `--escape-landing` tabulates, per escape q, where the stream re-synchronises (distance modulo 6) after each escape. H = b4b3 and L = b2b1b0 are only labels for bit groups; no signed or other meaning is assumed.

    python tools/orf_tokens.py path/to/file.ORF --rows 400
    python tools/orf_tokens.py path/to/file.ORF --all

**`value_map_probe.py`** (by @mtakemoto) measures suffix bridge energies under the three candidate suffix mappings from lead #32, against an exact permutation null, in 128-token blocks of the #11 parse. It is a frozen, pre-registered experiment: the sample IDs per phase (`discovery`, `validation`) and the settings are fixed on purpose, so it reruns that one design rather than measuring arbitrary files. It prints aggregate JSON only. `--self-test` runs its tests.

    python tools/value_map_probe.py --phase discovery --measured-by @yourhandle --sample 1993 NAME path/to/file.ORF

**`orf_v0_unpack.py`** scores candidate bit layouts for the uncompressed V0 files (`packed-12`, `packed-12.8`, `packed-16`, lead #28) on a small window of each file: value range, smoothness at same-colour horizontal and vertical distance 2 against distance 1, row correlation, and a row-stride test for the chosen layout. Text statistics only; it prints the layout with the lowest roughness and the margin to the next one.

    python tools/orf_v0_unpack.py path/to/file.ORF

**`findings_index.py`** lists the verified findings under `findings/` by variant, with finder, verifier, title and status (verified or superseded). `--check` validates the files (file name, `Author:` matches the handle, `Verified by:` is another person, `Lead:` is `#n`, `Variant:` matches the folder, referenced IDs exist) and exits 1 on errors; CI runs it on pull requests.

    python tools/findings_index.py
    python tools/findings_index.py --check

All of them use the standard library only (Python 3.8+). Contributions of new tools are welcome. Follow the rules above and RULES.md.

**`v0_spec_check.py`** is an independent, aggregate-only implementation of
`specs/V0.md` at `bf56d39`, supporting lead #75. Original payload logic and
synthetic tests were written without target files, reference code, or output
hashes. Shared container code is limited to `orf_signature.Tiff` header/endian
and integer reads; an original wrapper validates relevant IFD descriptors.

    python -I tools/v0_spec_check.py --help
    python -I tools/v0_spec_check.py --self-test
    python -I tools/test_v0_spec_check.py
    python -I tools/v0_spec_check.py --measured-by @yourhandle --sample ID PUBLIC_NAME path/to/file.ORF

Repeat `--sample` for multiple files. IDs are distinct positive decimals; public
names may repeat. Match records by input SHA-256, never basename. Check CC0
licensing before supplying downloaded files. Each JSONL result includes public
identity, input/output hashes, measured signature, aggregates, selectors, source
hashes and pinned spec metadata. Failures emit sanitized categories, preserve
other results and return a nonzero exit code. No decoded data is written.

Selectors are **unverified spec generalizations**: packed-12 `IIRS` is plain,
`IIRO` reverses global four-byte words; no strip gaps means natural rows; one
packed-12 gap at the even-field boundary means two fields; packed-16 uses TIFF
byte order. Unsupported cases fail without trying alternatives. First/second
unit order is a convention, not physical pixel-order proof. The S4.3/S6 wording
ambiguity is resolved by preserving packed-16 stored words with **no numeric
shift**, including low nibbles. Above-4095 and nonzero-low-nibble counts are
separate measurements. Hashing uses explicit uint16 little-endian image rows.

Read-only mmap, individual strip reads, strict integer size classification and
row streaming are bounded by 8 GiB per file, 100,000 per dimension, 250,000,000
pixels, 4,096 IFDs and 1,000,000 strips. Malformed relevant fields, tied largest
IFDs, repeated pointers, overlaps, nonascending strips and unsupported gaps are
rejected. Report mismatches under these frozen assumptions; do not tune them to
expected hashes.

Input opening uses `os.O_NONBLOCK` where the platform has it: the acquired
descriptor is checked with `fstat` before any mmap/read, so a FIFO without a
writer is rejected promptly and later inputs still run. Where the flag is missing
(Windows), a non-regular path is refused by `os.stat` before opening, and the
opened descriptor is still checked with `fstat`. Descriptors close on success
and failure. Symlinks to regular files remain usable. `--help` and `--self-test`
are portable; the FIFO test skips where FIFOs or `O_NONBLOCK` are absent.
