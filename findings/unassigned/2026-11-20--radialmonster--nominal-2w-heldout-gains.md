# Fixed nominal 2W gains on four public candidate-token streams

Author: @radialmonster
Verified by: @radialmonster
Lead: #848
Variant: unassigned
Builds on: #29, #658, #666

## Claim

Adding one same-field nominal `2W` donor to a five-lag local model lowered held-out loss for `q>0` on E-M1 Mark II sample 1993, and raised it slightly on OM-1 sample 5283. Both results repeat exactly, and the signs persist in the next test band. In that band `q>0` also gains on E-M1 Mark II sample 1995 and OM-5 sample 6343. On 6343 the `2W+128` control gains more. For suffix `b0`, `2W` raises loss in all six measured sample and band pairs.

## Original evidence

`tools/same_field_2w_probe.py` at `f835a31722fd36fe3162b12e0af09b9f9e3e5909` uses the declared strip payload selected by the repository TIFF locator. Starting at payload bit zero, take complete candidate tokens with zeros before a one stop bit and a five-bit suffix, with no extra skip. Each band contains 262144 candidate tokens. Start scoring at offset `2W+128` within each band, where `W` is the measured payload width. Omit positions if `q>=17` at the target or any local or remote donor. On this common support, fit fixed binary half-count models on band 0, using the five nearest same-field lags, with or without a sixth same-field donor. Gain is local loss minus augmented loss, in bits per retained test target. The exact tables, unseen contexts, support and endpoints are in the command output.

The original comparison tests band 1. Public CC0 raw.pixls.us inputs:

- 1993, `Olympus - E-M1MarkII - 16bit (4:3).ORF`, `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`, 5240 × 3912.
- 5283, `OM System - OM-1 - 16bit (4:3).ORF`, `bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b`, 5220 × 3912.

| ID | Field | Local loss | Gain at 2W | Gain at 2W−128 | Gain at 2W+128 |
| --- | --- | ---: | ---: | ---: | ---: |
| 1993 | `q>0` | 0.341991039 | +0.000816817 | +0.000059159 | −0.000013832 |
| 1993 | `b0` | 0.999997911 | −0.000147428 | −0.000104131 | −0.000052856 |
| 5283 | `q>0` | 0.991113763 | −0.000009694 | −0.000148241 | −0.000102629 |
| 5283 | `b0` | 0.998786197 | −0.000111510 | −0.000136125 | −0.000097534 |

## Verification

The discovery producer started at 2026-11-20 19:47:52 UTC. After #848 was published at 19:49:01 UTC, a fresh producer run and a separate parser and count run started at 19:50:07 UTC. The production repeat exactly matched every band-0 and band-1 support field, endpoint and model row for both original inputs. For all 48 model comparisons in the verification run, the separate implementation matched geometry, bit endpoints, support, taps, every train and test table cell and unseen-context counts exactly, and losses and gains within `1e-12`. Both implementations share the TIFF payload locator. Both completed with exit 0 and empty stderr.

The fresh run extends the same band-0 fit to test band 2 on both original files and two additional predeclared public CC0 inputs:

- 1995, `Olympus - E-M1MarkII - 16bit (4:3).ORI`, `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`, 5240 × 3912.
- 6343, `OM System - OM-5 - 16bit (4:3).ORF`, `ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7`, 5240 × 3912.

| ID | Field | Local loss | Gain at 2W | Gain at 2W−128 | Gain at 2W+128 |
| --- | --- | ---: | ---: | ---: | ---: |
| 1993 | `q>0` | 0.235245966 | +0.001270045 | +0.000401799 | +0.000298671 |
| 1993 | `b0` | 1.000103133 | −0.000092898 | −0.000118405 | −0.000059979 |
| 5283 | `q>0` | 0.989153971 | −0.000073312 | −0.000039761 | −0.000063523 |
| 5283 | `b0` | 0.998734145 | −0.000122947 | −0.000131587 | −0.000083458 |
| 1995 | `q>0` | 0.365945109 | +0.000551154 | −0.000035245 | −0.000100117 |
| 1995 | `b0` | 1.000040060 | −0.000087230 | −0.000008197 | −0.000119967 |
| 6343 | `q>0` | 0.844426780 | +0.000140729 | −0.000072114 | +0.000224294 |
| 6343 | `b0` | 0.999677057 | −0.000149205 | −0.000070637 | −0.000038312 |

Each band entry below is retained targets / candidate targets / exclusive payload bit endpoint.

| ID | Band 0 | Band 1 | Band 2 |
| --- | --- | --- | --- |
| 1993 | 251535 / 251536 / 1595634 | 251536 / 251536 / 3190511 | 251536 / 251536 / 4776099 |
| 5283 | 248973 / 251576 / 1822446 | 249164 / 251576 / 3645413 | 248723 / 251576 / 5471016 |
| 1995 | 251535 / 251536 / 1595135 | 251536 / 251536 / 3190489 | 251536 / 251536 / 4785827 |
| 6343 | 251268 / 251536 / 1725464 | 251253 / 251536 / 3443804 | 251278 / 251536 / 5163308 |

All files had prior exposure. Results describe only these samples, fields, fixed offsets, and test bands. The displaced controls may retain structure. Physical row alignment, statistical significance, generalization, and the private greedy search in #29 item 5 remain open.

## Reproduce

At `f835a31722fd36fe3162b12e0af09b9f9e3e5909`, substitute paths to the four hashed inputs above. The verification mode scores the two original pairs plus the four band-2 pairs.

```text
python -I -B tools/same_field_2w_probe.py --phase discovery --sample 1993 PATH1993 --sample 5283 PATH5283
python -I -B tools/same_field_2w_probe.py --phase verification --sample 1993 PATH1993 --sample 5283 PATH5283 --sample 1995 PATH1995 --sample 6343 PATH6343
```
