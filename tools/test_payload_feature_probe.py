#!/usr/bin/env python3
"""Independent direct bit-string and malformed-input checks for #299 baseline."""
from collections import Counter
import contextlib
import hashlib
import io
import itertools
import json
import math
import os
import random
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from payload_feature_probe import features, main, report, strip_extents, window_starts


def direct(buf):
    bits = "".join(format(byte, "08b") for byte in buf)
    groups = [(int(bit), len(list(run))) for bit, run in itertools.groupby(bits)]
    runs = [[0] * 16 for _ in range(2)]
    for bit, length in groups:
        runs[bit][min(length, 16) - 1] += 1
    counts = Counter(bits[i:i+2] for i in range(len(bits) - 1))
    histogram = [buf.count(value) for value in range(256)]
    return {
        "bytes": len(buf), "ones": bits.count("1"),
        "one_fraction": bits.count("1") / len(bits),
        "transition_counts_00_01_10_11": [counts[k] for k in ("00", "01", "10", "11")],
        "transition_fraction": sum(a != b for a, b in zip(bits, bits[1:])) / (len(bits) - 1),
        "byte_entropy_bits": -sum(n / len(buf) * math.log2(n / len(buf)) for n in histogram if n),
        "run_counts_by_bit_length_1_to_15_then_ge16": runs,
        "longest_run_by_bit": [max([n for value, n in groups if value == bit] or [0]) for bit in (0, 1)],
        "first_bit": groups[0][0], "first_run_bits": groups[0][1],
        "last_bit": groups[-1][0], "last_run_bits": groups[-1][1],
    }


def container(payload, order="<", overrides=None):
    tags = {0x100: 7, 0x101: 3, 0x111: 74, 0x117: len(payload), 0x103: 1}
    tags.update(overrides or {})
    data = (b"II" if order == "<" else b"MM") + struct.pack(order + "HIH", 0x4f52, 8, 5)
    for tag, value in sorted(tags.items()):
        data += struct.pack(order + "HHII", tag, 4, 1, value)
    return data + struct.pack(order + "I", 0) + payload


