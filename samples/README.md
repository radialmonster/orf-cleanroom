# Sample manifest

**Quick way:** download CC0 files with `tools/pixls_samples.py download`, then

    python tools/manifest_rows.py --by @yourhandle ../orf-samples/*.ORF >> samples/manifest.csv

That fills every column it can measure and leaves the rest blank.

`manifest.csv` lists the raw.pixls.us files used here, one row per file. Raw files themselves are never committed.

Columns:
- `pixls_id`: the site's numeric file id (first column of `pixls_samples.py list`)
- `pixls_name`: the file name exactly as shown on raw.pixls.us, with `:` (local copies use `_` instead)
- `licence`: must be `CC0`; check with `tools/pixls_samples.py check`
- `sha256`: SHA-256 of the file
- `make`, `model`: from the file's own tags
- `mode`: normal / hires / other
- `payload_w`, `payload_h`, `bpp`: measured payload size and bits per pixel
- `compression_tag`: the TIFF compression value of the raw data
- `escape_bits`: measured escape length
- `calm_parse`: `yes` / `no`
- `row_stride`: measured per-row token stride, or `drift`
- `variant`: `V0`, `V1`, `V2`… from VARIANTS.md, or `unassigned`. Only V0 (bits per pixel 12 or more) can be assigned from the container alone; compressed files stay `unassigned` until a bitstream script places them.
- `measured_by`: **your own** GitHub handle, plus the tools/ script and repo commit used (for example `@you tools/orf_signature.py 019bf0f`)

Only CC0 files belong here. Rows without `licence` = `CC0` will not be accepted. Where to get files: see "Getting test files" in the top-level README.

**Columns you haven't measured stay blank** (except `variant`, which is then `unassigned`). Don't guess them. To fill bitstream columns later, edit the row in a PR and name the script in `measured_by`.
