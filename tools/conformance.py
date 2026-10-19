#!/usr/bin/env python3
"""Conformance runner for the reference ORF decoder (decoder/orf_decode.py).

Runs the decoder on the given files and prints one line per file, then a
summary line.  Aggregates to stdout only; no file is written.

Per file: input sha256, variant/packing, WxH, bytes consumed vs payload
size (exact end?), min/max, values out of 12-bit range, CFA smoothness
(mean |x - x two columns left|), and the OUTPUT HASH: SHA-256 of the
decoded values as little-endian uint16, row-major, unshifted.

Two independent implementations (or two people running this decoder)
agree on a file when the output hashes match.  --csv prints the rows in
the samples/conformance-V0.csv format.  Compressed files are listed as
"not yet specified" and skipped (no hash).

Usage: python -I tools/conformance.py [--csv] [--v0-only] FILE...
Clean room: uses only the repo's findings and leads (see decoder/).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "decoder"))
import orf_decode  # noqa: E402

COLS = ["input_sha256", "variant", "packing", "order", "width", "height",
        "payload_bytes", "consumed_bytes", "exact_end", "min", "max",
        "out_of_range", "smooth", "output_sha256", "row_layout"]


def row(r):
    out = []
    for c in COLS:
        v = r.get(c)
        if c == "input_sha256":
            v = r.get("sha256")
        if isinstance(v, float):
            v = "%.3f" % v
        out.append("" if v is None else str(v))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--csv", action="store_true",
                    help="print CSV rows (header + one row per decoded file)")
    ap.add_argument("--v0-only", action="store_true",
                    help="skip compressed files silently")
    a = ap.parse_args(argv)
    n = exact = oor = comp = err = 0
    rows = []
    for p in a.files:
        try:
            r = orf_decode.decode_file(p)
        except Exception as e:  # report and go on
            err += 1
            print("ERROR %s: %s" % (os.path.basename(p), e), file=sys.stderr)
            continue
        if r["variant"] != "V0":
            comp += 1
            if not a.v0_only and not a.csv:
                print("%s  %s  compressed  not yet specified"
                      % (r["sha256"], r.get("model", "?")))
            continue
        n += 1
        exact += bool(r["exact_end"])
        oor += r["out_of_range"]
        rows.append(row(r))
        if not a.csv:
            print("%s  %s %s/%s %sx%s  consumed %s/%s exact=%s  min %s max %s"
                  "  oor %s  smooth %.2f  out %s%s"
                  % (r["sha256"], r.get("model", "?"), r["packing"], r["order"],
                     r["width"], r["height"], r["consumed_bytes"],
                     r["payload_bytes"], r["exact_end"], r["min"], r["max"],
                     r["out_of_range"], r["smooth"], r["output_sha256"],
                     "  UNVERIFIED" if "unverified" in str(r.get("status", "")) else ""))
    if a.csv:
        print(",".join(COLS))
        for x in sorted(rows):
            print(",".join(x))
    print("summary: V0 decoded %d, exact-end %d, out-of-range values %d, "
          "compressed (not yet specified) %d, errors %d"
          % (n, exact, oor, comp, err), file=sys.stderr if a.csv else sys.stdout)
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
