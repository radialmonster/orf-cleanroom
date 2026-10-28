# Synthetic adaptive-state recovery differs from fixed-k self recovery

Author: @radialmonster
Verified by: @radialmonster
Lead: #610
Variant: unassigned
Builds on: #300, #330, #337, #609

## Claim

In the frozen synthetic discovery set, fixed5 has finite-window boundary suffix stability in 35/36 real-stream trials against its own unedited baseline, but 0/36 against adaptive64 generator truth. This distinction concerns only the stated synthetic inputs and finite-window metrics; it does not identify camera framing or guarantee permanent synchronization.

## Original evidence

The lead fixed discovery seeds 400..403, four 256-magnitude uniform 0..31 source streams and their bit-shuffled controls, three parser laws, three edits, three anchors and 128-bit original windows: 216 trials. Startup k=5, zero bit-length zero and 64-symbol line-reset timing are supplied synthetic conventions. The state update uses the example threshold/run structure in US7715639B2; no predictor filter, sign/low-bit packing, capped escape or camera sample is modeled. The independently written parser, coordinate mapping and state arithmetic matched all discovery fields.

## Verification

A fresh post-lead discovery run exactly reproduced all 216 records. The predeclared separate validation distribution, seeds 500..507, generated eight new synthetic source streams and their eight controls after the lead, yielding 432 further trials. These are new synthetic input files, not new camera files, bodies, captures or independent human verification. The separate independent implementation matched all 648 records, identities and fields. Both implementations assisted the same human.

All records have a full 128-bit observation window; there were no short windows. Tables report suffix-stable boundary/state successes over the fixed group denominator (36 discovery, 72 validation); all other outcomes for a defined metric are censored. State is N/A for fixed5; generator truth is N/A for shuffled streams. Self-baseline compares unedited and edited parses of the same law. Truth compares the edited parse with the unedited adaptive64 generating parse. A state match across adaptive32 and adaptive64 is a finite observation under different transition laws, not proof they are equivalent.

| Split | Stream | Parser | Self boundary | Self state | Truth boundary | Truth state |
|---|---|---|---|---|---|---|
| discovery | real | adaptive64 | 8/36 | 8/36 | 8/36 | 8/36 |
| discovery | real | adaptive32 | 9/36 | 8/36 | 6/36 | 4/36 |
| discovery | real | fixed5 | 35/36 | N/A | 0/36 | N/A |
| discovery | shuffle | adaptive64 | 12/36 | 11/36 | N/A | N/A |
| discovery | shuffle | adaptive32 | 12/36 | 11/36 | N/A | N/A |
| discovery | shuffle | fixed5 | 35/36 | N/A | N/A | N/A |
| validation | real | adaptive64 | 20/72 | 20/72 | 20/72 | 20/72 |
| validation | real | adaptive32 | 20/72 | 20/72 | 20/72 | 12/72 |
| validation | real | fixed5 | 72/72 | N/A | 9/72 | N/A |
| validation | shuffle | adaptive64 | 25/72 | 23/72 | N/A | N/A |
| validation | shuffle | adaptive32 | 25/72 | 23/72 | N/A | N/A |
| validation | shuffle | fixed5 | 72/72 | N/A | N/A | N/A |

The held-out fixed5 result is 72/72 self boundary versus 9/72 truth boundary; the discovery zero does not generalize to this second synthetic distribution. Each success requires at least three subsequent completed words and 32 original bits, plus bidirectional mapped boundary equality through the finite window; state recovery additionally requires every corresponding decision state to match. These conditions do not require equal values. A suffix match does not prove permanent recovery.

Original/edited truncated-word counts are retained separately:

| Split | Stream | Parser | Original truncated | Edited truncated |
|---|---|---|---|---|
| discovery | real | adaptive64 | 33/36 | 32/36 |
| discovery | real | adaptive32 | 30/36 | 31/36 |
| discovery | real | fixed5 | 27/36 | 27/36 |
| discovery | shuffle | adaptive64 | 36/36 | 36/36 |
| discovery | shuffle | adaptive32 | 36/36 | 36/36 |
| discovery | shuffle | fixed5 | 33/36 | 33/36 |
| validation | real | adaptive64 | 57/72 | 64/72 |
| validation | real | adaptive32 | 57/72 | 64/72 |
| validation | real | fixed5 | 63/72 | 63/72 |
| validation | shuffle | adaptive64 | 63/72 | 68/72 |
| validation | shuffle | adaptive32 | 63/72 | 68/72 |
| validation | shuffle | fixed5 | 57/72 | 57/72 |

Comparable real-stream values use only identical spans wholly after the edit. Zero mismatches occurred among the following comparison counts; unmatched spans are not evidence of value agreement.

| Split | Parser | Reference | Comparable values | Mismatches |
|---|---|---|---:|---:|
| discovery | adaptive64 | self_baseline | 171 | 0 |
| discovery | adaptive64 | truth_reference | 171 | 0 |
| discovery | adaptive32 | self_baseline | 179 | 0 |
| discovery | adaptive32 | truth_reference | 158 | 0 |
| discovery | fixed5 | self_baseline | 504 | 0 |
| discovery | fixed5 | truth_reference | 155 | 0 |
| validation | adaptive64 | self_baseline | 426 | 0 |
| validation | adaptive64 | truth_reference | 426 | 0 |
| validation | adaptive32 | self_baseline | 426 | 0 |
| validation | adaptive32 | truth_reference | 426 | 0 |
| validation | fixed5 | self_baseline | 1131 | 0 |
| validation | fixed5 | truth_reference | 447 | 0 |

