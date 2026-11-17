# Token parse ends 0-7 bits before the payload end; the final 1-run is leftover bits plus the last token

Author: @radialmonster
Verified by: @ruedbi
Lead: #87
Variant: unassigned
Builds on: #11, 2026-10-20--radialmonster--trailing-one-bit-in-compressed-payloads, 2026-10-21--radialmonster--compressed-tail-full-cohort-reproduction
Reproduces: 2026-10-21--radialmonster--token-end-and-final-run
Partial: payload endpoint and terminal-run composition only; whether the leftover bits are padding or a truncated final token, and the cause of the zero endings, are not established

## Claim

On the 87 distinct CC0 `size_class=variable` files of lead #87, a k=5 parse (q zero bits, stop bit 1, 5-bit suffix; escape at q >= 17 parsed as an ordinary token) that accepts a token only when its whole length fits inside the payload ends 0-7 bits before the payload end. The residual-length histogram is 0: 11, 1: 8, 2: 17, 3: 17, 4: 14, 5: 14, 6: 4, 7: 2.

The lead's final run of 1 bits is fully accounted for by those leftover bits and the last accepted token. Let `L` be the leftover bits, `q` and `s` the last accepted token's q and suffix, and `p` the suffix of the token before it. The trailing run of `p + "0"*q + "1" + s + L` (include `p` only when `q = 0`) equals the measured full-payload trailing run on 87 of 87 files. There is no separate 1-bit end marker to account for.

Consequences for the lead:

- The five zero-ending payloads are exactly the five whose leftover bits end in 0. Their residuals are 1431 `110`, 2152 `0110`, 5286 `100`, 6345 `0110`, 7802 `01110`. The final 0 is therefore outside the last complete token, not a property of the last token's suffix.
- The two ten-bit runs, 3210 and 6343, are 2 leftover 1 bits + six 1 bits from `q = 0, s = 31` + two 1 bits from the preceding suffix (`11011` and `01011`), giving 10. The other run lengths decompose the same way.
- For 76 of the 87 files the terminal run begins in bits outside the last complete token; for 11 the leftover is empty and the run is entirely token bits.

A separate tool issue surfaced. The upstream `tools/orf_tokens.py` `scan()` at commit a3fdd6f accepts a final token whose stop bit is inside the payload but whose 5-bit suffix lies past the payload end; it reads that suffix from zero padding. On six files its `bits consumed` is 1-2 bits larger than the payload: 1079, 2150, 7266, 7796, 7798 and 7801. The bounded parse leaves 6-7 bits on those six and rejects the extra token. The trailing-one counts themselves are unaffected because they count bytes, but `orf_tokens.py --all` reports an end position past the payload and a last token that is not in the file on those six.

Not established: whether the leftover bits are encoder padding or the start of a truncated final token. The leftover length is exactly the payload's byte-alignment remainder (0-7), and 49 of the 76 non-empty residuals are all 1s while 27 are not, so no fixed 0-fill or 1-fill rule fits. The zero endings are explained only as "the leftover ends in 0"; a deeper cause is not shown.

## Original evidence

Lead #87, opened by @radialmonster on 2026-10-19, counts trailing 1 bits in the last byte of the then-available CC0 variable-size files and reports 82 of 87 positive with runs of 1 to 10. The corrected full-cohort counts are verified in `2026-10-21--radialmonster--compressed-tail-full-cohort-reproduction` (PR #134); that finding explicitly leaves the token endpoint, padding and the zero-ending cause untested. The token model and the payload locator are from #11 and `tools/orf_tokens.py` (last changed at a3fdd6f); the cohort is the frozen 87-row file `tools/cohorts/lead87-trailing-ones-v1-full.json`, SHA-256 `13d58cd6149671e53cbd853956ac40f0b4673f00bebe3b79e0d10fd1f2ce49e2`.

## Verification

Self-run by the finder on 2026-10-21 UTC, after the lead and after finding PR #134. All 87 files are the frozen cohort; each local file's SHA-256 was checked against the cohort before measurement, and no unused publicly listed CC0 file exists (the catalogue has 104 CC0 files, all already used or listed). This is a new measurement on the same cohort (bounded token endpoint vs. the earlier last-byte count), not unseen-body validation.

Method, fixed before looking at the results: parse MSB-first; accept a token only if `pos + q + 6 <= payload_bits`; stop at the first token that does not fit; call the remaining 0-7 bits the residual. Decompose the full-payload trailing run as described above. The script is in Reproduce.

Residual length: 0: 11, 1: 8, 2: 17, 3: 17, 4: 14, 5: 14, 6: 4, 7: 2.
Full-payload trailing run: 0: 5, 1: 12, 2: 8, 3: 8, 4: 12, 5: 8, 6: 17, 7: 8, 8: 7, 10: 2. This matches the corrected histogram in #134 exactly.

