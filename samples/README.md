# Sample manifest

**Quick way:** download CC0 files with `tools/pixls_samples.py download`, then

    python tools/manifest_rows.py --by @yourhandle ../orf-samples/*.ORF >> samples/manifest.csv

That fills every column it can measure and leaves the rest blank. For your own files, add `--own` (you confirm they're yours or the owner agreed). If one of "your" files turns out to be identical to a raw.pixls.us file, the tool records it as that CC0 file, which is better: others can re-test it.

On Windows, `>>` may write CRLF line endings; `.gitattributes` converts them to LF when you commit, so the warning git prints is harmless.

`manifest.csv` lists the files used here, one row per file: raw.pixls.us CC0 files and contributors' own files. Raw files themselves are never committed.

Columns:
- `source`: `pixls` (raw.pixls.us, CC0) or `own` (a contributor's file, not shared)
- `pixls_id`: the site's numeric file id (first column of `pixls_samples.py list`)
- `pixls_name`: the file name exactly as shown on raw.pixls.us, with `:` (local copies use `_` instead)
- `licence`: `CC0` for raw.pixls.us files (check with `tools/pixls_samples.py check`); `not-shared` for own files
- `sha256`: SHA-256 of the file
- `make`, `model`: from the file's own tags
- `mode`: `normal` / `hires`, measured from the payload width (over 6000 = High Res Shot)
- `payload_w`, `payload_h`, `bpp`: measured payload size and bits per pixel
- `size_class`: `packed-12`, `packed-12.8` or `packed-16` when the payload size exactly matches that fixed packing; `variable` otherwise (compressed). See FINDINGS F4.
- `compression_tag`: the TIFF compression value of the raw data
- `escape_bits`: measured escape length
- `calm_parse`: `yes` / `no`
- `row_stride`: measured per-row token stride, or `drift`
- `variant`: `V0`, `V1`, `V2`… from VARIANTS.md, or `unassigned`. Only V0 (`size_class` is `packed-…`) can be assigned from the container alone; compressed files stay `unassigned` until a bitstream script places them.
- `measured_by`: **your own** GitHub handle, plus the tools/ script and the last commit that changed that script, not the repo's HEAD; `manifest_rows.py` fills this in for you (for example `@you tools/orf_signature.py 019bf0f`). Never overwrite it; when you add columns to an existing row, append `; @you <script> <commit>`.

Allowed rows: CC0 raw.pixls.us files, and your own files (`source` = `own`). Non-CC0 raw.pixls.us files are not accepted. Rows from own files can't be re-measured by others, so findings resting only on them are marked `not yet reproducible`. Where to get files: see "Getting test files" in the top-level README.

**Columns you haven't measured stay blank** (except `variant`, which is then `unassigned`). Don't guess them. To fill bitstream columns later, edit the row in a PR and name the script in `measured_by`.
