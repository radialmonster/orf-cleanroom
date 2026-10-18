# orf-cleanroom

An open, clean-room effort to document and decode **compressed Olympus / OM System ORF** raw files, so that a decoder can be written from independently established facts and contributed to [LightCraft](https://github.com/storytold/lightcraft).

Today LightCraft decodes uncompressed ORF only; compressed ORF (the default on most Olympus and OM System interchangeable-lens bodies) opens the embedded JPEG preview.

**Read [RULES.md](RULES.md) before contributing.** The whole point of this repo is provenance: every fact here must come from public specifications, patents, or measurements of the files themselves.

## Start here

New? These need no knowledge of the bitstream:
1. **Add manifest rows:** download a few CC0 files for a model that isn't in `samples/manifest.csv` yet and add rows with `tools/manifest_rows.py` (see samples/README.md).
2. **Reproduce F2:** run `tools/orf_signature.py` on more bodies and append an entry to FINDINGS.md confirming or contradicting it.
3. **Write a reproduction script for part of F1** (see OPEN-QUESTIONS 6).

Issues labelled [`good first issue`](https://github.com/radialmonster/orf-cleanroom/labels/good%20first%20issue) are the same kind of task. All issues: https://github.com/radialmonster/orf-cleanroom/issues

## How to help
- **Samples:** upload varied ORFs (daylight, indoor, high ISO, different bodies) to [raw.pixls.us](https://raw.pixls.us). They are CC0, so anyone here can use them. Please don't attach raw files to this repo.
- **Analysis:** pick an item from [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) or the issues, comment that you're working on it, and report back with numbers and a way to reproduce them.
- **Findings:** established results go in [FINDINGS.md](FINDINGS.md) with their evidence.

## Getting test files

Use [raw.pixls.us](https://raw.pixls.us), a public collection of raw samples. **Not every file there is CC0.** The `/data/` mirror and the bulk git clones mix CC0 and non-CC0 files (for example CC BY-NC-SA), and the file names don't tell you which is which. Only CC0 files may be used here.

Use `tools/pixls_samples.py`. It reads the site's own licence listing:

    python tools/pixls_samples.py list                    # CC0 Olympus/OM ORF and ORI files
    python tools/pixls_samples.py download ../orf-samples --model OM-5 --max 3
    python tools/pixls_samples.py check ../orf-samples/*.ORF   # licence of files you already have

`download` fetches CC0 files only, verifies each SHA-256, and refuses to save inside the repo. `check` looks files up by SHA-256 and tells you if one is not CC0 or not a raw.pixls.us file. Run it on anything you got another way.

Record each file you use in `samples/manifest.csv` (see samples/README.md).

**Have an Olympus or OM System camera?** Please upload a few varied ORFs (daylight, indoor, high ISO, and High Res Shot if your body has it) to raw.pixls.us as CC0. That's the most useful single contribution, because then everyone can test on them. Don't attach raw files to this repo or its issues.

## Contributing changes

`main` is protected, so all changes go through pull requests:
1. Fork the repo and create a branch.
2. Make your change. Findings go at the **end** of FINDINGS.md as a new entry (append-only; a CI check enforces it).
3. Open a pull request and include the line "I confirm this follows RULES.md".

To claim a task, comment on its issue first so work isn't duplicated.

## Layout
- `RULES.md`: the clean-room contract
- `AGENTS.md`: instructions for AI coding agents
- `FINDINGS.md`: what has been established, with evidence (append-only)
- `OPEN-QUESTIONS.md`: what is still unknown, plus unverified hypotheses
- `VARIANTS.md`: the variant registry, keyed by measured file signatures
- `samples/manifest.csv`: raw.pixls.us files used, with their measured signature and variant
- `tools/`: analysis scripts (our own code only)
- `stats/`: aggregate tables only, no images or raw payloads

## Licence
Everything in this repo (text, tables and code) is dedicated to the public domain under [CC0 1.0](LICENSE). By contributing, you agree your contribution is released under CC0 too.
