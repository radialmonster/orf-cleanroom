# Sample manifest

**Quick way:** download CC0 files with `tools/pixls_samples.py download`, then

    python tools/manifest_rows.py --by '@yourhandle' --append samples/manifest.csv ../orf-samples/*

That fills every column it can measure and leaves the rest blank. For your own files, add `--own` after confirming they're yours. If one of your files turns out to be identical to a raw.pixls.us file, the tool records it as that CC0 file, which is better: others can re-test it.

To reuse previously verified records without contacting the catalogue, pass
`--licence-records records.json`. The JSON is an array of records or an object
with a `files` array; each record needs a positive numeric `id`, public ORF/ORI
`name`, lowercase `sha256`, and `licence` (for example `CC0`). Extra fields are
ignored. The caller must have retained the original licence verification and
public identity; supplying JSON does not itself verify provenance. The tool
matches the measured local hash and skips a hash if any supplied record for it
is non-CC0. Include known restricted records: the offline file cannot reveal
catalogue entries omitted from it. `--own` still requires ownership or the
owner's agreement and cannot override a supplied non-CC0 record.

For a file that has not yet been checked, `python -I -B tools/pixls_samples.py
check --json FILE...` checks its hash against the live catalogue and prints a
JSON object usable as `--licence-records`. Its `files` array contains known
identities, including non-CC0 matches; `unknown_inputs` lists unrecognized input
positions (one-based) without local paths, and `unreadable_inputs` lists files
that could not be read. Unknown files have no public identity or verified licence
and need their own provenance. A non-CC0 match or unreadable input gives exit
status 1. Save the output as UTF-8 and retain it with the original verification;
later matching hashes can reuse that record without another catalogue check.
For example, in PowerShell use `python -I -B tools/pixls_samples.py check --json
FILE | Set-Content -Encoding utf8 records.json` and check the Python exit status.

Use `--append` rather than shell `>>`: on Windows, `>>` can write CRLF line endings.
When the append destination is new or empty, add `--header` to create its column header.

`manifest.csv` lists the files used here, one row per file: public CC0 files and contributors' own files. Raw files themselves are never committed.

Columns:
- `source`: `pixls` (raw.pixls.us, CC0), `own` (a contributor's file, not shared), or `public-cc0` (a publicly shared owner-authorized CC0 file outside raw.pixls.us)
- `pixls_id`: the site's numeric file id (first column of `pixls_samples.py list`), empty for other sources
- `pixls_name`: the public filename, exactly as shown on raw.pixls.us for `pixls` files, including `:` (local copies use `_` instead)
- `licence`: `CC0` for verified public CC0 files (reuse the verified record for the same SHA-256); `not-shared` for own files
- `sha256`: SHA-256 of the file
- `make`, `model`: from the file's own tags, spelled as the tags spell them (e.g. `E-M5MarkIII`; the raw.pixls.us list may write `E-M5 Mark III`)
- `mode`: `normal` / `hires`, measured from the payload width (over 6000 = High Res Shot)
- `payload_w`, `payload_h`, `bpp`: measured payload size and bits per pixel
- `size_class`: `packed-12`, `packed-12.8` or `packed-16` when the payload size exactly matches that fixed packing; `variable` otherwise (compressed). See the fixed-size payloads lead (#28).
- `compression_tag`: the TIFF compression value of the raw data
- `escape_bits`: measured escape length
- `calm_parse`: `yes` / `no`
- `row_stride`: measured per-row token stride, or `drift`
- `variant`: `V0`, `V1`, `V2`, or any later `V<n>` from VARIANTS.md, or `unassigned`. Only V0 (`size_class` is `packed-…`) can be assigned from the container alone; compressed files stay `unassigned` until a bitstream script places them.
- `measured_by`: **your own** GitHub handle, exactly your GitHub login (case aside), or the PR will not merge automatically; plus the tools/ script and the last commit that changed that script, not the repo's HEAD; `manifest_rows.py` fills this in for you (for example `@you tools/orf_signature.py 019bf0f`). Older rows may cite an older commit; that's expected, since each row records the script version that measured it. Never overwrite it. Rows are append-only (below).

Allowed rows: CC0 raw.pixls.us files, owner-authorized public CC0 files, and your own files (`source` = `own`). Non-CC0 raw.pixls.us files are not accepted. Rows from own files can't be re-measured by others, so findings resting only on them are marked `not yet reproducible`. Where to get files: see "Getting test files" in the top-level README.

For `public-cc0`, leave `pixls_id` empty and put the owner's public filename in `pixls_name`. Retain a JSON list of records containing `name`, lowercase `sha256`, `licence` (`CC0`), `owner_declaration_url` and `public_source_url`; pass it as `--public-cc0-records FILE`. Establish the owner's CC0 declaration and public source yourself before using the mode; the tool validates record structure and matching bytes, not ownership or licence truth. Include the retained provenance record under `samples/` in the intake PR and cite it in related findings. A maintainer reviews the provenance and merges these rows manually. This mode never contacts the catalogue.

**Columns you haven't measured stay blank** (except `variant`, which is then `unassigned`). Don't guess them. 

**Rows are append-only.** Existing rows are never edited or removed; CI requires the old file to be an exact prefix of the new one. To fill bitstream columns for a file already listed, add a new row for the same `sha256` with your handle and script in `measured_by`. A file may have several rows, and a second row from a different person is welcome as an independent measurement. To see CC0 files not yet listed: `python tools/pixls_samples.py list --missing samples/manifest.csv`. No claim or announcement is needed; pick files at random so people spread out. Each new row must have every column; `source` `pixls` needs licence `CC0` and a numeric `pixls_id`, `source` `own` needs licence `not-shared` and an empty `pixls_id`, and `source` `public-cc0` needs licence `CC0`, an empty `pixls_id` and a public name; `measured_by` must start with `@yourhandle `. Eligible PRs appending only `pixls` or `own` rows under your own handle merge automatically; `public-cc0` rows require maintainer review.

**A file that fails to parse is a lead, not a bad file.** The container readers are strict on purpose: `tools/orf_signature.py` (and so `manifest_rows.py`) stops on a file with an IFD offset outside the file, a width or height tag with more than one value, overlapping or out-of-file strips, or missing strip tables, and prints `FILE: reason` with exit status 1. `tools/capture_pair_calibration.py` treats a file whose EXIF pointer (tag 0x8769) is not exactly one LONG as having no capture metadata, without an error. All 104 local CC0 files of 2026-10-27 pass, so a failure on a new file, above all one from a body or firmware not yet in the manifest, more likely means an unusual container than a broken download. Check the hash first (a truncated or corrupt copy is the common case). If the file is intact, don't loosen the check, skip the file or edit around it: record the error text, body, firmware and file size (no serial numbers or other owner identifiers for own files) and open a lead with `Variant: container`, so the layout gets measured.
