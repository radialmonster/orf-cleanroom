# Findings

**Append-only.** Add new entries at the end. Never edit or delete existing ones; to correct one, append a new entry that refers to it. See RULES.md.

Entry format: `## F<number> (<YYYY-MM-DD>, @<author>): <title>`, followed by the claim, the evidence and how to reproduce it.

---

## F1 (2026-10-18, @radialmonster): initial results

Status: early. These were measured on compressed ORFs from several bodies. Each still needs a reproducible script in `tools/` running on named raw.pixls.us files before it counts as established for this repo.

### Token structure (well supported)
- Reading MSB-first, the stream in the studied files parses as tokens: `q` zero bits, a stop bit, then a 5-bit suffix `b4..b0`. An escape occurs at `q >= 17`.
- On a 5240-wide body the token count per row matches the image width (stride 5240), consistent with **one token per pixel**.
- The suffix splits into `H = b4b3` and `L = b2b1b0`, with L read as a 3-bit two's-complement value (-4..3). Within a token, H and L are statistically independent. `b1` and `b0` behave as fair coins.
- No row/column parity effect and no byte-alignment artefact were found.

### Dependence between neighbouring tokens (well supported on one body, looser on another)
- At horizontal distance 1 and 3, dependence is cross-field only: H of one token predicts L of the next (mutual information ~0.12 bit), and L predicts the next H (~0.07). Same-field dependence there is ~0.
- At horizontal distance 2 and vertical distance 2, dependence is same-field only (L-L ~0.04, H-H ~0.02).
- So two chains interleave along a row, consistent with a 2x2 colour-filter pattern.
- About 97% of the H→next-L information is carried by `b4` predicting the **sign** of the next L.

### Geometry (one body so far)
- Token positions align with the embedded preview as a plain raster at the Exif crop scale, over part of the frame.
- The signed residual correlates with the preview's horizontal luminance gradient. That is suggestive of horizontal-difference prediction, but it was chosen from several candidates and isn't confirmed.

### Larger bodies
- Files from larger sensors share a 31-bit escape. Their ordinary code is not yet understood.

## F2 (2026-10-18, @radialmonster): the compression tag doesn't identify compressed ORF

- Claim: on every compressed ORF tested, the raw IFD's TIFF Compression tag (0x103) is 1 ("uncompressed"), and BitsPerSample is 16. The tag can't be used to classify. Bits per pixel (payload bytes x 8 / pixels) can: about 6-8.5 for the compressed bodies tested, and 16.00 for an uncompressed body (E-1).
- Also seen: High Res Shot-sized payloads (8172-10400 wide) in the same container with the same tag values.
- Evidence: `tools/orf_signature.py` on raw.pixls.us CC0 files from E-P7, E-M1MarkII, E-M5, E-1, OM-1, OM-3 and OM-5 Mark II (17 files).
- Reproduce: `python tools/orf_signature.py <those files>`.

## F3 (2026-10-18, @radialmonster): entry format update (process note, not a finding)

- From now on, an entry may include `Builds on: F<n> (@handle)` when it uses someone else's result, and `Submitted by: @handle` when the person adding it isn't the author. See RULES.md, "Credit".

## F4 (2026-10-18, @radialmonster): fixed-size payloads are exact; everything else is compressed

- Claim: uncompressed ORF payloads have a size exactly equal to width x height x 12, 12.8 or 16 bits. Compressed payloads have data-dependent sizes, 6-8.5 bits per pixel on the bodies tested. A bits-per-pixel threshold alone misleads: High Res Shot files from older bodies are 12.8 bpp packed (uncompressed), while newer bodies' High Res Shot files are compressed (6-7 bpp).
- Census of every CC0 Olympus / OM System ORF on raw.pixls.us (65 models):
  - packed-12 (9): C5060WZ, C7070WZ, SH-2, SP-510UZ, SP-550UZ, SP-565UZ, SP-570UZ, XZ-10, XZ-2
  - packed-12.8 (5): E-300, E-330, E-500, plus the High Res Shot files of E-M5 Mark II and PEN-F
  - packed-16 (3): E-1, E-10, E-400
  - variable (48): E-3, E-410, E-420, E-450, E-5, E-510, E-620, E-M1, E-M10, E-M10 Mark II/III/IIIs/IV, E-M1 Mark II/III, E-M1X, E-M5, E-M5 Mark II/III, E-P1, E-P2, E-P3, E-P5, E-P7, E-PL1, E-PL2, E-PL3, E-PL5, E-PL6, E-PL7, E-PL8, E-PL9, E-PL10, E-PM1, E-PM2, OM-1, OM-1 Mark II, OM-3, OM-5, OM-5 Mark II, PEN-F, STYLUS1, STYLUS1s, TG-4, TG-5, TG-6, TG-7, XZ-1, including High Res Shot sizes (8172-10400 wide) on E-M1 Mark II and later.
- Builds on: F2 (@radialmonster).
- Evidence: `tools/orf_signature.py` (`size_class` column) on raw.pixls.us CC0 files from the bodies above. Reproduce: `tools/pixls_samples.py download DIR` (all CC0 Olympus/OM files), then `tools/orf_signature.py DIR/*` and count `size_class` per model.

## Frozen: new findings go in findings/

This file is now frozen history. New findings go one per file in [findings/](findings/README.md), organised by variant, and CI rejects any further change to this file. Cite the entries above as `F1`..`F4`. By variant: F2, F3 and F4 belong to `container`; F1 belongs to `V1`. They stay here and are not moved.
