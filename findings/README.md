# Findings

This folder holds **verified findings only**: results that were reproduced in a second, separate run. The verifier may be the finder, though a different person is preferred. Unverified results are *leads*, and leads are GitHub issues, not files.

Open leads: `gh issue list -R radialmonster/orf-cleanroom --label lead`, or https://github.com/radialmonster/orf-cleanroom/issues?q=is%3Aopen+label%3Alead

## How a lead becomes a finding
1. The finder publishes a lead issue (template: "Lead"). It stays an issue.
2. Someone reproduces it in a new run, done after the lead was posted. A different person is preferred; the finder may do it themselves. Use at least one file or body the lead did not use. If that is impossible (the lead already used every CC0 file of the model), say so in the Verification section; a wider run on the same files (for example the whole frame instead of a prefix) still counts as a new run if you describe it.
3. The verifier opens a PR that adds the finding file here, with `Author:` the finder, `Verified by:` themselves (the PR author) and `Lead:` the issue number. When it merges, the lead issue is labelled and closed. If the finding covers only part of a lead with several claims, add `Partial: <which part>`; the lead is then labelled `partly-verified` and stays open for the rest.
4. If the numbers do not match, nothing goes in this folder. The reproducer comments their numbers on the lead issue.

CI cannot check that the second run is really new or on other files; the Verification section is where you show it.

If the lead gives no method or file list, define your own measure before looking at all the results, describe it in the Verification section, and say that the lead's exact figures could not be reproduced. Its claim is what you verify.

## Upgrading a self-verified finding
A finding verified by its own finder is `self-verified`. A different person can upgrade it to `verified`: reproduce it, then add a new file named for the original finder, with `Author:` the finder, `Verified by:` you, the same `Lead:`, and `Reproduces: <finding ID>`. The lead stays closed; its label changes from `self-verified` to `verified`. Look for candidates: https://github.com/radialmonster/orf-cleanroom/issues?q=label%3Aself-verified

Example, `findings/V1/2026-11-02--alice--tag-is-1-on-compressed-orf.md`, where Bob reproduced Alice's self-verified `2026-10-18--alice--tag-is-1-on-compressed-orf`:

    # Tag is 1 on compressed ORF

    Author: @alice
    Verified by: @bob
    Lead: #123
    Variant: V1
    Reproduces: 2026-10-18--alice--tag-is-1-on-compressed-orf

    (then the usual sections; Verification describes Bob's run)

Files are independent, so there are no numbers to pick and no merge conflicts.

## Folders
- [`container/`](container/): facts about the file container, or that span variants
- [`V0/`](V0/), [`V1/`](V1/), [`V2/`](V2/): bitstream findings for that variant (see [VARIANTS.md](../VARIANTS.md))
- [`unassigned/`](unassigned/): bitstream findings whose variant isn't known yet

A new variant gets a new folder `V<n>` with a README, added together with its section in VARIANTS.md.

## File name and ID
`YYYY-MM-DD--finder--short-slug.md`, for example `2026-10-18--alice--tag-is-1-on-compressed-orf.md`.

- The date is the day of the verification PR, in UTC. The handle is the **finder** (the lead's author), not the verifier (they are the same person in a self-verification).
- Double hyphens separate the three fields. GitHub handles can't contain `--`.
- The slug is lowercase letters, digits and single hyphens.
- The finding's ID is the file name without `.md`.

## Format

    # <title>

    Author: @finder
    Verified by: @reproducer
    Lead: #123
    Variant: container
    Builds on: 2026-10-18--alice--some-finding, #45
    Corrects: <ID>
    Reproduces: <ID>
    Partial: <which part of the lead this verifies>

    ## Claim
    What was found, in plain sentences.

    ## Original evidence
    The finder's tools/ script and commit, the files (raw.pixls.us id + SHA-256, or `own` + SHA-256) and numbers, as on the lead.

    ## Verification
    A new run, done after the lead was posted: what was run, on which files (at least one the lead did not use, or say why that is impossible), and the numbers.

    ## Reproduce
    The exact commands.

- `Author:` is required and must match the finder handle in the file name. `Verified by:` is required and is the PR author. It may equal `Author:` (self-verification); a different person is preferred.
- `Lead:` is the lead issue (`#n`) by the finder. It must exist and carry the `lead` label.
- `Variant:` is required and must match the folder.
- `Builds on:` and `Corrects:` are optional lists of finding IDs (or `#n` issues). Delete the lines you don't use.
- `Reproduces:` is optional and used only for the upgrade above: one finding ID with the same `Author:` and `Lead:`, and a `Verified by:` who is not the finder and not already a verifier of it. `findings_index.py --check` verifies that the ID exists.
- `Partial:` is optional: use it when the finding verifies only part of the lead's claims, and name that part. The lead stays open, labelled `partly-verified`. Without it, the lead is closed.
- Don't put the RULES.md sign-off or the clean-room declaration in the file; they go in the PR description.
- Numbers come with the `tools/` script that produced them. Results that rest only on `own` files are marked `not yet reproducible` (RULES.md, "Data").

## Rules
- An existing finding file is never edited, renamed or deleted by anyone but the repo owner. CI rejects it.
- To correct a verified finding, add a new verified finding with `Corrects: <ID>` (it needs its own lead and its own verification). The index then shows the old one as superseded.
- Findings are about the files and bitstream, with the clean-room rules of [RULES.md](../RULES.md).

## Status
- **self-verified**: the verifier is the finder.
- **verified**: the verifier is a different person, or a later `Reproduces:` file by a different person upgraded it.
- **superseded**: a later finding lists it in `Corrects:` (either of the above can be superseded).

    python tools/findings_index.py           # per variant: ID, author, status, title, verifiers
    python tools/findings_index.py --check   # validate every file (CI runs this)
