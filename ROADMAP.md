# Roadmap: from findings to decoders

The point of this repo is a decoder anyone can use, built only from facts that were checked twice. This page says how a fact travels, where each variant stands, and what to do next. All CC0.

## The pipeline

1. **Findings** (`findings/`): verified facts, one file each, never edited. Unverified results are leads (GitHub issues).
2. **SPEC** (`specs/V<n>.md`): one section per variant, assembled only from findings. Each statement cites its finding ID. A statement resting on a lead cites `lead #n` and is marked unverified. A missing piece is listed as a gap, and a gap is a lead.
3. **Reference decoder** (`decoder/orf_decode.py`): small, stdlib only, each layout step commented with the finding or lead it relies on. It prints aggregates only and writes no files. Compressed variants are reported as "not yet specified".
4. **Conformance** (`tools/conformance.py`, `samples/conformance-V0.csv`): per file, an output hash (SHA-256 of the decoded values as little-endian uint16, row-major, unshifted). A decoder conforms when its hashes match on the CC0 files.

Nothing enters a later stage without the earlier one: no decoder step without a spec line, no spec line without a finding or a lead cited.

## Status per variant (honest)

- Container: verified. Compression tag is 1 on every file (so it cannot tell variants apart); a fixed-size payload is told by exact size. The strip layout (gaps between strips on 6 files) is an observation, not yet a finding.
- V0 packed-12: verified (self-verified, so a second person's run would upgrade it). Decoder: exact payload end on 9 of 9 CC0 files. Pixel order inside a unit is undecided.
- V0 packed-12.8: lead #70 only, unverified. Decoder: exact payload end on 5 of 5. Pad byte not yet explained.
- V0 packed-16: lead #71 only, unverified. Decoder: exact end on 3 of 3; E-400 has 793 words with a non-zero low nibble, unexplained.
- V1, V2 and other compressed variants: stub specs `specs/V1.md` and `specs/V2.md` (verified facts, lead-only items and Gaps; no bitstream decoded). The decoder detects them and stops. Open leads are under the `variant:V1` and `variant:V2` labels. This is where most of the work remains: no compressed payload can be decoded yet.

Exact numbers: run `python -I tools/conformance.py <files>`; the committed result is `samples/conformance-V0.csv`.

## How to move things forward

- **Fill a spec gap.** Each gap in `specs/` is a lead. Pick one at random among unclaimed leads (see README "Start here"), measure it, publish it. When it is verified, a PR replaces "lead #n (unverified)" in the spec with the finding ID, and the decoder comment is updated in the same PR.
- **Change the decoder.** A decoder or decoder change is a code PR. It waits for maintainer review (like any tool). Each step it adds must cite the finding or lead it relies on, in a comment and in the PR description. A step with only a lead is flagged unverified in the decoder output.
- **Verify a decoder independently.** Write a second implementation without reading the first, or have a different person run the same decoder, then run `tools/conformance.py` on the CC0 files. Matching output hashes on every file is the evidence. Mismatches are leads: say which file and which value differ.
- **Add compressed variants.** Same path: leads, then findings, then a spec section (stubs `specs/V1.md` and `specs/V2.md` exist; fill them in), then decoder support, then a `conformance-V1.csv`.

## Recording "reproduces conformance" with the existing system

The lightest fit is a normal lead and finding, so automerge keeps working with no change:

- A lead "V0 decoder conformance hashes" whose Evidence is `samples/conformance-V0.csv` at a named commit of `tools/conformance.py`.
- Someone else runs the tool (their own copy or their own implementation) on the same CC0 files and opens a PR adding a finding whose `Lead:` is that lead and `Verified by:` is themselves, with the matching or differing hashes in its Verification section.
- A different implementation's hashes, if they match, are the strongest form; say so in the finding.

No automerge change is needed. If per-decoder badges are wanted later, that would need an automerge change, which this PR does not make.

## Where to start

Lead and gap list: `specs/V0.md` (Gaps section), the Gaps lists in `specs/V1.md` and `specs/V2.md`, and the open leads. A second-implementation conformance check on V0 needs no bitstream knowledge beyond the spec.
