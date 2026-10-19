# tools

Analysis scripts, all original code (see RULES.md).

Each script should:
- take raw.pixls.us file paths as arguments and not download anything itself (`pixls_samples.py` is the one exception);
- print or write aggregate statistics only, with no images or pixel dumps;
- run on CPU, with GPU acceleration optional;
- state at the top which finding (an ID from `findings/`), lead issue (`#n`) or OPEN-QUESTIONS item it supports.

## Example tools

**`pixls_samples.py`** lists, checks and downloads raw.pixls.us Olympus/OM samples using the site's licence listing. It downloads CC0 files only and verifies SHA-256. See the top-level README.

**`manifest_rows.py`** turns local CC0 files into ready-made `samples/manifest.csv` rows, combining the licence listing with `orf_signature.py`.

**`orf_signature.py`** prints one CSV row per file with its measured container and payload facts: SHA-256, magic, make, model, payload size, bits per sample, compression tag, payload offset and bytes, and bits per pixel. It reads the TIFF structure only and decodes nothing.

    python tools/orf_signature.py path/to/* > rows.csv

**`bit_runs.py`** gives a histogram of zero-bit runs in the payload (MSB-first), as aggregate numbers. It's a starting point for bitstream work (the F1 lead, #11).

    python tools/bit_runs.py path/to/file.ORF --mb 1

Example output on raw.pixls.us `8549_OM System - OM-5 Mark II - 16bit (4_3).ORF` (CC0), first 1 MB:

    q= 0  share=0.48036
    q= 1  share=0.27349
    q= 2  share=0.13019
    q= 3  share=0.06272

**`orf_tokens.py`** parses the token stream described in lead #11 (q zero bits, stop bit, 5-bit suffix; escape at q >= 17) and prints aggregate statistics per file: tokens against width x height, bit alignment at multiples of the width, q histogram and escapes, suffix bit balance, H/L shares, and mutual information at token lags 1-3 (H->L, L->H, L->L, H->H), the b2 context gain and vertical lag 2, each with a baseline that shows the estimator bias. Numbers are printed as measured, whether or not they match that lead. It parses a prefix by default (`--max-tokens`, `--rows`); `--all` parses the whole payload.

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
