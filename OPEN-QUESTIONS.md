# Open questions

1. **Value assembly:** how q, H and L combine into a signed residual. No mapping tried so far beats the trivial baseline. To test: take tokens from several CC0 V1 files, tabulate (q, suffix) against neighbouring-pixel differences, and test candidate assemblies for consistency with a smooth image.
2. **Predictor:** which neighbours the residual is relative to. The horizontal-gradient lead (see the F1 lead, #11) needs testing by integrating along rows. To test: fit candidate predictors (left, up, mixtures, odd/even rows or columns) to partly assembled values; the right one gives a markedly narrower residual distribution.
3. **Row stride drift:** on some bodies the per-row token count drifts instead of staying equal to the width. Why? To test: list the manifest files with `row_stride` drift, measure per-row token counts, and check for row headers, padding or per-row byte alignment.
4. **Horizontal offset ramp:** the alignment offset with the preview grows with row band. Is that an artefact of the alignment method or real?
5. **Larger sensors:** the ordinary (non-escape) code in files sharing the 31-bit escape. Code-length statistics on larger-sensor files, compared with V1, would constrain it. Lead #37 found no q=30 (31-bit) escape in 11 CC0 files with the parse from #11 (escapes at q 17 to 29), so whether the escape exists in other files or needs a different parse is also open.
6. **Reproduction:** turn each finding into a script in `tools/` that runs on named CC0 files, and reproduce each other's leads (the open issues labelled `lead`; `python tools/findings_index.py` lists the verified findings). Good starting files for the F1 lead (#11) (5240-wide payloads): raw.pixls.us ids 6343 (OM-5), 8549 (OM-5 Mark II), and the 5240-wide E-M1MarkII files, all CC0.
7. **V2 classification:** which compressed manifest files belong to V2, or to some further variant, is not settled (their `variant` stays `unassigned`). To test: define a signature (payload width, bits per pixel, escape behaviour) in a `tools/` script, run it over all CC0 manifest files, and report which files it separates and how strongly.

## Hypotheses (unverified, not evidence)

- **H1: one shared decompression scheme across most compressed ORF bodies**, with per-model differences limited to dimensions, crop, levels, white balance and colour. Source: a general AI-assistant summary of unknown provenance, so it carries no weight here. Our own measurements so far show at least two bitstream behaviours (V1 and V2 in VARIANTS.md). To test: classify every manifest file and see whether V2 reduces to V1 under some parameter.
- **H2: High Res Shot files need separate handling.** Source: vendor documentation that the mode exists. To test: measure their signature.
