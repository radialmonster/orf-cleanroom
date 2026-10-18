# Findings

One file per finding, in the folder for the variant it concerns. Nobody numbers anything and nobody edits anyone else's file, so pull requests don't conflict.

Older entries F1-F4 stay in [FINDINGS.md](../FINDINGS.md), which is frozen. Cite them as `F1`..`F4`.

## Folders
- [`container/`](container/): facts about the file container, or that span variants
- [`V0/`](V0/), [`V1/`](V1/), [`V2/`](V2/): bitstream findings for that variant (see [VARIANTS.md](../VARIANTS.md))
- [`unassigned/`](unassigned/): bitstream findings whose variant isn't known yet

A new variant gets a new folder `V<n>` with a README, added together with its section in VARIANTS.md.

## File name and ID
`YYYY-MM-DD--handle--short-slug.md`, for example `2026-10-18--alice--f2-on-seven-bodies.md`.

- Double hyphens separate the three fields. GitHub handles can't contain `--`.
- The slug is lowercase letters, digits and single hyphens.
- The finding's ID is the file name without `.md`.

## Format

    # <title>

    Author: @handle
    Submitted by: @handle
    Variant: container
    Builds on: F2, 2026-10-18--alice--some-finding
    Reproduces: <ID>
    Corrects: <ID>

    ## Claim
    What you found, in plain sentences.

    ## Evidence
    The tools/ script and its last commit, and the files by raw.pixls.us id + SHA-256
    (or `own` + SHA-256), with the numbers.

    ## Reproduce
    The exact commands.

- `Author:` is required and must match the handle in the file name. Add only your own work under your own handle.
- `Submitted by:` only when you add someone else's result (for example from a Discussion). The author stays the one who found it.
- `Variant:` is required and must match the folder: `container`, `V0`, `V1`, `V2`, `unassigned`, ...
- `Builds on:`, `Reproduces:` and `Corrects:` are optional. Each is a comma-separated list of finding IDs (`F1`..`F4` for legacy ones). Delete the lines you don't use.
- Evidence: numbers come with the `tools/` script that produced them. Results that rest only on `own` files are marked `not yet reproducible` (RULES.md, "Data").

## Rules
- An existing finding file is never edited, renamed or deleted, by anyone. CI rejects it.
- To correct or retract a finding, add a new file with `Corrects: <ID>` that says what was wrong.
- Findings are about the files and bitstream, with the clean-room rules of [RULES.md](../RULES.md).

## Status comes from peer validation
Nobody needs a maintainer's sign-off.

- **lead**: no finding by a different author reproduces or corrects it yet.
- **reproduced**: a finding by a different author lists it in `Reproduces:`. That means you ran the same checks, preferably on other files, and got matching results.
- **disputed**: a finding by a different author lists it in `Corrects:`.

If your results don't match, don't write `Reproduces:`. Write a finding with `Corrects:` and show your numbers. Reproducing your own finding doesn't change its status.

See the current state with:

    python tools/findings_index.py           # per variant: ID, author, title, status
    python tools/findings_index.py --check   # validate every file (CI runs this)
