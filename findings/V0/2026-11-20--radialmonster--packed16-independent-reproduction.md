# Independent reproduction of packed-16 whole-frame word layout

Author: @radialmonster
Verified by: @mszyndel
Lead: #71
Variant: V0
Reproduces: 2026-10-21--radialmonster--packed16-whole-frame-word-layout
Builds on: #75, 2026-10-20--radialmonster--e400-low-nibble-floor-mean-interpolation, 2026-10-21--radialmonster--iiro-packed12-and-packed16-whole-frame-byte-order

## Claim

On all three public packed-16 files, the complete declared-strip payload is width*height*2 bytes and has contiguous strips/rows. Whole-frame smoothness chooses LE for E-1/E-400 and BE for E-10, matching their II/II/MM marks. Nonzero low-nibble word counts are 0, 793, 0. Every published whole-frame score, margin and explicit stride value reproduces at printed precision. All three full reference conformance rows, including unshifted output hashes and exact ends, match.

The E-400 exceptions are retained as stored words; this does not independently test their physical cause or the separate neighbour-interpolation finding. The three-file byte-order agreement is not proof of a general selector or a new-body rule, and black level/saturation remains open.

## Original evidence

Lead #71 and the reproduced whole-frame finding were authored by @radialmonster. The latter's exact read-only packed16_whole.py is inline in its Reproduce section, present at source snapshot 46345de1b93f6384616a362485f2e2b76bf9732e (finding file last changed in 461c7a41cc0769253f760694147f257b384529bd). The extracted script SHA-256 is `d915eca8c16b305434a0ee81df0321f33617258756d2600d26d3322838b88417`. It uses only the repository TIFF helper and stdlib, concatenates declared strips in table order, scores both orders over every row and repeats the chosen order at five stride deltas. It does not use decoder/ for those measurements.

Public raw.pixls.us identities and retained verified-CC0 hashes:

- 1800: `Olympus - E-1 - 16bit (4:3).ORF`, SHA-256 `042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c`.
- 2151: `Olympus - E-400 - 16bit (4:3).ORF`, SHA-256 `1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b`.
- 5424: `Olympus - E-10 - 16bit (4:3).ORF`, SHA-256 `2bfdade72439017a60a47aad1e5bbcb1aca36f2be7a21e94a4257a678fb6f4da`.

## Verification

Fresh runs by @mszyndel on 2026-11-20 UTC followed the fixed plan in #71 comment 7046789154. Every download matched the retained verified CC0 content hash. The complete retained 104-file CC0 inventory has exactly these three recorded packed-16 inputs; the original finding already used all three, so no unused applicable public input exists in that inventory. This is a new contributor's full-frame reproduction on the same captures, not a new body, scene or blind cohort.

The unchanged inline script reproduced the complete table:

| ID | Strips/gaps | Payload bytes | Words | Nonzero low nibble | LE score | BE score | Chosen/mark | Margin |
|---|---|---|---|---|---|---|---|---|
| 1800 | 16/0 | 10317568 | 5158784 | 0 | 0.12640 | 1.41385 | LE/II | 11.185 |
| 2151 | 89/0 | 21402240 | 10701120 | 793 | 0.07800 | 1.40865 | LE/II | 18.059 |
| 5424 | 15/0 | 7598208 | 3799104 | 0 | 1.66098 | 0.09016 | BE/MM | 18.422 |

The chosen-order vertical roughness at each explicit row-stride delta, in bytes, also matches:

| ID | delta -2 | delta -1 | delta 0 | delta +1 | delta +2 |
|---|---|---|---|---|---|
| 1800 | 0.0781 | 0.6409 | 0.0643 | 0.6423 | 0.0785 |
| 2151 | 0.0460 | 0.6632 | 0.0388 | 0.6628 | 0.0452 |
| 5424 | 0.0566 | 0.7526 | 0.0457 | 0.7456 | 0.0541 |

The baseline measure covers every row. Shifted-stride comparisons retain the published script's rule of skipping a row whose complete extent would be outside the payload; they are not asserted to cover an equal set of physical rows. A one-byte shift is much rougher; a two-byte shift remains smoother on these files.

Auxiliary default-window runs with the reviewed a4bf2af4b6a9036ae0c90936f4e8080520fb5f77 orf_v0_unpack.py snapshot reproduce u16-le/u16-le/u16-be and the original margins 6.58/16.28/18.59. Those window scores use a different normalization than the whole-frame script and are not compared as identical measures.

At source snapshot 46345de1b93f6384616a362485f2e2b76bf9732e, tools/conformance.py --csv with the existing reference decoder reproduces every field of all three matching samples/conformance-V0.csv rows. Output SHA-256 is over stored uint16 words, little-endian for hashing, row-major and unshifted, preserving the 793 E-400 low-nibble exceptions:

- 1800: `63c910928a97106d8102f571d4a52ee6f044088e4a6e8ab9bbbbf78bdf31018d`.
- 2151: `90bc69a504e06a54fc5635581e16320417b9fdd9ace3cd2e283f2247834e9d0c`.
- 5424: `b05f48502e9ff5107ac93f72478d7d52092e5f389d1025ad25576c664761ca47`.

All nine jobs exited zero with no timeout (600 seconds per whole-frame input; 300 per default/conformance run). Measurement stderr was empty; conformance emitted its normal zero-error summary. Input hashes matched before and after each file's runs. No decoded values, images or previews were saved. This shares the published tools/locator and uses the existing reference decoder; it is not an independently written decoder or independent physical evidence. The private-pool extension mentioned on #71 was not measured and contributes no result here.

## Reproduce

Read the original finding's complete inline script and its repository import, then save the reviewed script as packed16_whole.py in scratch. At source snapshot 46345de1b93f6384616a362485f2e2b76bf9732e, with the three exact hash-matched CC0 inputs:

    python -I -B packed16_whole.py FILE1800 FILE2151 FILE5424
    python -I -B tools/conformance.py --csv FILE1800 FILE2151 FILE5424

For the auxiliary original-window comparison, use a4bf2af4b6a9036ae0c90936f4e8080520fb5f77:

    python -I -B tools/orf_v0_unpack.py FILE1800 FILE2151 FILE5424

The local run used separate per-file invocations to enforce the stated budgets and retain stdout/stderr/exits. Compare every explicitly labelled order/stride value and complete conformance row by input hash; do not shift the stored E-400 words. Preserve failures/timeouts as unknown without choosing a replacement file or adapting the measure. All numbers use public CC0 files; no result depends on private inputs. V0 G2/G7 retain general byte-order/new-body and black-level/saturation questions.
