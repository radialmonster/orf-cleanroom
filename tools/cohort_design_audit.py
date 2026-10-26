#!/usr/bin/env python3
"""Audit categorical cohort identifiability for hypothesis #299.

Original stdlib metadata analysis, no raw decoding or feature fitting. Reads a
public manifest and explicit IDs; prints aggregates and public input identities.
Manifest mode is a width proxy (hires when width >6000; samples/README.md),
not independently observed capture mode. Redundancy with geometry is structural.
File rows are not established independent captures. Treatment coding drops each factor's
lexicographic first level, with an intercept. Exact rational nullspace vectors
prove column aliases; no fitted response or causal percentages are produced.
"""
import argparse
import collections
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys

FACTORS = ("body", "recorded_mode", "geometry", "extension")
FIELDS = ("pixls_id", "pixls_name", "sha256", "licence", "make", "model", "mode", "payload_w", "payload_h")


def reduce_matrix(matrix):
    """Return exact reduced row echelon form and pivot columns."""
    if not matrix or not matrix[0] or len({len(r) for r in matrix}) != 1:
        raise ValueError("nonempty rectangular matrix required")
    rows = [[Fraction(x) for x in row] for row in matrix]
    pivots = []
    for col in range(len(rows[0])):
        pos = next((i for i in range(len(pivots), len(rows)) if rows[i][col]), None)
        if pos is None:
            continue
        p = len(pivots)
        rows[p], rows[pos] = rows[pos], rows[p]
        divisor = rows[p][col]
        rows[p] = [x / divisor for x in rows[p]]
        for i in range(len(rows)):
            if i != p:
                mult = rows[i][col]
                rows[i] = [a - mult * b for a, b in zip(rows[i], rows[p])]
        pivots.append(col)
        if len(pivots) == len(rows):
            break
    return rows, pivots


def design(records, factors):
    levels = {f: sorted({r[f] for r in records}) for f in factors}
    terms = [(f, level) for f in factors for level in levels[f][1:]]
    labels = ["intercept"] + [f + "=" + level for f, level in terms]
    matrix = [[1] + [int(r[f] == level) for f, level in terms] for r in records]
    return labels, matrix, levels


def load_records(text, ids):
    if not ids or len(set(ids)) != len(ids) or any(not re.fullmatch(r"[0-9]+", i) for i in ids):
        raise ValueError("unique numeric public IDs required")
    candidates = {i: set() for i in ids}
    for row in csv.DictReader(text.splitlines()):
        if row.get("pixls_id") in candidates:
            if row.get("source") != "pixls" or any(not row.get(f) for f in FIELDS):
                raise ValueError("selected manifest row lacks required metadata")
            candidates[row["pixls_id"]].add(tuple(row[f] for f in FIELDS))
    records = []
    for identity in ids:
        if len(candidates[identity]) != 1:
            raise ValueError("selected ID absent or conflicting audited manifest rows")
        row = dict(zip(FIELDS, next(iter(candidates[identity]))))
        if row["licence"] != "CC0" or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
            raise ValueError("CC0 public record and SHA-256 required")
        w, h = int(row["payload_w"]), int(row["payload_h"])
        if w <= 0 or h <= 0:
            raise ValueError("positive geometry required")
        row.update(body=json.dumps([row["make"], row["model"]], ensure_ascii=True),
                   recorded_mode=row["mode"], geometry="%dx%d" % (w, h),
                   extension=Path(row["pixls_name"]).suffix.lower())
        records.append(row)
    if len({r["sha256"] for r in records}) != len(records):
        raise ValueError("selected IDs alias identical content")
    return records


def audit(records):
    labels, matrix, levels = design(records, FACTORS)
    reduced, pivots = reduce_matrix(matrix)
    aliases = []
    for free in range(len(labels)):
        if free in pivots:
            continue
        vector = [Fraction(0)] * len(labels)
        vector[free] = Fraction(1)
        for row, pivot in zip(reduced, pivots):
            vector[pivot] = -row[free]
        aliases.append({label: str(value) for label, value in zip(labels, vector) if value})
    conditional = {}
    for omitted in FACTORS:
        _, smaller, _ = design(records, [f for f in FACTORS if f != omitted])
        conditional[omitted] = len(pivots) - len(reduce_matrix(smaller)[1])
    cells = collections.Counter(tuple(r[f] for f in FACTORS) for r in records)
    return {"files": len(records), "levels": levels, "columns": labels,
            "rank": len(pivots), "columns_count": len(labels),
            "nullity": len(labels) - len(pivots), "nullspace": aliases,
            "conditional_rank_increment": conditional,
            "residual_row_dimension": len(records) - len(pivots),
            "cells": [{"factors": dict(zip(FACTORS, cell)), "files": count}
                      for cell, count in sorted(cells.items())],
            "body_support": [{"body": b, "files": sum(r["body"] == b for r in records),
                              **{f: sorted({r[f] for r in records if r["body"] == b})
                                 for f in FACTORS if f != "body"}} for b in levels["body"]],
            "inputs": [{f: r[f] for f in FIELDS} for r in records]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--ids", nargs="+", required=True)
    args = ap.parse_args(argv)
    try:
        content = Path(args.manifest).read_bytes()
        records = load_records(content.decode("utf-8-sig"), args.ids)
        report = audit(records)
        report["manifest_sha256"] = hashlib.sha256(content).hexdigest()
        report["tool_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        report["scope"] = "categorical additive metadata design; no independent captures, causal effects, clusters or variant assignment established"
        print(json.dumps(report, sort_keys=True, indent=2))
    except (OSError, UnicodeError, ValueError, KeyError):
        print("cohort audit failed: unreadable input or invalid/conflicting metadata", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
