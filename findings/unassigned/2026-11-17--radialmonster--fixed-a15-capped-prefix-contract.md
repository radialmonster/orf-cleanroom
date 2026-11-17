# Fixed A15 capped-prefix contract on public E-M1 Mark II files

Author: @radialmonster
Verified by: @radialmonster
Lead: #807
Variant: unassigned
Builds on: #197, #603, 2026-10-28--radialmonster--fixed-capped-prefix-first-escape

## Claim

Under the declared fixed A15/D12/k5 whole-strip contract, public id 1993 stops
at an invalid capped word after 3,746,386 complete words. The previously known
id 1995 negative control stops at its first word. A fresh post-lead run
reproduces both ledgers; predeclared id 1997 separately stops at an invalid
capped word after 7,829,398 complete words. These failures reject only the
declared full contract for these files. None reaches N, so strict N/end and
tail termination are not tested; no physical framing or camera codec follows.

## Original evidence

Lead #807 used `tools/capped15_contract_probe.py` at merged commit
`220388329665742b337796fdc555837232940d43`, source SHA-256
`e37a83a086abf41a7a148b7bbdaed5c62e23e062eedd0097a104539f719a6a83`;
its `tools/orf_signature.py` import SHA-256 is
`1dab1d4b54b987bfa5458ea7f419fb3aee047107374ac9375edf5fe0a1af48cd`.
Discovery public CC0 raw.pixls.us id 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256
`0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`,
gave invalid value 50 after 3,746,386 words. Public CC0 id 1995,
`Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256
`8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`,
gave first-word invalid value 271; that value is within the earlier derived
264–271 interval and is a consistency control, not an independent discovery.

## Verification

The lead opened at 21:29:12 UTC on 2026-11-17. The fresh producer and
reference runs started at 21:30:22 UTC. They reproduced the original two result
objects and applied the same fixed contract to predeclared public CC0 id 1997,
`Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256
`89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`.
The retained CC0 inventory and manifest identify all three files. They were
previously studied. The finder performed this verification.

A separately written reference with its own TIFF locator and scanner matched
the full aggregate ledgers on all three files. It shares the fixed grammar and
human account. Agreement checks the implementation. Both processes exited
zero with empty stderr. The producer ran in about 3.86 seconds without timing out.

| ID | strip bits | completed | ordinary | capped | ordinary q sum | complete endpoint | unread bits | invalid word start | examined position | invalid value | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1993 | 126081000 | 3746386 | 3746385 | 1 | 447997 | 22926374 | 103154626 | 22926374 | 22926401 | 50 | invalid escape |
| 1995 | 126147400 | 0 | 0 | 0 | 0 | 40 | 126147360 | 40 | 67 | 271 | invalid escape |
| 1997 | 126140424 | 7829398 | 7829395 | 3 | 922781 | 47899272 | 78241152 | 47899272 | 47899299 | 58 | invalid escape |

For completed words the endpoint is `40 + 6*completed + ordinary_q_sum +
21*capped`; unread bits are relative to it. The examined position is the bit offset immediately after the rejected word. Counts of completed capped words do not
assert their values. All three stop before N, so their N/end condition is not
observed.

The contract selects the unique largest-strip-byte-count IFD, requires one
valid strip and 5240x3912 geometry, reads MSB first from bit zero, and treats
39 zeros then one as the startup marker. With A=15, D=12 and k=5, q<15 is q
zeros then one and five suffix bits; otherwise the word is 15 zeros followed
by 12 bits whose upper seven-bit value is at least 15. There is no additional
escape separator, header, interior marker, reset, adaptation or padding. The
full contract requires exactly N=20,498,880 words ending at strip end.

Japanese grant JP4468858B2 paragraphs 0055–0057 (pp.9–10, Figures 11–12)
describe the ordinary and capped-original-D branches; paragraphs 0071–0074
(p.12, Figure 14) describe the second-embodiment marker formula. D=12/A=15 and
marker-at-zero are post-hoc camera hypotheses. A wrong start, width, grammar,
interior control or other assumption can explain failure; the result does not
exclude other patent interpretations or establish actual camera syntax.

## Reproduce

After reviewing the tool/import and matching local files to retained CC0
identities and hashes, run at the named commit with a hard 120-second phase
limit, preserving stdout, stderr, exit status and timeout:

    python -I -B tools/capped15_contract_probe.py --phase verification --sample 1993 PATH1993 --sample 1995 PATH1995 --sample 1997 PATH1997

A timeout, input identity/read failure or ambiguous/unsupported container is
unknown, not a grammar contradiction. No file substitution, offset search or
alternative terminal fill is permitted.
