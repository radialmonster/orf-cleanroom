# Roadmap: from findings to decoders

The point of this repo is a decoder anyone can use, built only from facts that were checked twice. This page says how a fact travels, where each variant stands, and what to do next. All CC0.

## The pipeline

1. **Findings** (`findings/`): verified facts, one file each, never edited. Unverified results are leads (GitHub issues).
2. **SPEC** (`specs/V<n>.md`): one section per variant, assembled only from findings. Each statement cites its finding ID. A statement resting on a lead cites `lead #n` and is marked unverified. A missing piece is listed as a gap, and a gap is a lead.
3. **Reference decoder** (`decoder/orf_decode.py`): small, stdlib only, each layout step commented with the finding or lead it relies on. It prints aggregates only and writes no files. Compressed variants are reported as "not yet specified".
4. **Conformance** (`tools/conformance.py`, `samples/conformance-V0.csv`): per file, an output hash (SHA-256 of the decoded values as little-endian uint16, row-major, unshifted). A decoder conforms when its hashes match on the CC0 files.

Nothing enters a later stage without the earlier one: no decoder step without a spec line, no spec line without a finding or a lead cited.

## Status per variant (honest)

- Container: verified. Compression tag is 1 on every file (so it cannot tell variants apart); a fixed-size payload is told by exact size. The strip layout (gaps between strips on 6 files) is an observation, not yet a finding; lead #77 (unverified) explains it as a two-field row layout, which the decoder applies (spec S1.4).
- V0 packed-12: verified (self-verified, so a second person's run would upgrade it). Decoder: exact payload end on 9 of 9 CC0 files. Pixel order inside a unit is undecided. Two-field row layout on 6 files: lead #77; header rule: lead #78 (candidate rule; whole-frame re-run on all 9 CC0 files across findings `2026-10-20--radialmonster--iirs-iiro-header-whole-frame-byte-order` and `2026-10-21--radialmonster--iiro-packed12-and-packed16-whole-frame-byte-order`, both Partial and on the same files, no new body; both leads still open).
- V0 packed-12.8: self-verified (finding `2026-10-20--radialmonster--packed-12-8-groups-of-ten-values`; a second person's run would upgrade it). Decoder: exact payload end on 5 of 5; pad byte 0 in every group. Open: pixel order inside a unit (G4), black level per body (G7).
- V0 packed-16: lead #71 only, unverified (byte order versus the TIFF mark holds 3 of 3 whole-frame in finding `2026-10-21--radialmonster--iiro-packed12-and-packed16-whole-frame-byte-order`, Partial, same three files). Decoder: exact end on 3 of 3; E-400 has 793 words with a non-zero low nibble, floor-mean interpolated pixels on 791 of 792 interior (finding `2026-10-20--radialmonster--e400-low-nibble-floor-mean-interpolation`, self-verified, partial; one exception open, G3).
- V1, V2 and other compressed variants: stub specs `specs/V1.md` and `specs/V2.md` (verified facts, lead-only items and Gaps; no bitstream decoded). Token parse statistics: tokens per pixel 1.027 to 1.036 on four non-5240-wide bodies and 1.155 on TG-7 (finding `2026-10-21--radialmonster--tokens-per-pixel-on-non-5240-bodies`, Partial for lead #29, see V1.md S1.4). The decoder detects them and stops. Open leads are under the `variant:V1` and `variant:V2` labels. This is where most of the work remains: no compressed payload can be decoded yet.

Exact numbers: run `python -I tools/conformance.py <files>`; the committed result is `samples/conformance-V0.csv`. A blind second implementation written from `specs/V0.md` alone (`tools/v0_spec_check.py`, #93) matches all 17 hashes with exact payload ends: finding `2026-10-19--radialmonster--independent-v0-hash-agreement` (findings/V0, partial verification of lead #75). So V0 decoding is reproducible from the spec on these files. Still open: pixel order inside a unit (G4) and the layout selectors in general (G6).

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

No automerge change is needed. If per-decoder badges are wanted later, that would need an automerge change, which is not planned.

## Where to start

Lead and gap list: `specs/V0.md` (Gaps section), the Gaps lists in `specs/V1.md` and `specs/V2.md`, and the open leads. A second-implementation conformance check on V0 needs no bitstream knowledge beyond the spec.
