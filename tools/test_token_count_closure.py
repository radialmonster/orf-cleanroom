#!/usr/bin/env python3
"""Synthetic checks for token_count_closure.py; no real samples needed."""
import contextlib
import hashlib
import io
import json
import os
import random
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import token_count_closure as C


class State:
    """Independent restatement of the rule state, shared by the reference parser and encoder."""

    def __init__(self, rule):
        self.rule = rule
        self.us = []
        if rule[0] == "J":
            self.kmin, self.ctx, self.nmax = int(rule[1]), int(rule[3]), int(rule[5:])
            self.a = [2 ** self.kmin] * self.ctx
            self.n = [1] * self.ctx

    def k(self):
        r = self.rule
        if r[0] == "F":
            return int(r[1:])
        if r[0] == "J":
            c = len(self.us) % self.ctx
            k = self.kmin
            while self.n[c] * 2 ** k < self.a[c] and k < 12:
                k += 1
            return k
        prev = lambda lag: self.us[-lag] if len(self.us) >= lag else 0
        if r[0] == "P":
            base = prev(int(r[1])).bit_length() - int(r[3])
        else:
            base = max(prev(1), prev(2)).bit_length() - int(r[2])
        return min(12, max(5, base))

    def push(self, q, s, k):
        u = 17 * 2 ** k if q >= 17 else q * 2 ** k + s
        if self.rule[0] == "J":
            c = len(self.us) % self.ctx
            self.a[c] += u
            self.n[c] += 1
            if self.n[c] == self.nmax:
                self.a[c] //= 2
                self.n[c] //= 2
        self.us.append(u)


def reference(data, rule):
    bits = "".join(format(x, "08b") for x in data)
    st = State(rule)
    pos = esc = ksum = 0
    while True:
        k = st.k()
        stop = bits.find("1", pos)
        if stop < 0 or stop + 1 + k > len(bits):
            break
        q = stop - pos
        s = int(bits[stop + 1:stop + 1 + k], 2) if k else 0
        pos = stop + 1 + k
        esc += q >= 17
        ksum += k
        st.push(q, s, k)
    return len(st.us), pos, esc, ksum


def encode(rule, values):
    """Encode values (each < 17 << k at its time) under the rule; returns bytes and pad bits."""
    st = State(rule)
    out = []
    for v in values:
        k = st.k()
        q, s = v >> k, v & ((1 << k) - 1)
        out.append("0" * q + "1" + (format(s, "0%db" % k) if k else ""))
        st.push(q, s, k)
    bits = "".join(out)
    pad = (-len(bits)) % 8
    bits += "0" * pad
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)), pad


