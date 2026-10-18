# Findings

**Append-only.** Add new entries at the end. Never edit or delete existing ones; to correct one, append a new entry that refers to it. See RULES.md.

Entry format: `## F<number> (<YYYY-MM-DD>, @<author>): <title>`, followed by the claim, the evidence and how to reproduce it.

---

## F1 (2026-10-18, @radialmonster): initial results

Status: early (edited). These were measured on compressed ORFs from several bodies. Each still needs a reproducible script in `tools/` running on named raw.pixls.us files before it counts as established for this repo.

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
