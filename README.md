# orf-cleanroom

An open, clean-room effort to document and decode **compressed Olympus / OM System ORF** raw files, so that a decoder can be written from independently established facts and contributed to [LightCraft](https://github.com/storytold/lightcraft).

Today LightCraft decodes uncompressed ORF only; compressed ORF (the default on most Olympus and OM System interchangeable-lens bodies) opens the embedded JPEG preview.

**Read [RULES.md](RULES.md) before contributing.** The whole point of this repo is provenance: every fact here must come from public specifications, patents, or measurements of the files themselves.

## How to help
- **Samples:** upload varied ORFs (daylight, indoor, high ISO, different bodies) to [raw.pixls.us](https://raw.pixls.us). They are CC0, so anyone here can use them. Please don't attach raw files to this repo.
- **Analysis:** pick an item from [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) or the issues, comment that you're working on it, and report back with numbers and a way to reproduce them.
- **Findings:** established results go in [FINDINGS.md](FINDINGS.md) with their evidence.

## Getting test files

Use [raw.pixls.us](https://raw.pixls.us). It's a public collection of raw samples, mostly released under CC0.
- **Browse:** the repository table on the front page lists every camera by make and model, with a **License** column for each sample. Look under OLYMPUS and OM Digital Solutions.
- **Download single files:** from the table, or from the HTTPS mirror at https://raw.pixls.us/data/.
- **Download everything:** `git clone https://raw.pixls.us/data.lfs.git` (needs Git LFS), or `git clone https://raw.pixls.us/data.annex.git && cd data.annex && git annex get .` (needs git-annex). It's large, so you may prefer just the Olympus/OM folders.
- **Check the licence on each file.** Some samples are not CC0 (the front page links a "non-CC0" view, `https://raw.pixls.us/?noncc0#repo`). Only CC0 files may be used for anything published here.
- **Record what you use:** add each file to `samples/manifest.csv` with its SHA-256, so others can get exactly the same file.

**Have an Olympus or OM System camera?** Please upload a few varied ORFs (daylight, indoor, high ISO, and High Res Shot if your body has it) to raw.pixls.us as CC0. That's the most useful single contribution, because then everyone can test on them. Don't attach raw files to this repo or its issues.

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
