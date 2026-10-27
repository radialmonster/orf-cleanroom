#!/usr/bin/env python3
"""Independent determinant/minor and metadata tests for #299 design audit."""
import contextlib
import csv
from fractions import Fraction
import io
import itertools
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cohort_design_audit import FACTORS, FIELDS, audit, design, load_records, main, reduce_matrix


def determinant(rows):
    if len(rows) == 1:
        return rows[0][0]
    return sum((-1) ** j * rows[0][j] * determinant(
        [r[:j] + r[j + 1:] for r in rows[1:]]) for j in range(len(rows)))


def minor_rank(rows):
    for size in range(min(len(rows), len(rows[0])), 0, -1):
        for ri in itertools.combinations(range(len(rows)), size):
            for ci in itertools.combinations(range(len(rows[0])), size):
                if determinant([[rows[r][c] for c in ci] for r in ri]):
                    return size
    return 0


def manifest(rows):
    stream = io.StringIO()
    out = csv.DictWriter(stream, fieldnames=FIELDS + ("source",))
    out.writeheader()
    out.writerows(rows)
    return stream.getvalue()


def record(i, model, mode, width):
    return dict(zip(FIELDS + ("source",), (str(i), "test%d.ORF" % i, "%064x" % i, "CC0",
                             "make", model, mode, str(width), "10", "pixls")))


class Tests(unittest.TestCase):
    def test_quoted_multiline_models_keep_distinct_bodies(self):
        rows = [record(1, 'camera\nvariant', 'normal', 10),
                record(2, 'cameravariant', 'normal', 10)]
        report = audit(load_records(manifest(rows), ['1', '2']))
        self.assertEqual(len(report['levels']['body']), 2)
        self.assertEqual(report['rank'], 2)

    def test_exact_rank_all_binary_3x3(self):
        for values in itertools.product((0, 1), repeat=9):
            rows = [list(values[i:i + 3]) for i in (0, 3, 6)]
            self.assertEqual(len(reduce_matrix(rows)[1]), minor_rank(rows))
        self.assertEqual(len(reduce_matrix([[1, 2, 3, 4], [2, 4, 6, 8]])[1]), 1)

    def test_aliases_and_conditional_increment(self):
        rows = [record(1, "a", "low", 10), record(2, "a", "low", 10),
                record(3, "b", "high", 20), record(4, "b", "high", 20)]
        records = load_records(manifest(rows), ["1", "2", "3", "4"])
        report = audit(records)
        self.assertEqual((report["rank"], report["nullity"]), (2, 2))
        self.assertEqual(report["conditional_rank_increment"], dict.fromkeys(FACTORS, 0))
        self.assertEqual([r["files"] for r in report["cells"]], [2, 2])
        labels, matrix, _ = design(records, FACTORS)
        for alias in report["nullspace"]:
            for row in matrix:
                self.assertEqual(sum(x * Fraction(alias.get(label, "0"))
                                     for x, label in zip(row, labels)), 0)
        self.assertEqual(audit(records[::-1])["nullspace"], report["nullspace"])

    def test_crossed_design(self):
        rows = [record(i + 1, b, m, 10) for i, (b, m) in enumerate(
            itertools.product(("a", "b"), ("low", "high")))]
        report = audit(load_records(manifest(rows), [str(i) for i in range(1, 5)]))
        self.assertEqual((report["rank"], report["nullity"]), (3, 0))
        self.assertEqual(report["conditional_rank_increment"]["body"], 1)
        self.assertEqual(report["conditional_rank_increment"]["recorded_mode"], 1)

    def test_shapes(self):
        for rows in ([[0]], [[1, 2, 3]], [[0, 0], [0, 0]],
                     [[1, 0], [0, 1], [1, 1]],
                     [[Fraction(1, 2), Fraction(1, 3)], [3, 2]]):
            self.assertEqual(len(reduce_matrix(rows)[1]), minor_rank(rows))
        for rows in ([], [[]], [[1], [1, 2]]):
            with self.assertRaises(ValueError):
                reduce_matrix(rows)

    def test_cli_sanitized_failure_and_success(self):
        for payload in (b"wrong,header\n1,2\n", b"\xff"):
            err = io.StringIO()
            with patch.object(Path, "read_bytes", return_value=payload):
                with contextlib.redirect_stderr(err):
                    self.assertEqual(main(["--manifest", "PRIVATE-PATH", "--ids", "1"]), 1)
            self.assertNotIn("PRIVATE-PATH", err.getvalue())
        out = io.StringIO()
        payload = manifest([record(1, "a", "normal", 10)]).encode()
        with patch.object(Path, "read_bytes", return_value=payload):
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["--manifest", "unused", "--ids", "1"]), 0)
        self.assertIn('"rank": 1', out.getvalue())

    def test_duplicate_and_conflict(self):
        row = record(1, "a", "normal", 10)
        self.assertEqual(len(load_records(manifest([row, row]), ["1"])), 1)
        for changed in (dict(row, mode="other"), dict(row, sha256="f" * 64)):
            with self.assertRaises(ValueError):
                load_records(manifest([row, changed]), ["1"])
        for ids in (["1", "1"], ["2"], []):
            with self.assertRaises(ValueError):
                load_records(manifest([row]), ids)
        with self.assertRaises(ValueError):
            load_records(manifest([dict(row, licence="unknown")]), ["1"])
        with self.assertRaises(ValueError):
            load_records(manifest([row, dict(row, pixls_id="2")]), ["1", "2"])

    def test_non_numeric_public_id_is_rejected(self):
        row = record(1, "a", "normal", 10)
        row["pixls_id"] = "not-a-public-id"
        with self.assertRaises(ValueError):
            load_records(manifest([row]), ["not-a-public-id"])

    def test_non_public_source_is_rejected(self):
        row = dict(record(1, "a", "normal", 10), source="own")
        with self.assertRaises(ValueError):
            load_records(manifest([row]), ["1"])

    def test_duplicate_audited_column_cannot_override_body(self):
        row = record(1, "camera-a", "normal", 10)
        for field, replacement in (("model", "camera-b"), ("payload_w", "100"),
                                   ("pixls_id", "2"), ("source", "own")):
            text = manifest([row]).splitlines()
            text[0] += "," + field
            text[1] += "," + replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                load_records("\n".join(text) + "\n", ["1"])


if __name__ == "__main__":
    unittest.main()
