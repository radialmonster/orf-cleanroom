# Clean-room rules

## Allowed sources
- Public specifications: TIFF / TIFF-EP, Exif, DNG, JPEG, and similar published standards.
- Patents (their prose and figures), as a description of a method. Constants and bit layouts are confirmed from the files themselves.
- The files' own structure: tags, maker notes, embedded previews, and measurements of the compressed data.
- Your own original code and analysis.

## Not allowed
- Code from any other raw decoder, including **LibRaw, rawspeed and dcraw**, and any project derived from them.
- Write-ups, wikis, blog posts or forum posts that describe what such code does.
- The *output* of such decoders, used as a reference, an oracle, a test expectation or a comparison, even as a black box.
- Anything from pull requests or branches whose decoder was developed with any of the above.

If you have read the ORF decompression code in any of those projects, you're welcome to help with samples, tooling and testing, but please don't contribute to decoder logic or findings about the bitstream.

## Data
- Raw files are never committed. Reference them by SHA-256, plus the raw.pixls.us id and name when they come from there.
- **raw.pixls.us files:** use only CC0 ones (check with `tools/pixls_samples.py check`).
- **Your own files are welcome.** You can test with raws you shot yourself, or ones whose owner agreed. Publish only aggregate numbers and the file's SHA-256, never the file or images from it. Results that rest only on files others can't get are marked `not yet reproducible` until a CC0 copy exists. Uploading a few to raw.pixls.us as CC0 fixes that.
- Don't use files whose licence you don't know, or that are under a non-CC0 licence (e.g. the CC BY-NC-SA files on raw.pixls.us).
- No images of decoded or preview data are committed. Aggregate statistics only.

## Findings are files, and never edited
- Each finding is its own file `findings/<folder>/YYYY-MM-DD--handle--short-slug.md`, in the folder for its variant (`container`, `V0`, `V1`, `V2`, `unassigned`). Format and rules: findings/README.md.
- An existing finding file is never edited, renamed or deleted, by anyone, so nobody's work can be erased.
- To correct or retract a finding, add a new file with `Corrects: <ID>` that says which one and why.
- Status is peer validation, not maintainer sign-off: a finding is a *lead* until a finding by a different author lists it in `Reproduces:`, and is *disputed* if a different author lists it in `Corrects:`. `tools/findings_index.py` shows the status.
- FINDINGS.md holds the first four findings (F1-F4) and is frozen. CI rejects any change to it.
- CI rejects pull requests that modify or remove existing finding files, or that add a finding file that doesn't validate.

## Credit
Everyone who finds something keeps the credit for it.
- Each finding names its author (`@handle`) in its file name and its `Author:` line. Because existing files are never edited, that credit can't be edited away, and a later correction is a new file that leaves the original and its author in place.
- If your work builds on someone else's finding, say so with a `Builds on: <ID>` line (`F1`..`F4` for the legacy ones). If you reproduce one, list it in `Reproduces:`; the reproducer is credited in the index.
- Add only your own work under your own handle. If you're adding someone else's result, for example from a Discussion, credit them as the author (file name and `Author:`) and add `Submitted by: @you`. Such a PR needs a maintainer, because the file name handle differs from the PR author.
- In `samples/manifest.csv`, rows are append-only and `measured_by` is never overwritten. When you measure more columns of a file already listed, add a new row for the same `sha256` under your own handle.
- Pull requests are squash-merged with the contributor kept as the commit author. Add `Co-authored-by:` lines for anyone else who did the work.
- When a decoder built from this work is contributed to LightCraft or elsewhere, it credits every finding author it relies on, by name and finding ID.

## Sign-off
By opening a pull request you confirm that your contribution follows these rules and is released under CC0 1.0 (see LICENSE). Please say so in the PR description ("I confirm this follows RULES.md").
