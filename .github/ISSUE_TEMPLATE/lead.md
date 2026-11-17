---
name: Lead (a result someone else can check)
about: Publish something you found, with the numbers and the steps to reproduce it
title: "<short statement of the result>"
labels: lead
---
Variant: unassigned
<!-- container, unassigned, or a variant V<n> (V0, V1, V2, ... any number; see VARIANTS.md). To propose a new variant, write the next free V<n>. A labeler reads this line. Keep it as the first line. -->

## Claim
<!-- What you found, in plain sentences. One result per lead; split separate results into separate issues. -->

## Evidence
<!--
- Tool and commit: the tools/ script and the last commit that changed it (git log -1 --format=%h -- tools/NAME.py).
- Files: list each input. Give the public identity and SHA-256 for public files, including the raw.pixls.us id where applicable. Use anonymous labels for unshared files and include SHA-256 only with the owner's explicit permission. Mark results based only on unshared inputs `not yet reproducible`.
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
