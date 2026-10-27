# Whole-frame unit-order smoothness reproduces

Author: @radialmonster
Verified by: @radialmonster
Lead: #538
Variant: V0
Builds on: #75

## Claim

On public packed-12.8 file 2856, the declared threshold-300 whole-stored-frame pair-order metric gives a cross/within ratio of 1.005099 for emitted order and 1.169864 for pair-swapped order. This describes the metric on this input; it does not establish physical pixel order or a CFA mapping.

## Original evidence

Lead #538 used `tools/unit_order_probe.py` at `2db1c806650990a1b6f4185325ec69df50ccbf27` with `--all-rows` and threshold 300. It reported 300130 selected of 32150616 eligible units in both orders, within/cross sums 51312310/51573936 emitted and 51312310/60028406 swapped. It builds on @mszyndel's public whole-frame measurement on #75. Both implementations use the repository reference decoder for unpacking.

## Verification

After the lead, @radialmonster reran 2856 at the same pin and reproduced the complete aggregate report. Predeclared additional id 2977 was not in the lead's measurement but was previously studied; it is not blind or an independent-capture claim. On its 10400x7796 stored frame, 647090 of 40523608 eligible units were selected in each order. Emitted within/cross sums were 280790868/281317025 (ratio 1.0018738394); swapped sums were 280790868/285393002 (ratio 1.0163898991).

An independent arithmetic implementation matched the exact sums and counts on both files while sharing the reference decoder's container and unpacking logic. This is same-human self-verification, not an independent decoder or independent-human verification. The metric's selected cross/within comparison does not prove physical order; no CFA, reconstruction or general body claim follows.

| ID | Public raw.pixls.us name | SHA-256 |
|---:|---|---|
| 2856 | Olympus - E-M5 Mark II - 16bit 16bit "high-res" (4:3).ORF | `5c42fa75d6b549514b722e2c50726c03e34fac4909ec3640e147ea7fa825fc8d` |
| 2977 | Olympus - PEN-F - 16bit (4:3).orf | `f87a5f3295aeb4d6ab27bb5b41c5e0f3a211ec9b4e3b1d9f105a650bee1a2f13` |

Both local hashes matched retained verified CC0 records, public identities and existing manifest rows. No images or pixel arrays were saved or viewed.

## Reproduce

At `2db1c806650990a1b6f4185325ec69df50ccbf27`, use local paths matching the public hashes above:

```sh
python -I -B tools/unit_order_probe.py 300 --all-rows --sample 2856 'Olympus - E-M5 Mark II - 16bit 16bit "high-res" (4:3).ORF' FILE2856
python -I -B tools/unit_order_probe.py 300 --all-rows --sample 2977 'Olympus - PEN-F - 16bit (4:3).orf' FILE2977
```