Key rows (residual bits are the payload bits after the last accepted token; `prev suffix` is the preceding token's suffix):

| raw.pixls.us id | residual | residual bits | q | suffix | prev suffix | run |
| ---: | ---: | --- | ---: | --- | --- | ---: |
| 1431 | 3 | `110` | 4 | `01011` | `10011` | 0 |
| 2152 | 4 | `0110` | 0 | `11100` | `11000` | 0 |
| 5286 | 3 | `100` | 1 | `00100` | `00011` | 0 |
| 6345 | 4 | `0110` | 0 | `00001` | `00000` | 0 |
| 7802 | 5 | `01110` | 0 | `00110` | `00000` | 0 |
| 3210 | 2 | `11` | 0 | `11111` | `11011` | 10 |
| 6343 | 2 | `11` | 0 | `11111` | `01011` | 10 |
| 1079 | 6 | `010011` | 1 | `00011` | `00000` | 2 |
| 2150 | 7 | `0011111` | 0 | `01010` | `10111` | 5 |
| 7266 | 7 | `0001111` | 0 | `00010` | `00010` | 4 |
| 7796 | 6 | `001101` | 0 | `01110` | `10000` | 1 |
| 7798 | 6 | `011011` | 4 | `00110` | `00110` | 2 |
| 7801 | 6 | `001101` | 0 | `00010` | `01001` | 1 |

The six 6-7-bit residuals are the six files on which upstream `scan()` overshoots the payload by 1-2 bits; 1079, 2150, 7266, 7796, 7798 and 7801. The reconstruction check had 0 mismatches on all 87. Every file's payload ends at the end of the file; there are no trailing bytes after the payload to complete a leftover token.

Limits: one token model (k=5, escape skip 0); the residual is not decoded or assigned a meaning; no claim about a wider range of bodies or about a decoder's behavior at the end. The difference between padding and a truncated final token is not resolved.

Independent verification was conducted by @ruedbi on 2026-11-17 using Python standard library (Python 3.8.10) with `scan_fit()` on local samples from the frozen cohort (ids 1993, 1994, 1995, 1996, 1997, 1998). Across all tested files, the bounded parse terminated with residuals strictly between 0 and 7 bits (residual lengths: 1993: 4; 1994: 4; 1995: 2; 1996: 3; 1997: 4; 1998: 4), and the trailing run reconstructed from the terminal tokens and residual matched the full-payload trailing ones run exactly with 0 mismatches.

## Reproduce

Download the CC0 files outside the repository, then run the script from the repository root. The downloader fetches the whole CC0 set; the cohort JSON selects the 87 measured hashes.

```sh
python -I tools/pixls_samples.py download /path/to/lead87-samples
python -I tools/pixls_samples.py check /path/to/lead87-samples/*
python -I endpoint.py /path/to/lead87-samples
```

`endpoint.py`:

```python
import collections
import hashlib
import json
import os
import sys

sys.path.insert(0, "tools")
import orf_tokens as T

WIN = 12


def scan_fit(buf):
    """k=5 parse; accept a token only if q zeros + stop + 5 suffix bits fit."""
    nbits = len(buf) * 8
    pad = buf + bytes(WIN)
    pos = 0
    last = (None, None)
    prev = (None, None)
    while pos + 6 <= nbits:
        win = int.from_bytes(pad[pos >> 3:(pos >> 3) + WIN], "big")
        avail = WIN * 8 - (pos & 7)
        v = win & ((1 << avail) - 1)
        if v == 0 or avail - v.bit_length() + 6 > avail:
            q = 0
            p = pos
            while p < nbits and not (buf[p >> 3] >> (7 - (p & 7))) & 1:
                q += 1
                p += 1
            if p + 6 > nbits:
                break
            s = 0
            for k in range(1, 6):
                s = (s << 1) | ((buf[(p + k) >> 3] >> (7 - ((p + k) & 7))) & 1)
            pos = p + 6
        else:
            q = avail - v.bit_length()
            if pos + q + 6 > nbits:
                break
            s = (v >> (avail - q - 6)) & 31
            pos += q + 6
        prev, last = last, (q, s)
    return pos, last[0], last[1], prev[0], prev[1]


def trailing_ones(buf):
    n = 0
    for b in reversed(buf):
        k = 0
        while k < 8 and (b >> k) & 1:
            k += 1
        n += k
        if k < 8:
            break
    return n


def main(sample_dir):
    cohort = json.load(open("tools/cohorts/lead87-trailing-ones-v1-full.json", encoding="utf-8"))
    index = {}
    for root, _, files in os.walk(sample_dir):
        for name in files:
            index[name.split("_")[0]] = os.path.join(root, name)
    residual_hist = collections.Counter()
    run_hist = collections.Counter()
    bad = []
    for s in cohort["samples"]:
        p = index[s["id"]]
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if sha != s["sha256"]:
            bad.append((s["id"], "sha"))
            continue
        w, h, buf = T.locate(p)
        nbits = len(buf) * 8
        endpos, q, suf, pq, ps = scan_fit(buf)
        residual = nbits - endpos
        resbits = format(buf[-1], "08b")[8 - residual:] if residual else ""
        run = trailing_ones(buf)
        tail = (format(ps, "05b") if q == 0 and ps is not None else "")
        tail += "0" * q + "1" + format(suf, "05b") + resbits
        reconstructed = len(tail) - len(tail.rstrip("1"))
        if reconstructed != run:
            bad.append((s["id"], "run", reconstructed, run))
        residual_hist[residual] += 1
        run_hist[run] += 1
        print("%s\t%d\t%s\t%d\t%d\t%d\t%d\t%d" % (
            s["id"], residual, resbits, q, suf, ps if ps is not None else -1, run, reconstructed))
    print("residual", dict(sorted(residual_hist.items())))
    print("run", dict(sorted(run_hist.items())))
    print("bad", bad)


if __name__ == "__main__":
    main(sys.argv[1])
```

Expected final three lines:

```text
residual {0: 11, 1: 8, 2: 17, 3: 17, 4: 14, 5: 14, 6: 4, 7: 2}
run {0: 5, 1: 12, 2: 8, 3: 8, 4: 12, 5: 8, 6: 17, 7: 8, 8: 7, 10: 2}
bad []
```