class FeatureTests(unittest.TestCase):
    def test_exhaustive_two_bytes(self):
        for value in range(65536):
            buf = value.to_bytes(2, "big")
            self.assertEqual(features(buf), direct(buf))

    def test_random_and_edge_runs(self):
        rng = random.Random(299)
        for length in (1, 3, 31, 256, 1024):
            for buf in (bytes(rng.randrange(256) for _ in range(length)),
                        b"\x00" * length, b"\xff" * length, b"\xaa" * length):
                got, reference = features(buf), direct(buf)
                self.assertAlmostEqual(got.pop("byte_entropy_bits"), reference.pop("byte_entropy_bits"), places=12)
                self.assertEqual(got, reference)
        with self.assertRaises(ValueError):
            features(b"")

    def test_window_geometry(self):
        self.assertEqual(window_starts(10, 2, 3), [0, 4, 8])
        self.assertEqual(window_starts(7, 2, 3), [0, 2, 5])
        for args in ((5, 2, 3), (10, 0, 3), (10, 2, 1)):
            with self.assertRaises(ValueError):
                window_starts(*args)

    def test_container_and_hash_gate(self):
        for order in ("<", ">"):
            data = container(bytes(range(30)), order)
            digest = hashlib.sha256(data).hexdigest()
            with patch("builtins.open", return_value=io.BytesIO(data)):
                row = report("1", "synthetic", digest, "unused", 3, 3)
            self.assertEqual(row["payload_offset"], 74)
            self.assertEqual([w["payload_byte_start"] for w in row["windows"]], [0, 13, 27])
            self.assertEqual(row["windows"][0]["features"], features(bytes(range(3))))
            with patch("builtins.open", return_value=io.BytesIO(data)):
                with self.assertRaises(ValueError):
                    report("1", "synthetic", "0" * 64, "unused", 3, 3)

    def test_invalid_strips_and_dimensions(self):
        for override in ({0x111: 999}, {0x117: 999}, {0x117: 0}, {0x100: 0}):
            data = container(b"abcdef", overrides=override)
            with patch("builtins.open", return_value=io.BytesIO(data)):
                with self.assertRaises(ValueError):
                    report("1", "synthetic", hashlib.sha256(data).hexdigest(), "unused", 1, 3)
        tags = {0x100: [2], 0x101: [2], 0x111: [0, 1], 0x117: [2, 2]}
        with patch("builtins.open", return_value=io.BytesIO(b"1234")):
            with patch("payload_feature_probe.Tiff") as tiff:
                tiff.return_value.all_ifds.return_value = [tags]
                with self.assertRaises(ValueError):
                    report("1", "synthetic", hashlib.sha256(b"1234").hexdigest(), "unused", 1, 3)

    def test_reject_multiple_dimension_values(self):
        for tag_index in (0, 1):
            data = bytearray(container(bytes(range(20))))
            # Width and height tags are the first two sorted IFD entries.
            struct.pack_into("<II", data, 10 + tag_index * 12 + 4, 2, len(data))
            data.extend(struct.pack("<II", 5, 6))
            with self.subTest(tag_index=tag_index), patch("builtins.open", return_value=io.BytesIO(data)):
                with self.assertRaises(ValueError):
                    report("1", "synthetic", hashlib.sha256(data).hexdigest(), "unused", 4, 3)

    def test_strip_validation_and_order(self):
        for offsets, counts in (([], []), ([0], [1, 1]), ([0], [0]),
                                ([-1], [2]), ([0], [11]), ([0, 1], [2, 2]),
                                ([0, 0], [2, 2]), (["0"], [2])):
            with self.assertRaises(ValueError):
                strip_extents(offsets, counts, 10)
        self.assertEqual(strip_extents([7, 1], [3, 4], 10), [
            {"strip_index": 0, "file_byte_start": 7, "payload_byte_start": 0, "bytes": 3},
            {"strip_index": 1, "file_byte_start": 1, "payload_byte_start": 3, "bytes": 4}])

    def test_real_multistrip_table_gap_and_reversed_physical_order(self):
        # Two 10-byte strips, table arrays at 74 and 82; bytes 90..99
        # form a gap. Table order deliberately reverses physical order.
        for order in ("<", ">"):
            data = (b"II" if order == "<" else b"MM") + struct.pack(order + "HIH", 0x4f52, 8, 5)
            for tag, count, value in ((0x100, 1, 5), (0x101, 1, 4), (0x103, 1, 1),
                                      (0x111, 2, 74), (0x117, 2, 82)):
                data += struct.pack(order + "HHII", tag, 4, count, value)
            data += struct.pack(order + "I", 0)
            data += struct.pack(order + "4I", 110, 100, 10, 10)
            data += b"G" * 10 + b"\xff" * 10 + b"\x00" * 10
            with patch("builtins.open", return_value=io.BytesIO(data)):
                row = report("1", "synthetic", hashlib.sha256(data).hexdigest(), "unused", 4, 3)
            self.assertEqual(row["payload_bytes"], 20)
            self.assertEqual([s["file_byte_start"] for s in row["strips"]], [110, 100])
            self.assertEqual(row["omitted_windows"], [
                {"payload_byte_start": 8, "reason": "crosses_strip_boundary"}])
            self.assertEqual([w["file_byte_start"] for w in row["windows"]], [110, 106])
            self.assertEqual([w["features"]["ones"] for w in row["windows"]], [0, 32])

    def test_boundary_exact_fit_and_adjacent_strips(self):
        data = bytes(range(20))
        tags = {0x100: [5], 0x101: [4], 0x111: [0, 10], 0x117: [10, 10]}
        for size, windows, accepted, omitted in ((10, 2, [0, 10], []),
                                                (4, 3, [0, 16], [8])):
            with patch("builtins.open", return_value=io.BytesIO(data)):
                with patch("payload_feature_probe.Tiff") as tiff:
                    tiff.return_value.all_ifds.return_value = [tags]
                    row = report("1", "synthetic", hashlib.sha256(data).hexdigest(), "unused", size, windows)
            self.assertEqual([w["payload_byte_start"] for w in row["windows"]], accepted)
            self.assertEqual([w["payload_byte_start"] for w in row["omitted_windows"]], omitted)

    def test_every_planned_window_omitted(self):
        data = bytes(range(20))
        tags = {0x100: [5], 0x101: [4], 0x111: list(range(20)), 0x117: [1] * 20}
        with patch("builtins.open", return_value=io.BytesIO(data)):
            with patch("payload_feature_probe.Tiff") as tiff:
                tiff.return_value.all_ifds.return_value = [tags]
                row = report("1", "synthetic", hashlib.sha256(data).hexdigest(), "unused", 4, 3)
        self.assertEqual(row["windows"], [])
        self.assertEqual(row["omitted_windows"], [
            {"payload_byte_start": start, "reason": "crosses_strip_boundary"}
            for start in (0, 8, 16)])
        self.assertEqual(len(row["strips"]), 20)

    def test_cli_sanitized_errors_and_validation(self):
        output = io.StringIO()
        with patch("payload_feature_probe.report", side_effect=OSError("PRIVATE")):
            with contextlib.redirect_stdout(output):
                code = main(["--sample", "1", "synthetic", "a" * 64, "PRIVATE"])
        self.assertEqual(code, 1)
        self.assertNotIn("PRIVATE", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["errors"], [{"pixls_id": "1", "error_type": "OSError"}])
        for values in (("0", "a" * 64), ("1", "bogus")):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    main(["--sample", values[0], "synthetic", values[1], "unused"])


if __name__ == "__main__":
    unittest.main()
