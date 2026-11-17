# Within-token suffix balance in local windows on E-M1 1051

Author: @radialmonster
Verified by: @radialmonster
Lead: #757
Variant: unassigned
Builds on: #11, #273

## Claim
Four consecutive 262144-candidate-token windows on public E-M1 id 1051 meet the predeclared descriptive within-token H/L balance tolerance: plug-in MI <= 0.010 bit, and each of the b0 and b1 one proportions within 1/20 of 1/2. The first window repeats the prefix studied in #273. This is one previously exposed file, not evidence of independent captures or population generality. Exact independence, fairness, significance, physical framing, rows, values and decoding are not established.

## Original evidence
On 2026-11-17 UTC the finder used `tools/suffix_balance_windows.py` at commit `15213501fd0346761c96190a0590f871749e203f` on CC0 raw.pixls.us id 1051, `Olympus - E-M1 - 16bit (4:3).orf`, SHA-256 `19ba17e778ae802d4039f0e88bb1cd68825780788b8058c479067e32b9a63eda`. The protocol was posted before discovery in #11 comment 6954442883. Results for the first four windows appear below and in #757. The retained CC0 record and manifest match the input hash.

## Verification
A fresh run at 2026-11-17 16:46 UTC, after #757 was opened, repeated all four original windows and added the four predeclared subsequent windows plus their first two combined. This is a wider run on the same file; no new file or independent human was used. The entire payload was previously exposed to measurement, and the combined window overlaps two others. Each window completed and passed the fixed tolerance. The four original 4x8 tables, counts, exact proportions and MI reproduced in the new run. A separately written literal-bit parser and window arithmetic matched all 4x8 cells, exact counts and fractions, and MI within 1e-14 bit; it shared the TIFF locator and human account and does not provide independent captures. The tool prints all full tables.

Start | Length | Retained | Escapes | b0 ones / retained | b1 ones / retained | MI bits
---: | ---: | ---: | ---: | ---: | ---: | ---:
0 | 262144 | 262141 | 3 | 127583/262141 | 128750/262141 | 0.00385633431194809
262144 | 262144 | 262144 | 0 | 127757/262144 | 128215/262144 | 0.003772993813710898
524288 | 262144 | 262144 | 0 | 127447/262144 | 127300/262144 | 0.003715778310288631
786432 | 262144 | 262144 | 0 | 125845/262144 | 126926/262144 | 0.0034549995213939136
1048576 | 262144 | 262144 | 0 | 126052/262144 | 126505/262144 | 0.003991973381703529
1310720 | 262144 | 262142 | 2 | 125957/262142 | 127084/262142 | 0.003842445446927709
1572864 | 262144 | 262143 | 1 | 126108/262143 | 127131/262143 | 0.003940221323979073
1835008 | 262144 | 262144 | 0 | 127032/262144 | 127722/262144 | 0.003730191720092406
1048576 | 524288 | 524286 | 2 | 252009/524286 | 253589/524286 | 0.0038891522492923935

Indices count all complete candidates, including q >= 17; only q < 17 contribute to tables and denominators. H=suffix>>3 and L=suffix&7. This fixed parse starts at payload bit zero, reads q zero bits, a stop bit and five suffix bits MSB-first, and assumes no extra escape skip. Empty or incomplete windows have undefined metrics. MI is the unsmoothed plug-in value compared at full precision, while proportions use exact rational comparisons. These are descriptive measurements, not statistical tests or evidence of physical syntax.

## Reproduce
After reading the script and imports and matching the local hash to the retained CC0 record, run from the named commit:

    python -I -B tools/suffix_balance_windows.py --mode discovery --sample 1051 'Olympus - E-M1 - 16bit (4:3).orf' PATH_TO_CC0_FILE
    python -I -B tools/suffix_balance_windows.py --mode verification --sample 1051 'Olympus - E-M1 - 16bit (4:3).orf' PATH_TO_CC0_FILE