The 24 generated bitstrings were saved after the lead under scratch with this identity ledger. Hashes are SHA-256 of ASCII `0`/`1` bitstrings; the paired counts are bit length / ones. Python `3.14.7` and source SHA-256 `e663f001dd122ae09c2c0f30efe5381cbbbd2e5444a17b4844ba4913aa592de7` were used. These are public reproducible synthetic inputs, not sample-derived arrays or pixel data.

| Split | Seed | Real bits/ones | Real SHA-256 | Shuffle bits/ones | Shuffle SHA-256 |
|---|---:|---:|---|---:|---|
| discovery | 400 | 1509/844 | `99b69609c9c4f59747ded2365c02ed234f2acc11de706129c7dba38e8ff0fcbf` | 1509/844 | `908420c62815d3e30934dfc0286dc025ab0ab6852a05a5e5e3ea78403ba69c3b` |
| discovery | 401 | 1501/864 | `9cfc7692bb127c81755df1d06616782036dee9aa23a1808e330b17856aca485d` | 1501/864 | `054164f367c7efcee9d4941d6b534274cdade979baeb11c28312a9a0bbbdb481` |
| discovery | 402 | 1516/894 | `8d28c6cb42af7a97e7d8d9b42ec000259cad4ba71de1255c21d5c1db3db64b00` | 1516/894 | `6d2a4ab9d081107f8ea8e6ef52b4c6a4442f435b48f0f3cdc546d2112574a94b` |
| discovery | 403 | 1517/851 | `52360cc4ebdbec60c22251563fba04b180dca523feb20c8c0bbfd7892a1813e1` | 1517/851 | `d9dc142cf0e06d036e23e8c1f9571a940cd11d0bfb27c2f87e8d1cc225befd0a` |
| validation | 500 | 1552/723 | `e7b27fd49eaa8553a50c9f33c8ab1288ee6c433f377d93597272006acabc7d1a` | 1552/723 | `260ad7b8c497e9934b044fe649b9ed09de01ad455c7ae4a583a329a770651ce7` |
| validation | 501 | 1506/699 | `bafb630092164440400d051e4fd0a29bee76d78789afce1f68244c6e2420550d` | 1506/699 | `62b7ec6a8667bd72e82aac8b3aded9980e3dd90a8b7b6723c0017664b18623cb` |
| validation | 502 | 1553/772 | `2df186ead979db6f4fe9f90dec30aae2f50bfa68e9809a1c780b555dc01db799` | 1553/772 | `4319dc4f2a1f0a3ca4c00d439307521412fc628dd2dad75988c1232a18a144a0` |
| validation | 503 | 1454/677 | `abfdd8d1630010a8f037d5636da3936686fe4da63587ef46e3ce3c1aa368f1e9` | 1454/677 | `4f2ae351c8204aa06038c94f655e22f6f625a8ef698ea78d2fb02be1a88126a3` |
| validation | 504 | 1531/770 | `735a2e6b2c88c452fcd5b2bd0dc13b7b55e2cb1c8ce3f86010efec9329b6cd54` | 1531/770 | `426e84951f5deea4be2bed3df6a4825cddfa29427e0d45223a50fa8d577c4a4f` |
| validation | 505 | 1532/696 | `f4f8d19184e97af5a4fc85f4d019ea3b3aa91d39042a6438f23cc2ded9dfaf67` | 1532/696 | `745732786cf5f7cb1c59747de240fbd67e1aa6af40cae2defd4fbad5d9fa27a6` |
| validation | 506 | 1449/653 | `5f869ff7977df4d11e44f1e6325eaa8976edb9ee11c201a92fc9603504df3dfc` | 1449/653 | `8503d17e2949958a7da381595fd53cc88e20235514540c584e863d2e0fca1754` |
| validation | 507 | 1517/725 | `060865beda160abefc883686ccfb2d4d74ed549416f17ddd49fac6da3152c270` | 1517/725 | `75a44a9044d46d6534fc0ca5e9f72d04e4f4a1c274e2ba7bdc989ca27b8556b7` |

The discovery distribution draws each magnitude uniformly in 0..31. Validation selects a low (0..3) or high (16..31) range by a random bit, then draws within it. Both use `random.Random(seed)`; each bit-shuffle resets `random.Random(seed+10000)`. These two distributions and seeds were frozen before discovery, not sampled independent camera scenes. No significance or codec inference follows.

## Reproduce

At commit 480edb0468204e0f1a5071339838e5292350428d, run:

```text
python -I -B tools/patent_adaptive_state_probe.py --split discovery
```

Aggregate JSON includes every trial, both censor flags, tail lengths, state hits and value comparisons. After the lead, run the separately held-out validation split with `python -I -B tools/patent_adaptive_state_probe.py --split validation`.
