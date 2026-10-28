# Patent source notes

Reviewed 2026-10-21. Builds on [lead #196](https://github.com/radialmonster/orf-cleanroom/issues/196).
These are primary method references, not findings that any patent is implemented
in ORF. Descriptions below are paraphrases of publication text, including machine
English translations; relevance assessments are research judgments. No images,
patent drawings or decoder implementations were used in this review.
The user supplied the patent identifiers; this review consulted primary patent
publications only. The user's earlier discovery process was not audited.

## Olympus sources

### US7259698B2: bounded-prefix codes and control markers

[Publication text](https://patents.google.com/patent/US7259698B2/en), read 2026-10-28; original assignee Olympus Imaging and inventor Takashi Ishikawa are as listed in the publication record. The described encoder uses a capped zero prefix and a second encoding for larger upper-part values; it retains a fixed-width lower part. In its stated example, D=15, k=5 and max_prefix=12. This is a conditional example, not an ORF specification.

The first embodiment describes 48 zero bits as a control marker, with preceding packing to a byte boundary. The second describes a 48-bit marker of 47 zero bits followed by one, followed by encoded data; it also describes packing before an inserted marker. Its general second-embodiment expression makes the zero-run length `8 * floor((max_prefix + 2*D)/8) + 7`. With the patent's D=15 and max_prefix=12 this gives 47; with the hypothetical D=12 and max_prefix=12 it gives 39. The latter parameter choice is an arithmetic illustration, not a parameter assignment stated for an ORF file.

The independently reported 87-file initial-token census in `2026-10-21--radialmonster--four-payloads-start-q47` found 39 initial zero bits followed by one on 83 files and 47 followed by one on four. These literal prefixes coincide with the two illustrated run lengths. The census used a k=5 candidate parse that consumes five suffix bits after the one; the patent's second-embodiment marker itself ends at that one and then the next encoded data begin. Therefore the existing token count does not establish a marker boundary or prove the patent grammar. Initial padding, strip placement and other bitstream explanations remain possible; inventor/assignee and a pattern match do not establish implementation. The patent does not specify that a marker must recur within each payload or fix its insertion schedule.

The observed first-word bits in `2026-10-28--radialmonster--fixed-capped-prefix-first-escape` also give a **post-hoc conditional bound**, without another sample scan. Assume the second-embodiment marker at payload bit zero, fixed k=5 and fixed D. The marker formula permits max-prefix A=10..17 for D=15/47 zeros and A=8..15 for D=12/39 zeros. Under the A=12 test, the observed word begins with twelve zeros followed by the D-bit value v. For another A, if A<12 then the candidate D-bit value is `v >> (12-A)`; if A>=12 and the extra A-12 observed bits are zero, its range is `v << (A-12)` through `(v << (A-12)) + 2**(A-12)-1`, since trailing bits beyond the measured word are unknown. The escape branch requires a value of at least `32*A`.

| D | Observed v | Files | Conditional result among marker-compatible A |
|---:|---:|---|---|
| 15 | 0 | 7267, 7269, 7801 | All A=10..17 impossible under this fixed single-block assumption. |
| 15 | 256 | 7803 | A=10..12 impossible; A=13..17 not ruled out by these bits. |
| 12 | 33 | 1995 | All A=8..15 impossible under this fixed single-block assumption. |
| 12 | 65 | 1993, 1997 | A=8..14 impossible; A=15 gives the possible interval 520..527. |
| 12 | 0 | 1998 | All A=8..15 impossible under this fixed single-block assumption. |

These bounds retain every completion of the unknown trailing bits; a permitted range is not evidence that the corresponding parameter occurs. They do not address different marker alignment, D, k, interior controls or adaptation, and do not assign decoded values or establish a camera codec. The D=12 choice and this range analysis follow already observed data, so neither is blind confirmation.

A useful next test would first freeze exact candidate parameters, initial alignment, escape branch, and expected marker scheduling from a stated source or independent metadata; preserve initial and interior marker candidates separately, use matched null controls and held-out captures, and report mismatches and undefined cases. Searching for a preferred long zero run or shifting the parse after seeing these known prefixes would not independently establish framing. No sample was newly measured in this source review.

### US7715639B2: prediction-error filtering and adaptive k

[Publication text](https://patents.google.com/patent/US7715639B2/en), read 2026-10-28. The described example separates the least significant bit of a prediction error before a recurrence, then uses the corrected error and flatness state to determine a Golomb-Rice parameter. These are public patent methods, not established ORF syntax.

For signed integer error `P` and previous correction `Cprev`, formulas 10, 11, 13 and 14 specify `P_even = 2*floor(P/2)`, low bit `L = P-P_even`, `C = floor(P_even/2)+floor(Cprev/2)` and corrected error `E = P_even-C`. Formulas 17 and 19 recover `P_even = 2*(E+floor(Cprev/2))` and `P = P_even+L`; the example initializes the preceding correction to zero. Mathematical floor matters for negative inputs. The stated absolute-value treatment also carries sign information separately, although an alternate folded mapping is described.

For example, starting with previous correction zero, errors `(-3,-1,0,1,3)` give corrected errors `(-2,0,1,1,2)`, low bits `(1,1,0,1,1)` and correction states `(-2,-2,-1,-1,0)`; the specified inverse restores the input sequence. Losing the low bit makes the inversion ambiguous: at previous correction zero, errors 0 and 1 have the same corrected error. This is an algebraic property of the cited formulas, not a measured image result.

The described example also derives k from the preceding absolute corrected error and two run-length thresholds, resetting the runs at line boundaries. The publication discusses sign and low-bit data separately from the Golomb-Rice magnitude; the reviewed passages do not establish their ORF byte/bit placement, an ORF initial k, or physical line boundaries. The source offers alternative predictors and mappings. A reproducible ORF hypothesis would need independently justified side-stream placement, startup and row/reset behavior and held-out controls; it must not splice this publication to US7259698B2 merely because both use Golomb-Rice terminology. No sample was newly measured in this source review.

### JP2008312193A: RAW analysis feeding JPEG parameters

[Publication text](https://patents.google.com/patent/JP2008312193A/en).
The record identifies Takashi Ishikawa, Olympus Imaging, priority 2007-05-16,
application JP2008049599A. The previously examined
[JP4869149B2](https://patents.google.com/patent/JP4869149B2/en) has the same
recorded inventor and priority date but application JP2007130261A: these are
distinct applications.
These application numbers and dates are from the Google Patents records and
were not separately checked against J-PlatPat.

RAW steps S21/S23/S25 describe adjacent-pixel differences, frequency counts and
Huffman-based variable-length coding. Later steps S51/S53 select between two
Huffman tables using entropy. Those selected tables go to the JPEG
processor at S37 and encode quantized DCT coefficients at S71/S73. They must not
be assumed to apply to the RAW Figure 8 table discussed in #196.

The reviewed text supplies no complete RAW signed-residual mapping, codeword
table, traversal/reset or escape syntax. This is useful architectural context,
not a newly specified ORF parser.

### JP2006340045A: parallel JPEG processing

[Publication text](https://patents.google.com/patent/JP2006340045A/en).
Olympus; Example 1 and claim 5 describe first and second JPEG processors,
code-amount estimation, predicted quantization and parallel operation. Example 2
describes DCT, quantization and variable-length stages. These passages concern
throughput and JPEG size control; they do not specify a Bayer residual grammar.

### JP3085465B2: transform coding and code budgets

[Publication text](https://patents.google.com/patent/JP3085465B2/en).
Olympus Optical. The second embodiment, circuits 214/216/218/220/222, describes
cosine transformation, quantization, previous-block DC differences and Huffman
coding of DC and AC zero-run/coefficient pairs. The first embodiment discusses
budget-triggered termination and end-of-block coding. These are transform-domain,
rate-controlled mechanisms, not a complete lossless sensor-sample syntax.

### JP3012698B2: block allocation and AC truncation

[Publication text](https://patents.google.com/patent/JP3012698B2/en).
Olympus Corp and Olympus Optical Co Ltd (original assignees as listed).
Paragraphs [0103]-[0107] describe Y/Cr/Cb blocks,
transform/quantization, AC bit budgets, DC differences and zigzag AC coding.
[0108]-[0109] truncate AC to a budget and emit an end-of-block code; [0114]
stores quantization parameters. These passages describe lossy rate control,
not an ORF residual specification.

## Adjacent references: reviewed text

- [JP4682102B2](https://patents.google.com/patent/JP4682102B2/en), Canon:
  second-embodiment steps S201-S206 use RAW compression ratio to select later
  JPEG quantization/Huffman tables. Useful pipeline context, not Olympus symbols.
- [JP2009165141A](https://patents.google.com/patent/JP2009165141A/en), Qualcomm:
  the description around steps 620/624/628 gives a unary quotient and an m-bit
  remainder; steps 636/640/644 discuss positive-even/negative-odd folding.
  Claims 1/4 concern slice DC differences and Golomb-Rice coding. This is a
  generic transform-domain algorithm reference; steps 604/608 describe zero
  runs, and step 612 selects the coding parameter from run length.
  Equations rendered as images were not
  inspected; this review does not certify an exact formula or update rule.
- [JP2006067117A](https://patents.google.com/patent/JP2006067117A/en), Canon:
  its abstract concerns target-size encoding with lossy/lossless paths and
  re-encoding. JP4869149B2 lists
  [JP4533043B2](https://patents.google.com/patent/JP4533043B2/en), the grant
  corresponding to this A publication, in its family citations. No direct
  citation of the A publication was verified.

## Sources only triaged or not reviewed

- [JP4359773B2](https://patents.google.com/patent/JP4359773B2/en), Sony:
  opening text concerns JPEG/MPEG, DCT/quantization and target size.
  Detailed coding relevance remains to be reviewed.
- [JPH07322252A](https://patents.google.com/patent/JPH07322252A/en):
  user-supplied identifier. Direct Japanese publication text remains unavailable
  in this review; do not treat its claims or detailed algorithm as established.
  The public [EP0684738A2 publication](https://patents.google.com/patent/EP0684738A2/en)
  lists JP13262294A / JPH07322252A under a 1994-05-23 priority and Canon as
  original assignee. The reviewed EP text describes block image encoding with
  an orthogonal transform, masked transform coefficients and encoding of the
  masked blocks; claim 11 specifies a discrete cosine transform. It is a related
  priority publication, not a transcription or proof that each Japanese claim
  or passage is identical. These record links have not been separately checked
  against J-PlatPat or Espacenet. The EP text does not establish a lossless
  sensor-residual grammar or use in ORF; no patent drawings were inspected.

## Remaining research question

None of the reviewed Olympus passages provides a new complete lossless RAW bit
grammar. The actual residual/magnitude/sign mapping, framing, traversal and
escape rules remain open in #196 and the variant specs. Shared inventors,
similar components or matching statistics do not establish implementation.
Resemblance to generic Rice or signed-folding schemes is not evidence for ORF.

Before proposing another patent-based parser, identify the exact text-defined
rule, distinguish unspecified choices, and declare an experiment that can
falsify it on ORF files. Any resulting implementation claim needs independent
file measurements under RULES.md; this source review is not a verified finding.
