#!/usr/bin/env python3
"""Lead #31: aggregate suffix equality against an exact block-permutation mean.

Original clean-room analysis; stdlib Python 3.8+. Candidate W-token blocks are
coordinates, not established image geometry. This measures single-symbol
equality, not dictionary coding. See the frozen public cohort/design metadata.
Within each cohort, sample IDs and content hashes must be distinct; this does
not establish that files represent independent captures or scenes.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
import re
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_signature
import orf_tokens

DESIGN_ID = "lead31-suffix-matches-v1"
DESIGN_SHA256 = "e37e9678da83bf61c8fa3af4652bafed156d767b048893f46bed8a42dd1c7ee9"
PREFIX = 262144
LABELS = ("1", "2", "3", "4", "W-2", "W", "W+2", "2W-2", "2W", "2W+2")
METRICS = ("P", "M", "E", "observed_rate", "expected_rate", "difference", "ratio")


def suffix_histogram(qs, ss):
    # Qwen draft, independently reviewed and repaired before execution; see
    # task-3-report.md. Validate even unavailable suffixes; reject subclasses.
    if type(qs) not in (list, tuple) or type(ss) not in (list, tuple):
        raise TypeError("Inputs must be list or tuple")
    if len(qs) != len(ss):
        raise ValueError("Inputs must have equal length")
    counts = [0] * 32
    for q, s in zip(qs, ss):
        if type(q) is not int or type(s) is not int:
            raise TypeError("Elements must be int")
        if q < 0 or not 0 <= s <= 31:
            raise ValueError("Invalid token range")
        if q < 17:
            counts[s] += 1
    return tuple(counts)


class InputError(ValueError):
    """A stable, public error code, without file paths or exception messages."""


class UsageError(Exception):
    """CLI syntax failure; argparse's message may contain private arguments."""


class SanitizedArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError from None


def positive_int(value, code):
    if type(value) is not int or value <= 0:
        raise InputError(code)
    return value


def lag_values(width):
    if width is None:
        return (1, 2, 3, 4, None, None, None, None, None, None)
    positive_int(width, "invalid_width")
    return (1, 2, 3, 4, width - 2, width, width + 2,
            2 * width - 2, 2 * width, 2 * width + 2)


def rational(value):
    return None if value is None else {
        "numerator": value.numerator, "denominator": value.denominator}


def metric_fields(pairs, matches, expected):
    return {"P": pairs, "M": matches, "E": rational(expected),
            "observed_rate": rational(Fraction(matches, pairs) if pairs else None),
            "expected_rate": rational(expected / pairs if pairs else None),
            "difference": rational((matches - expected) / pairs if pairs else None),
            "ratio": rational(Fraction(matches) / expected if expected else None)}


def null_row(label, lag, reason):
    return dict({"label": label, "lag": lag, "status": "failed", "reason": reason,
                 "alias_of": None}, **{key: None for key in METRICS})


def lag_rows(width, compute=None, failure=None):
    """Retain every label and expose numeric aliases, including invalid lags."""
    seen, cache, rows = {}, {}, []
    for label, lag in zip(LABELS, lag_values(width)):
        alias = seen.get(lag) if lag is not None else None
        if lag is not None and lag not in seen:
            seen[lag] = label
        if failure:
            row = null_row(label, lag, failure)
        elif lag <= 0:
            row = null_row(label, lag, "invalid_lag")
        else:
            if lag not in cache:
                cache[lag] = metric_fields(*compute(lag))
            row = dict({"label": label, "lag": lag, "status": "ok", "reason": None,
                        "alias_of": None}, **cache[lag])
        row["alias_of"] = alias
        rows.append(row)
    return rows


