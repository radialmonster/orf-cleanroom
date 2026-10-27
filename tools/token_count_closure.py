#!/usr/bin/env python3
"""Whole-payload token-count closure under fixed and causal adaptive suffix widths.

Original measurement for specs/V1.md G3/G8 and lead #339; not a decoder.
Parse from payload bit 0 (orf_tokens.locate), MSB first. A token is q zero
bits, one stop bit and k suffix bits, with k chosen by the rule BEFORE the
token. q >= 17 (candidate escape) consumes the same q+1+k bits and no more.
The token value used for rule state is u = (q << k) | s, or 17 << k for an
escape. k is clamped to [kmin, 12]. Only complete tokens are counted. The
score is d = tokens - W*H, rel = d / (W*H), and the unconsumed residual bits.
A correct one-token-per-site grammar would give d near 0 on every file; a
small d alone does not prove a syntax.

Rules (frozen 2026-10-26 before any cohort results):
  F4 F5 F6 F7      fixed k; F5 is the #11 parse.
  J<m>c<c>n<n>     JPEG-LS-style accumulator per context (c=1 shared, c=2 by
                   token index mod 2): N=1, A=2**m at start; k = smallest
                   k >= m with N<<k >= A; then A += u, N += 1, and at N == n
                   both halve. m in {0,5}, c in {1,2}, n in {8,32,128}.
  P<l>o<o>         k = max(5, bitlen(u[t-l]) - o), l in {1,2}, o in {0,1,2};
                   u before the first token is 0.
  Mo<o>            k = max(5, bitlen(max(u[t-1], u[t-2])) - o), o in {0,1,2}.

--table adds the F5 joint count of min(q,17) x suffix (18 x 32, row-major).
--summarize reads this tool's JSON lines and prints, per rule, the files with
|rel| < 1e-4 and < 1e-3 and the median |rel|, split by odd/even raw.pixls.us
id (declared discovery/validation halves); the Spearman rank correlation of
bpp with F5 rel over all files and within each public name (extension
dropped) with three or more files; and, with tables, for each declared token
predicate the min and max over files of count/d (files with d >= 1000).
A predicate counting exactly the extra tokens would give 1 on every file.
These are descriptive statistics, not significance tests.

    python -I -B tools/token_count_closure.py --sample ID PUBLIC_NAME FILE
        [--sample ...] [--rules all|F5,Mo2,...] [--table] [--hash]
    python -I -B tools/token_count_closure.py --summarize RESULTS.jsonl [...]
    python -I -B tools/test_token_count_closure.py

Each sample prints one JSON line, so separate runs can be concatenated.
--hash adds the input SHA-256 (leave it off for files you may not identify).
Stdlib, Python 3.8+. Reads input files and prints aggregates only.
"""
import argparse
import array
import collections
import hashlib
import json
import os
import statistics
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_tokens as T  # noqa: E402

KMAX = 12
ESC_Q = 17
WIN = 16  # bytes in the read window; enough for q + 1 + KMAX in the fast path


def rule_names():
    names = ["F4", "F5", "F6", "F7"]
    for kmin in (0, 5):
        for ctx in (1, 2):
            for nmax in (8, 32, 128):
                names.append("J%dc%dn%d" % (kmin, ctx, nmax))
    for lag in (1, 2):
        for off in (0, 1, 2):
            names.append("P%do%d" % (lag, off))
    for off in (0, 1, 2):
        names.append("Mo%d" % off)
    return names


RULES = rule_names()


