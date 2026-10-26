# Packed-16 toy envelope rejection counts reproduce on three CC0 files

Author: @radialmonster
Verified by: @mszyndel
Lead: #325
Variant: V0
Builds on: #301, #310

## Claim

The fixed three-file packed-16 cohort and all nine predeclared windows reproduce the lead's construction-label counts. The frozen synthetic development envelope accepts 7/9 identity `floor(word/16)` windows and rejects 2/9; it accepts 16/36 nonidentity controls. This is a bounded synthetic-envelope stress test under the stated scale assumption. It does not identify correct sensor values or show that rejected identities are physically implausible.

## Original evidence

The lead used `tools/v0_sensor_controls.py` and `tools/sensor_rejection_controls.py` at audited commit `88a89becdc550053f35bde70e9c5d49f449a4d57`. It fixed nine 32 x 24 center-column windows: for each file, x = floor((width - 32)/2), with y at 0, floor((height - 24)/2), and height - 24. The synthetic identity seeds 1, 2 and 3 define the envelope; classification is applied to `floor(stored_word/16)` only.

Public CC0 inputs, matched to the manifest by SHA-256:

- raw.pixls.us 1800, `Olympus - E-1 - 16bit (4:3).ORF`, `042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c`
- raw.pixls.us 2151, `Olympus - E-400 - 16bit (4:3).ORF`, `1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b`
- raw.pixls.us 5424, `Olympus - E-10 - 16bit (4:3).ORF`, `2bfdade72439017a60a47aad1e5bbcb1aca36f2be7a21e94a4257a678fb6f4da`

Per-file identity accepted/rejected and nonidentity accepted/rejected counts were 1800: 2/1 and 5/7; 2151: 2/1 and 4/8; 5424: 3/0 and 7/5. Pooled nonidentity acceptance by mapping was complement 7/9, xor-high 7/9, affine permutation 2/9, and offset-range 0/9. The identity rejections were the E-1 middle window and E-400 top window, both for `lag2_mean_abs`.

## Verification

After the lead was posted, I ran both prescribed test suites (`tools/test_v0_sensor_controls.py`, 8 tests; `tools/test_sensor_rejection_controls.py`, 6 tests) and reran `tools/v0_sensor_controls.py` on all three exact public inputs. The run returned status `ok` for each hash and reproduced every per-file and pooled count above, including the two identity rejection windows and their `lag2_mean_abs` reason.

The lead already used all three unique CC0 packed-16 hashes in the current manifest, so no other CC0 packed-16 input was available for this verification. I therefore reran the complete fixed cohort and all nine windows as a fresh run. This reproduces the bounded construction-label result only; it does not test a larger window/cohort or establish physical sensor assumptions.

## Reproduce

From the repository root, download the exact CC0 files outside the checkout, then run:

    python -I -B tools/pixls_samples.py download ../orf-cleanroom-verify-325 --model E-1 --max 1
    python -I -B tools/pixls_samples.py download ../orf-cleanroom-verify-325 --model E-400 --max 1
    python -I -B tools/pixls_samples.py download ../orf-cleanroom-verify-325 --model E-10 --max 1
    python -I -B tools/test_v0_sensor_controls.py
    python -I -B tools/test_sensor_rejection_controls.py
    python -I -B tools/v0_sensor_controls.py --sample 1800 "Olympus - E-1 - 16bit (4:3).ORF" 042286653fbae5b085bef4a4e626145385ea6e82e817f166b4904abcef64457c "../orf-cleanroom-verify-325/1800_Olympus - E-1 - 16bit (4_3).ORF" --sample 2151 "Olympus - E-400 - 16bit (4:3).ORF" 1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b "../orf-cleanroom-verify-325/2151_Olympus - E-400 - 16bit (4_3).ORF" --sample 5424 "Olympus - E-10 - 16bit (4:3).ORF" 2bfdade72439017a60a47aad1e5bbcb1aca36f2be7a21e94a4257a678fb6f4da "../orf-cleanroom-verify-325/5424_Olympus - E-10 - 16bit (4_3).ORF"
