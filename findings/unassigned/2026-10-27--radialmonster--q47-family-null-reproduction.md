# Candidate family counts versus Bernoulli reproduce on wider q47 prefixes

Author: @radialmonster
Verified by: @radialmonster
Lead: #577
Variant: unassigned
Builds on: #86, 2026-10-27--mtakemoto--public-code-family-counts

## Claim
The fixed nine-family 131072-byte real/Bernoulli counts on four selected public q47-prefix files reproduce. Predeclared 262144-byte windows on the same captures are reported separately. These are descriptive candidate parses and do not establish a codec, framing, pixel correspondence or variant membership.

## Original evidence
The fixed four files, nine families and null were declared before measurement in https://github.com/radialmonster/orf-cleanroom/issues/86#issuecomment-6453875933. Prefix p equals measured ones divided by 1048576; one same-length Bernoulli buffer per file is generated with Random(20261021), reset per file and shared by all families. Density is preserved in expectation, not exactly. Resetting seeds induces dependence across files. One draw is not significance evidence.

Each entry below is real completed words / consumed bits; null completed words / consumed bits. Residual bits equal 1048576 minus consumed bits; rate per input bit equals completed words divided by 1048576. An incomplete final word is not counted.
| Family | 7267 real; null | 7269 real; null | 7801 real; null | 7803 real; null |
|---|---:|---:|---:|---:|
| rice_stop1_k5 | 151472 / 1048573; 148149 / 1048575 | 148565 / 1048570; 147165 / 1048575 | 148861 / 1048574; 148230 / 1048575 | 146376 / 1048571; 147182 / 1048575 |
| rice_stop1_k4 | 171375 / 1048576; 172410 / 1048572 | 168639 / 1048568; 171154 / 1048572 | 172879 / 1048573; 172508 / 1048572 | 169853 / 1048576; 171172 / 1048572 |
| rice_stop1_k3 | 204940 / 1048575; 206275 / 1048574 | 201534 / 1048570; 204332 / 1048574 | 207221 / 1048576; 206429 / 1048574 | 202892 / 1048575; 204361 / 1048574 |
| rice_stop0_k5 | 152209 / 1048574; 151242 / 1048574 | 152752 / 1048573; 152076 / 1048574 | 151367 / 1048573; 151183 / 1048574 | 152027 / 1048576; 152063 / 1048574 |
| exp_golomb_k2 | 203774 / 1048568; 202995 / 1048575 | 197383 / 1048567; 199365 / 1048575 | 205643 / 1048575; 203285 / 1048575 | 197790 / 1048572; 199425 / 1048575 |
| exp_golomb_k3 | 169441 / 1048576; 170220 / 1048574 | 164504 / 1048568; 167605 / 1048574 | 171882 / 1048570; 170391 / 1048574 | 165840 / 1048576; 167627 / 1048574 |
| elias_gamma_k0 | 335399 / 1048575; 332170 / 1048574 | 323005 / 1048567; 322640 / 1048574 | 337439 / 1048575; 332966 / 1048574 | 323457 / 1048575; 322758 / 1048574 |
| elias_delta_k0 | 0 / 0; 39239 / 901373 | 0 / 0; 41121 / 1031380 | 0 / 0; 38582 / 901373 | 0 / 0; 41173 / 1031380 |
| fibonacci_k0 | 162039 / 1048573; 164073 / 1048573 | 158044 / 1048567; 157920 / 1048573 | 162410 / 1048574; 164597 / 1048573 | 158415 / 1048567; 157997 / 1048573 |

| ID | file SHA-256 | ones | null SHA-256 | geometry |
|---|---|---:|---|---|
| 7267 | 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756 | 504693 | b0f80e0e33569e0f5a066772355e7ff58456e4e9a784862589649783689711c7 | 10386 x 7792 |
| 7269 | dd2a6c1c4ca4d86201207925477e2ea8e50ebd53d7df9117847093f5023540ec | 493390 | eb478817c5e9132cba16e0ac5703dc0429d7c3cde61e902f93ecd30ededcb691 | 8172 x 6132 |
| 7801 | 8832599870d20a96f28897e3e28d9705a4bd05871c9833c7c60a8b59d7d64b82 | 505584 | 6f22a0654f745964ee6f48e1ae774ec9caa066baa99a00e5cbd10bb201bdd4d2 | 10386 x 7792 |
| 7803 | 63a5b4da41fdbe8b31213ca7a11408dfd0453d893f17ac09a73471580ffbd8f0 | 493513 | 862dd9533394bca2d7d3c4edd195387c0794cde8459a9bbf357657b5abeb9d5c | 8172 x 6132 |

All local snapshots matched retained verified CC0 records and manifest identity/hash rows. Public names: 7267 and 7269 are OM System - OM-1 Mark II - 16bit (4:3).orf; 7801 and 7803 are OM System - OM-3 - 16bit (4:3).ORF. An independent per-bit family counter and bytewise null generator matched all 72 cells, null hashes, p and geometry; both implementations assist the same human. These are previously studied selected files, not independent captures.


## Verification
After #577 was posted and its current text scanned, the four initial reports were rerun and matched their full original JSON exactly. The predeclared 262144-byte windows below reuse the same four captures, so are neither new captures nor blind files. Each entry gives real count / consumed bits; null count / consumed bits. Divide count by 2097152 for its finite-window rate; residual bits equal 2097152 minus consumed bits. Zero completed words is an observed zero, not a completed parse.