def lag_counts(qs, ss, width, lag, histograms=None):
    """Exact conditional mean, grouping pairs before Fraction arithmetic."""
    positive_int(width, "invalid_width")
    positive_int(lag, "invalid_lag")
    suffix_histogram(qs, ss)
    if len(qs) % width:
        raise InputError("incomplete_block")
    if histograms is None:
        histograms = [suffix_histogram(qs[i:i + width], ss[i:i + width])
                      for i in range(0, len(qs), width)]
    groups, pairs, matches = Counter(), 0, 0
    for i in range(max(0, len(qs) - lag)):
        j = i + lag
        if qs[i] < 17 and qs[j] < 17:
            pairs += 1
            matches += ss[i] == ss[j]
            groups[i // width, j // width] += 1
    expected = Fraction(0)
    totals = [sum(h) for h in histograms]
    for (a, b), count in groups.items():
        ha, hb = histograms[a], histograms[b]
        if a == b:
            numerator = sum(c * (c - 1) for c in ha)
            denominator = totals[a] * (totals[a] - 1)
        else:
            numerator = sum(x * y for x, y in zip(ha, hb))
            denominator = totals[a] * totals[b]
        expected += count * Fraction(numerator, denominator)
    return pairs, matches, expected


def analyze_tokens(qs, ss, width, requested=PREFIX):
    positive_int(width, "invalid_width")
    positive_int(requested, "invalid_prefix")
    suffix_histogram(qs, ss)
    if len(qs) != requested:
        raise InputError("token_count_mismatch")
    retained = requested - requested % width
    if retained == 0:
        raise InputError("insufficient_data")
    q, s = qs[:retained], ss[:retained]
    histograms = [suffix_histogram(q[i:i + width], s[i:i + width])
                  for i in range(0, retained, width)]
    return {"tokens_parsed": requested, "tokens_retained": retained,
            "tokens_discarded": requested - retained, "blocks": retained // width,
            "escapes_parsed": sum(x >= 17 for x in qs),
            "escapes_retained": sum(x >= 17 for x in q),
            "lags": lag_rows(width, lambda lag: lag_counts(q, s, width, lag, histograms))}


def checked_parse(payload, width, requested=PREFIX):
    positive_int(width, "invalid_width")
    positive_int(requested, "invalid_prefix")
    qs, ss, _, end = orf_tokens.parse(payload, requested, width, esc_extra=0)
    try:
        suffix_histogram(qs, ss)
    except (TypeError, ValueError):
        raise InputError("invalid_tokens") from None
    if len(qs) != requested:
        raise InputError("token_count_mismatch")
    if type(end) is not int or end != sum(q + 6 for q in qs):
        raise InputError("invalid_consumed_bits")
    if end > len(payload) * 8:
        raise InputError("payload_overrun")
    return qs, ss, end


def validate_cohort(cohort):
    if type(cohort) is not dict or set(cohort) != {
            "design_id", "design_sha256", "phase", "samples"}:
        raise InputError("invalid_cohort")
    if cohort["design_id"] != DESIGN_ID or cohort["design_sha256"] != DESIGN_SHA256:
        raise InputError("design_mismatch")
    if type(cohort["phase"]) is not str or cohort["phase"] not in ("discovery", "validation", "replication"):
        raise InputError("invalid_phase")
    samples = cohort["samples"]
    if type(samples) is not list or not samples:
        raise InputError("invalid_cohort_samples")
    ids, hashes = set(), set()
    for sample in samples:
        if type(sample) is not dict or set(sample) != {"id", "name", "sha256"}:
            raise InputError("invalid_sample_identity")
        ident, name, sha = sample["id"], sample["name"], sample["sha256"]
        positive_int(ident, "invalid_sample_id")
        if ident in ids:
            raise InputError("duplicate_sample_id")
        if (type(name) is not str or not name.strip() or name != name.strip()
                or any(ord(c) < 32 or ord(c) == 127 for c in name)
                or "/" in name or "\\" in name
                or not name.upper().endswith((".ORF", ".ORI"))):
            raise InputError("invalid_sample_name")
        if type(sha) is not str or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise InputError("invalid_sample_hash")
        if sha in hashes:
            raise InputError("duplicate_sample_hash")
        ids.add(ident)
        hashes.add(sha)
    return cohort


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def validate_mapping(cohort, mappings):
    paths = {}
    for ident, path in mappings:
        if type(ident) is str and re.fullmatch(r"[1-9][0-9]*", ident):
            ident = int(ident)
        if type(ident) is not int or ident <= 0:
            raise InputError("invalid_mapping_id")
        if ident in paths:
            raise InputError("duplicate_mapping_id")
        paths[ident] = path
    if set(paths) != {s["id"] for s in cohort["samples"]}:
        raise InputError("mapping_coverage_mismatch")
    return paths


def check_layout(data, signature):
    best = max(orf_signature.Tiff(data).all_ifds(),
               key=lambda d: sum(d.get(0x117) or [0]))
    width, height = signature["payload_w"], signature["payload_h"]
    positive_int(width, "invalid_dimensions")
    positive_int(height, "invalid_dimensions")
    if signature["size_class"] != "variable":
        raise InputError("unsupported_size_class")
    offsets, lengths = best.get(0x111), best.get(0x117)
    if (type(offsets) is not list or type(lengths) is not list
            or len(offsets) != 1 or len(lengths) != 1):
        raise InputError("unsupported_strips")
    offset, length = offsets[0], lengths[0]
    if (type(offset) is not int or offset < 0 or type(length) is not int
            or length <= 0 or offset + length > len(data)):
        raise InputError("invalid_payload_bounds")
    if (offset != signature["payload_offset"]
            or length != signature["payload_bytes"]):
        raise InputError("signature_layout_mismatch")


def measure_sample(sample, path):
    result = dict(sample, status="failed", reason=None, signature=None, variant=None)
    width = None
    try:
        with open(path, "rb") as stream:
            data = stream.read()
        if hashlib.sha256(data).hexdigest() != sample["sha256"]:
            raise InputError("sample_hash_mismatch")
        sig = orf_signature.signature(path)
        # The signature's local basename is replaced with the public identity.
        sig["file"] = sample["name"]
        result["signature"] = sig
        if type(sig["payload_w"]) is int and sig["payload_w"] > 0:
            width = sig["payload_w"]
        if sig["sha256"] != sample["sha256"]:
            raise InputError("sample_hash_mismatch")
        check_layout(data, sig)
        w, h, payload = orf_tokens.locate(path)
        if (w != width or h != sig["payload_h"] or len(payload) != sig["payload_bytes"]
                or payload != data[sig["payload_offset"]:sig["payload_offset"] + sig["payload_bytes"]]):
            raise InputError("locate_signature_mismatch")
        qs, ss, end = checked_parse(payload, width)
        result.update(analyze_tokens(qs, ss, width))
        result.update(status="ok", consumed_bits=end)
    except InputError as exc:
        result["reason"] = str(exc)
    except OSError:
        result["reason"] = "input_io_error"
    except (ValueError, KeyError, TypeError, IndexError, struct.error, OverflowError):
        result["reason"] = "invalid_input_structure"
    if result["status"] != "ok":
        result["lags"] = lag_rows(width, failure=result["reason"])
    return result


def source_hashes():
    directory = os.path.dirname(os.path.abspath(__file__))
    hashes = {}
    for name in ("suffix_match_probe.py", "test_suffix_match_probe.py",
                 "orf_tokens.py", "orf_signature.py"):
        with open(os.path.join(directory, name), "rb") as stream:
            hashes[name] = hashlib.sha256(stream.read()).hexdigest()
    return hashes


def main(argv=None):
    parser = SanitizedArgumentParser(description=__doc__)
    parser.add_argument("--cohort", help="public cohort JSON (phase and expected identities)")
    parser.add_argument("--measured-by", help="human investigator's GitHub handle")
    parser.add_argument("--sample", nargs=2, action="append", default=[], metavar=("ID", "FILE"))
    parser.add_argument("--self-test", action="store_true", help="deterministic synthetic tests only")
    try:
        args = parser.parse_args(argv)
    except UsageError:
        print(json.dumps({"metric_version": DESIGN_ID, "status": "failed",
                          "reason": "invalid_cli_arguments", "samples": []}, sort_keys=True))
        return 2
    if args.self_test:
        import test_suffix_match_probe
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_suffix_match_probe)
        return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1
    output = {"metric_version": DESIGN_ID,
              "run_utc": datetime.now(timezone.utc).isoformat(),
              "source_sha256": source_hashes(),
              "settings": {"requested_tokens": PREFIX, "esc_extra": 0, "escape_q": 17,
                           "bit_order": "MSB-first", "block_width": "payload_w",
                           "labels": list(LABELS)}, "samples": []}
    try:
        if not args.cohort or not args.measured_by or not re.fullmatch(
                r"@?[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", args.measured_by):
            raise InputError("missing_or_invalid_arguments")
        output["measured_by"] = args.measured_by
        with open(args.cohort, encoding="utf-8") as stream:
            cohort = validate_cohort(json.load(stream, object_pairs_hook=unique_object))
        output.update({key: cohort[key] for key in ("design_id", "design_sha256", "phase")})
        try:
            paths = validate_mapping(cohort, args.sample)
        except InputError as exc:
            output["samples"] = [dict(s, status="failed", reason=str(exc), signature=None,
                                      lags=lag_rows(None, failure=str(exc)))
                                 for s in cohort["samples"]]
            raise
        output["samples"] = [measure_sample(s, paths[s["id"]]) for s in cohort["samples"]]
        output["status"] = "ok" if all(s["status"] == "ok" for s in output["samples"]) else "failed"
    except InputError as exc:
        output.update(status="failed", reason=str(exc))
    except (OSError, ValueError, TypeError, KeyError):
        output.update(status="failed", reason="invalid_cohort_input")
    print(json.dumps(output, sort_keys=True, allow_nan=False))
    return 0 if output["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
