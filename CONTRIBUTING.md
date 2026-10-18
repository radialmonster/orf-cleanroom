# Contributing

Thanks for helping. Read [RULES.md](RULES.md) first; it's short.

## Flow
1. Pick a task: "Start here" in the README, or an issue labelled `good first issue`. Comment on the issue to claim it.
2. Fork the repo and create a branch.
3. Make one focused change per pull request.
   - New findings go at the **end** of FINDINGS.md as `## F<n> (YYYY-MM-DD, @you): title`. Existing entries are never edited (CI enforces this).
   - Manifest rows: use `tools/manifest_rows.py`.
   - Numbers come with the `tools/` script that produced them.
4. Open a pull request and fill in the template checklist.

## Clean-room declaration
For work on the bitstream or decoder logic (FINDINGS entries, OPEN-QUESTIONS, decoding tools), you must not have read the ORF decompression code of LibRaw, rawspeed, dcraw or projects derived from them. If you have, you can still help with samples, the manifest, tooling and testing; just say so in your PR.

## Your own files
Welcome. Measure them locally and publish only numbers and SHA-256 (see RULES.md, "Data").

## Requirements
Python 3.8 or newer, standard library only. CI checks that every tool compiles and runs `--help` on Python 3.8 and 3.12.

## Credit
Your handle stays on what you found. See RULES.md, "Credit".