def run(buf, rule):
    """Parse buf under one rule. Returns (tokens, bits consumed, escapes, sum of k)."""
    if rule not in RULES:
        raise ValueError("unknown rule")
    nbits = len(buf) * 8
    pad = bytes(buf) + bytes(WIN)
    frm = int.from_bytes
    pos = n = esc = ksum = 0
    kind = rule[0]
    if kind == "F":
        fixed = int(rule[1:])
    elif kind == "J":
        kmin, ctx, nmax = int(rule[1]), int(rule[3]), int(rule[5:])
        acc = [1 << kmin] * ctx
        cnt = [1] * ctx
    elif kind == "P":
        lag, off = int(rule[1]), int(rule[3])
    else:
        off = int(rule[2])
    u1 = u2 = 0
    while True:
        if kind == "F":
            k = fixed
        elif kind == "J":
            c = n % ctx if ctx > 1 else 0
            a, nn = acc[c], cnt[c]
            k = kmin
            while (nn << k) < a and k < KMAX:
                k += 1
        else:
            if kind == "P":
                k = (u1 if lag == 1 else u2).bit_length() - off
            else:
                k = (u1 if u1 > u2 else u2).bit_length() - off
            k = 5 if k < 5 else (KMAX if k > KMAX else k)
        if pos + 1 + k > nbits:
            break
        avail = WIN * 8 - (pos & 7)
        v = frm(pad[pos >> 3:(pos >> 3) + WIN], "big") & ((1 << avail) - 1)
        if v == 0 or avail - v.bit_length() + 1 + k > avail:
            # zero run (or run plus suffix) longer than the window: count bit by bit
            q = 0
            p = pos
            while p < nbits and not (buf[p >> 3] >> (7 - (p & 7))) & 1:
                q += 1
                p += 1
            if p + 1 + k > nbits:
                break
            s = 0
            for i in range(1, k + 1):
                s = (s << 1) | ((buf[(p + i) >> 3] >> (7 - ((p + i) & 7))) & 1)
            pos = p + 1 + k
        else:
            q = avail - v.bit_length()
            if pos + q + 1 + k > nbits:
                break
            s = (v >> (avail - q - 1 - k)) & ((1 << k) - 1)
            pos += q + 1 + k
        if q >= ESC_Q:
            esc += 1
            u = ESC_Q << k
        else:
            u = (q << k) | s
        if kind == "J":
            acc[c] = a + u
            nn += 1
            if nn == nmax:
                acc[c] >>= 1
                nn >>= 1
            cnt[c] = nn
        u2, u1 = u1, u
        ksum += k
        n += 1
    return n, pos, esc, ksum


def joint_table(buf):
    """F5 counts of min(q,17)*32 + suffix over the whole payload (576 cells)."""
    qa, sa = array.array("B"), array.array("B")
    T.scan(buf, 1 << 62, 0, 0, None, qa, sa, ESC_Q, None, 0)
    tab = [0] * (18 * 32)
    for q, s in zip(qa, sa):
        tab[q * 32 + s] += 1
    return tab


def report(sample_id, name, path, rules, table, with_hash):
    w, h, buf = T.locate(path)
    if w <= 0 or h <= 0:
        raise ValueError("bad payload geometry")
    out = {"pixls_id": sample_id, "pixls_name": name, "payload_w": w, "payload_h": h,
           "payload_bytes": len(buf), "bpp": 8 * len(buf) / (w * h), "rules": {}}
    if with_hash:
        with open(path, "rb") as handle:
            out["sha256"] = hashlib.sha256(handle.read()).hexdigest()
    for rule in rules:
        n, used, esc, ksum = run(buf, rule)
        out["rules"][rule] = {"tokens": n, "d": n - w * h, "rel": (n - w * h) / (w * h),
                              "residual_bits": len(buf) * 8 - used, "escapes": esc,
                              "mean_k": ksum / n if n else 0.0}
    if table:
        out["f5_table"] = joint_table(buf)
    return out


