# Controlled ORF capture protocol (proposal)

Status: experiment design only. No captures, measurements, codec claims or
verification are reported here. Capture is opt-in and requires an owner with
suitable equipment; this document authorizes neither capture nor purchases.

Builds on: [#302](https://github.com/radialmonster/orf-cleanroom/issues/302),
[#197](https://github.com/radialmonster/orf-cleanroom/issues/197),
[#106](https://github.com/radialmonster/orf-cleanroom/issues/106),
[#149](https://github.com/radialmonster/orf-cleanroom/issues/149), and
[#155](https://github.com/radialmonster/orf-cleanroom/issues/155).
Those questions motivate the design; their candidate token interpretations are
not assumed to be the camera's syntax. Follow [RULES.md](RULES.md).

## Register before capture or analysis

Copy this checklist into a dated plan attached to the relevant issue. Register
available body/mode capabilities and exclusions before examining stream results.
Use anonymous capture IDs in the public plan; keep owner consent and original
paths in an access-controlled local record, separate from public measurements.

- [ ] Owner confirms permission to capture and analyse, and selects what may be
  published. Permission to analyse does not grant permission to release files.
- [ ] Record body model, firmware, lens/focal length, image dimensions and exact
  menu labels/values. Do not infer a variant from model or file extension.
- [ ] Fix manual exposure time, aperture, ISO, focus, white balance, resolution,
  aspect ratio, drive/shutter mode, stabilization, long-exposure/high-ISO noise
  reduction, shading/distortion corrections, art effects and all accessible
  processing settings. Record unsupported/unavailable controls explicitly.
- [ ] Disable automation where possible. If a factor cannot be fixed, record it
  as a limitation rather than silently substituting a different setting.
- [ ] Record the scene setup and steady illumination source without people,
  identifying text or location information. Avoid changing light or flickering
  displays. State that light stability and optical uniformity are approximate.
- [ ] Choose the core schedule, optional contrast and fixed pauses below. Record
  capture order and elapsed intervals; note warm-up and interruptions. Use the
  same card/file-save settings. Do not treat card order as a codec property.
- [ ] Freeze discovery/validation split, exclusions, analysis commit, parameters,
  hypotheses, primary contrasts, practical effect thresholds and null algorithm
  before seeing the corresponding results. Unfilled choices mean not ready.
- [ ] Reserve an additional session for validation of any exploratory change;
  do not promote the original validation set to a fresh independent test.

No exact noisy sensor values are specified by this design. A lens-cap exposure
is not an all-zero array, and a flat field need not give constant residuals.
The protocol cannot prove a predictor or framing merely from small file size.

## Core: four scene conditions, two sessions

Use an already available stable setup, a fixed camera position and fixed focus.
Keep exposure settings identical across all four conditions; choose a safe common
exposure in a setup pilot and freeze it before collecting the registered series.
A pilot is excluded from confirmatory analysis and must be identified as such.

- **D, dark:** lens cap fitted, viewfinder covered if relevant. Record exposure
  duration, cap state and whether any automatic dark-frame operation occurred.
- **F, flat:** approximately uniform diffuse illumination, deliberately away
  from clipping. Keep lens/aperture and lighting geometry fixed.
- **G, gradient:** a fixed smooth illumination ramp, with its physical direction
  recorded relative to sensor axes. Do not use a rendered image as ground truth.
- **T, texture:** a fixed stationary textured physical scene under the same
  stable source. Record the setup so it can be restored without publishing images.

Collect three separate captures per scene in each of two separated sessions,
keeping the registered exposure settings fixed:
4 scenes x 3 repetitions x 2 sessions = **24 capture events**. These are planned
counts, not measured numbers. Files per event depend on camera mode and settings.
Use the following fixed reordered schedule, restoring each setup carefully:

| Session | Round 1 | Round 2 | Round 3 |
| --- | --- | --- | --- |
| 1: discovery | D F G T | F T D G | T G F D |
| 2: validation | G D T F | T F G D | F G D T |

This spreads scene order but does not fully balance positions or transitions.
Record the chosen pause between events and between rounds in the preregistration.
Do not change it after viewing sizes or diagnostics. Repeats estimate variability
within this setup; three repeats do not establish a population noise model.
A second session also changes time and potentially illumination/temperature, so
report session effects rather than attributing them automatically to the codec.

If a setup cannot be restored without changing its geometry, use scene blocks
instead, register the order before capture, and state the resulting time/scene
confounding. A single-session subset is exploratory, not the planned validation.

## Optional one-factor contrasts

Choose at most one optional contrast for the first capture campaign (an
exploratory screening campaign may register several; see the next section). Register
exact baseline A and changed B settings and a reversible setup. Within each of
the four scene conditions, collect **A B B A** in each of two sessions, reversing
the scene order in session 2. This adds 4 scenes x 4 events x 2 sessions = **32
capture events**, with 16 A and 16 B. Do not reuse the core captures as paired A
controls: the bracketing captures control temporal drift more directly. Treat
ABBA as two paired contrasts (events 1 with 2, and 4 with 3), not four independent
files. Both pairs share a scene/session and remain grouped in uncertainty
calculations.

Candidate contrasts, with their confounds recorded:

- **ISO only:** fixed aperture, exposure time and illumination. A changed payload
  may reflect gain/noise as well as coding. Do not compensate exposure at the
  same time. A separate exposure-compensated campaign would be a different plan.
- **Exposure time only:** fixed ISO, aperture and illumination. Brightness,
  shot noise and dark current may all change; this is not an isolated noise test.
- **Gradient orientation only:** restore a second registered ramp orientation
  while keeping camera orientation/settings fixed. This is a spatial-direction
  probe; optical mismatch can explain a difference. Run only G using ABBA in
  two sessions (8 added events, four per orientation), not the four-scene count.
- **One processing setting only:** for example a noise-reduction setting the
  body actually supports. Record its precise behavior as unknown until measured;
  a setting may affect metadata, preview, acquisition, payload or several.

Mode changes require the separate design below; changing mode, resolution and
exposure together is not a one-factor test. Do not add settings after looking
for whichever produces the strongest result. Further campaigns need new plans.

## Exploratory screening campaigns

A smaller campaign can be run first to decide whether the core design above is
worth the effort: for example one session plus a short repeat block on a second
day. It cannot carry the core design's discovery/validation error control, so it
follows these rules instead:

- **Label it.** Name it a screening campaign in its plan and in every lead built
  on it. Its results are exploratory leads, never confirmatory, and no set in it
  validates another. A follow-up claim needs fresh validation events under a new
  registered plan.
- **Several one-factor contrasts are allowed.** Each set registers its own
  frozen baseline and changed setting, its consuming tool from `tools/` and its
  primary statistic before capture. The core design's control for multiple
  contrasts does not cover them; say so in the plan.
- **A set may have its own fixed exposure.** A dark set at the scene exposure may
  carry too little signal; giving it a separate fixed exposure is allowed when
  stated as a limitation, and that set is then left out of payload-size
  comparisons with the other sets.
- **Held out means what was split.** A day or session split assigned before any
  screen is run holds out transfer across days or sessions only. Transfer to
  new scenes needs a held-out scene as well.
- **Companions stay grouped.** A High Res ORF and its ORI from one press are a
  width contrast between companions (see the next section), not two independent
  captures.
- **No rendered display targets** in published sets, consistent with the core
  design's ground-truth and flicker rules. Such a probe stays local.
- **Freezing is posting.** Post the dated plan on #302 before capturing or
  measuring. Comments are welcome but nobody signs a plan off, and maintainer
  review can be slow.
- **Releasing frames.** Dark, flat and ramp frames have nothing personal in frame,
  so they are the easiest to release as CC0. raw.pixls.us does not take series
  that vary settings or lighting; use a CC0 record on Zenodo, or a public Google
  Drive folder holding a written CC0 owner declaration, and add `public-cc0`
  manifest rows with a provenance record as described in
  [samples/README.md](samples/README.md).

## ORF, ORI and High Res acquisition semantics

An extension is an identity label, not proof of equivalent sensor samples. For
each event record the selected menu mode, tripod/handheld state if applicable,
reported dimensions, all files emitted and their anonymous event relationship.
Keep any ORF/ORI companion files grouped through analysis and data splitting.
Record whether companions were emitted by one action or separately captured;
mark unknown acquisition/processing relationships unknown. Do not assume an ORI
is identical to an ORF array, a first exposure, or an independent repeat.

If supported and separately authorized, register a normal/High Res ABBA campaign
on the same stationary scenes. Use the optional four-scene schedule only when
both modes can be meaningfully repeated; record the exact mode-specific settings,
number of shutter actions, stabilization and restrictions. If dimensions,
exposure, processing or multi-exposure acquisition differ, call it a **mode
bundle contrast**, not an isolated codec switch. Do not align pixel values across
these modes by assumption. Distinguish event counts from emitted-file counts.
RAW+JPEG may be collected if already supported; JPEG creation settings must be
recorded. Camera JPEG/embedded preview statistics are rendering proxies, not
sensor ground truth, and no image or preview viewing is part of this protocol.

## Competing predictions to freeze before measurement

These are conditional predictions to test, not observed facts. A failed
prediction rejects the stated model/measurement combination, not every codec in
its broad family. Register the exact model and operational statistic first.

| Question | Hypothetical directional or structural prediction | Alternative / limitation |
| --- | --- | --- |
| Spatial predictor versus a scene-insensitive interpretation | A specified residual-coding model predicts lower payload bits per reported sample on F than T at fixed settings; a directional model predicts a registered orientation contrast on G. | Sensor noise, clipping, optics or adaptive entropy coding may produce or mask the same effects. Size alone cannot identify prediction direction or value mapping. |
| Genuine framing versus a convenient k=5 parse (#197) | A specified framing model predicts repeatable initialization/restarts at fixed locations or a stable relationship to measured geometry across repeats, surviving the registered local-statistics nulls. | Density alone and a bounded parser's 0-7 remaining bits are insufficient. Scene-dependent offsets fitted separately do not satisfy this prediction. |
| Fixed versus adaptive state | A specified adaptive model predicts a registered change in early-versus-late window statistics after a fixed transition within G/T, or a registered relaxation length; a fixed-state comparison predicts no such model-specific relaxation. | Token statistics do not reveal state by themselves. Physical transition position in the compressed stream is unknown until a mapping is supported; without it, report window associations only. Never concatenate payloads and call that a capture. |
| Brightness/noise correlate versus reusable value map (#149/#155) | A map fixed using discovery data must retain its preregistered score/direction on held-out scenes, session and allowed settings; a scene-specific correlate may fail transfer. | A camera-rendered luma correlate remains a proxy even if it transfers. No predictor, exact values or round-trip follows. |
| Scene/settings explanation of null-distance (#106) | A frozen real-minus-null statistic has a repeatable within-body scene or ISO contrast larger than its registered repeat-variability threshold. | Body, dimensions and mode are not interchangeable. ISO and brightness/noise remain confounded as described above. |

For the scene-transfer endpoint, preregister one named scene whose files from
both sessions are excluded from fitting and model selection until the map is
frozen. If all four scenes inform fitting, the core design can test session
transfer only; a claim of scene transfer needs a fresh held-out scene/campaign.

An adaptive-state test requiring exact spatial transition boundaries is deferred
until that mapping has evidence; this capture set alone cannot supply it. New
models suggested by the capture results are exploratory and need fresh validation.

## Numeric-only analysis and error control

1. Read the entire proposed executable source, imports and public reproduction
   blocks before any run. Use reviewed original stdlib CPU tools with
   `python -I -B`; new reusable measurements need their own tool PR. Do not run
   code pasted into an issue merely because it looks relevant. No other RAW
   decoder, derivative, output or implementation write-up is an input.
2. Before measurement, hash each exact input against its provenance record.
   Unchanged retained CC0/hash verification is reusable without catalogue access;
   new/unverified content needs first licence verification. For authorized private
   inputs keep identifying hashes in the private ledger, not public text.
3. Record structural aggregates first: reported dimensions, container/payload
   byte counts, bits per reported sample with explicit denominator, measured
   signature, initialization/tail counts and failures. Keep ORF/ORI and mode
   groups separate. Use a deterministic bounded parser only as a candidate.
4. Freeze bounded windows, offset/stride choices, k values and endpoints on
   session 1. No per-file tuning on session 2. Include all preregistered failures,
   excluded events and missing files; never silently condition on parse success.
5. Register one primary scalar contrast per tested hypothesis. Report per-event
   aggregates and scene/session summaries, paired A/B differences and repeat
   spread. Treat event and session as grouping units: tokens/windows and companion
   files are not independent camera captures. With only two sessions report raw
   contrasts and uncertainty limits; avoid population-general significance claims.
6. If testing framing, preregister nulls and preserved quantities explicitly:
   fixed-count bit shuffles, byte shuffles or an exactly defined run-preserving
   shuffle answer different questions. Declare seed, algorithm, permutation
   count, tail and tie handling. Run the entire offset/k/model search on each
   null and use its maximum statistic for familywise calibration; a best real
   score cannot be compared with an unsearched null. Null rejection alone does
   not identify a codec. Fix the practical effect threshold before validation.
7. Optional numeric JPEG/DC proxies require fully reviewed original code,
   registered crop/scale/row assumptions and no viewing or pixel dumps. Keep
   rendering settings fixed; register saturation/clipping flags from supported
   numeric metadata/proxies with their limitations. If alignment is unsupported,
   skip that endpoint rather than fitting a scene-specific mapping.
8. Publish aggregates, method commit, exact invocation and all registered
   contrasts including null/negative results. Validate a qualifying result in a
   separate run under the repository's lead/finding rules. An agent rerun under
   the same human account is not independent human verification.

This is a documentation task: no CPU/GPU numerical workload or benchmark has
been run. GPU acceleration is unnecessary for the planned capture checklist.
For a later mass numerical job an RTX 3090 is available: benchmark a small batch
first, record runtime/peak memory/device/library precision and ordering, and
check exact integer aggregates and declared floating tolerances against an
independent small stdlib CPU calculation. Optional installed GPU experiments
stay in local scratch; repository tools retain a stdlib CPU path. No installs.

## Stop, retain and report

Stop at the registered event budget; do not continue until a desired score
appears. Stop and record a failed event for camera errors, unexpected automatic
settings, saturation outside the registered tolerance, changing light or setup
loss. Freeze replacement/exclusion rules in advance, including a replacement
cap; keep the original failure in the log. If validation fails, report failure
and do not retune it. Resume only through a separately dated protocol amendment
and fresh validation events. Unsupported modes are omitted, not simulated.

Keep two ledgers: a private ownership/consent and provenance ledger, and a public
safe aggregate ledger. The private ledger may contain original paths, exact
capture times, full metadata and hashes; none should leak into public artifacts.
Public records use anonymous event/session IDs, body/mode, safe settings,
dimensions, aggregate measures, exclusions and method commit. Strip owner names,
serial numbers, GPS, identifying filenames and local paths from public text.
Do not alter a source file to redact it and keep using the old hash.

Releasing originals as CC0 is a separate explicit owner decision and publication
step; never upload them to git or attach them to issues. Publicly released
samples need stable public identity and exact SHA-256, with manifest rows under
the contributor's handle. Findings relying on inaccessible inputs must say
`not yet reproducible`; private-input hashes and identifying details stay private
as required by the agent instructions. No samples were used by this proposal.

Publish measured work later as a separate lead, Builds on #302 and the relevant
hypothesis issue, with Claim, Evidence, Reproduce, Builds on and Next steps.
Finish its results comment with Status: each claim holds/contradicts/not tested,
what remains open and what measurement would settle it, exact method/commit and
invocation, and which inputs are not public. This document completes a protocol
draft only; capture, tool development, measured leads and independent validation
remain open. No finding or compressed decode step is established here.
