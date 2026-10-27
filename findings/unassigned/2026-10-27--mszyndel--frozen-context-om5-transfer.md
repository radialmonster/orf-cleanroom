# Frozen contexts reproduce the OM-5 transfer result on one window

Author: @mszyndel
Verified by: @radialmonster
Lead: #362
Variant: unassigned
Builds on: #332, 2026-10-26--radialmonster--frozen-context-cohort-reproduction
Partial: Reproduces the reported id 6343 window and extends the fixed model to the two predeclared files and disjoint windows; codec, physical reconstruction and general transfer remain open.

## Claim

The original one-window score for OM-5 id 6343 reproduces: the frozen order-8 score exceeds the order-0 score and is lower than its exact-count shuffled control. Further predeclared windows show mixed order-8 versus order-0 results. These are predictive negative log likelihoods plus model costs, not serialized sizes or a codec.

## Original evidence

Lead #362 used `tools/frozen_bit_context.py` at `4aa4d8067994d0e233443b5bb6886e31d0e7390b`, discovery ids 1993 and 1995 at logical-strip byte 65536 and validation id 6343 at byte 65536, with 65536 bytes per window. It reported order 0 at 524344.8533856651 bits, order 8 at 540436.5321042684, and the shuffled order-8 control at 581747.1436578293. Its selected order-8 discovery table SHA-256 is `1f395ec3446c96b3c7415e2ff5e6d11ad79684695410315132a1e19584bbdc71`.

## Verification

After the lead was posted, I froze the design in issue comment 6444775912 and ran the original validation window plus all six file/offset combinations below. This includes new public validation files 6344 and 5283 and a disjoint second band on each file. Discovery remains ids 1993 and 1995 at byte 65536. Each validation file and offset is a separate report with its own model charge; 65536 bytes, orders 0–8 and seed 298 are unchanged. Order 8 was selected from discovery in every report and its discovery-table hash matched the lead. The original three scores matched exactly in this run, within the declared 1e-7-bit tolerance. No validation-based selection was performed. Both probability tables, including the order-0 density baseline, are fitted on discovery alone. Each report charges 3076 bits for order 8 and 16 bits for order 0.

| Public ID | Validation byte offset | Order 0, bits | Order 8, bits | Shuffled order 8, bits |
| --- | ---: | ---: | ---: | ---: |
| 6343 | 65536 | 524344.8533856651 | 540436.5321042684 | 581747.1436578293 |
| 6343 | 131072 | 524327.3141966385 | 540189.0890900982 | 581620.5174105016 |
| 6344 | 65536 | 523924.5440794801 | 497053.1526807098 | 586954.7647631376 |
| 6344 | 131072 | 523934.5986788450 | 497825.4261775054 | 586553.2059735665 |
| 5283 | 65536 | 523979.6865683735 | 576431.6212291418 | 585432.2618778407 |
| 5283 | 131072 | 524039.3829341093 | 575133.0516278360 | 585655.2395634482 |

The added OM-5 file reverses the original order-8 versus order-0 comparison; these selected files and windows do not establish a general body, capture or scene effect. The shuffle is one deterministic exact-count control, not calibrated significance. No grammar, reconstruction, actual coding size or round trip is established.

All inputs are public CC0; local hashes matched retained verification records and existing manifest rows. Public identity and SHA-256:

- 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` (discovery)
- 1995, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` (discovery)
- 6343, `OM System - OM-5 - 16bit (4:3).ORF`, `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`
- 6344, `OM System - OM-5 - 16bit (4:3).ORF`, `42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512`
- 5283, `OM System - OM-1 - 16bit (4:3).ORF`, `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`


A separate maintainer run reproduced all six reports. A separately structured numerical reference counted contexts with padded binary-string slices and rounded exact Fraction probabilities, matching all nine discovery-table hashes exactly and all 162 discovery/validation/shuffle scores within 1e-7 bit. The original and new reports contain 524288 validation bits each. Counts and quantization use exact integers; likelihoods use binary64 log2 and summation. Terra and its supervisor both act for verifier @radialmonster; those two runs are not independent human verifications of one another. Lead author @mszyndel is a different contributor.

## Reproduce

With the five locally retained hash-matched CC0 files, use the repository at `3ea12f2c65ad138fc031656b0dca747cd20e681e` (tool last changed `2f97969e7e7c21018a442002adfa049d64a7cc52`). The tool SHA-256 is `c510539104cbe6fb2260c58e35a8772970d4091755232d77745f3c4be034270c`. Substitute each local file path for the corresponding variable below; no new catalogue check is needed for these retained exact hashes.

    python -I -B tools/test_frozen_bit_context.py
    python -I -B tools/frozen_bit_context.py --manifest samples/manifest.csv --offset 65536 --validation-offset OFFSET --bytes 65536 --discovery ID1993_FILE ID1995_FILE --validation VALIDATION_FILE

Run the second command six times, once for each row in the table, setting `OFFSET` and `VALIDATION_FILE` to that row. All commands read inputs and print aggregate results; paths above are placeholders, not literal shell variables. The test suite passed 15 tests. Per-report tool CPU times were 1.39–1.41 seconds in this run; peak memory was not measured.
