# Learned suffix-table horizontal-shift sensitivity

Author: @radialmonster
Verified by: @radialmonster
Lead: #840
Variant: unassigned
Builds on: #11, #155, #803, 2026-11-17--radialmonster--learned-suffix-table-vertical-shifts

## Claim

On discovery inputs 1997 and 1998 the fixed 1995-trained table's declared horizontal alignment is not a unique positive maximum: ranks 6/400 and 54/400, with best shifts 396 and 381. Fresh post-lead runs reproduce both; predeclared extensions 1993 and High Res 1994 likewise fail the criterion, at ranks 53/400 and 27/400. This describes a fixed candidate map on a coarse circular grid; it does not establish physical displacement, framing or a codec.

## Original evidence

Lead #840 used the predeclared #11 protocol and `tools/suffix_table_shift_probe.py --axis horizontal` at `da3e48dbcf80a411f1423f5a09bfe94af224cf89`, tool SHA-256 `b685f38ef13fb90ee07f4baa65c99dbf80193de3d315289a2b15aa0785dd8ebd`. The 32-bin table was trained on even preview rows of public 1995 with lambda 1, smoothness 10 and no intercept. All cases use 600 candidate rows, include q>=17 suffixes without extra skipping, row-center targets and globally center predictions. For k=0..399 compare Y[r,c] with P[r,(c+k) mod 400]; ranks and ties use absolute tolerance 1e-12. The predeclared criterion requires r(0)>0 and r(0)>r(k)+1e-12 for every nonzero k. Full original score curves are in #840.

Training 1995 is `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`. Discovery 1997 has the same public name, SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`; 1998 is `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`. These public CC0 files are previously studied, not blind capture validation. The fit hash and zero scores agree with #803 historical controls; #155 five-decimal correlations also match.

| ID | r(0) | best r | best k | rank | zero ties | criterion |
|---:|---:|---:|---:|---:|---|---|
| 1997 | 0.10555837065892784 | 0.1064971902240679 | 396 | 6/400 | [0] | no |
| 1998 | 0.08531411752241273 | 0.09557025786974288 | 381 | 54/400 | [0] | no |

## Verification

A fresh self-verification run began at 19:23:51 UTC on 2026-11-20, after lead #840 was posted at 19:22:45 UTC. Both original result objects repeat exactly, including their complete score curves. The fitted 32 binary64 big-endian weights hash to `c7162dbb1376e8f8799dc717f3e93a51f65a38dbd80ca80065f2fbee402bda5f`; zero scores reproduce #803 and #155 controls. Both original files and the two predeclared extensions return defined scores on 400 columns. Their preview is 400x300 blocks, with 46 used rows on 1997/1998/1993 and 23 on 1994.

| Stage | ID | r(0) | best r | best k | zero rank | zero-tied shifts | specific |
|---|---:|---:|---:|---:|---:|---|---|
| repeat | 1997 | 0.10555837065892784 | 0.1064971902240679 | 396 | 6/400 | [0] | no |
| repeat | 1998 | 0.08531411752241273 | 0.09557025786974288 | 381 | 54/400 | [0] | no |
| extension | 1993 | 0.08695732081826399 | 0.13783564469346526 | 123 | 53/400 | [0] | no |
| extension | 1994 | 0.055165792149468575 | 0.05693229027545144 | 393 | 27/400 | [0] | no |

Reserved extensions are 1993 and High Res 1994, both `Olympus - E-M1MarkII - 16bit (4:3).ORF`, respectively SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8` and `f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23`. Their outcomes are separate extensions, not prior claim outcomes. All targets were previously exposed; held out means only table-fit held out. A separate fit and scorer sharing feature extraction matched all 1600 scores within 1e-12 and all decisions; maximum differences by table order were 1.38778e-15, 7.35631e-16, 6.43929e-15 and 3.16414e-15. Its fitted binary64 hash differs from the producer due to numerical rounding. Both runs used the same human account, exited zero with empty stderr and finished within the hard 180-second limit (34.60 and 35.27 seconds). This is self-verification, not independent-human verification.

Circular wrapping changes a seam; scores are dependent and are not calibrated p-values. Scene content and rendered preview can affect them. A positive or negative criterion outcome cannot independently establish token framing, physical rows, pixel values or decoding.

## Reproduce

Read the tool and imports at the named commit, verify retained CC0 identity and local hashes, and run with an external hard 180-second phase limit:

    python -I -B tools/suffix_table_shift_probe.py --axis horizontal --phase verification --train PATH1995 --sample 1997 PATH1997 --sample 1998 PATH1998 --sample 1993 PATH1993 --sample 1994 PATH1994

Retain exit, stderr, timeout and full aggregate reports. Hashes before and after separate reads do not guarantee an atomic snapshot. Timeout, incompatible input and undefined scores are unknown.
