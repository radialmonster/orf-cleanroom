#!/usr/bin/env python3
"""Measure literal byte-tail one-bit counts for lead #87, without decoding.

Match the frozen cohort by input SHA-256, reuse the original signature and
contiguous payload locator, and emit only public metadata and aggregate counts.
Standard library only; Python 3.8+.
Each measurement snapshot must match the cohort hash before its payload is counted.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
import struct
import sys
import unittest


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from orf_signature import signature
from orf_tokens import locate_data


# These are input-format errors raised by the original helpers, not a catch-all.
PARSE_ERRORS = (ValueError, TypeError, KeyError, IndexError, struct.error, OverflowError)


def sha256_file(path):
    """Hash file bytes without retaining the file in memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_tail(data, start):
    count = 0
    for index in range(len(data) - 1, start - 1, -1):
        byte = data[index]
        if byte == 0xFF:
            count += 8
            continue
        while byte & 1:
            count += 1
            byte >>= 1
        break
    return count


def trailing_ones_from_bytes(data):
    """Independently count the final byte, final eight bytes and full byte tail.

    The final bit is the low-order bit of the final byte. Empty bytes return
    (0, 0, 0); for example, b'\x03\xff' returns (8, 10, 10).
    """
    last_byte = _count_tail(data, max(0, len(data) - 1))
    last_eight = _count_tail(data, max(0, len(data) - 8))
    full = _count_tail(data, 0)
    if last_byte != min(full, 8) or last_eight != min(full, 64):
        raise AssertionError("independent tail windows disagree with their caps")
    return last_byte, last_eight, full


def validate_cohort(cohort):
    """Validate the declaration without repairing or filtering its membership."""
    if not isinstance(cohort, dict):
        return False
    if type(cohort.get("schema_version")) is not int or cohort["schema_version"] != 1:
        return False
    if type(cohort.get("lead")) is not int or cohort["lead"] != 87:
        return False
    for field in ("cohort_id", "manifest_commit"):
        value = cohort.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    expected = cohort.get("expected_count")
    samples = cohort.get("samples")
    if type(expected) is not int or expected <= 0:
        return False
    if not isinstance(samples, list) or len(samples) != expected:
        return False
    ids, hashes = set(), set()
    for sample in samples:
        if not isinstance(sample, dict):
            return False
        sample_id = sample.get("id")
        name = sample.get("public_name")
        digest = sample.get("sha256")
        if not isinstance(sample_id, str) or not sample_id.strip():
            return False
        if not isinstance(name, str) or not name.strip():
            return False
        if name in (".", "..") or any(char in name for char in ("/", "\\", "\0")):
            return False
        if (not isinstance(digest, str) or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest)):
            return False
        if sample_id in ids or digest in hashes:
            return False
        ids.add(sample_id)
        hashes.add(digest)
    return True


def summarize(samples):
    full_counts = [sample["full_payload_trailing_ones"] for sample in samples]
    positive = sum(count > 0 for count in full_counts)
    return {
        "sample_count": len(samples),
        "positive_count": positive,
        "zero_count": len(samples) - positive,
        "max_full_payload_run": max(full_counts, default=0),
        "histogram_last_byte": dict(sorted(Counter(
            sample["last_byte_trailing_ones"] for sample in samples).items())),
        "histogram_last_eight_bytes": dict(sorted(Counter(
            sample["last_eight_bytes_trailing_ones"] for sample in samples).items())),
        "histogram_full_payload": dict(sorted(Counter(full_counts).items())),
    }


def empty_result(measured_by):
    result = {
        "schema_version": 1,
        "lead": 87,
        "cohort_id": None,
        "measured_by": measured_by,
        "cohort_sha256": None,
        "source_sha256": {},
        "samples": [],
        "failures": [],
        "summary": summarize([]),
    }
    sources = {
        "trailing_ones_probe": __file__,
        "orf_signature": signature.__code__.co_filename,
        "orf_tokens": locate_data.__code__.co_filename,
    }
    for name, path in sources.items():
        try:
            result["source_sha256"][name] = sha256_file(path)
        except OSError:
            result["source_sha256"][name] = None
    if None in result["source_sha256"].values():
        result["failures"].append({"sample_id": None, "category": "source_unreadable"})
    return result


