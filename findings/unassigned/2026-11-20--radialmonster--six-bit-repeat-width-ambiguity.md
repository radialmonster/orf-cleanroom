# An ideal six-bit repeat admits both literal candidate widths

Author: @radialmonster
Verified by: @radialmonster
Lead: #868
Variant: unassigned
Builds on: #339, #574, #864

## Claim

For every nonconstant six-bit cyclic binary template and every start phase, the literal zero-run/one-stop parses with four or five suffix bits both settle to one six-bit word per period. The `k=4` stable phase is a zero immediately before a one, with `q=1`. The `k=5` stable phase is a one, with `q=0`. The ideal repeat admits both widths at different phases.

## Original evidence

`tools/periodic_rice_orbit.py` at `9bbcaffd0a301646b467cf4a4cb4b4ebc90ec19a` enumerates all 64 generated six-bit templates, six starting phases and both widths. A transition consumes `q+1+k` bits, from the current phase through the unary zeros, stop one and suffix. Return to the same phase makes the future trajectory repeat. On a nonconstant template with period six, `k=5` lands directly on the stop phase. For `k=4`, the next phase is immediately before the stop. From a one, successive steps walk backward through a run of ones until a zero immediately before a one. From a zero, the next step reaches such a zero. A nonconstant six-bit template has at most five consecutive cyclic ones.

Among the 372 nonconstant template-and-start cases per width, the numbers with transients of 0, 1, 2, 3, 4 and 5 words are 96, 186, 48, 24, 12 and 6 for `k=4`, and 186, 186, 0, 0, 0 and 0 for `k=5`. All eventual cycles contain one six-bit word. The all-zero template has no stop for either width. On the all-one template, `k=4` advances by five bits per word and cycles through six phases in 30 bits, while `k=5` consumes six bits per word in a fixed phase.

## Verification

Discovery began at 21:07:08 UTC on 2026-11-20. After #868 was published at 21:07:35 UTC, the fresh verification began at 21:08:56 UTC. All 768 period-six records matched exactly. The predeclared periods five and seven supplied 320 and 1792 additional generated cases. A separately written repeated-string parser matched all 2880 phase paths, quotients, word lengths, cycle entry indices and summaries exactly. Here p is the template length, including templates with shorter primitive periods.

| Period p | Cases per width | No-stop cases per width | Eventual one-word p-bit cycle, k=4 | Eventual one-word p-bit cycle, k=5 |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 160 | 5 | 155 | 0 |
| 6 | 384 | 6 | 372 | 378 |
| 7 | 896 | 7 | 686 | 882 |

A single word consumes exactly one template period when `q=p-k-1`, which requires `p>=k+1`. A fixed phase is the weaker condition that the word length is a multiple of p. At p=5, `k=5` has 25 start cases reaching a fixed phase with a ten-bit word, and none reaching a five-bit word. At p=7, `k=4` has 196 nonconstant start cases reaching a four-word cycle of 21 bits. The table includes all-one cases where applicable.

The fitted six-bit repeat from #864 motivates the idealization. The enumeration uses generated templates alone. Physical origins, finite strip endpoints and behavior at actual exceptions remain open.

## Reproduce

At `9bbcaffd0a301646b467cf4a4cb4b4ebc90ec19a`:

```text
python -I -B tools/periodic_rice_orbit.py --phase discovery
python -I -B tools/periodic_rice_orbit.py --phase verification
```

The summary keys encode transient words, cycle words and cycle bits. To obtain the nonconstant distributions, omit the two constant templates and count `cycle_start` over the remaining cases.
