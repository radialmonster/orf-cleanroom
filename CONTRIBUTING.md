# Contributing

Thanks for helping. Read [RULES.md](RULES.md) first; it's short.

## Flow
Submit from your own GitHub account so the work is linked to you. New to git or GitHub? An AI assistant can walk you through the account, fork and pull request (AGENTS.md tells it how).

1. Pick a task: "Start here" in the README, or an issue labelled `good first issue`. Comment on the issue to claim it.
2. Fork the repo and create a branch.
3. Make one focused change per pull request.
   - New findings go at the **end** of FINDINGS.md as `## F<n> (YYYY-MM-DD, @you): title`. Existing entries are never edited (CI enforces this).
   - Manifest rows: use `tools/manifest_rows.py`.
   - Numbers come with the `tools/` script that produced them.
4. Before opening the PR, check `git diff`: only your intended lines, no whole-file line-ending changes. If you changed a tool, run `python -m py_compile tools/*.py` and its `--help`.
5. Open a pull request. The PR template's checklist includes the RULES.md sign-off and, for bitstream work, the clean-room declaration; tick them yourself, as they're your statements.

## Clean-room declaration
For work on the bitstream or decoder logic (FINDINGS entries, OPEN-QUESTIONS, decoding tools), you must not have read the ORF decompression code of LibRaw, rawspeed, dcraw or projects derived from them. If you have, you can still help with samples, the manifest, tooling and testing; just say so in your PR.

## Your own files
Welcome. Measure them locally and publish only numbers and SHA-256 (see RULES.md, "Data").

## Requirements
Python 3.8 or newer, standard library only. CI checks that every tool compiles and runs `--help` on Python 3.8 and 3.12.

## Credit
Your handle stays on what you found. See RULES.md, "Credit".
