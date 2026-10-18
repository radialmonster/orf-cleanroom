# Instructions for AI agents

Read [RULES.md](RULES.md) first and follow it. It applies to everything you write here.

- Never read, search for, fetch, run or compare against code or output from other raw decoders (LibRaw, rawspeed, dcraw or derivatives), or write-ups about them. If a task seems to need them, stop and say so.
- Use only public specifications, patents, the sample files themselves, and code you write from scratch.
- **FINDINGS.md is append-only.** Add new entries at the end. Never edit, reorder or delete existing entries, including your own earlier ones. To correct or retract one, append a new entry that names the entry it corrects.
- Don't commit raw files, images, or decoded or preview pixel data. Commit aggregate statistics only.
- Get test files from raw.pixls.us (see README, "Getting test files") and use only ones whose licence is CC0.
- Reference samples by raw.pixls.us name and hash, and add each one you use to `samples/manifest.csv` with its measured signature.
- Classify files by measured signature (VARIANTS.md), never by model name alone or by what another decoder does.
- Put a reproducible script in `tools/` for every number you report.
- State in your PR description that the work follows RULES.md.
