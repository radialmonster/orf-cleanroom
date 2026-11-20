# Synthetic suffix-width endpoint ambiguity

Author: @radialmonster
Verified by: @radialmonster
Lead: #844
Variant: unassigned
Builds on: #29, #187

## Claim

On synthetic bits `0101010` repeated eight times, the candidate stop-1/k5 and stop-0/k6 parses each produce eight complete words ending at bit 56; a fresh run repeats this and the residual example. A predeclared distinct repeated word shows the same opposite-polarity closure, and a second residual example likewise has equal counts with different tails. With fixed stop polarity and the same starting position, increasing k strictly increases each corresponding completed-word endpoint while both parses exist; equal counts can nevertheless leave different residual tails. These are properties of the specified synthetic candidate grammar, not evidence of camera coding or physical row boundaries.

## Original evidence

The discovery command used `tools/suffix_width_synthetic_controls.py` at merged commit `8b5a8a582311f3e399d3b97771ca5424b9f7db4c` (#843). Recorded source SHA-256: controls `f43d0cf44d9fb34ba67f3e56e5cfada0e4ba904e5611a71e65ecf66b2c747d5e`, imported scanner `34f3a9de2a6814c08ba2ba3c0e80145c9d0f0675bba7a4486a851e4ad1ff6581`, and transitive TIFF helper `1dab1d4b54b987bfa5458ea7f419fb3aee047107374ac9375edf5fe0a1af48cd`. The controls compare scanner counts/endpoints to an independent bit-string trace. Fixtures are deliberately constructed and had been exposed in tool tests; they are not blind.

Discovery on eight `0101010` words gives both parses endpoints 7,14,21,28,35,42,49,56, with q histograms [[1,8]] and [[0,8]], respectively, and zero residual bits. The hex bytes `0040` under stop 1 yield one q=9 word for each width. The k5 endpoint is 15 with residual 1 and the k6 endpoint is 16 with residual 0.

For fixed polarity, `next_stop(i)` cannot move backward as i increases. Consequently `F_k(i)=next_stop(i)+1+k` is monotone in i and strictly larger in k; induction from a common start strictly orders equal-index completed endpoints. This proves the stated ordering under that grammar, not an identification rule for real streams.

## Verification

Lead #844 was posted at 19:35:06 UTC on 2026-11-20 and the claim scan was clean at 19:35:55. The fresh verification producer began at 19:36:24.518 and ended at 19:36:24.604, exiting zero with empty stderr under a hard 15-second limit. It repeated the two discovery fixtures exactly, including all word endpoints, q histograms and residual counts. A separately implemented per-bit reference began at 19:36:24.619, exited zero, and matched all four cases exactly on those fields. It used the same human account; this is self-verification, not independent-human verification.

The predeclared synthetic extension `0111010` repeated 16 times gives both opposite-polarity candidates 16 endpoints 7,14,...,112 and zero residual bits; stop-1/k5 has q=1 sixteen times and stop-0/k6 has q=0 sixteen times. On hex bytes `0041` under stop 1, both widths complete one q=9 word: k5 ends at 15 with one residual bit and k6 ends at 16 with none. The last bit is a stop for the next k5 candidate but its suffix is truncated. These additional generated fixtures serve as an analogue of the repository's post-lead sample-extension rule; they are not camera files or independent captures and were already exposed in tests.

## Reproduce

After reviewing the tool and imports at the pinned commit:

    python -I -B tools/suffix_width_synthetic_controls.py --phase verification

No raw files are read. The aggregate output must include both original fixtures and both extensions; incomplete or inconsistent results do not verify the lead. Physical row boundaries, actual stop polarity and camera suffix width remain open.
