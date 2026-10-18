# Variants

Variants are defined by **what can be measured in the files**, not by camera model. Model names are listed as observations only. A variant is never inferred from another decoder's behaviour (see RULES.md).

## Signature fields
- **Container:** compression tag (note F2: it reads 1 even on compressed files, so use bits per pixel instead), maker-note version, raw data offset and length.
- **Payload:** width x height, bits per pixel (payload bytes x 8 / pixels).
- **Bitstream:** escape length, whether the calm parse (F1) works, per-row token stride.
- **Mode:** normal, High Res Shot / pixel-shift, other.

## Status levels
`unknown` → `parse understood` → `decodes` (sensor values produced) → `verified` (reproducible internal checks pass on named raw.pixls.us files)

## Merging variants
Two variants merge only when the same script in `tools/` reproduces both and they pass the same internal checks: row stride, lossless round-trip, agreement with the embedded preview at the Exif crop. Never by comparison with another converter.

## Assigning a variant
A manifest row gets a variant only from measurements: V0 when bits per pixel is 12 or more; V1 or V2 when a bitstream script in `tools/` shows the matching signature. Otherwise it stays `unassigned`.

## Tracking
One issue per variant (https://github.com/radialmonster/orf-cleanroom/issues), labelled `variant:Vn`, with the work split into `decode` (bitstream → sensor values) and `develop` (levels, crop, CFA pattern, white balance, colour).

---

## V0: uncompressed ORF
- Signature: payload bits per pixel at the container bit depth or above.
- Status: `decodes` in LightCraft already. Listed for completeness and classification.

## V1: calm-parse compressed
- Signature: compressed; the calm parse from F1 works (q zeros, stop bit, 5-bit suffix, escape at q ≥ 17); per-row stride equals the payload width on at least one body (5240 wide).
- Models seen: none recorded yet. The PR that assigns a manifest row to this variant also adds its model here.
- Status: `parse understood`. Value assembly and predictor open (OPEN-QUESTIONS 1-2). On some bodies the stride drifts (question 3), which may split this variant.

## V2: 31-bit-escape compressed
- Signature: compressed; files from larger sensors share a 31-bit escape; the ordinary code doesn't fit the V1 parse.
- Models seen: none recorded yet. The PR that assigns a manifest row to this variant also adds its model here.
- Status: `unknown` (question 5).

## Unassigned
- High Res Shot / pixel-shift files: not yet classified, so they get their own variants once measured.
- ORI files: not yet classified.
