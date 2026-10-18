# Open questions

1. **Value assembly:** how q, H and L combine into a signed residual. No mapping tried so far beats the trivial baseline.
2. **Predictor:** which neighbours the residual is relative to. The horizontal-gradient lead (see F1 in FINDINGS.md) needs testing by integrating along rows.
3. **Row stride drift:** on some bodies the per-row token count drifts instead of staying equal to the width. Why?
4. **Horizontal offset ramp:** the alignment offset with the preview grows with row band. Is that an artefact of the alignment method or real?
5. **Larger sensors:** the ordinary (non-escape) code in files sharing the 31-bit escape.
6. **Reproduction:** turn each finding into a script in `tools/` that runs on named CC0 files, and reproduce each other's leads (`python tools/findings_index.py` lists them). Good starting files for F1 (5240-wide payloads): raw.pixls.us ids 6343 (OM-5), 8549 (OM-5 Mark II), and the 5240-wide E-M1MarkII files, all CC0.

## Hypotheses (unverified, not evidence)

- **H1: one shared decompression scheme across most compressed ORF bodies**, with per-model differences limited to dimensions, crop, levels, white balance and colour. Source: a general AI-assistant summary of unknown provenance, so it carries no weight here. Our own measurements so far show at least two bitstream behaviours (V1 and V2 in VARIANTS.md). To test: classify every manifest file and see whether V2 reduces to V1 under some parameter.
- **H2: High Res Shot files need separate handling.** Source: vendor documentation that the mode exists. To test: measure their signature.
