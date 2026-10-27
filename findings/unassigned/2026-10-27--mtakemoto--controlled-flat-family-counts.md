# Controlled OM-3 candidate family counts reproduce

Author: @mtakemoto
Verified by: @radialmonster
Lead: #339
Variant: unassigned
Builds on: 2026-10-27--mtakemoto--public-code-family-counts, #338
Partial: nine candidate-family counts and k=5 prefix/whole endpoints on the original three public controlled files

## Claim
The nine original whole-payload candidate-family counts reproduce on the lead's white and two capped dark files, both in real order and after its fixed byte shuffle. The k=5 3M-byte prefix and whole endpoints reproduce as well. These are bounded candidate parses, not evidence of a particular codec or a physical pixel map.

## Original evidence
#339 used `tools/code_family_screen.py` at `4787e490c63df740785078c657de29ff4eee4612`, with a whole-payload byte shuffle seeded 20261022. It reported count minus W×H for nine candidate families on a white and two dark OM-3 files, and k=5 prefix and whole counts/endpoints. The controlled captures were shared by their owner under CC0; retained names, hashes and public source links are in `samples/om3-flat-338-provenance.json`.

## Verification
After the lead, I measured the same three controlled files and predeclared public CC0 id 7797 at `d2c85dab445f20a4bd35752ffda79df9db7df93b`. All 54 original real/shuffle table values match. The additional 7797 is a previously studied busy High Res file, not another flat capture or independent body. Every cell is completed words minus W×H:

| Family | White real / shuffle | Dark ISO 200 real / shuffle | Dark ISO 800 real / shuffle | 7797 real / shuffle |
| --- | ---: | ---: | ---: | ---: |
| Rice stop 1 k5 | +11 / -3904353 | +5 / -2407431 | +10 / -2865197 | +2838628 / +322825 |
| Rice stop 1 k4 | +14 / -3892757 | +31 / -1015034 | +36086 / -383245 | +8423660 / +8406008 |
| Rice stop 1 k3 | +67 / +538597 | +1397356 / +3702643 | +3438985 / +3759797 | +19693183 / +20120743 |
| Rice stop 0 k5 | +7808 / -3493 | -16969 / -1192330 | -1212017 / -1976751 | +1599365 / +820089 |
| Exp-Golomb k2 | -297492 / -3262262 | +1268575 / +1919700 | +3036849 / +2728782 | +20727456 / +20093361 |
| Exp-Golomb k3 | -8208160 / -6789777 | -3032476 / -2829808 | -427326 / -504335 | +8927753 / +8700305 |
| Elias gamma | +101378 / +519452 | +12592928 / +14366372 | +15699448 / +15809046 | +65839164 / +65037350 |
| Elias delta | -20420640 / -15405660 | -20420640 / -8569706 | -20420640 / -7125077 | -50159760 / -16817254 |
| Fibonacci | -20321491 / -20321494 | -10143865 / -9789873 | -6588251 / -5850044 | +2365508 / +3069606 |

Real k=5 prefix (completed words / consumed bits) is 3998448 / 23999995, 3998457 / 23999997 and 3996244 / 23999998 for white, ISO 200 and ISO 800 respectively. Whole real counts/endpoints are 20420651 / 122570965, 20420645 / 122570967 and 20420650 / 122640301, with 3, 1 and 3 residual bits. All match #339. Real Elias delta completes zero words on each controlled file and 7797: the negative values equal minus W×H and indicate an incomplete candidate parse, not negative codewords.

A separately implemented bitwise counter matched all 72 candidate-family cells across the eight runs: prefix and whole counts/endpoints, residuals and minus-sites agree exactly. The implementations were run by agents assisting the same human verifier, not additional independent-human verifiers.

| Input | Public name | SHA-256 |
| --- | --- | --- |
| White | PA210010.ORF | d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e |
| ISO 200 | PA200010.ORF | b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4 |
| ISO 800 | PA200012.ORF | c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7 |
| 7797 | OM System - OM-3 - 16bit (4:3).ORF | 318e35647d93b2c598c0fec1d0d075336d2e2f5e6930faee05f32182c9a8ac5f |

All inputs passed retained CC0, manifest and local hash gates. Container and recompression claims and other families remain outside this Partial result.

## Reproduce
At `d2c85dab445f20a4bd35752ffda79df9db7df93b`, run once per hash-matched input with `real`, then replace `real` by `shuffle`. This reads the file and prints aggregate numbers only.

```sh
python -I -B - FILE real <<'PY'
import random, sys
sys.path.insert(0, 'tools')
import code_family_screen as screen, orf_tokens
w, h, payload = orf_tokens.locate(sys.argv[1])
buf = bytearray(payload)
if sys.argv[2] == 'shuffle':
    random.Random(20261022).shuffle(buf)
bits = bin(int.from_bytes(buf, 'big'))[2:].zfill(len(buf) * 8)
families = [('rice_stop1',5),('rice_stop1',4),('rice_stop1',3),('rice_stop0',5),
            ('exp_golomb',2),('exp_golomb',3),('elias_gamma',0),('elias_delta',0),('fibonacci',0)]
for family, k in families:
    (pb, pc), (end, count) = screen.count_family(bits, family, k, min(3000000,len(buf))*8)
    print(family, k, 'prefix_words', pc, 'prefix_bits', pb, 'words', count,
          'consumed', end, 'residual', len(bits)-end, 'minus_sites', count-w*h)
PY
```