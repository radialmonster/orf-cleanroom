# Learned suffix-table vertical-shift sensitivity

Author: @radialmonster
Verified by: @ruedbi
Lead: #803
Variant: unassigned
Builds on: #155, #351, 2026-11-04--radialmonster--suffix-luma-table-weak-transfer
Reproduces: 2026-11-17--radialmonster--learned-suffix-table-vertical-shifts
Partial: vertical-shift sensitivity on public CC0 targets 1997 and 1998 with 1995 training; other targets and horizontal axis not re-run.

## Claim

The fixed #155 table's declared alignment ranks 2/46 on public CC0 targets 1997 and 1998 (trained on 1995), so neither meets the unique-positive-maximum criterion (operationally_specific = false). Best shifts are k=45 on 1997 and k=1 on 1998.

## Original evidence

Lead #803 trained on public CC0 1995 (`Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`) and tested 1997 and 1998 using `tools/suffix_table_shift_probe.py` at commit `027ee79787ba02c95011338bfedbf6db7cc960c7`. Best shifts were 45 and 1, respectively, with ranks 2/46.

## Verification

Independent verification was conducted by @ruedbi on 2026-11-18 using Python standard library (Python 3.8+) and `tools/suffix_table_shift_probe.py`.

All 8 unit tests in `tools/test_suffix_table_shift_probe.py` passed.

A fresh rerun was performed with `--phase discovery` on targets 1997 and 1998 using 1995 as the training input:

- Training input 1995: 5240x3912, 600 candidate rows, preview 400x300, 46 used preview rows. 32-entry table weights hash (binary64 big-endian): `c7162dbb1376e8f8799dc717f3e93a51f65a38dbd80ca80065f2fbee402bda5f`.
- Target 1997 (`89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`):
  r(0) = 0.10555837065892783, best r = 0.10593632342207254 at shift k=45; zero_min_rank = 2/46, zero_ties = [0], operationally_specific = false.
- Target 1998 (`4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`):
  r(0) = 0.08531411752241273, best r = 0.08649043052126802 at shift k=1; zero_min_rank = 2/46, zero_ties = [0], operationally_specific = false.

All scores, ranks, best shifts, and table SHA-256 match the published finding exactly.

## Reproduce

Using standard library Python and `tools/suffix_table_shift_probe.py`:

```bash
python -I -B tools/test_suffix_table_shift_probe.py
python -I -B tools/suffix_table_shift_probe.py --phase discovery --train <path-to-1995> --sample 1997 <path-to-1997> --sample 1998 <path-to-1998>
```

Check that the output JSON matches the table weights hash, zero_r scores, best_shifts and zero_min_rank (2/46) above.