class Tests(unittest.TestCase):
    def test_identity_rejected_before_any_sample_read(self):
        for samples in ((('1', 'good.ORF'), ('01', 'good.ORF')),
                        (('1', 'good.ORF'), ('2', 'private/path.ORF')),
                        (('1', 'private\\path.ORF'),), (('1', 'name\n.ORF'),),
                        (('1', ''),), (('0', 'good.ORF'),), (('-1', 'good.ORF'),),
                        (('\u0661', 'good.ORF'),)):
            args = []
            for sid, name in samples:
                args += ['--sample', sid, name, 'unused']
            out, err = io.StringIO(), io.StringIO()
            with self.subTest(samples=samples), mock.patch.object(C, 'report') as report, \
                 contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as raised:
                    C.main(args)
                self.assertEqual(raised.exception.code, 2)
                report.assert_not_called()
                self.assertEqual(out.getvalue(), '')

    def test_valid_public_punctuation_and_optional_hash(self):
        name = 'OM System - STYLUS1,1s - "high-res" (4:3).ORF'
        for extra, expected in (([], False), (['--hash'], True)):
            with self.subTest(extra=extra), mock.patch.object(C, 'report', return_value={'ok': True}) as report, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(C.main(['--sample', '01', name, 'private-file'] + extra), 0)
            self.assertEqual(report.call_args.args[:3], ('1', name, 'private-file'))
            self.assertEqual(report.call_args.args[-1], expected)

    def test_report_uses_one_file_snapshot_for_hash_and_payload(self):
        tags = [(256, 2), (257, 2), (273, 62), (279, 8)]
        first = (struct.pack('<2sHIH', b'II', 42, 8, len(tags)) +
                 b''.join(struct.pack('<HHII', tag, 4, 1, value) for tag, value in tags) +
                 struct.pack('<I', 0) + b'\xff' * 8)
        second = first[:-8] + bytes(8)
        for with_hash in (False, True):
            with self.subTest(with_hash=with_hash), \
                    mock.patch('builtins.open', side_effect=[io.BytesIO(first), io.BytesIO(second)]) as opened:
                result = C.report('1', 'public.ORF', 'sample.ORF', ['F5'], False, with_hash)
            self.assertEqual(opened.call_count, 1)
            self.assertEqual(result['rules']['F5']['tokens'], C.run(b'\xff' * 8, 'F5')[0])
            if with_hash:
                self.assertEqual(result['sha256'], hashlib.sha256(first).hexdigest())
            else:
                self.assertNotIn('sha256', result)

    def test_rules_match_reference(self):
        rng = random.Random(20261026)
        cases = [b"", b"\0", b"\xff", bytes(20) + b"\x80\xff", bytes([0x80]) * 9]
        cases += [bytes(rng.randrange(256) for _ in range(rng.randrange(1, 60))) for _ in range(40)]
        # sparse ones: long zero runs and large q values
        cases += [bytes(rng.choice((0, 0, 0, 1, 0x40)) for _ in range(80)) for _ in range(10)]
        for rule in C.RULES:
            for data in cases:
                self.assertEqual(C.run(data, rule), reference(data, rule), (rule, data.hex()))

    def test_encoded_streams_close_exactly(self):
        rng = random.Random(7)
        for rule in C.RULES:
            values = [int(rng.expovariate(1 / 40)) % 500 for _ in range(3000)]
            data, pad = encode(rule, values)
            n, used, esc, ksum = C.run(data, rule)
            # trailing zero pad bits never complete a token
            self.assertEqual(n, len(values), rule)
            self.assertEqual(len(data) * 8 - used, pad, rule)

    def test_adaptive_stream_overcounts_under_f5(self):
        rng = random.Random(3)
        values = [rng.randrange(64, 200) for _ in range(4000)]
        data, _ = encode("P1o0", values)
        self.assertEqual(C.run(data, "P1o0")[0], len(values))
        self.assertGreater(C.run(data, "F5")[0], len(values))

    def test_unknown_rule(self):
        with self.assertRaises(ValueError):
            C.run(b"\xff", "F9")

    def test_joint_table_counts(self):
        data, _ = encode("F5", [0, 31, 32, 100, 17 * 32 + 3, 5])
        tab = C.joint_table(data)
        self.assertEqual(sum(tab), 6)
        for q, s in ((0, 0), (0, 31), (1, 0), (3, 4), (17, 3), (0, 5)):
            self.assertEqual(tab[q * 32 + s], 1)

    def test_ranks_and_spearman(self):
        self.assertEqual(C.ranks([3, 1, 1, 2]), [3.0, 0.5, 0.5, 2.0])
        self.assertAlmostEqual(C.spearman([1, 2, 3, 4], [10, 20, 25, 99]), 1.0)
        self.assertAlmostEqual(C.spearman([1, 2, 3], [3, 2, 1]), -1.0)
        self.assertIsNone(C.spearman([1, 1, 1], [1, 2, 3]))

    def test_summarize(self):
        recs = []
        for i, (bpp, d) in enumerate([(6.0, 2), (6.5, 300), (7.0, 2000), (8.0, 9000)], 1):
            tab = [0] * 576
            tab[1 * 32] = d  # q==1 tokens equal the excess exactly
            tab[0] = 100000 - d
            recs.append({"pixls_id": str(i), "pixls_name": "Make - Body - 16bit (4:3).ORF",
                         "bpp": bpp, "rules": {"F5": {"d": d, "rel": d / 100000},
                                               "F6": {"d": -d, "rel": -d / 100000}},
                         "f5_table": tab})
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "r.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(json.dumps(r) for r in recs) + "\n")
            out = C.summarize([path])
            self.assertEqual(out["files"], 4)
            self.assertEqual(out["rules"]["F5"]["all"]["lt_1e-4"], 1)
            self.assertEqual(out["rules"]["F5"]["odd"]["n"], 2)
            self.assertAlmostEqual(out["f5_vs_bpp"]["spearman"], 1.0)
            self.assertEqual(out["f5_vs_bpp"]["negative_d"], 0)
            self.assertAlmostEqual(out["f5_vs_bpp"]["within_name"]["Make - Body - 16bit (4:3)"]["spearman"], 1.0)
            top = out["predicates"]["tightest"][0]
            self.assertEqual((out["predicates"]["files"], top["min"], top["max"]), (2, 1.0, 1.0))
            self.assertIn(top["name"], ("q==1", "q>=1"))
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(recs[0]) + "\n")
            with self.assertRaises(ValueError):
                C.summarize([path])

    def test_cli_errors(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            C.main(["--sample", "1", "x", "nope", "--rules", "F9"])
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.orf")
            with open(bad, "wb") as handle:
                handle.write(b"not a tiff")
            out = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
                self.assertEqual(C.main(["--sample", "1", "x", bad, "--rules", "F5"]), 1)
            self.assertNotIn(tmp, err.getvalue())
            short = os.path.join(tmp, "short.jsonl")
            rec = {"pixls_id": "1", "pixls_name": "x.ORF", "bpp": 7.0,
                   "rules": {"F5": {"d": 5000, "rel": 0.05}}, "f5_table": [1] * 10}
            with open(short, "w", encoding="utf-8-sig") as handle:
                handle.write(json.dumps(rec) + chr(10))
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
                self.assertEqual(C.main(["--summarize", short]), 1)
            self.assertIn("summarize: IndexError", err.getvalue())
            self.assertNotIn(tmp, err.getvalue())


if __name__ == "__main__":
    unittest.main()
