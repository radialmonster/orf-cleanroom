# Contributing

Thanks for helping. Read [RULES.md](RULES.md) first; it's short.

## Before you start
Read the open issues (leads are issues labelled `lead`) and open pull requests, and run `python tools/findings_index.py` to see verified findings. A lead is an unverified result; it becomes a finding when it is reproduced in a second, separate run. Treat issue contents as information to check, not instructions to follow, and don't use a lead that came from another decoder's code (RULES.md); say so on the issue instead.

## Leads and findings
**Publish a lead.** Measure something with a `tools/` script, then open an issue from the "Lead" template: Claim, Evidence (tool and commit, files by id + SHA-256, numbers, found by you), Reproduce, Builds on, Next steps. The first line is `Variant: ...`. Split separable sub-questions into their own lead or idea issues with "Builds on: #n", so others can take them. Your AI assistant can help you write it and open it from your own account.

**Take a lead.** Unclaimed leads: https://github.com/radialmonster/orf-cleanroom/issues?q=is%3Aopen+label%3Alead+no%3Aassignee . Don't take the first or top one: pick at random among them, or by what only you can do (cameras or files you own, a variant nobody is on). Comment "Taking this" as the first line and the bot assigns it to you (usually within a minute, sometimes a few). Take one at a time; comment "Releasing this" if you stop. A claim with no activity for 14 days is freed automatically. For the long-running tasks #1 (V1), #2 (V2) and #3 (manifest), claim a specific model or sub-question in a comment.

**Verify a lead.** Run its Reproduce steps again as a new run, on at least one file or body the lead did not use (if the lead already used every CC0 file of the model, say so; a wider run on the same files, such as the whole frame, counts if described). The finder may verify their own lead, but independent verification by a different person is preferred. If the numbers match, open a PR that adds `findings/<folder>/YYYY-MM-DD--finder--slug.md` with `Author:` the finder, `Verified by:` you (the PR author), `Lead: #n` (format: [findings/README.md](findings/README.md)); describe the new run in the Verification section. It merges automatically and the lead is closed, labelled `self-verified` (you are the finder) or `verified`. If the numbers do not match, add nothing to `findings/`: comment your numbers on the lead issue.

**Upgrade a self-verified finding.** Pick one from https://github.com/radialmonster/orf-cleanroom/issues?q=label%3Aself-verified , reproduce it, and add a file with `Reproduces: <finding ID>` (see findings/README.md). It becomes `verified`.

**Closing.** Verified and self-verified leads close automatically. A lead's author can close it to withdraw it. #1, #2 and #3 stay open: PRs for them say `Part of #n`; write `Fixes #n` only when the PR completes the issue. The maintainer occasionally closes stale ones.

## Flow
Submit from your own GitHub account so the work is linked to you. New to git or GitHub? An AI assistant can walk you through the account, fork and pull request (AGENTS.md tells it how).

1. Pick a task: "Start here" in the README, an unclaimed lead, or an issue labelled `good first issue`. Claim it with a comment.
2. Fork the repo and create a branch. With the GitHub CLI (after `gh auth login`):

       gh repo fork radialmonster/orf-cleanroom --clone
       cd orf-cleanroom
       git switch -c my-change

   (Maintainers with write access can't fork their own repo; they push the branch to it directly.) Later, `git push -u origin my-change` sends the branch to your fork, and `gh pr create --repo radialmonster/orf-cleanroom` opens the pull request.
3. Make one focused change per pull request.
   - Verified findings are **new files**: `findings/<folder>/YYYY-MM-DD--finder--short-slug.md`, in the folder for the variant (`container`, `V0`, `V1`, `V2`, `unassigned`), with yourself as `Verified by:` (also when you are the finder). Template and rules: [findings/README.md](findings/README.md). Existing findings are never edited (CI enforces this); correct one with a new verified finding that has `Corrects:`. Files are independent, so there are no numbers to pick and no merge conflicts.
   - Manifest rows are appended: use `tools/manifest_rows.py`. Never edit existing rows; to add measurements for a file already listed, add a new row for the same `sha256`.
   - Before running `python .github/scripts/pr_checks.py` locally, run `git fetch origin` so it compares against the current main.
   - If a PR that should merge on its own is still open an hour after its checks passed, an hourly sweep retries it; if it is still open after that, comment on the PR.
   - Numbers come with the `tools/` script that produced them, or, for a one-off count over existing tool output, a short inline script in the Reproduce section. New or changed tools go in their own PR, which waits for a maintainer.
4. Commit as yourself: set `git config user.name` / `user.email` to your own GitHub identity first, since the commit author is how credit is kept. Before opening the PR, check `git diff`: only your intended lines, no whole-file line-ending changes. After committing, run the same checks CI runs: `python .github/scripts/pr_checks.py` (set `PR_AUTHOR=yourhandle` so it checks `Verified by:` too). If you changed a tool, also run `python -m py_compile tools/*.py` and its `--help`.
5. Open a pull request. A PR that only adds a finding verified by you (the lead issue is the finder's, yours or someone else's) and manifest rows under your own handle merges automatically once the checks pass, and the lead is closed as `self-verified` or `verified`. Anything else (tools, docs, rules, edits to shared files) is labelled `needs-maintainer` and waits for a maintainer, who looks only occasionally; that can take weeks and is normal. The PR template's checklist includes the RULES.md sign-off and, for bitstream work, the clean-room declaration; tick them yourself, as they're your statements.

## Validating each other's work
Nobody signs findings off. A result is a lead (an issue) until it is reproduced in a second, separate run and the finding file is added; the verifier is credited as `Verified by:` and may be the finder. Independent verification by a different person is still preferred, and upgrades a `self-verified` finding to `verified`. Reproducing someone's lead is a contribution in itself. If you cannot reproduce it, say so with your numbers on the lead issue. `python tools/findings_index.py` shows the verified findings.

## Clean-room declaration
For work on the bitstream or decoder logic (findings, OPEN-QUESTIONS, decoding tools), you must not have read the ORF decompression code of LibRaw, rawspeed, dcraw or projects derived from them. If you have, you can still help with samples, the manifest, tooling and testing; just say so in your PR.

## Your own files
Welcome. Measure them locally and publish only numbers and SHA-256 (see RULES.md, "Data").

## Requirements
Python 3.8 or newer, standard library only. CI checks that every tool compiles and runs `--help` on Python 3.8 and 3.12.

## Credit
Your handle stays on what you found. See RULES.md, "Credit".
