---
name: Lead (a result someone else can check)
about: Publish something you found, with the numbers and the steps to reproduce it
title: "<short statement of the result>"
labels: lead
---
Variant: unassigned
<!-- container, V0, V1, V2 or unassigned (see VARIANTS.md). A labeler reads this line. Keep it as the first line. -->

## Claim
<!-- What you found, in plain sentences. One result per lead; split separate results into separate issues. -->

## Evidence
<!--
- Tool and commit: the tools/ script and the last commit that changed it (git log -1 --format=%h -- tools/<script>.py).
- Files: list every file used, each as raw.pixls.us id + SHA-256, or `own` + SHA-256 (own files: numbers only, never the file). Verifiers need this list to pick files the lead did not use.
- The numbers, as produced by the script. Say how strong each is and on how many files.
- Found by @yourhandle, date.
-->

## Reproduce
<!-- The exact commands, so someone can run them on the same files and on others. -->

## Builds on
<!-- Findings (file names) or issues (#n) this uses, or "nothing". -->

## Next steps
<!--
Make this useful to the next person:
- What is untested.
- Which other files or bodies to try.
- Open questions.
List separable sub-questions one per line ("- [ ] ..."). Anyone can take one on its own,
or publish it as its own lead (once you have numbers) with "Builds on: #<this issue>".
-->

- [ ] This follows RULES.md: public specs, patents and my own measurements only; I have not read the ORF decompression code of LibRaw, rawspeed, dcraw or their derivatives, and nothing here comes from their output.
