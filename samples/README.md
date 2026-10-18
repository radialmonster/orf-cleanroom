# Sample manifest

`manifest.csv` lists the raw.pixls.us files used here, one row per file. Raw files themselves are never committed.

Columns:
- `pixls_id`: the site's numeric file id (from the download URL, `getfile.php/<id>/...`)
- `pixls_name`: the file name as shown on raw.pixls.us
- `licence`: must be `CC0`; check with `tools/pixls_samples.py check`
- `sha256`: SHA-256 of the file
- `make`, `model`: from the file's own tags
- `mode`: normal / hires / other
- `payload_w`, `payload_h`, `bpp`: measured payload size and bits per pixel
- `compression_tag`: the TIFF compression value of the raw data
- `escape_bits`: measured escape length, blank if unknown
- `calm_parse`: yes / no / untested
- `row_stride`: measured per-row token stride, or `drift`
- `variant`: V-id from VARIANTS.md, or `unassigned`
- `measured_by`: **your own** GitHub handle, plus the tools/ script and repo commit used (for example `@you tools/orf_signature.py 019bf0f`)

Only CC0 files belong here. Rows without `licence` = `CC0` will not be accepted. Where to get files: see "Getting test files" in the top-level README.

Columns you haven't measured stay blank or `untested`. Don't guess them.
