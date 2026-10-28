# tools

**`escape_matched_control_probe.py`** compares q=0 counts in 24 candidate
words after q>=17 anchors at skips 0 and 12 bits, against the nearest earlier
q=0 anchor with the same suffix whose two horizons end before that escape.
All horizons stop at the requested complete-token prefix endpoint. Output
retains individual counts, unmatched and incomplete cases, and control reuse.
This descriptive comparison does not establish escape syntax or independent
physical alignment; matching the suffix does not match neighboring context.
Verify public provenance and the sample hash before use.

    python -I -B tools/escape_matched_control_probe.py --sample PUBLIC_NAME SHA256 FILE --tokens 262144
    python -I -B tools/test_escape_matched_control_probe.py

**`token_position_control_probe.py`** compares 24-token windows at nominal
positions zero, floor(W/4), floor(W/2) and floor(3W/4), each against its own
row complement. Rows are W candidate tokens from token zero; W is the payload
width, not an established physical stride. q>=17 tokens are omitted without
index compaction. Per-row q and unsigned-suffix contrasts are equally weighted
only where both windows and complements are nonempty; the main comparison
uses the common valid-row intersection across all four offsets. Undefined
rows, ties, prefix shortfalls, tail tokens and escape counts are retained.
This fixed control is descriptive, not a calibrated null or the historical
unspecified statistic in #29. Verify retained public provenance and hashes.

    python -I -B tools/token_position_control_probe.py --sample PUBLIC_NAME SHA256 FILE --tokens 262144
    python -I -B tools/test_token_position_control_probe.py

**`rice_fixed_ones_count_tail.py`** computes an exact synthetic upper tail for
the number of complete stop-1 Rice words in a uniformly ordered N-bit stream
with exactly K ones, including ones in suffix bits. It supports N up to 4096,
k from 0 through 8 and nonnegative target counts. Its hypergeometric draws
represent an adaptive reveal of unary bits, not a literal bitstream prefix.
The assumed uniform fixed-ones ordering is not established for camera data;
this is a null-model control, not a camera significance test. It extends the
small exact joint count/residual model with a count-only tail at larger N.

    python -I -B tools/rice_fixed_ones_count_tail.py --bits 4 --k 1 --ones 2 --count 2
    python -I -B tools/test_rice_fixed_ones_count_tail.py

**`rice_iid_count_moments.py`** extends the small exact synthetic joint null
with floating-point mean and central variance of the number of completed
stop-1 Rice words for an externally supplied iid stop probability. Binary
block composition uses k+1 states and normalizes each probability row after
composition; zero-weight paths are excluded and variances are not clipped.
N is at most 1,000,000,000, k is 0 through 8, and the rational probability's
denominator is at most 1000. Selected small exact and large high-precision
checks do not establish a uniform numerical error bound. This is not a joint
distribution, a camera significance test, or a calibrated test using p fitted
from the same data.

    python -I -B tools/rice_iid_count_moments.py --bits 1000000 --k 5 --stop-probability 1/3
    python -I -B tools/test_rice_iid_count_moments.py

**`prefix_whole_null_probe.py`** compares #106's fixed 1,500,000-token
candidate prefix with a complete bounded parse of the same payload. It uses
stop 1, five suffix bits, no extra escape skip, q capped at 8 and pair-centered
integer lag moments. Density counts only complete bytes before each endpoint;
the prefix projection uses the full payload length as in #594. Null projections
are undefined at density 0 or 1, matching the historical CLI. A prefix shortfall,
partial final word or zero variance remains explicit. These are descriptive
candidate-token projections, not a codec, physical row, pixel or ISO-cause test.
Verify retained CC0 identity and manifest before each hash-checked snapshot.

    python -I -B tools/prefix_whole_null_probe.py --sample PUBLIC_NAME SHA256 FILE
    python -I -B tools/test_prefix_whole_null_probe.py


**`rice_finite_count_null.py`** extends the finite terminal-residual model of
#87 with a joint completed-word-count and residual-length distribution for a
synthetic iid bit stream. It uses exact rational arithmetic for fixed N up to
32 bits, k from 0 through 8 and an externally specified rational stop-bit
probability with denominator at most 1000. The distribution includes truncated
words and p=0/1. These small limits do not scale to a whole frame. Estimating p
from the same data changes the null calibration; the output is not a camera
significance test, framing identification or physical-row claim.

    python -I -B tools/rice_finite_count_null.py --bits 16 --k 5 --stop-probability 1/2
    python -I -B tools/test_rice_finite_count_null.py

The separate `--ones K` option counts all N bits (including suffixes) and
computes the exact joint integer counts under uniform order conditioned on K.
This is a different null from iid bits using p=K/N; uniform ordering is an
assumption and is not established for camera streams.

    python -I -B tools/rice_finite_count_null.py --bits 4 --k 1 --ones 2


**`synthetic_phase_exact_null.py`** illustrates the nested phase-change
control in #296 on eight synthetic bits containing four ones. It fits fixed
period-two phase and a phase change at the midpoint on the same observations,
then refits both on all 70 distinct orderings. The exact upper-tail rank includes
ties and the observed ordering; superuniformity assumes the stated uniform
conditional orbit. Positive fitted gain can occur under that null. This toy is
not a held-out prediction or a claim about camera data or exchangeability.

    python -I -B tools/synthetic_phase_exact_null.py --observed 10100101
    python -I -B tools/test_synthetic_phase_exact_null.py


**`token_phase_rotation_control.py`** supports #144, building on #508. It
refits joint period/phase and fixed-period phase for the observed sequence and
each conditional block rotation, then compares their exact common-interval
head-minus-rest contrasts. Sixteen references rotate independent 5240-token
blocks and the partial blocks separately in training and test, using the stated
seed and rejection draws. Results are descriptive: block seams, partial blocks,
the fixed partition, and prior exposure limit interpretation; no calibrated
significance, physical row, codec or population claim follows. Hash-match the
input to its retained verified CC0 record. Aggregate JSON only.

    python -I -B tools/token_phase_rotation_control.py --sample ID PUBLIC_NAME VERIFIED_SHA256 FILE
    python -I -B tools/test_token_phase_rotation_control.py

**`e400_boundary_probe.py`** tests the previously excluded boundary words in
lead #79. Every nonzero-low4 word within two pixels of any stored-raster edge
is tested with axial-2/diagonal-1 families, available-neighbour renormalization,
coordinate clamp, and reflection without edge repetition. Remapped duplicates
remain separate terms. Exact residual numerator ranges and denominator counts,
and floor/ceiling/nearest-half-up matches are emitted by low nibble. Clamp may
change CFA parity; none of these arithmetic candidates identifies camera policy.
No row-layout detection, fit, sensor ground truth, images or decoder change. Verified CC0
SHA-256 is checked before parsing; failures are sanitized. Stdlib only.

    python -I -B tools/e400_boundary_probe.py FILE --sha256 VERIFIED_SHA256
    python -I -B tools/test_e400_boundary_probe.py

Analysis scripts, all original code (see RULES.md).

**`synthetic_resync_classify.py`** supports research plan #300 with frozen
nearest-centroid source-generator classification on disjoint synthetic LCG
seeds. Recovery indicators, censored distances and length/density are separate
feature ablations. Real and exact-length/popcount-preserving bit-shuffle
training/evaluation groups are crossed; complete confusion matrices and exact
rational scores retain every held-out trial. Shuffle labels refer to source
generators, not shuffle codec identity. Length/density can retain perfect
source-label classification without any coding structure. No camera files,
significance, generator identification in general or finding is asserted.
CPU stdlib only, aggregates only; no input files or image data.

    python -I -B tools/synthetic_resync_classify.py --self-test
    python -I -B tools/synthetic_resync_classify.py

Each script should:
- take raw.pixls.us file paths as arguments and not download anything itself (`pixls_samples.py` is the one exception);
- print or write aggregate statistics only, with no images or pixel dumps;
- run on CPU, with GPU acceleration optional;
- state at the top which finding (an ID from `findings/`), lead issue (`#n`) or spec Gap (`specs/V<n>.md`) it supports.

**`suffix_window_probe.py`** supports lead #11's remaining local-extent question.
Four consecutive 262144-candidate-token windows report all H/L pair tables and
plug-in MI at lags 1..3, with endpoint escape omissions preserving indices.
Pairs stay inside windows; intervening escapes remain. Every cell and the
strict alternating-order criterion are reported, including null/short windows.
These descriptive token-index windows are not physical rows, a stationarity
test, historical reproduction or decoder. Unknown framing remains unresolved.
Reuse retained CC0 provenance after verifying the exact input hash.

    python -I -B tools/suffix_window_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_suffix_window_probe.py

## Example tools

**`token_donor_comb_probe.py`** supports the remaining donor-comb question in
lead #30, building on #11. First 262144 complete candidate tokens, payload
bit zero, no extra escape skip. Count b2(t-lag) by b2(t) for every lag
2W-2, 2W, 2W+2, separately for all four nominal target row/column parity
classes. W is payload width, not established token row length. Omit pairs
with q>=17 at either endpoint without compacting indices; intervening
escapes remain. Emit every 2x2 table, pair/omission count and binary Pearson.
Short prefixes and input errors fail the CLI while retaining available
reports. This is a descriptive nominal lattice, not physical rows,
serpentine inference, significance or reproduction of the unspecified
historical donor metric. Reuse retained CC0 records after local hash checks.

    python -I -B tools/token_donor_comb_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_donor_comb_probe.py

**`token_framing_probe.py`** is the corrected null comparison for lead #197,
building on the superseded probe in #198. Bernoulli bits use the measured ones
fraction as their success probability; density is preserved in expectation.
Byte shuffling preserves the exact byte histogram. Separate zero/one run-length
shuffles retain alternating values and exact per-value maximal-run multisets.
Output is aggregate JSON with exact counts, all input outcomes and a completion
flag; any failed input exits nonzero. Short residuals and null separation do not
establish true codec boundaries. Reuse retained CC0 records after local hash checks.

    python -I -B tools/token_framing_probe.py --sample ID PUBLIC_NAME path/to/file.ORF --bytes 131072 --seed 20261021
    python -I -B tools/test_token_framing_probe.py

