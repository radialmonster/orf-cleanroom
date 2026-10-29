# Literal long zero-run census in public payloads

Author: @radialmonster
Verified by: @radialmonster
Lead: #699
Variant: unassigned
Builds on: #197, #603

## Claim

In two previously studied public payloads, the only terminated maximal zero run of length at least 39 is the startup run of exactly 39 zeros. The same count holds in each of four fixed prefix-preserving byte-shuffle controls per file. The absence of later long runs in both real and these controls does not distinguish them or identify framing.

## Original evidence

The lead measured whole selected payloads 1993 and 1995 with `tools/payload_zero_run_probe.py` at commit `f908ec460b4f161258c289b9017cda5478d18007`. Fresh values for those original cases appear below.

## Verification

After the lead was posted, the original files were freshly rerun and the predeclared same-body 1997 and 1998 files were measured. Those additional files qualify verification; all inputs were previously exposed, and the verifier is the finder. Independent literal-bit and segment-based implementations matched all counts, EOF status and shuffled-tail hashes exactly; both share a TIFF locator and assisted the same human.

Count literal maximal zero runs in every bit of the selected payload, without token parsing. A terminated run is consecutive zeros followed by one. Report exact 39, exact 47 and at least 39 separately; a 47 run is one maximal run, not an additional exact-39 run. Disjoint regions give startup priority: startup starts at bit zero; preserved-internal starts later and terminates before bit 48; seam-crossing starts before bit 48 and terminates at or after it; later starts at bit 48 or later. An all-zero terminal run is EOF-censored and reported separately by length, region and seam-crossing flag.

Four controls preserve the first six bytes, then shuffle every remaining payload byte with a fresh `Random(seed)` for seeds 20261022..20261025. This preserves the tail-byte histogram but not its run histogram. The table lists terminated counts as exact39/exact47/at-least39, EOF-censored terminal run, and SHA-256 of the shuffled tail. These controls are descriptive, not calibrated significance tests.

| ID | Real or seed | Payload bytes | Startup | Preserved internal | Seam crossing | Later | Terminal zero run | Shuffled tail SHA-256 |
|---|---|---:|---|---|---|---|---|---|
| 1993 | real | 15760125 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | N/A |
| 1993 | 20261022 | 15760125 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | 4338ba568b93146a36ad02059c24c39a17f6d81b245a7e1714926aeeaca10799 |
| 1993 | 20261023 | 15760125 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | ad526c4f7d36316c79417aaae117f509e217795af342c5e7f3cf015c62a98165 |
| 1993 | 20261024 | 15760125 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | 7c2f884ca8a8c3b227610d12cc7545def2822ac5a3c3c179f4ef53bfa1da4ee3 |
| 1993 | 20261025 | 15760125 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | 14e191c0ea2ded2168df9ceafaf5e1f9f647148f6f952fc8b9d452fbecf019f1 |
| 1995 | real | 15768425 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | N/A |
| 1995 | 20261022 | 15768425 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | c6b433d257075e12e4ad8602440db6a03b602e0ba9f999d61a171acf5a3e4c1f |
| 1995 | 20261023 | 15768425 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | 2 (later, crosses=False) | e9bd9c080536da34437ccb954d5d0a4c4fd4cb760ceac5a3e3878fe544bac2c7 |
| 1995 | 20261024 | 15768425 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | 1 (later, crosses=False) | 91f8fae4deebc075cf0b4d27993a4565c654a2fac8e3d1ec2b20109663f7d807 |
| 1995 | 20261025 | 15768425 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | 1 (later, crosses=False) | d348af4caba01de6313a6dc6ee15365df1a43e577af0c3edfb05fa661e3de990 |
| 1997 | real | 15767553 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | N/A |
| 1997 | 20261022 | 15767553 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | 292990c0fca8b8f3b5d8ef200834acd5c7137e67e8d594f6c211f622ab093056 |
| 1997 | 20261023 | 15767553 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | 45e9f6d7b9c3061cac19c6f3d02dd6234de1e74cc6983f9439fb4a3d712e89c4 |
| 1997 | 20261024 | 15767553 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | 1 (later, crosses=False) | 5c17d4b1243caa6181165a029437317f99006e2f6c769e2b0485bfbbdd92f2e4 |
| 1997 | 20261025 | 15767553 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | 9a7b9d242f5e145beaf701fe6d6c04f55070c8ebb98bc13e78a142f55c497294 |
| 1998 | real | 15772675 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | N/A |
| 1998 | 20261022 | 15772675 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | 3 (later, crosses=False) | 15d01b2364fee518a7ef591834e78aa974997c4e76695fb0e500598e64fb3808 |
| 1998 | 20261023 | 15772675 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | 0e1d86e735aa6a12f3990a24a87c850b498316606d6e1abdf827f5f884e9135a |
| 1998 | 20261024 | 15772675 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | 2 (later, crosses=False) | c857eeabe5afd3e398108468f8c04c14ff17f1f90b8d63958758a9afbe47c2ad |
| 1998 | 20261025 | 15772675 | 1/0/1 | 0/0/0 | 0/0/0 | 0/0/0 | none | 86ea81c7cd4974561f983f7b350f94e9c75a6f100bf849a1eed3225374004961 |

The observed 39-zero startup runs lie within the preserved six-byte prefix. Neither these run counts nor their controls identify a marker, restart, physical row or entropy grammar.

## Reproduce

Retained verified public CC0 inputs:

- 1993: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`
- 1995: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`
- 1997: `Olympus - E-M1MarkII - 16bit (4:3).ORI`, SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`
- 1998: `Olympus - E-M1MarkII - 16bit (4:3).ORF`, SHA-256 `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`

At commit `f908ec460b4f161258c289b9017cda5478d18007`, verify identities and hashes, substitute paths, and run:

```text
python -I -B tools/payload_zero_run_probe.py --sample 1993 "Olympus - E-M1MarkII - 16bit (4:3).ORF" 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8 FILE1993
python -I -B tools/payload_zero_run_probe.py --sample 1995 "Olympus - E-M1MarkII - 16bit (4:3).ORI" 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f FILE1995
python -I -B tools/payload_zero_run_probe.py --sample 1997 "Olympus - E-M1MarkII - 16bit (4:3).ORI" 89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a FILE1997
python -I -B tools/payload_zero_run_probe.py --sample 1998 "Olympus - E-M1MarkII - 16bit (4:3).ORF" 4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71 FILE1998
```

The tool emits all region counts, EOF-censored runs, seeds, shuffled-tail hashes and source hashes. Separately justified framing or control assumptions remain open on the existing corpus.