def ranks(values):
    """Average ranks (ties share the mean rank)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for t in range(i, j + 1):
            out[order[t]] = (i + j) / 2
        i = j + 1
    return out


def spearman(x, y):
    a, b = ranks(x), ranks(y)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sab = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    saa = sum((p - ma) ** 2 for p in a)
    sbb = sum((q - mb) ** 2 for q in b)
    return sab / (saa * sbb) ** 0.5 if saa > 0 and sbb > 0 else None


def predicates():
    """Declared token predicates on (q capped at 17, suffix)."""
    out = {}
    for t in range(1, 18):
        out["q>=%d" % t] = lambda q, s, t=t: q >= t
        out["q==%d" % t] = lambda q, s, t=t: q == t
    for v in range(32):
        out["s==%d" % v] = lambda q, s, v=v: s == v
        out["q==0&s==%d" % v] = lambda q, s, v=v: q == 0 and s == v
        out["q>=1&s==%d" % v] = lambda q, s, v=v: q >= 1 and s == v
    for v in range(1, 32):
        out["s>=%d" % v] = lambda q, s, v=v: s >= v
        out["q==0&s>=%d" % v] = lambda q, s, v=v: q == 0 and s >= v
    for b in range(5):
        out["q>=1&b%d" % b] = lambda q, s, b=b: q >= 1 and (s >> b) & 1 == 1
    return out


def summarize(paths):
    files = {}
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rec = json.loads(line)
                    if rec["pixls_id"] in files:
                        raise ValueError("duplicate pixls_id in results")
                    files[rec["pixls_id"]] = rec
    if not files:
        raise ValueError("no results")
    rules = sorted({r for rec in files.values() for r in rec["rules"]}, key=RULES.index)
    out = {"files": len(files), "rules": {}}
    for rule in rules:
        cell = {}
        for half, parity in (("odd", 1), ("even", 0), ("all", None)):
            vals = [abs(rec["rules"][rule]["rel"]) for i, rec in files.items()
                    if rule in rec["rules"] and (parity is None or int(i) % 2 == parity)]
            if vals:
                cell[half] = {"n": len(vals), "lt_1e-4": sum(v < 1e-4 for v in vals),
                              "lt_1e-3": sum(v < 1e-3 for v in vals),
                              "median_abs_rel": statistics.median(vals)}
        out["rules"][rule] = cell
    f5 = {i: rec for i, rec in files.items() if "F5" in rec["rules"]}
    if len(f5) >= 2:
        ids = sorted(f5, key=int)
        out["f5_vs_bpp"] = {
            "spearman": spearman([f5[i]["bpp"] for i in ids], [f5[i]["rules"]["F5"]["rel"] for i in ids]),
            "negative_d": sum(f5[i]["rules"]["F5"]["d"] < 0 for i in ids),
            "min_rel": min(f5[i]["rules"]["F5"]["rel"] for i in ids),
            "max_rel": max(f5[i]["rules"]["F5"]["rel"] for i in ids)}
        groups = collections.defaultdict(list)
        for i in ids:
            groups[os.path.splitext(f5[i]["pixls_name"])[0]].append(i)
        out["f5_vs_bpp"]["within_name"] = {
            g: {"n": len(v), "spearman": spearman([f5[i]["bpp"] for i in v],
                                                  [f5[i]["rules"]["F5"]["rel"] for i in v])}
            for g, v in sorted(groups.items()) if len(v) >= 3}
    tabled = [rec for rec in f5.values() if "f5_table" in rec and rec["rules"]["F5"]["d"] >= 1000]
    if tabled:
        cells = {}
        for name, pred in predicates().items():
            ratios = [sum(rec["f5_table"][c] for c in range(576) if pred(c // 32, c % 32))
                      / rec["rules"]["F5"]["d"] for rec in tabled]
            cells[name] = {"min": min(ratios), "max": max(ratios)}
        best = sorted(cells.items(), key=lambda kv: (kv[1]["max"] / kv[1]["min"]
                                                     if kv[1]["min"] > 0 else float("inf"), kv[0]))
        out["predicates"] = {"files": len(tabled), "declared": len(cells),
                             "tightest": [dict(name=k, **v) for k, v in best[:10]]}
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=__doc__.split("\n\n", 1)[1])
    parser.add_argument("--sample", nargs=3, action="append", metavar=("ID", "PUBLIC_NAME", "FILE"))
    parser.add_argument("--rules", default="all", help="all, or a comma list (default all)")
    parser.add_argument("--table", action="store_true", help="add the F5 q x suffix table")
    parser.add_argument("--hash", action="store_true", help="add the input SHA-256")
    parser.add_argument("--summarize", nargs="+", metavar="RESULTS")
    args = parser.parse_args(argv)
    if args.summarize:
        if args.sample:
            parser.error("--summarize takes no --sample")
        try:
            print(json.dumps(summarize(args.summarize), indent=2, allow_nan=False))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print("summarize: %s" % type(exc).__name__, file=sys.stderr)
            return 1
        return 0
    if not args.sample:
        parser.error("no --sample (or use --summarize)")
    rules = RULES if args.rules == "all" else args.rules.split(",")
    if any(r not in RULES for r in rules) or len(set(rules)) != len(rules):
        parser.error("unknown or repeated rule; known: " + ",".join(RULES))
    ids = [s[0] for s in args.sample]
    if any(not i.isascii() or not i.isdecimal() or int(i) <= 0 for i in ids) or len(set(ids)) != len(ids):
        parser.error("sample IDs must be distinct positive ASCII decimals")
    failed = False
    for index, (sample_id, name, path) in enumerate(args.sample, 1):
        try:
            print(json.dumps(report(sample_id, name, path, rules, args.table, args.hash)), flush=True)
        except (OSError, ValueError, KeyError, IndexError, TypeError, struct.error) as exc:
            failed = True
            print("input %d: %s" % (index, type(exc).__name__), file=sys.stderr)
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