Optional `--markov` adds a first-order binary Markov null fitted to adjacent-bit
counts of that same prefix, without wraparound or pseudocounts. The initial bit
uses its measured ones fraction; each following bit uses the fitted conditional
probability given the previous generated bit. An unobserved outgoing state falls
back to the measured ones fraction. Exact fit counts and fitted probability
estimates are reported.
This fitted probabilistic control does not exactly preserve finite density,
transitions or run histograms, or establish input stationarity or calibrated significance.
The default four-model report is unchanged.

    python -I -B tools/token_framing_probe.py --markov --sample ID PUBLIC_NAME path/to/file.ORF --bytes 131072 --seed 20261021

Optional `--local-byte-block 256` adds byte shuffling separately inside
consecutive fixed-size prefix blocks, including any short final block. A fresh
seeded generator is consumed in block order. Each block's exact byte histogram
and density are preserved, while within-block order, bit adjacency and maximal
runs are not. Output includes block size, complete-block count and tail bytes.
The default report is unchanged. These diagnostic blocks are not physical rows;
the assumed local permutation model does not calibrate significance or identify
camera framing. It can be combined with `--markov`.

    python -I -B tools/token_framing_probe.py --local-byte-block 256 --sample ID PUBLIC_NAME path/to/file.ORF --bytes 131072 --seed 20261021

Optional `--offset-bytes 1048576` selects an exact-length window of the
logical strip payload. The candidate parser restarts at that window's bit zero;
all null parameters and local-byte blocks use only that window. Reports retain
requested/actual length and absolute payload byte/bit anchors. A requested
window beyond the payload fails before statistics, including a short default
prefix. The old `prefix_bytes` and `requested_prefix_bytes` fields remain length
aliases for compatibility; `window` gives their offset context. Complete
zero-offset model statistics remain unchanged. These newly anchored parses are
not known whole-stream token boundaries and do not establish framing,
stationarity, significance or a decode. Use fixed offsets before outcomes.

    python -I -B tools/token_framing_probe.py --offset-bytes 1048576 --bytes 131072 --markov --local-byte-block 256 --sample ID PUBLIC_NAME path/to/file.ORF

Optional `--suffix-width-scan` adds every fixed suffix width k=2..8 to each
enabled model, keeping the default k5 reports unchanged. Each real/control byte
window is generated once and reused across widths, so the comparison uses
identical bit intervals rather than different token-block spans. Each candidate
consumes q zero bits, stop 1 and k suffix bits, with no extra escape skip. All
token/q0/ones counts and consumed/residual bits are retained; no complete token
gives a null q0 fraction. This is a descriptive common-window control comparison,
not calibrated significance, an estimator of optimal k or proof of camera
framing. Short residuals remain diagnostics. All enabled widths/models are
reported without selecting a winner; known-profile smoke files are not untouched
validation captures. Existing output is unchanged when the flag is absent.

    python -I -B tools/token_framing_probe.py --suffix-width-scan --markov --local-byte-block 256 --sample ID PUBLIC_NAME path/to/file.ORF --bytes 131072 --seed 20261021

**`token_anchor_sync_probe.py`** supports #197 with a distinct anchor diagnostic.
Restart the candidate q-zero/stop1/five-suffix parser at bits 0..7 of the same
exact byte window. Report every path's counts/q0/endpoints and the earliest
accepted token start common to all eight; only whole tokens count. Final
unaccepted cursors are excluded; no common start is censored and reported null.
Once paths meet their future is identical by determinism, which can also occur
on generated controls. Compare real/Bernoulli/byte/run/Markov/local-byte256 with
fresh seeded generators. Defaults: 131072 bytes, offsets 0/1048576, four seeds
20261021..20261024. Optional repeated offsets/seeds override those defaults.
Windows restart independently and are limited to 1 MiB. All local hashes must
match supplied retained verified CC0 hashes before TIFF parsing. Invalid inputs
and short windows return failure while retaining other aggregate records.
These known-profile descriptive diagnostics do not establish camera boundaries,
physical rows, significance, adaptation, values or a decode. No images or
raw/token arrays are emitted.

    python -I -B tools/token_anchor_sync_probe.py --sample ID PUBLIC_NAME VERIFIED_SHA256 FILE
    python -I -B tools/test_token_anchor_sync_probe.py

**`terminal_residual_null_probe.py`** supports lead #87 with finite iid
Bernoulli residual-length distributions for independently anchored first/last
4096-bit payload windows. It reports the complete PMFs, nonempty all-one
residual probabilities, observed candidate counts and every input failure.
The fair and in-sample fitted baselines are descriptive, not calibrated
significance tests. Tail-window anchors do not reproduce whole-payload
endpoints or decide padding versus a truncated token. Reuse retained CC0
verification after matching the exact local hash.

    python -I -B tools/terminal_residual_null_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_terminal_residual_null_probe.py

Optional `--fixed-density` adds exact counts for a uniform permutation of the
N window bits conditional on their K observed ones. For t complete tokens at
an N-bit boundary, the N-6t unary zeros have `choose(N-5t-1,t-1)` compositions;
the t stops are ones and the 5t suffix slots have `choose(5t,K-t)` assignments.
Summing their products over t counts complete-boundary strings. The empty
boundary contributes one at N=K=0. Nonempty residual count is `choose(N,K)`
minus the boundary count, including arbitrarily long rejected candidates.
Nonempty all-one residuals have length r=1..5, so their count is the sum of
boundary counts at `(N-r,K-r)`. Exact event counts and denominators accompany
floating joint/conditional probabilities; absent nonempty residuals give a
null conditional probability. This uses O(N) binomial evaluations per window
and a constant number of retained big integers, whose sizes grow with N.
Uniform bit-order exchangeability is a hypothetical control, not established
for camera data; conditioning density does not calibrate significance or
identify padding, codec framing or a decoder. Default output is unchanged.

    python -I -B tools/terminal_residual_null_probe.py --fixed-density --sample ID PUBLIC_NAME path/to/file.ORF

