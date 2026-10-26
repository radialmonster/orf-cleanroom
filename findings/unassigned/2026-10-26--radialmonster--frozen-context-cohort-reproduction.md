# Frozen binary-context result reproduces on the original E-M1 Mark II cohort

Author: @radialmonster
Verified by: @mszyndel
Lead: #332
Variant: unassigned
Partial: Reproduces the named four-file E-M1 Mark II cohort only; broader body transfer and codec/reconstruction claims remain open.

## Claim

The frozen order-8 binary-context baseline and its held-out score reproduce on the four-file E-M1 Mark II cohort in lead #332. Order 8 is selected from discovery alone; on the two held-out files its score, including the shared model/order description, is 985091.174130 bits. The order-0 baseline scores 1048395.198878 bits, and the exact-count shuffled order-8 control scores 1163320.347624 bits.

This is normalized predictive negative log likelihood plus explicit parameter cost. It is not an encoded file size, a codec, or a reconstruction.

## Original evidence

Lead #332 reports `tools/frozen_bit_context.py` at `5bb9a1f3a12ba285319990b915d2dd3d823c507d`, with two discovery windows at logical strip byte 65536 and two held-out windows at the same offset; each window is 65536 bytes.

- 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` (discovery)
- 1995, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f` (discovery)
- 1997, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a` (validation)
- 1998, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71` (validation)

Reported order-8 discovery-table SHA-256: `1f395ec3446c96b3c7415e2ff5e6d11ad79684695410315132a1e19584bbdc71`. The held-out order-8 NLLs before the shared 3076-bit cost are 490890.016149 and 491125.157981 bits. Order 0 is 1048395.198878 bits; literal length is 1048576 bits.

## Verification

After lead #332 was posted, I ran the current `tools/test_frozen_bit_context.py` (11 tests passed) and reran the frozen measurement with the four exact public CC0 inputs above. The current tool is at commit `4aa4d8067994d0e233443b5bb6886e31d0e7390b`; its order-8 discovery-table hash is unchanged. It selected order 8 and produced 985091.1741296058 validation bits, 1048395.1988777125 order-0 bits, 1163320.3476243266 shuffled order-8 bits, and per-file order-8 NLLs 490890.0161489296 and 491125.1579806761. These reproduce the lead's printed values to its reported precision.

For the required new-body check, I also applied the unchanged discovery pair to a separate public OM-5 validation file (raw.pixls.us id 6343). That one-file transfer measurement is outside this finding's claim and is reported separately as an open lead. All files used here are public CC0 samples; their identities and hashes are listed above or in that lead.

## Reproduce

Download the CC0 files into a folder outside the repository, then run the tests and both measurements:

    python -I -B tools/pixls_samples.py download ../orf-cleanroom-verify-332 --model E-M1MarkII --max 6
    python -I -B tools/pixls_samples.py download ../orf-cleanroom-verify-332 --model OM-5 --max 1
    python -I -B tools/test_frozen_bit_context.py
    python -I -B tools/frozen_bit_context.py --manifest samples/manifest.csv --offset 65536 --bytes 65536 --discovery "../orf-cleanroom-verify-332/1993_Olympus - E-M1MarkII - 16bit (4_3).ORF" "../orf-cleanroom-verify-332/1995_Olympus - E-M1MarkII - 16bit (4_3).ORI" --validation "../orf-cleanroom-verify-332/1997_Olympus - E-M1MarkII - 16bit (4_3).ORI" "../orf-cleanroom-verify-332/1998_Olympus - E-M1MarkII - 16bit (4_3).ORF"
    python -I -B tools/frozen_bit_context.py --manifest samples/manifest.csv --offset 65536 --bytes 65536 --discovery "../orf-cleanroom-verify-332/1993_Olympus - E-M1MarkII - 16bit (4_3).ORF" "../orf-cleanroom-verify-332/1995_Olympus - E-M1MarkII - 16bit (4_3).ORI" --validation "../orf-cleanroom-verify-332/6343_OM System - OM-5 - 16bit (4_3).ORF"
