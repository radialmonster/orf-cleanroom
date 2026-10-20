# Variants

Variants are defined by **what can be measured in the files**, not by camera model. Model names are listed as observations only. A variant is never inferred from another decoder's behaviour (see RULES.md).

Variants are numbered as they are found: V0, V1, V2, and any V<n> after that. The ones below are only those measured so far; there may be many more, per model, firmware, mode (High Res Shot, ORI) or something else. Splitting a variant into several, or proposing a new V<n> (next free number, with its signature), is welcome as a lead.

## Signature fields
- **Container:** compression tag (see the F2 lead, #10: it reads 1 even on compressed files, so use bits per pixel instead), maker-note version, raw data offset and length.
- **Payload:** width x height, bits per pixel (payload bytes x 8 / pixels).
- **Bitstream:** escape length, whether the calm parse (the F1 lead, #11) works, per-row token stride.
- **Mode:** normal, High Res Shot / pixel-shift, other.

## Status levels
`unknown` → `parse understood` → `decodes` (sensor values produced) → `verified` (reproducible internal checks pass on named raw.pixls.us files)

## Merging variants
Two variants merge only when the same script in `tools/` reproduces both and they pass the same internal checks: row stride, lossless round-trip, agreement with the embedded preview at the Exif crop. Never by comparison with another converter.

## Assigning a variant
A manifest row gets a variant only from measurements: V0 when `size_class` is `packed-…` (an exact fixed-size payload; a bits-per-pixel threshold is not enough); V1, V2 or another V<n> when a bitstream script in `tools/` shows the matching signature. Otherwise it stays `unassigned`.

## Tracking
Leads are labelled `variant:Vn` ([V0](https://github.com/radialmonster/orf-cleanroom/issues?q=is%3Aopen+label%3Alead+label%3Avariant%3AV0), [V1](https://github.com/radialmonster/orf-cleanroom/issues?q=is%3Aopen+label%3Alead+label%3Avariant%3AV1), [V2](https://github.com/radialmonster/orf-cleanroom/issues?q=is%3Aopen+label%3Alead+label%3Avariant%3AV2)), with the work split into `decode` (bitstream → sensor values) and `develop` (levels, crop, CFA pattern, white balance, colour).

---

## V0: fixed-size packing (uncompressed)
- Signature: `size_class` is `packed-12`, `packed-12.8` or `packed-16`: the payload size exactly equals width x height x that many bits (lead #28).
- Models seen (lead #28): C5060WZ, C7070WZ, SH-2, SP-510UZ/550UZ/565UZ/570UZ, XZ-2, XZ-10 (12); E-300, E-330, E-500, and High Res Shot files from PEN-F and E-M5 Mark II (12.8); E-1, E-10, E-400 (16).
- Findings: [findings/V0/](findings/V0/).
- Status: uncompressed, so not the main target here; listed for classification. Whether a given decoder covers every packing listed here is tracked in [specs/V0.md](specs/V0.md) and `samples/conformance-V0.csv` (reference decoder: exact payload end on all 17 CC0 files; packed-12.8 and packed-16 rest on leads #70, #71).

## V1: calm-parse compressed
- Signature: compressed; the calm parse from the F1 lead (#11) works (q zeros, stop bit, 5-bit suffix, escape at q ≥ 17); per-row stride equals the payload width on at least one body (5240 wide).
- Models seen: none recorded yet. The PR that assigns a manifest row to this variant also adds its model here.
- Findings: [findings/V1/](findings/V1/) (the F1 lead, #11, is the first candidate).
- Status: `parse understood`. Value assembly and predictor open (see [specs/V1.md](specs/V1.md), Gaps). On some bodies the stride drifts (same list), which may split this variant.

## V2: large-sensor compressed (not understood)
- Signature: compressed; files from larger sensors where the ordinary code does not fit the V1 parse (token counts near an independent-bits null, finding 2026-10-20--radialmonster--large-sensor-k5-parse-near-bernoulli-null). The name used to say "31-bit-escape"; that width is not established by measurement (specs/V2.md S2.2), so it is no longer part of the signature.
- Models seen: none recorded yet. The PR that assigns a manifest row to this variant also adds its model here.
- Findings: [findings/V2/](findings/V2/).
- Status: `unknown` (see [specs/V2.md](specs/V2.md), Gaps).

## Unassigned
- Findings whose variant isn't known yet: [findings/unassigned/](findings/unassigned/). Container facts that span variants: [findings/container/](findings/container/).
- High Res Shot / pixel-shift files: two of the 21 in the manifest (PEN-F, E-M5 Mark II) are packed-12.8, so V0 by signature; the other 19 are compressed and still `unassigned`. Whether the mode needs its own variants is open (hypothesis H2, [specs/V0.md](specs/V0.md) G5, which applies to both).
- ORI files: not yet classified.