Separate opt-in `--fixed-density-lengths` extends the terminal-residual null
probe (#87, Builds on #11/#224/#257) with all N+1 exact residual-length
numerators, their common choose(N,K) denominator, exact normalization and
floating PMF. It includes long rejected candidates, whose first r-5 bits
must be zero. Seven rolling integer coefficient rows avoid retaining a full
N-by-K table. O(N*K) integer operations and O(N+K) retained integers have
costs that grow with integer size; this option is slower than event-only
counts. Tiny floating probabilities can underflow; exact counts remain
available. Default and `--fixed-density` outputs are preserved. The uniform
fixed-density model assumes exchangeable order and remains descriptive:
length-specific probabilities do not establish framing, padding, calibrated
significance or decoding. Reuse retained CC0 verification after matching
local hashes; new content needs its first licence verification.

    python -I -B tools/terminal_residual_null_probe.py --fixed-density-lengths --sample ID PUBLIC_NAME path/to/file.ORF

**`e400_single_pass_probe.py`** supports the remaining exception in #79.
It marks nonzero-low4 words and tests connected same-colour neighbour
components of size one or two, excluding whole components touching a
two-pixel boundary. Equal coordinate parity uses diagonal-1; unequal uses
axial-2. For increasing/decreasing raster orders, each marked word is
replaced once by the floor four-neighbour mean; initial marked words must
be uint16 multiples of 16 and unmarked words are fixed. For a pair it
inverts the earlier equation and replays every admissible later-site
initial word. Reports contain aggregate equations, candidates, replays,
components and exclusions only. Known public values motivated the model.
Compatibility does not establish actual camera order, sensor values or
universal correction rules; zero-low4 mapped sites, edges and larger
components remain untested. Reuse verified CC0 provenance after matching
the local hash; new content needs its first licence verification.

    python -I -B tools/e400_single_pass_probe.py path/to/E400.ORF
    python -I -B tools/test_e400_single_pass_probe.py

**`e400_exception_probe.py`** supports lead #79 and `specs/V0.md` G3.
It scans a licence-checked packed-16 input in TIFF byte order and tests every
nonempty subset of the axial-2 and diagonal-1 neighbour families under floor,
ceiling and nearest-half-up means. Output contains aggregate counts by low
nibble, edge exclusions, and residual tests for words unmatched by either
full-family floor mean. It also tests clearing neighbour low nibbles; no
pixel values, neighbourhood arrays or images are printed. Subset matches
are descriptive and do not establish the camera's processing order.

    python -I -B tools/e400_exception_probe.py path/to/E400.ORF
    python -I -B tools/test_e400_exception_probe.py

**`suffix_match_probe.py`** supports lead #31 with exact suffix-equality counts
against independent within-block permutations that preserve escape positions.
It prints aggregate JSON, with every declared lag and explicit sample failures.
The frozen discovery and validation cohorts are in `tools/cohorts/`; later files
use a separate `replication` cohort with the same design metadata. Local paths
are supplied separately and never appear in output. This bounded descriptive
measure cannot establish or exclude dictionary coding. Synthetic exhaustive
permutation tests run with `python -I tools/suffix_match_probe.py --self-test`.

    python -I tools/suffix_match_probe.py --cohort PUBLIC_COHORT.json --measured-by @yourhandle --sample ID path/to/file.ORF

**`token_loop_probe.py`** supports the double-integration/Lorenzo and plain
running-sum bullets of lead #31. It parses the first rows x payload-width
candidate tokens with the #11 model and maps each suffix to three fixed
residuals. It reports peak-to-peak growth for second-order per-row,
per-parity, Lorenzo and running-sum loops against four within-row token
shuffles, with all cells and nulls retained. Rows are nominal W-token blocks,
not physical image rows; within-row shuffles preserve each row's value
multiset and mean. Double/Lorenzo cells use a predeclared 1.5x threshold;
running-sum cells use a 0.5..1.5 "equal to null" band. These are descriptive
comparisons, not significance tests, a decode or a reproduction of the lead's
private figures. Stdlib only, aggregates only; no images or raw values.

    python -I -B tools/token_loop_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_loop_probe.py

Optional `--null-mode global` shuffles all mapped values in the selected
prefix with the same fixed seed rule; the default remains `within-row`.
Global shuffling changes nominal-row allocation and row means, while the
within-row control preserves both. Both are descriptive surrogates, not
calibrated significance tests, physical-row evidence or a reconstruction.

    python -I -B tools/token_loop_probe.py --sample ID PUBLIC_NAME FILE --rows 300 --perms 4 --null-mode global

**`flat_predictor_screen.py`** reproduces the bounded #31 flat-capture candidate
search. The raster, channel, value and 254 dark anchor are assumptions, not a
codec or established per-channel calibration. Results report incomplete
candidates separately; the 5.7–6.3 bits/site subset was a post-hoc amendment.
The shuffled control permutes the first 300000 payload bytes, seed 20261022.
The optional cross screen uses unshuffled inputs and a 200000-byte prefix.

    python -I -B tools/flat_predictor_screen.py --dark FILE --dark-sha256 HASH
    python -I -B tools/test_flat_predictor_screen.py

**`code_family_screen.py`** supports lead #339. It screens a payload for standard containers
(magic counts; zlib, raw DEFLATE, gzip, bzip2 and lzma/xz decompression at the first byte offsets,
output capped, each hit marked complete or partial from the decompressor's end-of-stream state),
measures recompressibility, and parses the whole payload with Rice (k 0..8, both stop bits),
Exp-Golomb (0..6), Elias gamma/delta and Fibonacci codes, reporting prefix and whole-payload consumed
bits and completed codewords separately. `--shuffle` runs the same tests on shuffled payload bytes.
The screen is bounded and descriptive: it cannot exclude other framings, parameters or hybrid coders.

    python -I -B tools/code_family_screen.py path/to/file.ORF [--shuffle]
    python -I -B tools/test_code_family_screen.py

**`q_parity_covariance.py`** addresses V2 G0 by decomposing pooled lag-1 and
lag-2 Pearson covariance of capped candidate q values into within- and
between-token-index parity components. It retains escapes and token order,
requires the full requested prefix, and reports undefined cases explicitly.
The parity classes are token indices, not physical rows or CFA labels.

    python -I -B tools/q_parity_covariance.py path/to/file.ORF --tokens 1000000
    python -I -B tools/test_q_parity_covariance.py

**`whole_family_null.py`** supports V2 G0. It counts nine literal candidate
families over a whole payload and a single same-length Bernoulli control fitted
to its full-payload ones fraction. It retains packed bytes rather than a bit
list. Endpoints, residuals and count per stored site are descriptive; they do
not identify a codec, framing, physical pixel correspondence or variant. Density
is preserved only in expectation and one seeded draw does not show significance.

    python -I -B tools/whole_family_null.py path/to/file.ORF --seed 20261021
    python -I -B tools/test_whole_family_null.py

**`rice_boundary_compare.py`** supports #339 by comparing complete literal stop-1 Rice
k=4 and k=5 endpoints from bit 0 in a fixed payload prefix. It aggregates shared-boundary
interval spans and word counts, and reports unmatched tails and residual bits. `--shuffle`
shuffles the whole payload with the stated seed before taking the prefix. Shared endpoints
do not establish physical framing, synchronization or the correct code family.

    python -I -B tools/rice_boundary_compare.py path/to/file.ORF --prefix-bytes 3000000 [--shuffle]
    python -I -B tools/test_rice_boundary_compare.py

**`bayer_grid_probe.py`** supports lead #338. On the candidate k=5 parse it counts suffix
equality on the lag lattice `dy*W + dx` (dy 0..3, dx -4..4) over a token prefix, next to one fixed
shuffle that permutes ordinary suffixes within W-token blocks (escape positions kept). It also reports
whole-payload token and residual-bit counts, the positions of large-q tokens, and (row % 2, col % 2)
tables of the most common tokens for chosen row windows. Token index -> (row, col) uses W from the
TIFF tags; that is a coordinate choice, not an established pixel map or CFA phase.

    python -I -B tools/bayer_grid_probe.py path/to/file.ORF
    python -I -B tools/test_bayer_grid_probe.py

**`flat_parity_profile.py`** reports the fixed #338 nominal-block q=0/suffix
0/8 parity contrast, training on blocks 2:202 and evaluating later complete
blocks. `--tokens` selects a prefix; without it the whole candidate stream is
profiled. Consumed and residual bits describe the whole parse in either mode.
A null verdict is undefined even when exit status is zero. The fixed
shuffle is descriptive; token blocks do not establish physical rows.

    python -I -B tools/flat_parity_profile.py --sha256 HASH --tokens 8000000 path/to/file.ORF
    python -I -B tools/test_flat_parity_profile.py

**`pixls_samples.py`** lists, checks and downloads raw.pixls.us Olympus/OM samples using the site's licence listing. It downloads CC0 files only and verifies SHA-256. See the top-level README.

**`manifest_rows.py`** turns local CC0 files into ready-made `samples/manifest.csv` rows, combining the licence listing with `orf_signature.py`.

**`strip_contiguity_audit.py`** supports #11 by auditing table-order strip
adjacency on the unique largest-strip-total IFD. It separately reports one-strip
inputs, gaps, negative table deltas, nonascending offsets and physical overlaps.
Invalid counts in any candidate IFD or a tied largest total fail explicitly;
this is a conservative selector, not unconditional equivalence to older
first-winner behavior. Provenance must be verified separately. `PUBLIC_ID`
may be a truthful public-CC0 label or pixls identifier; no local paths or payload
bytes are printed. This is container geometry, not a bitstream finding.

    python -I -B tools/strip_contiguity_audit.py --sample PUBLIC_ID PUBLIC_NAME SHA256 FILE
    python -I -B tools/test_strip_contiguity_audit.py

**`orf_signature.py`** prints one CSV row per file with its measured container and payload facts: SHA-256, magic, make, model, payload size, bits per sample, compression tag, payload offset and bytes, and bits per pixel. It reads the TIFF structure only and decodes nothing.

It exits with status 1 if any input fails, while preserving successful CSV rows
and reporting each failed input on stderr. Status 0 means every requested input
succeeded; `--help` also exits 0, and no arguments exits 2.

    python tools/orf_signature.py path/to/* > rows.csv

**`conformance.py`** runs the reference decoder (`decoder/orf_decode.py`) on files and prints per file the input SHA-256, packing, size, bytes consumed vs payload size, min/max, out-of-range count (for packed-16: words with a non-zero low nibble), smoothness and the output hash, then a summary. `--csv` gives the `samples/conformance-V0.csv` format. Supports ROADMAP.md.

    python -I tools/conformance.py path/to/*

**`test_orf_decode.py`** round-trip tests of the decoder on synthetic bytes: `python -I tools/test_orf_decode.py`.

**`bit_runs.py`** gives a histogram of zero-bit runs in the payload (MSB-first), as aggregate numbers. It's a starting point for bitstream work (the F1 lead, #11).

    python tools/bit_runs.py path/to/file.ORF --mb 1

Example output on raw.pixls.us `8549_OM System - OM-5 Mark II - 16bit (4_3).ORF` (CC0), first 1 MB:

    q= 0  share=0.48036
    q= 1  share=0.27349
    q= 2  share=0.13019
    q= 3  share=0.06272

**`orf_tokens.py`** parses the token stream described in lead #11 (q zero bits, stop bit, 5-bit suffix; escape at q >= 17) and prints aggregate statistics per file: tokens against width x height, bit alignment at multiples of the width, q histogram and escapes, suffix bit balance, H/L bit-group shares, the ones-density with the tokens per pixel a Bernoulli (independent-bits) null predicts next to the measured value, correlation of min(q,8) at token lags 1, 2, 3, 6 and the row stride, and mutual information at token lags 1-3 (H->L, L->H, L->L, H->H), the b2 context gain and vertical lag 2, each with a baseline that shows the estimator bias. Numbers are printed as measured, whether or not they match that lead. It parses a prefix by default (`--max-tokens`, `--rows`); `--all` parses the whole payload. `--escape-landing` tabulates, per escape q, where the stream re-synchronises (distance modulo 6) after each escape. H = b4b3 and L = b2b1b0 are only labels for bit groups; no signed or other meaning is assumed.

    python tools/orf_tokens.py path/to/file.ORF --rows 400
    python tools/orf_tokens.py path/to/file.ORF --all

**`token_row_stride.py`** scans a wide range of candidate token row strides
and scores a row-start q profile: for a stride S it folds the q sequence into
rows and compares the mean q of the first K tokens of each row with the rest,
over up to `--rows` rows. A positive peak is a candidate prefix periodicity;
on the calm E-M1 Mark II files the peak is the payload width, while busy
OM-5/OM-1 files peak at a larger, file-specific stride (for example S=5472 on
OM-5 id 6343, S=6010 on OM-1 id 5283 over 300 rows). This extends the W+/-4
scan of the row-period finding. Standard library only; `--self-test` runs a
synthetic check. The score is descriptive and does not establish a unique
physical row boundary. Supports specs/V1.md G3 and lead #30.

    python -I tools/token_row_stride.py path/to/file.ORF --rows 300
    python -I tools/token_row_stride.py --self-test

**`jpeg_dc.py`** decodes only the DC coefficient of each 8x8 block of a
baseline JPEG, for the first (luma) component. For an ORF it finds the largest
embedded preview (width and height at least 1000). On the E-M1 Mark II files the
3200x2400 preview gives a 400x300 luma grid. AC coefficients are skipped; no
image or pixel data is written. Standard library only. Supports the P0
token-to-luma probe and the geometry part of lead #11.

    python -I tools/jpeg_dc.py path/to/file.ORF

**`preview_pair_sensitivity.py`** supports the follow-up questions in leads
#327 and #295 that the 12x12 screen left open. It reuses `jpeg_dc.py` and the
same complete-block, area-mean, identity-aligned normalized grids as
`preview_pair_screen.py` at 12x12, 24x24 and 32x32, with the frozen r >= 0.98
cutoff and no alignment search. It reads standard EXIF capture time
(DateTimeOriginal, then DateTimeDigitized, then DateTime) and groups same-model
pairs by absolute camera-local wall-clock gap. It also compares exposure time,
F-number, ISO, lens model and focal length for same-model pairs above and below
the cutoff. Same-model uses the manifest `model` text matched by SHA-256. The
metadata comparison is a descriptive negative control, not a shared-exposure or
scene/capture classifier; time zones and wrong camera clocks are not corrected,
and EXIF agreement does not establish a shared scene. Time bins count scored
pairs for each grid and report unscored pairs separately; unscored pairs are
excluded from the high/low metadata classes. Read-only, standard library CPU,
aggregate JSON only. Verify input licences separately.

    python -I -B tools/preview_pair_sensitivity.py FILE [FILE ...] > sensitivity.jsonl
    python -I -B tools/test_preview_pair_sensitivity.py

**`token_luma_probe.py`** tests a fixed token-field to low-resolution luma
mapping against a within-row suffix permutation. The default `--map sum` takes
`v = b2 + b4`; `--map b2` and `--map b4` select that bit alone. Every map
zeroes escape markers, box-averages `v` over `--window` tokens within each row,
block-averages to the preview's luma DC grid, and correlates the row-centred
grids. The target comes from `jpeg_dc.py`; the null permutes the suffix tokens
within each row. It prints one aggregate line per file (`r`, shuffle mean and
sd, z, escape count). `--shift-null` additionally scores every circular shift
of the preview rows and prints the best shift, the observed rank among all
alignments (including the observed alignment), and the shift
mean, sd and maximum. A rank above 1 means a shifted preview scores at least as
well; the within-row shuffle null tests horizontal structure only, so the shift
null is a vertical-alignment sensitivity check, not a calibrated p-value. The
default `--rows 300` is the top token band; a full-frame reshape is not used
because the token row stride can drift. This is a low-frequency luma proxy, not
a full pixel decode. The camera rendering is a numerical sanity reference, not
sensor ground truth. Marginal map rankings do not establish unique bit
contribution or significance. Test:
`python -I tools/token_luma_probe.py --self-test`.

    python -I tools/token_luma_probe.py path/to/file.ORF --rows 300 --window 63 --perms 20
    python -I tools/token_luma_probe.py path/to/file.ORF --rows 300 --window 63 --perms 20 --shift-null
    python -I tools/token_luma_probe.py path/to/file.ORF --map b2 --rows 300 --window 63 --perms 20
    python -I tools/token_luma_probe.py --self-test

**`token_luma_stride_probe.py`** applies the same fixed b2+b4 luma map as
`token_luma_probe.py`, but takes W tokens from each S-token candidate row
(`--stride S`) instead of assuming a row is exactly the payload width. Optional
`--start-row` and `--offset` select later bands and the row-internal image
start; the null permutes the used suffix tokens within each W-token image row.
It prints aggregate `r`, shuffle mean and sd, z and escape count per file, and
writes nothing. A candidate stride is a periodicity of the q row-start profile,
not a physical row length, and a positive result is a low-frequency luma
correlate rather than a value mapping. Supports lead #149 and the row-stride
work of lead #144 / specs/V1.md G3.
`python -I tools/token_luma_stride_probe.py --self-test` checks the
stride/offset extraction and preview row crop.

    python -I tools/token_luma_stride_probe.py path/to/file.ORF --stride 5472 --rows 300
    python -I tools/token_luma_stride_probe.py path/to/file.ORF --stride 5472 --start-row 1000 --rows 300
    python -I tools/token_luma_stride_probe.py --self-test

**`token_luma_phase_probe.py`** keeps the fixed b2+b4 map and candidate stride
but scans the absolute row phase: row `r` is the W-token window at token
`r*S + phase`. A phase above `S-W` overlaps the next candidate row, so the phase
is an alignment hypothesis, not a physical row origin. The tool scans phases at
`--step`, refines the best over `--refine` phases, and can repeat the whole
search after `--perms` global suffix permutations; it prints phase 0, the best
phase and r, the top phases, null maxima and escape count, and writes nothing.
Supports the #296 stride/phase landscape and the phase-sensitivity question of
lead #149. `--self-test` checks a synthetic inserted phase.

    python -I tools/token_luma_phase_probe.py path/to/file.ORF --stride 5472 --rows 300
    python -I tools/token_luma_phase_probe.py path/to/file.ORF --stride 5472 --rows 300 --perms 1
    python -I tools/token_luma_phase_probe.py --self-test

**`token_value_probe.py`** supports leads #11 and #32 with band-wise
b2+b4 correlations, nominal versus whole-preview scale comparisons, column
statistics and fixed suffix-table transfer against numeric embedded-preview
luma DC. Rows are candidate token blocks at the payload width; physical row
boundaries and escape framing remain unresolved. The table measures a weak
statistical correlate, not sensor values, a predictor or a round-trip decode.
Within-row shuffles are descriptive; a four-shuffle z is not calibrated
significance. Licence-check the public training and test inputs first.

    python -I -B tools/token_value_probe.py --self-test
    python -I -B tools/token_value_probe.py table --train PUBLIC_TRAIN --test PUBLIC_TEST --rows 600 --mode s --lam 1 --smooth 10 --perms 4

**`value_map_probe.py`** (by @mtakemoto) measures suffix bridge energies under the three candidate suffix mappings from lead #32, against an exact permutation null, in 128-token blocks of the #11 parse. It is a frozen, pre-registered experiment: the sample IDs per phase (`discovery`, `validation`) and the settings are fixed on purpose, so it reruns that one design rather than measuring arbitrary files. It prints aggregate JSON only. `--self-test` runs its tests.

    python tools/value_map_probe.py --phase discovery --measured-by @yourhandle --sample 1993 NAME path/to/file.ORF

**`value_map_window_probe.py`** supports the later-window control in lead #32.
It reuses @mtakemoto's suffix bridge-energy arithmetic and the original #11
candidate scanner, scanning from payload bit zero while retaining only the
requested window. Start tokens must be multiples of 128; reported block indices
and lane parity are absolute. Each window holds at most 262144 tokens, and the
scan ends by token 100000000. It emits explicitly exploratory aggregate JSON,
source hashes, measured signature, absolute token/bit boundaries and escape
omissions. Licence-check samples first. The frozen six-file prefix experiment
is unchanged; later windows do not repair potential escape misalignment or
establish a decoder, physical row boundaries, or content/code causation.

    python -I -B tools/value_map_window_probe.py --sample ID PUBLIC_NAME path/to/file.ORF --measured-by @yourhandle --start-token 1048576
    python -I -B tools/test_value_map_window_probe.py

**`orf_v0_unpack.py`** scores candidate bit layouts for the uncompressed V0 files (`packed-12`, `packed-12.8`, `packed-16`, lead #28) on a small window of each file: value range, smoothness at same-colour horizontal and vertical distance 2 against distance 1, row correlation, and a row-stride test for the chosen layout. Text statistics only; it prints the layout with the lowest roughness and the margin to the next one.

    python tools/orf_v0_unpack.py path/to/file.ORF

**`layout_probe.py`** supports lead #77 by measuring strip gaps, stored-row
discontinuities, and natural versus two-field row-order scores over 400 centre
columns. By default it scores about 200 interior rows; `--all-rows` scores every
interior row, excluding the same boundary margins. Gap detection, pairing and
shift-curve sampling are unchanged. Output includes the scoring row counts.

    python -I tools/layout_probe.py --all-rows path/to/file.ORF

**`findings_index.py`** lists the verified findings under `findings/` by variant, with finder, verifier, title and status (verified or superseded). `--check` validates the files (file name, `Author:` matches the handle, `Verified by:` is another person, `Lead:` is `#n`, `Variant:` matches the folder, referenced IDs exist) and exits 1 on errors; CI runs it on pull requests.

    python tools/findings_index.py
    python tools/findings_index.py --check

**`trailing_ones_probe.py`** measures literal trailing one-bit counts for the
frozen full cohort in lead #87. It matches regular input files by streamed
SHA-256 regardless of filename or extension; duplicate cached copies count
once. It reuses `orf_signature.signature()` and the original
`orf_tokens.locate()` contiguous locator, checks their dimensions and payload
length agree, and requires `size_class=variable` and `compression_tag=1`.
Tag 1 alone does not distinguish fixed-size from compressed ORF payloads.
The frozen cohort has one strip per payload: this tool is not a generic parser
for separated strips.

The final byte, final eight bytes and whole payload are counted independently.
The tool checks that the two shorter counts equal `min(full, 8)` and
`min(full, 64)`; it makes no padding, token-end or decoder inference.
Measurement mode prints one JSON object containing public sample measurements,
sanitized failure categories, exact cohort-file and source hashes, and summary
histograms named `histogram_last_byte`, `histogram_last_eight_bytes` and
`histogram_full_payload`. Successful samples remain in frozen cohort order
when another required input fails; any failure returns a nonzero exit status.
No local paths or raw bytes appear in measurement output.

`--help` works alone. `--self-test` works alone and loads the independent
`test_trailing_ones_probe.py` unittest suite. Measurement mode requires all
three flags shown below.

    python -I tools/trailing_ones_probe.py --help
    python -I tools/trailing_ones_probe.py --self-test
    python -I tools/trailing_ones_probe.py --cohort tools/cohorts/lead87-trailing-ones-v1-full.json --sample-dir /path/to/samples --measured-by @yourhandle

**`byte_boundary_tail_probe.py`** supports lead #87 with an empirical reference
for trailing-one runs at every payload byte boundary, including cross-byte
runs. It compares the final run with all earlier boundaries in that same
payload, retaining full histograms, ties and exact ratio denominators. Empty
payloads reject; one-byte payloads have no earlier-boundary fractions. These
are descriptive frequencies, without endpoint exchangeability, significance,
padding, token-framing or decoder inference. Match local hashes to retained
CC0 verification before running; new content needs first verification. The
CLI retains successful samples and sanitized errors, exits nonzero for any
failure, and prints aggregates only. Stdlib; no sample data is written.

    python -I -B tools/byte_boundary_tail_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_byte_boundary_tail_probe.py

All of them use the standard library only (Python 3.8+). Contributions of new tools are welcome. Follow the rules above and RULES.md.

**`token_bit_chain_probe.py`** supports lead #29 item 4 and builds on #11.
It reports all four ordered b2/b4 bit-pair tables at lags 1..5, plug-in MI,
Pearson correlations and every fixed-seed within-block whole-token permutation
comparison. The fixed prefix contains at most 262144 complete tokens; whole
128-token blocks containing escapes and incomplete tails are omitted. Pairs
stay within retained blocks, which are not established camera rows. This is
descriptive pairwise dependence, not the historical multivariate conditional
chain, held-out gains, significance, a deeper law or a decoder. Licence-check
samples first; failures are sanitized and other sample reports retained.

    python -I -B tools/token_bit_chain_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_bit_chain_probe.py

**`v0_spec_check.py`** is an independent, aggregate-only implementation of
`specs/V0.md` at `bf56d39`, supporting lead #75. Original payload logic and
synthetic tests were written without target files, reference code, or output
hashes. Shared container code is limited to `orf_signature.Tiff` header/endian
and integer reads; an original wrapper validates relevant IFD descriptors.

    python -I tools/v0_spec_check.py --help
    python -I tools/v0_spec_check.py --self-test
    python -I tools/test_v0_spec_check.py
    python -I tools/v0_spec_check.py --measured-by @yourhandle --sample ID PUBLIC_NAME path/to/file.ORF

Repeat `--sample` for multiple files. IDs are distinct positive decimals; public
names may repeat. Match records by input SHA-256, never basename. Check CC0
licensing before supplying downloaded files. Each JSONL result includes public
identity, input/output hashes, measured signature, aggregates, selectors, source
hashes and pinned spec metadata. Failures emit sanitized categories, preserve
other results and return a nonzero exit code. No decoded data is written.

Selectors are **unverified spec generalizations**: packed-12 `IIRS` is plain,
`IIRO` reverses global four-byte words; no strip gaps means natural rows; one
packed-12 gap at the even-field boundary means two fields; packed-16 uses TIFF
byte order. Unsupported cases fail without trying alternatives. First/second
unit order is a convention, not physical pixel-order proof. The S4.3/S6 wording
ambiguity is resolved by preserving packed-16 stored words with **no numeric
shift**, including low nibbles. Above-4095 and nonzero-low-nibble counts are
separate measurements. Hashing uses explicit uint16 little-endian image rows.

Read-only mmap, individual strip reads, strict integer size classification and
row streaming are bounded by 8 GiB per file, 100,000 per dimension, 250,000,000
pixels, 4,096 IFDs and 1,000,000 strips. Malformed relevant fields, tied largest
IFDs, repeated pointers, overlaps, nonascending strips and unsupported gaps are
rejected. Report mismatches under these frozen assumptions; do not tune them to
expected hashes.

Input opening uses `os.O_NONBLOCK` where the platform has it: the acquired
descriptor is checked with `fstat` before any mmap/read, so a FIFO without a
writer is rejected promptly and later inputs still run. Where the flag is missing
(Windows), a non-regular path is refused by `os.stat` before opening, and the
opened descriptor is still checked with `fstat`. Descriptors close on success
and failure. Symlinks to regular files remain usable. `--help` and `--self-test`
are portable; the FIFO test skips where FIFOs or `O_NONBLOCK` are absent.

**`token_phase_probe.py`** supports the unverified token-phase part of lead #30
and builds on candidate parse #11. It reports every modulo-2..8 contingency
table between absolute token phase and joint suffix symbol `2*b4+b2`, together
with plug-in symbol entropy, phase-conditional entropy and mutual information.
The fixed prefix is 262144 complete tokens; escapes (`q>=17`) are omitted
without compacting indices, with zero extra escape bits. It requires a single
in-bounds variable-size strip and prints aggregate JSON with sample hashes,
measured dimensions, prefix shortfall, source hashes and sanitized failures.
Exit 1 signals any input failure or nonzero prefix shortfall; short-prefix
statistics remain visible but do not fulfill the declared fixed-prefix design.
Complete error-free reports return exit 0.
Licence-check downloaded samples first. This descriptive metric has no bias
correction, significance threshold or physical column interpretation; it does
not reproduce the historical conditional-context gain or private figures.

    python -I -B tools/token_phase_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_phase_probe.py

**`exif_sensitivity_probe.py`** supports the remaining ISO-setting question in
lead #106. It reports raw numeric Exif PhotographicSensitivity (0x8827) values
from the primary IFD's ExifIFD pointer alongside measured signatures. Missing
values remain absent; 65535 is flagged as a possible sentinel requiring extended
tags. It reads no maker notes, GPS, serials or preview pixels. It does not test
ISO/bpp correlation, scene content, or causality. Licence-check inputs first.

    python -I -B tools/exif_sensitivity_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_exif_sensitivity_probe.py

**`preview_date_stratification.py`** supports #347. It joins a complete
12x12 preview pair screen to hash-matched EXIF metadata and fixed public cohort
model/group labels. It reports same-second, same-day within/beyond 600 seconds,
different-day and unavailable timestamp buckets for all and same-model pairs,
including unscored and extension pair counts. Recorded times and model text do
not establish scene identity, physical camera identity or capture independence.
Cohort JSON is an array of objects with `sha256`, `model` and `group` (original
or extension); the UTF-8 files list contains one local path per line. Licence
verification is separate; no dates, previews or local paths are printed.

    python -I -B tools/preview_date_stratification.py --screen screen.jsonl --cohort cohort.json --files-from files.txt
    python -I -B tools/test_preview_date_stratification.py

**`capture_pair_calibration.py`** supports #295. It labels the pairs printed by
`preview_pair_screen.py` from each file's own metadata only (EXIF
DateTimeOriginal, payload width, file name): camera-written High Res ORF / ORI
companions require exactly matching stems after removing the extension; numeric
suffixes are preserved and copy suffixes are not normalized. Same-second
non-companions (bursts), same-session pairs within
600 s, same-day and different-day pairs. Same-session H pairs have unknown scene
identity; their hit rate is not an established false-positive rate. It reports
class counts alongside AUC and score ranges. A threshold is calibrated on
alternating shooting days only with at least 10 P and 10 H pairs on calibration
days; held-out validation also requires at least 10 of each. This descriptive
minimum does not establish statistical validity or independent captures. The
tool reports aggregates only; no previews, payloads or images.

    python -I -B tools/preview_pair_screen.py FILE ... > screen.jsonl
    python -I -B tools/capture_pair_calibration.py --screen screen.jsonl FILE ...
    python -I -B tools/test_capture_pair_calibration.py

**`token_lag_probe.py`** supports lead #29 item 6 and builds on #11 and
`suffix_joint_probe.py`'s bounded candidate scanner. In the first 262144 tokens,
it keeps complete 128-token blocks without q>=17, forms only within-block
pairs, and reports q>0 and low-three-suffix-symbol plug-in MI at all lags 1..5.
It emits exact contingency counts, 16 fixed-seed within-block whole-token
permutation MI values, selection counts, source/input hashes and sanitized
per-sample failures. Blocks are not established camera rows; comparison values
are descriptive, without a significance test. This different metric does not
reproduce #29's historical private held-out/smoothed estimates or establish
stationarity, magnitude meaning or a decoder. Check CC0 licences first.

    python -I -B tools/token_lag_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_lag_probe.py

**`token_scale_probe.py`** supports lead #29 item 7 with held-out binary-q
prediction from lag1 and preceding 8/16-token positive-q counts. It reports
exact training/test tables, losses, signed gains against frequency and lag1,
unseen contexts and all sixteen within-block permutation comparisons.
Requested-prefix completeness is explicit: incomplete inputs retain their
observed-block diagnostic scores, report `prefix_complete=false` and add an
`IncompletePrefix` error. Any shortfall or input failure exits nonzero; valid
reports survive mixed inputs, and failures expose public identity/error class.
Original even/odd 128-token blocks define the split; escape-containing blocks
and incomplete tails are omitted. Blocks are not physical rows, adjacent
split blocks may depend, and omission does not repair unknown framing.
These descriptive scores do not reproduce historical q-entropy estimates or
establish significance, a codec scale law or a decoder. Check CC0 licences first.

    python -I -B tools/token_scale_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_scale_probe.py

**`token_context_probe.py`** supports the held-out multivariate context step
for lead #29 item 4, building on #11 and the bounded `suffix_joint_probe.py`
scanner. Six fixed binary models use common within-block targets, Jeffreys
smoothing and original even/odd block training/test splits; escape-containing
blocks and incomplete tails are omitted. It reports exact train/test tables,
absolute held-out log-loss, nested gains, unseen-context counts and all sixteen
within-block whole-token permutation comparisons. Adjacent blocks can remain
dependent, and blocks are not camera rows. These descriptive transfer scores
do not reproduce historical private estimates or establish a conditional law,
significance or a decoder. Check CC0 licences before measurement.

    python -I -B tools/token_context_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_context_probe.py

**`token_zero_runs_probe.py`** supports the remaining b2 zero-run question in
lead #30 and builds on #11's candidate parse. In the first 262144 complete
tokens it splits at every q>=17 escape, omits that token, and counts maximal
positive-length b2 zero runs bounded by ones within a retained segment.
Leading, trailing and all-zero-segment censoring are reported separately.
It emits the full run histogram, integer moment sums, population moments and
the fitted positive-geometric variance `mean*(mean-1)`. This is descriptive,
without a fit/significance test, physical-row or run-copy interpretation.
Historical private figures have unspecified run-support/censoring definitions
and are not reproduced. Escape omission does not repair uncertain framing.
Outputs are aggregate JSON with hashes and sanitized per-sample failures;
licence-check samples first.

    python -I -B tools/token_zero_runs_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_zero_runs_probe.py

Optional `--start-token N --tokens K` selects K candidate tokens starting at
absolute token index N, counting escapes. Parsing always starts at payload
bit zero; only the selected window is retained in memory. Each window censors
both edges independently. Reports include skipped tokens/escapes, start and
length shortfalls, absolute start/end bit positions and selected-window bit
length. `prefix_shortfall` is retained as an alias of `token_shortfall` for
older consumers. Untouched windows can expose within-file variation but do
not establish stationarity, representativeness or a geometric law.

    python -I -B tools/token_zero_runs_probe.py --start-token 1048576 --tokens 262144 --sample ID PUBLIC_NAME path/to/file.ORF

**`escape_balance_probe.py`** supports the remaining b1/b0 suffix-balance
question in lead #11. In the fixed first 262144 complete candidate tokens,
it splits ordinary tokens strictly before versus after the first q>=17,
excluding every escape. Exact suffix histograms and b4..b0 one-counts are
reported, including empty groups, prefix shortfalls and sanitized failures.
No first escape means all ordinary tokens are in the before group. Framing
following an escape remains unknown; scene variation and unequal group sizes
prevent a causal interpretation. This new descriptive metric is not a
reproduction of historical private numbers. Check CC0 licences first.

    python -I -B tools/escape_balance_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_escape_balance_probe.py

**`token_width_lag_probe.py`** supports the nominal-width-lag part of lead #29
item 8, building on #11 and the bounded `suffix_joint_probe.py` scanner.
It reports exact binary tables and Pearson correlations at W, 2W, 2W-2,
2W+2 (past/current b2) and 2W-1 (past b4/current b2), pooled and by all four
target nominal-grid parity strata. W is measured payload width, not an
established token row stride or sensor/CFA grid. In the first 262144 complete
tokens it omits pairs with q>=17 at either endpoint without renumbering;
intervening escapes remain. Every candidate, omitted and retained pair count
is reported; empty/zero-variance correlations are null. These descriptive
aggregates do not reproduce historical private figures or establish donor
structure, parity invariance, significance or a decoder. Check CC0 licences first.

    python -I -B tools/token_width_lag_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_width_lag_probe.py

**`q_value_bridge_probe.py`** supports lead #32 with a preview-free bridge
metric for the q-inclusive readings `u=32*q+s` and `zigzag(u)`. It builds on
@mtakemoto's exact permutation-mean bridge design (#64) and #11's candidate
parse; PR #159 tests the same readings with a different predictor/preview
score. All four mapping/lane-count cells, exact block A/V terms, pooled
energies, separate absolute-parity pools and omissions are emitted. The fixed
262144-token prefix uses complete 128-token blocks, omitting whole blocks
containing q>=17 and the incomplete tail. No escape skip is added. Ratios
are sums of energies divided by sums of observed-multiset permutation means,
not averages of ratios or significance tests. Degenerate ratios are null.
Blocks and token parity are not physical rows/channels; omission cannot
repair unknown framing. Detrending removes drift, so these measurements
cannot establish a bounded reconstruction or reproduce historical private
growth figures. Licence-check public inputs first. Failed samples are
sanitized; successful reports survive and any failure makes the exit nonzero.

    python -I -B tools/q_value_bridge_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_q_value_bridge_probe.py

**`token_position_probe.py`** supports the still-open item 9 of lead #29,
building on #11 and `suffix_joint_probe.py`. It reports ordinary-q (0..16)
and unsigned-suffix (0..31) histograms at nominal positions 0..23 and the
remainder, plus pooled first10/first24/remainder counts, sums and means.
Only complete payload-width W-token rows from token0 contribute; q>=17
symbols are omitted without compacting indices. All escape omissions and
incomplete nominal-tail counts are explicit. W and origin are hypotheses,
not established physical rows; omission cannot repair unknown escape framing.
The historical row-start statistic did not specify its field/estimator, so
these new explicit metrics do not reproduce its values. No elevation criterion,
null model, significance or decoder is supplied. Check CC0 licences first.

    python -I -B tools/token_position_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_position_probe.py

**`token_b4_gate_probe.py`** supports the b4 significance-gate question in
lead #32 and builds on candidate parser #11. It emits complete low3/low4
unsigned histograms by b4, current-q/current-b4 and previous-q/current-b4
17-by-2 count tables, conditional probabilities and unsmoothed plug-in MI.
The first 262144 complete tokens use zero extra escape bits; q>=17 tokens
are omitted, with both endpoints required ordinary for lag1 pairs. Original
indices are preserved; omitted tokens are never joined. Both low-bit field
definitions are explicit because the historical phrase was unspecified.
No significance, independence, semantic gate or historical-number claim
follows; omission cannot repair unknown framing. Licence-check inputs first.

The b4-gate probe's optional `--q-stratified` flag adds exact within-q
low3/low4 contrasts and each file's equal-weight summary over its reported
support. Sparse strata and differing support limit comparisons. Missing files
or token-prefix shortfalls exit nonzero while retaining aggregate records.

    python -I -B tools/token_b4_gate_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_b4_gate_probe.py

**`suffix_width_probe.py`** supports the committed candidate k-scan requested
in V1 G8 and relates to lead #29 item 1. For each whole payload it reports
all k=2..8 and both stop-bit conventions: q opposite bits, one stop bit,
then k skipped suffix bits. Only complete tokens count; q>=17 has no extra
skip. Exact q histograms, escape counts, consumed/unconsumed lengths and
tokens per measured payload pixel are emitted. There are no row delimiters
or neighbour-dependence measures. Small residuals or near-one token ratios
do not establish the correct grammar, padding or a decoder. Single-strip
variable-size inputs with compression tag 1 are required; input size is
limited to 512 MiB. Failures are sanitized and successful samples retained.
Check CC0 licences first. Original scanner, stdlib only, aggregates only.

    python -I -B tools/suffix_width_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_suffix_width_probe.py

Optional `--block-tokens 262144` adds exact q0-count histograms over complete
fixed-size candidate-token blocks and separate tail counts, supporting the
within-file framing question in #197. The default output is unchanged. Blocks
under different grammars cover different bit intervals; a high q0 share or its
variation cannot select a true code or establish adaptation. All candidate
tokens, including q>=17, contribute; there is no fitted offset or escape skip.

    python -I -B tools/suffix_width_probe.py --block-tokens 262144 --sample ID PUBLIC_NAME path/to/file.ORF

**`token_count_closure.py`** supports specs/V1.md G3/G8 and lead #339. It parses
each whole payload from bit 0 under 25 suffix-width rules fixed in its docstring
before any cohort results: fixed k=4..7 and 21 causal adaptive rules
(JPEG-LS-style accumulators, previous-value bit length) with k chosen before each
token, and reports complete tokens minus W x H, the residual bits, escapes and
mean k. `--table` adds the k=5 joint count of min(q,17) x suffix. `--summarize`
reads the JSON lines back and prints per-rule closure counts by odd/even id, the
Spearman correlation of bpp with the k=5 excess (overall and within each public
name) and, for declared token predicates, the ten tightest ranges of
count / excess. A count near W x H does not prove a syntax; these are
descriptive statistics only.

    python -I -B tools/token_count_closure.py --sample ID PUBLIC_NAME path/to/file.ORF [--table]
    python -I -B tools/token_count_closure.py --summarize results.jsonl
    python -I -B tools/test_token_count_closure.py

**`token_affine_probe.py`** supports the untested GF(2) part of lead #29
item 4, building on #11 and #166/#169. It tests exact affine prediction of
current b2 and b4 from both bits at lags 1..12, with an intercept. All six
pooled/even/odd-target systems report context and target-augmented ranks.
The first 262144 complete candidate tokens use zero extra escape bits;
any 13-token context-plus-target window containing q>=17 is omitted without
compacting indices. A rank increase excludes only an exact affine predictor
of this context on these observed selected rows. It does not exclude noisy,
nonlinear or longer-context laws, identify a scrambler or physical rows,
reproduce historical private ranks, or decode. Escape omission cannot repair
uncertain framing. Check CC0 licences first. Stdlib, aggregate output only.

    python -I -B tools/token_affine_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_affine_probe.py

Every affine sample now reports `prefix_complete`. Incomplete requests retain
all selected-row diagnostic ranks/consistency but make the CLI exit nonzero;
those verdicts cover only observed rows. Failed public identities appear
in `failures`, with sanitized exception classes, while valid
reports remain in `samples`. Any input failure also exits nonzero. Every ID
is validated before reading samples. Existing complete-prefix ranks/counts
are unchanged. Reuse retained CC0 verification after matching the local hash.

**`suffix_width_lag_probe.py`** follows the neighbour-dependence question after
the candidate width scan (#29, V1 G8). All k=2..8 and stop=0,1 grammars use
their first 262144 complete tokens and zero extra escape skip. All lags1..5
report exact q-positive 2x2 and fixed low-two-suffix-bit 4x4 tables and
unsmoothed plug-in MI, omitting only q>=17 endpoints without compacting
indices. Intervening escapes remain; omission cannot repair unknown framing.
Reports include endpoints, shortfalls, omissions, public/source hashes and
sanitized failures. Equal alphabets do not remove finite-sample, marginal
or selection bias: MI does not rank/select grammars. No null, significance,
physical rows, historical private-value reproduction or decode is claimed.
Licence-check public inputs first. Stdlib, reads files/prints aggregates only.

    python -I -B tools/suffix_width_lag_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_suffix_width_lag_probe.py

Optional `--block-rotation-control` adds a separate matched descriptive
control for #29/V1 G8. Complete 128-token blocks from token zero are kept
only when every q<17; incomplete tails are excluded. At lag L=1..5, M=128-L
donors at indices 0..M-1 pair with fixed targets L..127. The control rotates
these M donor tokens by floor(M/2), modulo M. Both observed and control
tables therefore have identical donor/target marginals in each block and
pooled. Exact q-positive and low2 suffix tables, MI, signed observed-minus-
control differences and selection counts are reported for every grammar.
The default endpoint-only report stays unchanged. Whole-block selection
differs from that default. This single deterministic rotation preserves
block mixtures but can retain longer dependencies; it is not a null
distribution, significance test, unbiased correction or grammar selection.
Blocks are not physical rows and omission cannot repair escape framing.
Reuse retained CC0 verification after matching the local hash; new content
needs its first licence verification. Reports contain aggregates only.

    python -I -B tools/suffix_width_lag_probe.py --block-rotation-control --sample ID PUBLIC_NAME path/to/file.ORF

`token_phase_context_probe.py` also emits a separate `heldout` report for
lead #30. Complete 128-token blocks containing any q>=17 and the incomplete
tail are omitted. Original even-index blocks train; original odd-index
blocks test. Each retained block contributes local targets 2..127, so no
source triple crosses a split boundary. The fixed target/context are
Y=b2(t), C=2*b4(t-1)+b2(t-2); phase is the absolute index modulo m=2..8.
For identical held-out targets it compares Jeffreys-smoothed binary
P(Y|C) with P(Y|C,phase), emitting full train/test tables, denominators,
unseen-training-context counts, both log losses, and signed baseline-minus-
phase gains. Negative gains are retained. Absent training data predicts 0.5
with null gain; absent test data gives null loss/gain. This whole-block
selection differs from the earlier triple-wise plug-in tables, which remain
unchanged. Adjacent blocks may remain dependent; these descriptive scores
are not unbiased estimates, significance/null calibration, historical
private-gain reproduction, physical columns or a decoder. Excluding escapes
cannot repair unknown framing. Reuse prior CC0 verification after checking
the local file hash against its verified record; new content needs its first
licence verification.

    python -I -B tools/token_phase_context_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_phase_context_probe.py

**`token_band_profile.py`** supports lead #144's later-band question with
fixed candidate strides and absolute boundaries r*S from token zero. Each
300-row band reports exact capped-q contrast moments, signed mean/SE,
escape counts and incomplete-band accounting. Zero variance gives a null
score, retaining its signed mean. No stride search or phase refit occurs.
The default starts are candidate-row ordinals 0, 1000 and 2000, not physical
rows. Changing profiles can reflect content, phase or framing; they do not
establish stride drift, significance or a decoder. Candidate unary-plus-five
parsing keeps q>=17 with zero extra skip and caps q at 40. Reuse retained CC0
verification only after matching the supplied public SHA-256; the hash is
checked before parsing. Every supplied sample identity survives failures,
with a nonzero exit for any failure or shortfall. Reads/prints aggregates only.

    python -I -B tools/token_band_profile.py --sample ID PUBLIC_NAME VERIFIED_SHA256 path/to/file.ORF --stride 5240 --stride 5472
    python -I -B tools/test_token_band_profile.py

**`token_width_context_probe.py`** supports lead #29 item 5 with held-out
b2 prediction beyond five fixed local alternating taps. It adds nominal-width
remote bits separately/jointly and compares deterministic +128-lag controls.
All eleven models share target eligibility, original target-block train/test
splits, Jeffreys smoothing, exact tables, signed gains and unseen counts.
Contexts cross blocks; reused donors and adjacent splits remain dependent.
Shifted controls may retain width structure and are not exchangeable nulls.
This is descriptive tooling, not the historical feature search, physical
rows, significance or decoding. Hash-match retained verified CC0 inputs first.

    python -I -B tools/token_width_context_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_width_context_probe.py

**`token_phase_surrogate_probe.py`** adds a separate conditional phase-offset
comparison for #30, Builds on #11/#203/#211. It preserves the fixed 262144
candidate-token prefix, 128-token whole-block escape selection, original
even-block training/odd-block test split, local targets 2..127, context
C=2*b4(t-1)+b2(t-2), and target Y=b2(t). Every modulus 2..8 gets sixteen
surrogates: independently add a uniform offset 0..m-1 to all phase labels
in each retained block, leaving context/target ordering and split fixed.
Random(20261021+replicate) is restarted for each modulus and consumed in
retained original-block order, including both splits. Full observed and
surrogate train/test tables, offset histograms, Jeffreys losses, signed
gains, and rank counts (<, =, > observed) are emitted. There is no inferential
p-value: exchangeability of these offsets is assumed for this diagnostic,
not established for actual ORFs. Adjacent blocks can depend and within-block
phase structure remains. The comparison does not repair framing, reproduce
historical private gains, establish physical columns or decode. Known-profile
smoke inputs are tool validation rather than untouched confirmation. Reuse
retained CC0 records only after matching the local SHA-256. Stdlib, reads
samples and prints aggregates only; missing inputs and shortfalls exit nonzero.

    python -I -B tools/token_phase_surrogate_probe.py --sample ID PUBLIC_NAME path/to/file.ORF
    python -I -B tools/test_token_phase_surrogate_probe.py

**`token_tail_distribution_probe.py`** supports #144's candidate extra-token
question, Builds on #11/#218/#234. At a fixed supplied stride S and measured
width W, T=S-W defines tail positions [W,S). Every complete candidate row
contributes exact uncapped q and five-bit suffix histograms to the tail,
first-width [0,W), preceding [W-T,W), and middle [S//2,S//2+T) regions.
Both comparison windows have T tokens and fit inside first-width; they can
overlap each other for some geometries. Histograms include q>=17, with zero
extra escape skip. Reports retain region counts, q sums, localized escapes,
entropies, tail-versus-comparison total-variation distances, all band
shortfalls, endpoints and source/input hashes. Incomplete final candidate
rows contribute no region statistics. Defaults are 300 candidate rows at
ordinal starts 0/1000/2000, with absolute r*S boundaries and no phase/stride
fit. Position comparisons are descriptive and not exchangeable nulls;
differences cannot identify padding, headers, a field, physical rows or an
actual entropy grammar. Unknown post-escape framing remains unresolved.
No significance, historical private-number reproduction or decode is
claimed. Reuse retained CC0 verification after matching the supplied hash,
which the tool checks before TIFF parsing. Every sample identity survives
sanitized failures; any failure or shortfall returns nonzero. Stdlib,
reads files/prints aggregates only.

    python -I -B tools/token_tail_distribution_probe.py --sample ID PUBLIC_NAME VERIFIED_SHA256 path/to/file.ORF --stride 5472
    python -I -B tools/test_token_tail_distribution_probe.py

**`token_cyclic_phase_probe.py`** supports the fixed-stride phase question in
lead #144 and builds on #11/#218. For each original S-token candidate row,
the head at phase p uses positions `(p+j) mod S` for j=0..head-1; the rest is
its complement. Every phase therefore uses identical tokens, including wraps
within the original row, rather than shifting contiguous row boundaries.
All phases report exact capped-q sums and contrast moments, signed mean/SE,
and all minimum/maximum ties. Phase zero equals `token_band_profile.py`.
Defaults are head 32, 300 candidate rows, ordinal starts 0/1000/2000.
Candidate unary-plus-five parsing retains q>=17, caps q40, and skips zero
extra escape bits. Reports retain shortfalls, sanitized failures, hashes and
public identities; any sample failure/shortfall gives a nonzero exit. Reuse
retained CC0 provenance after matching local SHA-256; new content requires
first verification. Selected phase extrema are descriptive, with no null,
calibrated significance, true-framing, physical-row or decoder inference.
They do not estimate later best strides or separate scene from framing.
Stdlib only; reads files and prints aggregate JSON, no token/pixel dumps.

    python -I -B tools/token_cyclic_phase_probe.py --sample ID PUBLIC_NAME VERIFIED_SHA256 path/to/file.ORF --stride 5240
    python -I -B tools/test_token_cyclic_phase_probe.py

**`token_phase_holdout_probe.py`** extends #144's cyclic diagnostic (#240)
with a first-half training phase and a second-half evaluation at the frozen
phase. Selection maximizes mean capped-q head-minus-rest contrast, with the
lowest phase breaking ties. Heads wrap within each original absolute r*S
candidate row. The report retains all training phase contrast moments,
held-out selected/zero-phase moments, and 99 independently row-rotated
conditional reference contrast sums, with exact seeds and exceedance counts.
These references preserve each row's multiset and cyclic shape but remove
common phase; they are descriptive, without a p-value or physical-row claim.
Inputs reused from earlier studies remain exploratory. No stride search,
contiguous-boundary refit, true escape syntax or decoding is established.
Incomplete requested bands are rejected without phase selection.

    python -I -B tools/token_phase_holdout_probe.py --sample ID PUBLIC_NAME VERIFIED_SHA256 path/to/file.ORF --stride 5472
    python -I -B tools/test_token_phase_holdout_probe.py

`unit_order_probe.py` supports lead #75 and V0 gap G4 with the original
central-300-stored-row edge metric; `--all-rows` measures the entire stored
frame instead. It reports exact within/cross-unit sums,
selected counts, means and cross/within ratios for emitted and swapped pairs.
Selection is strictly gradient > THRESHOLD; an empty selection reports null
means/ratios, and zero within sum reports a null ratio. Every explicit public
sample identity survives sanitized failures, which make the exit nonzero.
Legacy directory arguments remain accepted, but output is now aggregate JSON
instead of formatted text; directory scans process regular files only.
Unspecified packings are explicitly skipped. Container parsing, byte-order
selection and unpacking reuse the reference decoder unchanged. The statistic
does not establish physical pixel order or change conformance hashes. Match
local hashes to retained verified CC0 records before measurement.

    python -I -B tools/unit_order_probe.py 300 --sample ID PUBLIC_NAME FILE
    python -I -B tools/unit_order_probe.py 300 --all-rows --sample ID PUBLIC_NAME FILE
    python -I -B tools/unit_order_probe.py 300 SAMPLE_DIR
    python -I -B tools/test_unit_order_probe.py

**`token_head_stride_probe.py`** adds a local head-by-stride diagnostic for
#144's remaining head-sensitive maximum question; Builds on #11/#218/#230.
Defaults: heads 8/32/128, integer strides supplied-center-16 through center+16,
150 training rows and 150 test rows. All absolute r*S candidate blocks retain
exact capped-q moments, escapes, signed mean/SE and completeness. For each
head, the greatest defined signed training score selects a stride; ties in
the computed floating score select the lowest stride. Undefined scores cannot
win. The test begins at candidate ordinal ceil(rows*maxS/minS) for EVERY
stride, so its earliest token is at or beyond the latest token used by ANY
training candidate. Global endpoints and the intervening gap are explicit.
All candidate test cells are printed, but only training chooses the reported
selection. Candidate windows cover different token spans, and heads overlap;
this is an exploratory descriptive comparison, with no null or calibrated
significance. A boundary maximum cannot establish a global peak. Known-profile
reused files are not untouched confirmation. No phase adjustment, physical
rows, actual escape syntax, historical private-value reproduction or decoder
inference. Candidate unary-plus-five retains q>=17, caps q at 40, skips zero
extra escape bits. Every requested split must complete; any shortfall or
sanitized input failure returns nonzero while retaining all input identities.
Match supplied hashes to retained verified CC0 records; the tool checks local
SHA256 before TIFF parsing. Stdlib only; reads files/prints aggregate JSON.

    python -I -B tools/token_head_stride_probe.py --sample ID PUBLIC_NAME VERIFIED_SHA256 CENTER path/to/file.ORF
    python -I -B tools/test_token_head_stride_probe.py

**`e400_zero_low4_probe.py`** addresses #79's zero-low4 selection limitation
(Builds on #146/#190/#215/#261). It counts the entire stored-raster interior,
excluding two pixels at every edge, with diagonal-1 means at equal coordinate
parity and axial-2 elsewhere. All four parity strata retain zero/nonzero-low4
denominators, exact means, floor-only means and nonmatches. Zero-low4 exact
candidates also retain a 0..4 histogram of nonzero-low4 selected neighbours.
These are arithmetic candidates, not identified corrections: constant and
affine scenes can satisfy all equalities without any mapping operation.
No camera mechanism, processing order, sensor values, significance, finding
or decoder change follows. Reuse retained CC0 provenance after local hash
matching; the required hash is checked before TIFF parsing. Stdlib only,
read-only packed16 strips, aggregate JSON, sanitized failures return 1.

    python -I -B tools/e400_zero_low4_probe.py FILE2151 --sha256 VERIFIED_SHA256
    python -I -B tools/test_e400_zero_low4_probe.py

**`payload_band_lag.py`** adds parser-independent raw-bit lag screening for
#296 (Builds on #144/#29/#30). It checks a required full-file SHA-256 before
reading a caller-declared contiguous payload extent. Supply ordered disjoint
byte-window starts and a frozen bit-lag grid. The first band selects the maximum
signed binary Pearson phi (lowest lag breaks exact ties); that lag is retained
unchanged on validation bands. Every lag cell retains exact pair/marginal/joint
counts. Absolute and payload-relative bit extents, uncovered bytes, all ties,
range-boundary winners and undefined constant windows are explicit. Each local
byte-shuffle replicate reruns the whole supplied lag search; maxima and the
frozen-lag scores are both printed. The null preserves each block's byte
histogram and within-byte structure, not arbitrary camera dependence. Results
are descriptive: sparse windows, coarse grids, overlapping pairs, no calibrated
p-values, no phase/change-point model, and no physical-row or decoder claim.
Establish the extent and retained CC0 provenance separately; a hash proves
identity, not licence. Stdlib CPU only; aggregate JSON and sanitized failures.

    python -I -B tools/payload_band_lag.py FILE --sha256 HASH --sample-id ID --sample-name PUBLIC_NAME --offset OFFSET --length LENGTH --starts 0 START2 START3 --window-bytes 65536 --lag-min 32768 --lag-max 65536 --lag-step 1024
    python -I -B tools/test_payload_band_lag.py

**`sensor_rejection_controls.py`** is a synthetic-only rejection-control
baseline for research plan #301. It prints exact aggregate range, lag-2,
coordinate-parity-lane and fixed-central-seam counts, with scalar features.
Development maxima from smooth, checker-textured and dark toy controls at two
noise scales define an illustrative upper-envelope rule; new seeds from the
same families receive full per-trial and scene/noise/mapping confusion reports.
The non-identity mappings are reversible by construction, not empirically
impossible sensor arrays. Complement can retain every feature, and valid toy
controls can exceed development maxima. With the strict binary64 comparison,
one of the 31 development non-identity rejections is a rounding-level tie
(lane spread exceeds its limit by about 4.55e-13), not discriminating evidence.
No universal thresholds, held-out scene/body validation, V0/ORF evidence,
effective precision, black level, CFA
or sensor truth is established. No files are read or written. CPU stdlib only;
`--benchmark` optionally includes experiment wall time, excluding JSON output.

    python -I -B tools/sensor_rejection_controls.py
    python -I -B tools/test_sensor_rejection_controls.py

**`cohort_design_audit.py`** supports #299/#318 with exact categorical design
rank, nullspace and conditional rank increments over explicit public manifest
IDs. The recorded mode is a width proxy; algebraic support does not establish
independent captures or causal effects. No raw files are read.

    python -I -B tools/cohort_design_audit.py --manifest samples/manifest.csv --ids 1993 1994 1995 1996
    python -I -B tools/test_cohort_design_audit.py

**`capture_metadata_audit.py`** supports #318's capture-group metadata question.
It checks every input hash and CC0 licence against retained records before
reading metadata, then reports model/time availability and repeated groups
without printing timestamps or local paths. Matching make, model and recorded
second does not establish the same physical camera or independent captures.
Timezone, subseconds and clock accuracy are not evaluated.

    python -I -B tools/capture_metadata_audit.py --licence-records RECORDS.json --sample ID PATH
    python -I -B tools/test_capture_metadata_audit.py

Repeat `--sample ID PATH` for each public sample in the declared cohort.

**`payload_feature_probe.py`** supports #299 with fixed raw-bit windows and
aggregate density, transitions, byte entropy and run spectra. Schema v2 follows
TIFF strip-table order, excludes physical gaps and explicitly omits planned
cross-strip windows without replacement, including adjacent strips. Zero usable
windows are reported, not replaced. This does not assign variants or clusters.
Match supplied hashes to retained CC0 records before using any sample tool.

    python -I -B tools/payload_feature_probe.py --sample ID PUBLIC_NAME VERIFIED_SHA256 FILE --window-bytes 65536 --windows 3
    python -I -B tools/test_payload_feature_probe.py

**`body_label_holdout.py`** supports #299/#329 using the aggregate feature
report and public manifest. File-held-out body centroids compare bitrate,
raw-bit means and their union with training-fold scaling; every fold and
failure remains visible. File holdout is not capture/scene holdout, causal
attribution or variant discovery. No raw files are read by this diagnostic.

    python -I -B tools/body_label_holdout.py --features FEATURES_JSON --manifest samples/manifest.csv --ids ID_A ID_B ID_C
    python -I -B tools/test_body_label_holdout.py

**`run_reorder_search.py`** supports #322 and the closed #297 protocol with a
complete frozen width/phase/window search under run-order surrogates. Exact
global run multisets, endpoints, density and transitions are preserved; local
window density and byte histograms are not. Complete candidate/maxima ledgers,
ties and boundary winners remain visible. Surrogate tail diagnostics do not
establish camera exchangeability, significance or framing.

    python -I -B tools/run_reorder_search.py --sample ID PUBLIC_NAME VERIFIED_SHA256 FILE
    python -I -B tools/test_run_reorder_search.py

**`synthetic_adaptive_resync.py`** supports #300 with original state-dependent
Rice grammars, explicit edit coordinates, incomplete tails and censored
recovery. State selects k injectively, so aligned-interval state/value equality
and coincident boundary/state recovery follow structurally. No camera inference,
generator classifier or matched null is supplied.

    python -I -B tools/synthetic_adaptive_resync.py --self-test
    python -I -B tools/synthetic_adaptive_resync.py

**`v0_sensor_controls.py`** supports #301/#325 with fixed packed-16 V0 windows
and the unchanged synthetic rejection envelope. Stored words are separate and
unclassified; floor(word/16) is an explicit diagnostic scale assumption. Both
identity rejection and nonidentity acceptance are retained. General layout
selectors, physical precision, black level, CFA and sensor truth remain open.

    python -I -B tools/v0_sensor_controls.py --sample ID PUBLIC_NAME VERIFIED_SHA256 FILE
    python -I -B tools/test_v0_sensor_controls.py

**`frozen_bit_context.py`** supports #298/#332 with discovery-selected binary
contexts, quantized probabilities, explicit model cost and file holdout. It
prints the complete order ledger and exact-count shuffled-bit control. Scores
are normalized predictive log loss plus parameter cost; no serialized coder,
framing/termination/padding cost, round trip or reconstruction is implemented.

    python -I -B tools/frozen_bit_context.py --manifest samples/manifest.csv --discovery DISCOVERY_FILE --validation VALIDATION_FILE
    python -I -B tools/test_frozen_bit_context.py

**`frozen_context_calibration.py`** tests a fixed seven-point odds calibration
of frozen order-0 and order-8 models on disjoint per-file windows. It reports
all calibration candidates and heldout scores with equal three-bit index costs;
calibration data transmission is excluded, and scores are not a codec.
Inputs require retained CC0 provenance matched by local hash and manifest.

    python -I -B tools/frozen_context_calibration.py --manifest samples/manifest.csv --discovery FILE1993 FILE1995 --validation FILE
    python -I -B tools/test_frozen_context_calibration.py

### `patent_capped_prefix_probe.py`

Tests two fixed source-grounded hypotheses from [US7259698B2](https://patents.google.com/patent/US7259698B2/en), not an identified ORF codec. `--width 15` uses the patent example D=15, k=5 and maximum prefix 12, with a 47-zero/one marker at payload bit zero. `--width 12` is a post-hoc exploratory D=12 choice with a 39-zero/one marker. The marker ends at the one; a capped escape is 12 zero bits followed by D value bits, with upper D-5 bits at least 12. Marker mismatch, invalid escape, incomplete terminal word and a user-selected `--max-words` limit are reported separately, with the stop bit and invalid escape value when present. This is a one-sided test of a single uninterrupted block: absence of an invalid escape does not establish the grammar, because random streams can also pass. An interior marker or adaptation could explain a failure of this restricted hypothesis. No interior marker, resynchronization, terminal fill, adaptive parameters or physical rows are inferred. `--tail-shuffle --seed 20261022` preserves the first five (D=12) or six (D=15) bytes and shuffles the entire remainder with a fresh RNG; the measured payload hash and mode are reported. This is a descriptive control, not a calibrated grammar null. `--sample PUBLIC_ID PUBLIC_NAME SHA256 PATH` checks a single local snapshot against its expected hash; establish the public identity and CC0 permission independently before use. Results are aggregate metadata only.

### `patent_adaptive_state_probe.py`

Synthetic-only perturbation control for #300, using the example threshold/run-state update in [US7715639B2](https://patents.google.com/patent/US7715639B2/en). Supplied conventions are k=5 startup, bit_length(0)=0, known line length and ordinary uncapped Rice serialization; no ORF side-bit placement, predictor, capped escape or physical rows are assumed. It compares each adaptive64, fixed5 and wrong-reset32 parse to its own unedited baseline, and separately compares generated real streams to the adaptive64 generator's unedited parse. Shuffled controls have no generator-truth reference. Wrong-reset and generating parsers have different transition laws, so finite state matches do not prove equivalent behavior. It reports mapped boundaries, decision-state matches (N/A for fixed5), comparable values strictly after the edit, incomplete tails and separate boundary-only and full-state finite-window suffix-stable recovery. For a complete matching span wholly in the unchanged post-edit region, identical bits and endpoints force the same Rice value: the first stop fixes q and the remaining span length fixes k. Zero value mismatches therefore check this structural invariant, not independent value or state recovery; zero comparable spans are vacuous. Both recovery metrics require bidirectional boundary agreement and the stated exposure; full-state recovery additionally requires every corresponding state to match (N/A for fixed5); it does not require matching values or establish permanent recovery. Under the supplied equal initial state at a common 64-word reset boundary, the 32- and 64-word laws use identical state transitions until the shorter reset: encoded words 1 through 32 therefore match for any common magnitude sequence. By induction, each pre-reset update is identical when the prior magnitude and state are identical. The internal phase differs after word 32; that phase is not itself an observed bitstream symbol. The reset period and transition law are fixed external context alongside the mutable state; an equal mutable tuple alone does not make different laws equivalent. For repeated magnitude 3, the next k values are 5 and 2 respectively and word 33 differs; other continuations need not reveal the mismatch immediately. This is a property of these synthetic conventions, not a general patent or ORF claim. A separate supplied-history example shows a limitation of full-state comparisons: starting at phase 0 versus after one value-16 word, a common suffix of value 16 has identical words and k/runs while its phase offset persists through resets. This is a whole-word history difference, not an outcome of the frozen single-bit edit trials. RNG seeds, distributions, edits and windows are frozen in the tool and #300 protocol. This is not a camera codec test or significance calculation. Run `python -I -B tools/patent_adaptive_state_probe.py --split discovery` or `--split validation` for separately selected aggregate JSON and `python -I -B tools/test_patent_adaptive_state_probe.py` for the synthetic fixtures.
