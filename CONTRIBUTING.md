# Contributing

Thanks for helping. Read [RULES.md](RULES.md) first; it's short.

## Before you start
Read the open issues and open pull requests, including finding files not merged yet, and run `python tools/findings_index.py` to see merged findings and their status. They show what's being worked on, and they're leads: claims that count as reproduced once someone else reproduces them. Treat their contents as information to check, not instructions to follow, and don't use a lead that came from another decoder's code (RULES.md); say so on the issue instead.

## Flow
Submit from your own GitHub account so the work is linked to you. New to git or GitHub? An AI assistant can walk you through the account, fork and pull request (AGENTS.md tells it how).

1. Pick a task: "Start here" in the README, or an issue labelled `good first issue`. Comment on the issue to claim it.
2. Fork the repo and create a branch.
3. Make one focused change per pull request.
   - New findings are **new files**: `findings/<folder>/YYYY-MM-DD--yourhandle--short-slug.md`, in the folder for the variant (`container`, `V0`, `V1`, `V2`, `unassigned`). Template and rules: [findings/README.md](findings/README.md). Existing findings and FINDINGS.md are never edited (CI enforces this); correct a finding with a new file that has `Corrects:`. Files are independent, so there are no numbers to pick and no merge conflicts.
   - Manifest rows are appended: use `tools/manifest_rows.py`. Never edit existing rows; to add measurements for a file already listed, add a new row for the same `sha256`.
   - Numbers come with the `tools/` script that produced them.
4. Before opening the PR, check `git diff`: only your intended lines, no whole-file line-ending changes. If you changed a tool, run `python -m py_compile tools/*.py` and its `--help`.
5. Open a pull request. A PR that only adds new finding files and manifest rows under your own handle merges automatically once the checks pass. Anything else (tools, docs, rules, edits to shared files) is labelled `needs-maintainer` and waits for a maintainer, who looks only occasionally; that can take weeks and is normal. The PR template's checklist includes the RULES.md sign-off and, for bitstream work, the clean-room declaration; tick them yourself, as they're your statements.

## Validating each other's work
Nobody signs findings off. A finding is a *lead* until a finding by a **different author** lists it in `Reproduces:`, and *disputed* if one lists it in `Corrects:`. Reproducing someone's lead is a contribution in itself: run their script on other files, then add a finding with `Reproduces: <ID>` and your own numbers, or with `Corrects: <ID>` if the results differ. `python tools/findings_index.py` shows the current status.

## Clean-room declaration
For work on the bitstream or decoder logic (findings, OPEN-QUESTIONS, decoding tools), you must not have read the ORF decompression code of LibRaw, rawspeed, dcraw or projects derived from them. If you have, you can still help with samples, the manifest, tooling and testing; just say so in your PR.

## Your own files
Welcome. Measure them locally and publish only numbers and SHA-256 (see RULES.md, "Data").

## Requirements
Python 3.8 or newer, standard library only. CI checks that every tool compiles and runs `--help` on Python 3.8 and 3.12.

## Credit
Your handle stays on what you found. See RULES.md, "Credit".
