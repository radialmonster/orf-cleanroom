# Sample manifest

`manifest.csv` lists the raw.pixls.us files used here, one row per file. Raw files themselves are never committed.

Columns:
- `pixls_name`: the file name as shown on raw.pixls.us
- `sha256`: SHA-256 of the file
- `make`, `model`: from the file's own tags
- `mode`: normal / hires / other
- `payload_w`, `payload_h`, `bpp`: measured payload size and bits per pixel
- `compression_tag`: the TIFF compression value of the raw data
- `escape_bits`: measured escape length, blank if unknown
- `calm_parse`: yes / no / untested
- `row_stride`: measured per-row token stride, or `drift`
- `variant`: V-id from VARIANTS.md, or `unassigned`
- `measured_by`: GitHub handle, plus the tools/ script and commit used

Only CC0 / public-domain files belong here. Where to get them: see "Getting test files" in the top-level README.
