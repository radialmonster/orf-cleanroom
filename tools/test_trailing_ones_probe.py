#!/usr/bin/env python3
"""Independent literal-bit and synthetic CLI checks for trailing_ones_probe."""

import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from test_v0_spec_check import make_orf
import trailing_ones_probe as probe
from trailing_ones_probe import trailing_ones_from_bytes


HISTOGRAMS = (
    "histogram_last_byte",
    "histogram_last_eight_bytes",
    "histogram_full_payload",
)


def literal_counts(data):
    bits = "".join(format(byte, "08b") for byte in data)
    full = len(bits) - len(bits.rstrip("1"))
    return min(full, 8), min(full, 64), full


class CounterTests(unittest.TestCase):
    def test_measure_sample_rejects_changed_snapshot_and_retains_valid(self):
        original = bytes(make_orf(b'\x00\xfe', 4, 4, extra=[(272, 2, [ord('T')])]).data)
        changed = bytes(make_orf(b'\x00\xff', 4, 4, extra=[(272, 2, [ord('T')])]).data)
        sample = {'id': '1', 'public_name': 'synthetic.orf', 'sha256': hashlib.sha256(original).hexdigest()}
        for second, expected in ((original, None), (changed, 'sha256_mismatch')):
            with self.subTest(expected=expected), patch('builtins.open', side_effect=[io.BytesIO(original), io.BytesIO(second)]):
                row, failure = probe.measure_sample(sample, 'unused')
            self.assertEqual(failure, expected)
            if expected:
                self.assertIsNone(row)
            else:
                self.assertEqual(row['input_sha256'], sample['sha256'])
                self.assertEqual(row['full_payload_trailing_ones'], 0)

    def test_exhaustive_two_byte_inputs(self):
        for value in range(65536):
            data = value.to_bytes(2, "big")
            self.assertEqual(trailing_ones_from_bytes(data), literal_counts(data),
                             data.hex())

    def test_explicit_boundaries(self):
        cases = (
            (b"", (0, 0, 0)),
            (b"\x00", (0, 0, 0)),
            (b"\x00\xfe", (0, 0, 0)),
            (b"\xff", (8, 8, 8)),
            (b"\xff\xff", (8, 16, 16)),
            (b"\xff" * 3, (8, 24, 24)),
            (b"\x03\xff", (8, 10, 10)),
            (b"\xff" * 9, (8, 64, 72)),
            (b"\x00\x80\xff", (8, 8, 8)),
        )
        for data, expected in cases:
            with self.subTest(payload=data.hex()):
                self.assertEqual(trailing_ones_from_bytes(data), expected)


class CliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="private-trailing-ones-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cache = self.root / "private-cache"
        self.cache.mkdir()
        self.cohort_path = self.root / "private-cohort.json"

    def sample(self, sample_id, payload, cache_name):
        # A one-character ASCII model fits inline in the existing fixture writer.
        data = bytes(make_orf(payload, 4, 4, extra=[(272, 2, [ord("T")])]).data)
        (self.cache / cache_name).write_bytes(data)
        return {
            "id": sample_id,
            "public_name": sample_id + ".orf",
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    def cohort(self, samples):
        return {
            "schema_version": 1,
            "lead": 87,
            "cohort_id": "synthetic-trailing-ones",
            "manifest_commit": "synthetic-only",
            "expected_count": len(samples),
            "samples": samples,
        }

    def test_mixed_snapshot_failure_keeps_later_verified_sample(self):
        first = bytes(make_orf(b'\x00\xfe', 4, 4, extra=[(272, 2, [ord('T')])]).data)
        changed = bytes(make_orf(b'\x00\xff', 4, 4, extra=[(272, 2, [ord('T')])]).data)
        good = bytes(make_orf(b'\x01\xff', 4, 4, extra=[(272, 2, [ord('T')])]).data)
        samples = [{'id': '1', 'public_name': 'first.orf', 'sha256': hashlib.sha256(first).hexdigest()},
                   {'id': '2', 'public_name': 'good.orf', 'sha256': hashlib.sha256(good).hexdigest()}]
        self.cohort_path.write_text(json.dumps(self.cohort(samples)), encoding='utf-8')
        original_open = open
        reads = {'first': iter((first, changed)), 'good': iter((good, good))}
        def read(path, mode='r', *args, **kwargs):
            if path in reads:
                return io.BytesIO(next(reads[path]))
            return original_open(path, mode, *args, **kwargs)
        with patch.object(probe, 'index_inputs', return_value=({samples[0]['sha256']: 'first', samples[1]['sha256']: 'good'}, False)), \
                patch('builtins.open', side_effect=read):
            result = probe.run_measurement(str(self.cohort_path), str(self.cache), 'tester')
        self.assertEqual(result['failures'], [{'sample_id': '1', 'category': 'sha256_mismatch'}])
        self.assertEqual([row['sample_id'] for row in result['samples']], ['2'])
        self.assertEqual(result['samples'][0]['full_payload_trailing_ones'], 9)
        self.assertEqual(result['summary']['sample_count'], 1)

    def run_probe(self, cohort_text):
        cohort_bytes = cohort_text.encode("utf-8")
        self.cohort_path.write_bytes(cohort_bytes)
        result = subprocess.run(
            [sys.executable, "-I", str(TOOLS_DIR / "trailing_ones_probe.py"),
             "--cohort", str(self.cohort_path), "--sample-dir", str(self.cache),
             "--measured-by", "synthetic-tester"],
            capture_output=True, text=True, timeout=30,
        )
        output = json.loads(result.stdout)
        self.assertIsInstance(output, dict)
        self.assertTrue({
            "schema_version", "lead", "cohort_id", "measured_by",
            "cohort_sha256", "source_sha256", "samples", "failures", "summary",
        }.issubset(output))
        self.assertEqual(output["measured_by"], "synthetic-tester")
        self.assertEqual(output["cohort_sha256"], hashlib.sha256(cohort_bytes).hexdigest())
        sources = output["source_sha256"]
        self.assertIsInstance(sources, dict)
        for name in ("trailing_ones_probe", "orf_tokens", "orf_signature"):
            self.assertRegex(sources[name], r"\A[0-9a-f]{64}\Z")
        self.assertIsInstance(output["samples"], list)
        self.assertIsInstance(output["failures"], list)
        for failure in output["failures"]:
            self.assertEqual(set(failure), {"sample_id", "category"})
            self.assertIsInstance(failure["category"], str)
            self.assertTrue(failure["category"])
        for private in (str(self.root), str(self.cache), str(self.cohort_path),
                        self.root.name, self.cache.name, self.cohort_path.name):
            self.assertNotIn(private, result.stdout)
            self.assertNotIn(private, result.stderr)
        self.assertNotIn("traceback", (result.stdout + result.stderr).lower())
        return result, output

    def assert_summary(self, output, payloads):
        counts = [literal_counts(payload) for payload in payloads]
        summary = output["summary"]
        self.assertEqual(summary["sample_count"], len(payloads))
        positives = sum(full > 0 for _, _, full in counts)
        self.assertEqual(summary["positive_count"], positives)
        self.assertEqual(summary["zero_count"], len(payloads) - positives)
        for index, name in enumerate(HISTOGRAMS):
            histogram = summary[name]
            self.assertIsInstance(histogram, dict)
            for key, count in histogram.items():
                self.assertRegex(key, r"\A(?:0|[1-9][0-9]*)\Z")
                self.assertIs(type(count), int)
                self.assertGreaterEqual(count, 0)
            self.assertEqual(sum(histogram.values()), len(payloads))
            self.assertEqual(
                {key: value for key, value in histogram.items() if value},
                dict(Counter(str(row[index]) for row in counts)),
            )
        if counts:
            self.assertEqual(summary["max_full_payload_run"], max(row[2] for row in counts))

    def assert_sample(self, actual, declared, payload):
        expected = {
            "sample_id": declared["id"],
            "public_name": declared["public_name"],
            "input_sha256": declared["sha256"],
            "measured_model": "T",
            "measured_width": 4,
            "measured_height": 4,
            "measured_payload_bytes": len(payload),
        }
        expected.update(zip(
            ("last_byte_trailing_ones", "last_eight_bytes_trailing_ones",
             "full_payload_trailing_ones"), literal_counts(payload),
        ))
        for key, value in expected.items():
            self.assertEqual(actual[key], value, key)

    def test_renamed_duplicate_cache_files_are_one_observation(self):
        payload = b"\x03\xff"
        declared = self.sample("public-positive", payload, "renamed.arbitrary")
        data = (self.cache / "renamed.arbitrary").read_bytes()
        (self.cache / "second-copy.bin").write_bytes(data)
        result, output = self.run_probe(json.dumps(self.cohort([declared])))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(output["cohort_id"], "synthetic-trailing-ones")
        self.assertEqual(output["failures"], [])
        self.assertEqual(len(output["samples"]), 1)
        self.assert_sample(output["samples"][0], declared, payload)
        self.assert_summary(output, [payload])

    def test_cohort_order_and_positive_zero_histograms(self):
        payloads = [b"\xff" * 9, b"\x00\xfe"]
        samples = [self.sample("public-long", payloads[0], "z-cache.data"),
                   self.sample("public-zero", payloads[1], "a-cache.data")]
        result, output = self.run_probe(json.dumps(self.cohort(samples)))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(output["failures"], [])
        self.assertEqual(len(output["samples"]), 2)
        for actual, declared, payload in zip(output["samples"], samples, payloads):
            self.assert_sample(actual, declared, payload)
        self.assert_summary(output, payloads)

    def test_missing_input_retains_success_and_only_public_failure(self):
        payload = b"\x00\xfe"
        good = self.sample("public-good", payload, "private-good.data")
        missing = {"id": "public-missing", "public_name": "missing.orf", "sha256": "a" * 64}
        result, output = self.run_probe(json.dumps(self.cohort([missing, good])))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(output["samples"]), 1)
        self.assert_sample(output["samples"][0], good, payload)
        self.assertEqual(len(output["failures"]), 1)
        self.assertEqual(output["failures"][0]["sample_id"], missing["id"])
        self.assert_summary(output, [payload])

    def test_invalid_cohorts_emit_failure_json_without_successes(self):
        first = self.sample("public-first", b"\x03\xff", "first.data")
        second = self.sample("public-second", b"\x00\xfe", "second.data")
        valid = self.cohort([first, second])
        duplicate_id = self.cohort([first, dict(second, id=first["id"])])
        duplicate_hash = self.cohort([first, dict(second, sha256=first["sha256"])])
        cases = {
            "duplicate IDs": duplicate_id,
            "duplicate hashes": duplicate_hash,
            "count mismatch": dict(valid, expected_count=3),
            "boolean count": dict(self.cohort([first]), expected_count=True),
            "zero count": dict(self.cohort([]), expected_count=0),
            "short hash": self.cohort([dict(first, sha256="a" * 63)]),
            "nonhex hash": self.cohort([dict(first, sha256="g" * 64)]),
            "uppercase hash": self.cohort([dict(first, sha256="A" * 64)]),
            "nonobject array": [],
            "nonobject null": None,
        }
        texts = {name: json.dumps(cohort) for name, cohort in cases.items()}
        texts["malformed JSON"] = '{"samples": ['
        for name, text in texts.items():
            with self.subTest(case=name):
                result, output = self.run_probe(text)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(output["samples"], [])
                self.assertEqual(len(output["failures"]), 1)
                self.assertIn("cohort", output["failures"][0]["category"])
                self.assert_summary(output, [])

    def test_fixed_size_tag_one_payload_is_not_variable(self):
        # 4 * 4 * 12 / 8 bytes is fixed-size, despite the fixture's tag 259 = 1.
        declared = self.sample("public-fixed", b"\xff" * 24, "fixed.data")
        result, output = self.run_probe(json.dumps(self.cohort([declared])))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output["samples"], [])
        self.assertEqual(len(output["failures"]), 1)
        failure = output["failures"][0]
        self.assertEqual(failure["sample_id"], declared["id"])
        self.assertIn("variable", failure["category"])
        self.assert_summary(output, [])


if __name__ == "__main__":
    unittest.main()
