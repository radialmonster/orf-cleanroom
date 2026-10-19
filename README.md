# orf-cleanroom

An open, clean-room effort to document and decode **compressed Olympus / OM System ORF** raw files, so that a decoder can be written from independently established facts and contributed to [LightCraft](https://github.com/storytold/lightcraft).

Today LightCraft decodes uncompressed ORF only; compressed ORF (the default on most Olympus and OM System interchangeable-lens bodies) opens the embedded JPEG preview.

**Read [RULES.md](RULES.md) before contributing.** The whole point of this repo is provenance: every fact here must come from public specifications, patents, or measurements of the files themselves.

## Start here

Results here are **leads** (GitHub issues) until they are reproduced in a second, separate run; then they become **findings** (files in `findings/`). A different person verifying is preferred; the finder may verify their own lead (status `self-verified`), and a different person can upgrade it later. Two main ways to help:

1. **Take a lead and reproduce, extend or refute it.** List the [unclaimed leads](https://github.com/radialmonster/orf-cleanroom/issues?q=is%3Aopen+label%3Alead+no%3Aassignee). Don't take the first or top one: many people doing the same investigation helps no one. Pick one at random among the unclaimed ones labelled `lead` or [`idea`](https://github.com/radialmonster/orf-cleanroom/issues?q=is%3Aopen+label%3Aidea+no%3Aassignee), or by what only you can do (cameras or files you own, a variant nobody is on). Comment "Taking this" as the first line and the bot assigns it to you; take one at a time, and comment "Releasing this" if you stop (claims with no activity for 14 days are freed automatically). Run the lead's steps on other files than it used. If your numbers match, open a PR adding the finding file (see findings/README.md); if not, comment your numbers on the lead. You can also upgrade a [`self-verified` finding](https://github.com/radialmonster/orf-cleanroom/issues?q=label%3Aself-verified) by reproducing it.
2. **Find a new lead and publish it.** Measure something with a `tools/` script, then open an issue from the "Lead" template: claim, evidence, reproduce steps, next steps. Split separable sub-questions into their own lead or idea issues ("Builds on: #n"). Use the "Idea" template for a hunch without numbers.

Other help, no bitstream knowledge needed:
- **Add manifest rows:** no claim or announcement needed. Run `python tools/pixls_samples.py list --missing samples/manifest.csv` to see the CC0 files not yet listed, pick some at random (not the first ones) so people spread out, and add rows with `tools/manifest_rows.py`, including ORI and High Res Shot files (see samples/README.md). Files are roughly 10-70 MB each; `download --model M` fetches one model. A second row for an already listed file, measured by a different person, is welcome as an independent measurement. Most useful: compressed bodies, especially the 5240-wide ones from OPEN-QUESTIONS 6 (OM-5, OM-5 Mark II, E-M1 Mark II).
- **V1 and V2:** #1 (V1) and #2 (V2) are only indexes of their open sub-questions; don't claim them. Take one of the `idea` issues they list, and publish what you measure as a lead.

All issues: https://github.com/radialmonster/orf-cleanroom/issues

## How to help
- **Samples:** upload varied ORFs (daylight, indoor, high ISO, different bodies) to [raw.pixls.us](https://raw.pixls.us). They are CC0, so anyone here can use them. Please don't attach raw files to this repo.
- **Analysis:** pick an item from [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) or a lead, say you're working on it, and publish the numbers and a way to reproduce them as a lead issue.
- **Findings:** [findings/](findings/README.md) holds only verified findings, one file each. A lead becomes a finding when it is reproduced in a second run and the file is added by PR.

## Getting test files

**Your own ORFs are welcome**: run the tools on them and publish the numbers (never the files). See RULES.md, "Data".

For files everyone can re-test, use [raw.pixls.us](https://raw.pixls.us), a public collection of raw samples. **Not every file there is CC0.** The `/data/` mirror and the bulk git clones mix CC0 and non-CC0 files (for example CC BY-NC-SA), and the file names don't tell you which is which. Only CC0 files may be used here.

Use `tools/pixls_samples.py`. It reads the site's own licence listing:

    python tools/pixls_samples.py list                    # CC0 Olympus/OM ORF and ORI files
    python tools/pixls_samples.py download ../orf-samples --model OM-5 --max 3   # exact model name from `list`
    python tools/pixls_samples.py check ../orf-samples/*       # licence of files you already have

On Windows, run these in Git Bash, or in PowerShell/cmd use a folder path like `..\orf-samples` and list files explicitly (they do not expand `*`).

`download` fetches CC0 files only, verifies each SHA-256, and refuses to save inside the repo. `check` looks files up by SHA-256 and tells you if one is not CC0 or not a raw.pixls.us file. Run it on files you got from elsewhere.

Record each file you use in `samples/manifest.csv` (see samples/README.md).

**Have an Olympus or OM System camera?** Please upload a few varied ORFs (daylight, indoor, high ISO, and High Res Shot if your body has it) to raw.pixls.us as CC0. That's the most useful single contribution, because then everyone can test on them. Don't attach raw files to this repo or its issues.

## Contributing changes

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: fork, branch, pull request; `main` is protected.

**Data pull requests merge automatically.** A PR that only adds a verified finding (`Verified by:` you, `Lead:` the finder's lead issue; the finder may be you) or appends rows to `samples/manifest.csv` under your own handle merges by itself once the checks pass, and the lead issue is closed as `self-verified` or `verified`. Anything else (tools, docs, rules, edits to the shared files) waits for a maintainer, who looks only occasionally, so it can take weeks. That's normal; nothing is wrong with your PR.

## Credit

Findings stay credited to whoever found them: the finder's handle is in each finding's file name and `Author:` line, the verifier is credited as `Verified by:` (which may be the finder), existing findings can't be edited, renamed or deleted, and anything built from this work credits them. See RULES.md, "Credit".

## Layout
- `RULES.md`: the clean-room contract
- `AGENTS.md`: instructions for AI coding agents
- `findings/`: verified findings only, one file each, by variant (unverified results are lead issues)
- `OPEN-QUESTIONS.md`: what is still unknown, plus unverified hypotheses
- `VARIANTS.md`: the variant registry, keyed by measured file signatures
- `samples/manifest.csv`: raw.pixls.us files used, with their measured signature and variant
- `tools/`: analysis scripts (our own code only), including `findings_index.py` (lists findings and their status)
- `stats/`: aggregate tables only, no images or raw payloads

## Licence
Everything in this repo (text, tables and code) is dedicated to the public domain under [CC0 1.0](LICENSE). By contributing, you agree your contribution is released under CC0 too.
