#!/usr/bin/env python3
"""Independent synthetic candidate-parse checks; no real samples needed."""
import collections
import contextlib
import io
import json
import os
import random
import sys
import stat
import struct
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suffix_width_probe as probe


def reference(data, k, stop):
    bits = "".join(format(x, "08b") for x in data)
    pos = 0
    hist = collections.Counter()
    while pos < len(bits):
        end = bits.find(str(stop), pos)
        if end < 0 or end + k + 1 > len(bits):
            break
        hist[end - pos] += 1
        pos = end + k + 1
    return hist, pos


class Tests(unittest.TestCase):
    def test_public_identity_validation_before_reporting(self):
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        cases = [([('1', 'public'), ('01', 'public')], False),
                 ([('1', 'public'), ('2', 'private/path')], False),
                 ([('1', 'public'), ('2', '')], False), ([('1', 'public'), ('2', 'private\\path')], False),
                 ([('1', 'public'), ('2', 'bad\nname')], False), ([('0', 'public')], False),
                 ([('1', 'public')], True)]
        if limit:
            cases.append(([('9' * (limit + 1), 'public')], False))
        for samples, simulated in cases:
            args = []
            for sid, name in samples:
                args += ['--sample', sid, name, 'unused']
            out, err = io.StringIO(), io.StringIO()
            conversion = mock.patch.object(probe, 'int', side_effect=ValueError('private detail'), create=True) if simulated else contextlib.nullcontext()
            with self.subTest(samples=samples[0][0][:4], simulated=simulated), mock.patch.object(probe, 'report') as report, conversion, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    probe.main(args)
                self.assertEqual(caught.exception.code, 2)
                report.assert_not_called()
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('private', err.getvalue())

    def test_valid_public_identity_spelling_is_preserved(self):
        name = 'OM - Élite "camera" (4:3).ORF'
        def report(sid, public, path, *args, **kwargs):
            return {'pixls_id': sid, 'pixls_name': public}
        args = ['--sample', '01', name, 'unused']
        out = io.StringIO()
        with mock.patch.object(probe, 'report', side_effect=report), contextlib.redirect_stdout(out):
            status = probe.main(args)
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(out.getvalue())['samples'], [{'pixls_id': '01', 'pixls_name': name}])


    def check(self, data, k, stop):
        hist, end = reference(data, k, stop)
        result = probe.scan(data, k, stop)
        self.assertEqual(result["q_histogram"], [[q, hist[q]] for q in sorted(hist)])
        self.assertEqual(result["tokens"], sum(hist.values()))
        self.assertEqual(result["q_ge_17"], sum(n for q, n in hist.items() if q >= 17))
        self.assertEqual(result["bits_consumed"], end)
        self.assertEqual(result["unconsumed_bits"], len(data) * 8 - end)
        self.assertEqual(sum((q + k + 1) * n for q, n in hist.items()), end)

    def test_hand_boundaries_and_complements(self):
        # 100 010 11: k2/stop1 gives q0 then q1, final incomplete stop.
        self.assertEqual(probe.scan(bytes([0x8b]), 2, 1)["q_histogram"], [[0, 1], [1, 1]])
        self.assertEqual(probe.scan(bytes([0x8b]), 2, 1)["bits_consumed"], 7)
        self.assertEqual(probe.scan(bytes([0x74]), 2, 0)["bits_consumed"], 7)
        for stop in (0, 1):
            for k in range(2, 9):
                for data in (b"", b"\0", b"\xff", b"\x01", b"\x80", bytes(8) + b"\xff"):
                    self.check(data, k, stop)

    def test_exhaustive_bytes_and_random_long(self):
        rng = random.Random(20261021)
        for stop in (0, 1):
            for k in range(2, 9):
                for byte in range(256):
                    self.check(bytes([byte]), k, stop)
                for _ in range(20):
                    self.check(bytes(rng.randrange(256) for _ in range(200)), k, stop)

    def test_escapes_and_incomplete_tail(self):
        for stop in (0, 1):
            for k in range(2, 9):
                data = bytes(20) + b"\xff\xff" + bytes(12)
                if not stop:
                    data = bytes(x ^ 255 for x in data)
                self.check(data, k, stop)
                self.assertGreater(probe.scan(data, k, stop)["q_ge_17"], 0)
        for k, stop in ((1, 1), (9, 1), (5, 2)):
            with self.assertRaises(ValueError):
                probe.scan(b"\xff", k, stop)

    def test_q0_blocks_against_independent_bit_parser(self):
        rng = random.Random(197)
        for data in (b"", b"\0" * 20, b"\xff" * 20,
                     bytes(rng.randrange(256) for _ in range(100))):
            bits = "".join(format(x, "08b") for x in data)
            for stop in (0, 1):
                for k in range(2, 9):
                    pos, flags = 0, []
                    while pos < len(bits):
                        end = bits.find(str(stop), pos)
                        if end < 0 or end + k + 1 > len(bits):
                            break
                        flags.append(end == pos)
                        pos = end + k + 1
                    for size in (1, 3, 7, 1000):
                        result = probe.scan(data, k, stop, size)
                        summary = result["q0_blocks"]
                        complete = len(flags) // size * size
                        hist = collections.Counter(sum(flags[i:i + size])
                                                   for i in range(0, complete, size))
                        self.assertEqual(summary["full_block_q0_histogram"],
                                         [[q0, hist[q0]] for q0 in sorted(hist)])
                        self.assertEqual(summary["full_blocks"], complete // size)
                        self.assertEqual(summary["tail_tokens"], len(flags) - complete)
                        self.assertEqual(summary["tail_q0"], sum(flags[complete:]))
                        self.assertEqual(sum(q0 * n for q0, n in hist.items())
                                         + summary["tail_q0"], sum(flags))
                        self.assertEqual(result["bits_consumed"], pos)
                    self.assertNotIn("q0_blocks", probe.scan(data, k, stop))
        for invalid in (-1, 1.5):
            with self.assertRaises(ValueError):
                probe.scan(b"\xff", 5, 1, invalid)

    def test_real_container_report_and_rejection(self):
        class Input(io.BytesIO):
            def fileno(self):
                return 123
        for endian, marker in (("<", b"II"), (">", b"MM")):
            entries = [(0x100, 10), (0x101, 10), (0x103, 1), (0x111, 74), (0x117, 2)]
            header = marker + struct.pack(endian + "HIH", 0x4f52, 8, 5)
            table = b"".join(struct.pack(endian + "HHII", tag, 4, 1, value)
                             for tag, value in entries)
            data = header + table + bytes(4) + b"\x8b\x81"
            regular = types.SimpleNamespace(st_mode=stat.S_IFREG)
            with mock.patch.object(probe.os, "stat", return_value=regular), mock.patch.object(probe.os, "fstat", return_value=regular):
                with mock.patch("builtins.open", return_value=Input(data)):
                    result = probe.report("1", "public", "input")
                self.assertEqual((result["payload_w"], result["payload_h"], result["payload_bytes"]), (10, 10, 2))
                self.assertEqual(len(result["cells"]), 14)
                for cell in result["cells"]:
                    hist, end = reference(data[-2:], cell["k"], cell["stop_bit"])
                    self.assertEqual(cell["bits_consumed"], end)
                    self.assertEqual(cell["tokens_per_pixel"], sum(hist.values()) / 100)
                with mock.patch("builtins.open", return_value=Input(data[:-1])):
                    with self.assertRaises(ValueError):
                        probe.report("1", "public", "input")

    def test_cli_mixed_failure_sanitization(self):
        output = io.StringIO()
        with mock.patch.object(probe, "report", side_effect=[{"pixls_id": "1"}, ValueError("secret path")]):
            with contextlib.redirect_stdout(output):
                status = probe.main(["--sample", "1", "one", "file1", "--sample", "2", "two", "file2"])
        self.assertEqual(status, 1)
        parsed = json.loads(output.getvalue())
        self.assertEqual(parsed["samples"], [{"pixls_id": "1"}])
        self.assertEqual(parsed["failures"], [{"pixls_id": "2", "error": "invalid_or_unreadable_input"}])
        self.assertNotIn("secret", output.getvalue())

    def test_cli_block_option_forwarding_and_rejection(self):
        with mock.patch.object(probe, "report", return_value={}) as report:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main(["--sample", "1", "one", "file1",
                                             "--block-tokens", "7"]), 0)
            report.assert_called_once_with("1", "one", "file1", 7)
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                probe.main(["--sample", "1", "one", "file1", "--block-tokens", "-1"])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