| Family | 7267 real; null | 7269 real; null | 7801 real; null | 7803 real; null |
|---|---:|---:|---:|---:|
| rice_stop1_k5 | 302947 / 2097152; 296271 / 2097149 | 296687 / 2097150; 294281 / 2097149 | 298256 / 2097148; 296918 / 2097149 | 293316 / 2097152; 294579 / 2097149 |
| rice_stop1_k4 | 342566 / 2097148; 344772 / 2097148 | 337012 / 2097152; 342229 / 2097148 | 346620 / 2097147; 345621 / 2097148 | 340520 / 2097152; 342634 / 2097148 |
| rice_stop1_k3 | 409863 / 2097147; 412610 / 2097151 | 402654 / 2097151; 408842 / 2097151 | 416097 / 2097150; 413823 / 2097151 | 406813 / 2097150; 409435 / 2097151 |
| rice_stop0_k5 | 304568 / 2097150; 302632 / 2097147 | 305409 / 2097147; 304294 / 2097147 | 302428 / 2097149; 302053 / 2097147 | 303967 / 2097147; 304036 / 2097147 |
| exp_golomb_k2 | 406928 / 2097150; 406175 / 2097151 | 393973 / 2097151; 399199 / 2097151 | 413920 / 2097152; 408703 / 2097151 | 397116 / 2097150; 400221 / 2097151 |
| exp_golomb_k3 | 338651 / 2097148; 340462 / 2097152 | 328374 / 2097152; 335326 / 2097152 | 345549 / 2097148; 342157 / 2097152 | 332826 / 2097150; 336076 / 2097152 |
| elias_gamma_k0 | 669427 / 2097147; 664228 / 2097152 | 644544 / 2097150; 645480 / 2097152 | 680647 / 2097151; 670918 / 2097152 | 649942 / 2097152; 648386 / 2097152 |
| elias_delta_k0 | 0 / 0; 90892 / 2097036 | 0 / 0; 89197 / 2086340 | 0 / 0; 93443 / 2097036 | 0 / 0; 87007 / 2097036 |
| fibonacci_k0 | 323604 / 2097124; 327683 / 2097152 | 316004 / 2097149; 315669 / 2097152 | 326620 / 2097151; 331946 / 2097152 | 317462 / 2097152; 317484 / 2097152 |

| ID | wider ones | wider null SHA-256 |
|---|---:|---|
| 7267 | 1008461 | cb6b2556ec7c604602e76983299301788a482b95c6403e56259584a74c9d13a6 |
| 7269 | 986235 | 822fc97cc172fa1179ec605201b5e76ba3bc2c4271b3e95654eb1a9da804626e |
| 7801 | 1016136 | 7dd730273cc2e6258bbab163df395686312d687462f7bf4419ef5afe27558a79 |
| 7803 | 989667 | 1df86561d902e1a6f36d7bb5289465653e8c05cb33ea543f27badb24ff141896 |

All four wider real Elias-delta parses complete zero words and leave the entire window unconsumed. One Bernoulli draw per file/window is descriptive; prefix p is refitted per window, while the reset seed induces dependence. A separately implemented per-bit family counter and bytewise Bernoulli generator matched all 144 fresh real/null cells, endpoints, residuals, rates, null hashes and identity fields; both implementations assist the same human verifier.

## Reproduce
At b5f51619296edbbc8d1aba154eb406a9fb18f2fa set FILE to one public file whose hash matches above; repeat per file. Python 3.14.7 was used. This prints aggregates only.

```sh
python -I -B - "$FILE" <<'PY'
import hashlib, json, random, sys
sys.path.insert(0, 'tools')
import orf_tokens, token_framing_probe as framing, code_family_screen as screen
with open(sys.argv[1], 'rb') as f: data = f.read()
w, h, payload = orf_tokens.locate_data(data)
prefix = payload[:131072]
if len(prefix) != 131072: raise ValueError('short window')
ones = sum(bin(b).count('1') for b in prefix)
null = framing.bernoulli_bytes(len(prefix), ones/(8*len(prefix)), random.Random(20261021))
families = [('rice_stop1',5),('rice_stop1',4),('rice_stop1',3),('rice_stop0',5),('exp_golomb',2),('exp_golomb',3),('elias_gamma',0),('elias_delta',0),('fibonacci',0)]
models = {}
for name, buf in [('real',prefix),('bernoulli',null)]:
    bits = bin(int.from_bytes(buf,'big'))[2:].zfill(len(buf)*8)
    models[name] = {}
    for family,k in families:
        _, (end,count) = screen.count_family(bits,family,k,len(bits))
        models[name][family+'_k'+str(k)] = dict(count=count,consumed_bits=end,residual_bits=len(bits)-end,rate=count/len(bits))
print(json.dumps(dict(sha256=hashlib.sha256(data).hexdigest(),width=w,height=h,ones_count=ones,null_sha256=hashlib.sha256(null).hexdigest(),models=models),indent=2))
PY
```

For the predeclared wider run, replace both occurrences of `131072` in the script with `262144`; p is re-estimated on that wider prefix. No whole-frame token-per-pixel estimate follows from these finite windows.
