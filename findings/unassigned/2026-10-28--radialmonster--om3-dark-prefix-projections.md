# Prefix token projections on public OM-3 dark files

Author: @radialmonster
Verified by: @radialmonster
Lead: #594
Variant: unassigned
Builds on: #106

## Claim

Two predeclared public OM-3 dark files with raw EXIF sensitivity tags 200 and 800 yield distinct prefix-based Bernoulli-null projections and lag correlations. This describes selected files; it does not establish a causal sensitivity effect.

## Original evidence

For 1,500,000 complete tokens from bit zero with no extra escape skip, the lead measured PA200010 and PA200012. Their projected real rates both display 1.0000 tokens/site; null rates are 0.8179 and 0.8308. The lag-1/lag-2 Pearson correlations of min(q,8), retaining escapes, are +0.4043/+0.3926 and +0.2418/+0.2400. The displayed-rate excesses real/null minus one are +22.2643% and +20.3659%. All measurements are prefix-based projections, not measured whole-frame token counts or a pixel mapping.

## Verification

After the lead, a fresh run exactly reproduced both original aggregate records and evaluated the four predeclared additional public CC0 dark files. All six hashes matched and every run produced 1,500,000 complete tokens. The table gives full public SHA-256, raw EXIF 0x8827 value, payload bytes, bit endpoint, ones in complete bytes before the endpoint, escape count, rates displayed to four decimals and correlations displayed to four decimals. Each payload is 5220 x 3912; complete-byte prefix bits are eight times floor(endpoint/8).

| File | SHA-256 | Raw tag | Payload bytes | Endpoint bits | Ones | Escapes | Real | Null | Lag 1 | Lag 2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PA200010.ORF | b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 | 200 | 15321371 | 9003519 | 3850471 | 2 | 1.0000 | 0.8179 | +0.4043 | +0.3926 |
| PA200011.ORF | a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3 | 200 | 15321370 | 9003521 | 3850976 | 1 | 1.0000 | 0.8180 | +0.4016 | +0.3801 |
| PA200012.ORF | c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7 | 800 | 15330038 | 9008576 | 4041655 | 1 | 1.0000 | 0.8308 | +0.2418 | +0.2400 |
| PA200013.ORF | b714b28697a94081b83d7dd6127ed295f3ffbf6045b098a93381e373f8e3b946 | 800 | 15330225 | 9008812 | 4041532 | 2 | 1.0000 | 0.8308 | +0.2461 | +0.2327 |
| PA200014.ORF | 49d1719d4120da07911488060c35f8d47dd76b9fc03c328d3cea8a190e298fca | 800 | 15330122 | 9008766 | 4042217 | 1 | 1.0000 | 0.8308 | +0.2370 | +0.2393 |
| PA200015.ORF | 84c484c11a8f4be00a9e93f8ae55787e134e3a0efa2424b0416925c42b67a278 | 800 | 15330131 | 9008518 | 4042541 | 1 | 1.0000 | 0.8309 | +0.2563 | +0.2407 |

The projected real rate is full payload bits divided by prefix bits per token and by W*H. The Bernoulli null uses the prefix complete-byte ones density p and expected length 6+(1-p)/p. Independent bounded token parsing and arithmetic matched counts, endpoints and rates; correlations matched within 1e-12. The independent check shares the payload locator and EXIF helper, and both implementations assisted the same human. All six files were previously exposed. The declared dark condition and tag values do not establish identical scene, temperature, shutter or processing, and the results do not identify the camera codec or physical row framing.

## Reproduce

At commit cf3e74928434b9e8cd18bf3a9962a0ac6e2f0e13, obtain all six owner-declared CC0 files and verify the exact hashes against the retained provenance and manifest. Substitute the two original files' local paths in this example, and repeat for the four additional files:

```text
python -I -B tools/orf_tokens.py --max-tokens 1500000 <PA200010-path> <PA200012-path>
```

The command reports endpoint, escape count, displayed real/null projections and four-decimal Pearson lags. Recompute the displayed excess as real/null minus one. For exact complete-byte counts and the raw EXIF tag, run the following from the checkout root once per file, substituting its local path and the corresponding published hash:

```sh
python -I -B - <local-sample-path> <published-sha256> <<'PY'
import hashlib, sys
from array import array
from collections import Counter
sys.path.insert(0, 'tools')
import orf_tokens, exif_sensitivity_probe
with open(sys.argv[1], 'rb') as f:
    data = f.read()
assert hashlib.sha256(data).hexdigest() == sys.argv[2]
w, h, payload = orf_tokens.locate_data(data)
q, suffix, escapes = array('B'), array('B'), Counter()
_, end = orf_tokens.scan(payload, 1500000, 0, 0, None, q, suffix, 8, escapes)
assert len(q) == 1500000 and end <= len(payload) * 8
whole = payload[:end // 8]
ones = sum(bin(b).count('1') for b in whole)
print('geometry', w, h, 'payload bytes', len(payload), 'tokens', len(q))
print('endpoint', end, 'complete-byte bits', len(whole) * 8, 'ones', ones)
print('escapes', sum(escapes.values()), 'raw sensitivity', exif_sensitivity_probe.sensitivity(data))
PY
```

The independent bounded parser and exact arithmetic were used for aggregate verification only.
