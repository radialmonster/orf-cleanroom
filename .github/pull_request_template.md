## What this adds

<!-- One focused change. Link the issue it addresses. -->

## Checklist
- [ ] I confirm this follows RULES.md.
- [ ] Raw files and images are not included; numbers only.
- [ ] Every number has the `tools/` script that produced it, and the files it ran on (raw.pixls.us id + SHA-256, or `own` + SHA-256).
- [ ] Findings: only new files under `findings/<folder>/`, named `YYYY-MM-DD--myhandle--slug.md`, with my own handle as `Author:` (or `Submitted by:` for someone else's work). Nothing existing is edited; FINDINGS.md is untouched.
- [ ] Manifest: rows are appended only (a new row for an already listed `sha256`), with `measured_by` starting `@myhandle `.
- [ ] If I reproduce or dispute a finding, its ID is in `Reproduces:` or `Corrects:`.
- [ ] For bitstream/decoder work: I have not read the ORF decompression code of LibRaw, rawspeed, dcraw or their derivatives.