def index_inputs(sample_dir, required_hashes):
    """Index regular cache files once; duplicate hashes keep one matched path."""
    paths = {}
    directory_error = False
    try:
        with os.scandir(sample_dir) as entries:
            for entry in sorted(entries, key=lambda entry: entry.name):
                try:
                    if not entry.is_file():
                        continue
                    digest = sha256_file(entry.path)
                except (OSError, ValueError):
                    # An unreadable required file will appear as a missing hash.
                    continue
                if digest in required_hashes:
                    paths.setdefault(digest, entry.path)
    except (OSError, ValueError):
        directory_error = True
    return paths, directory_error


def measure_sample(sample, path):
    """Return one public observation or one sanitized failure category."""
    try:
        sig = signature(path)
    except OSError:
        return None, "input_unreadable"
    except PARSE_ERRORS:
        return None, "parse_error"
    if sig["sha256"] != sample["sha256"]:
        return None, "sha256_mismatch"
    if sig["size_class"] != "variable":
        return None, "size_class_not_variable"
    if sig["compression_tag"] != 1:
        return None, "compression_not_tag1"
    if sig["payload_bytes"] <= 0:
        return None, "empty_payload"
    try:
        with open(path, "rb") as stream:
            data = stream.read()
        if hashlib.sha256(data).hexdigest() != sample["sha256"]:
            return None, "sha256_mismatch"
        width, height, payload = locate_data(data)
        del data
    except OSError:
        return None, "input_unreadable"
    except PARSE_ERRORS:
        return None, "locate_error"
    if (width != sig["payload_w"] or height != sig["payload_h"]
            or width <= 0 or height <= 0):
        return None, "geometry_mismatch"
    if len(payload) != sig["payload_bytes"]:
        return None, "payload_bytes_mismatch"
    last_byte, last_eight, full = trailing_ones_from_bytes(payload)
    return {
        "sample_id": sample["id"],
        "public_name": sample["public_name"],
        "input_sha256": sig["sha256"],
        "measured_model": sig["model"],
        "measured_width": width,
        "measured_height": height,
        "measured_payload_bytes": len(payload),
        "last_byte_trailing_ones": last_byte,
        "last_eight_bytes_trailing_ones": last_eight,
        "full_payload_trailing_ones": full,
    }, None


def run_measurement(cohort_path, sample_dir, measured_by):
    result = empty_result(measured_by)
    try:
        with open(cohort_path, "rb") as stream:
            cohort_bytes = stream.read()
    except (OSError, ValueError):
        result["failures"].append({"sample_id": None, "category": "cohort_unreadable"})
        return result
    result["cohort_sha256"] = hashlib.sha256(cohort_bytes).hexdigest()
    try:
        cohort = json.loads(cohort_bytes)
    except (ValueError, RecursionError):
        result["failures"].append({"sample_id": None, "category": "cohort_invalid"})
        return result
    if not validate_cohort(cohort):
        result["failures"].append({"sample_id": None, "category": "cohort_invalid"})
        return result
    result["cohort_id"] = cohort["cohort_id"]
    paths, directory_error = index_inputs(
        sample_dir, {sample["sha256"] for sample in cohort["samples"]})
    if directory_error:
        result["failures"].append({"sample_id": None, "category": "sample_directory_unreadable"})
    for sample in cohort["samples"]:
        path = paths.get(sample["sha256"])
        if path is None:
            row, category = None, "file_not_found"
        else:
            row, category = measure_sample(sample, path)
        if category is not None:
            result["failures"].append({"sample_id": sample["id"], "category": category})
        else:
            result["samples"].append(row)
    result["summary"] = summarize(result["samples"])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cohort", help="Frozen public cohort JSON")
    parser.add_argument("--sample-dir", help="Directory of input files, matched by SHA-256")
    parser.add_argument("--measured-by", help="Measurer's public handle")
    parser.add_argument("--self-test", action="store_true", help="Run independent synthetic unittest suite")
    args = parser.parse_args(argv)
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromName("test_trailing_ones_probe")
        outcome = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if outcome.wasSuccessful() else 1
    if not args.cohort or not args.sample_dir or not args.measured_by or not args.measured_by.strip():
        result = empty_result(args.measured_by)
        result["failures"].append({"sample_id": None, "category": "required_arguments_missing"})
    else:
        result = run_measurement(args.cohort, args.sample_dir, args.measured_by)
    print(json.dumps(result, indent=2))
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
