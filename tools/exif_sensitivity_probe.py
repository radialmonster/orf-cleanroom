#!/usr/bin/env python3
"""Report numeric Exif sensitivity tags and measured ORF signatures for lead #106.

Public TIFF/Exif tag structure only; no maker notes, GPS, serials, preview or
pixel decoding. Tag 0x8827 is PhotographicSensitivity (legacy ISOSpeedRatings).
Its raw SHORT values are reported, not calibrated ISO or a causal explanation.
65535 can be a sentinel: extended sensitivity tags are deliberately not read.
Check public sample licences with pixls_samples.py before use. Stdlib only.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orf_signature as signature


def sensitivity(data):
    """Read 0x8827 only via the primary IFD's ExifIFD pointer (0x8769).

    Return [] for an absent pointer/tag. Malformed supported entries fail rather
    than being silently interpreted as missing. Only standard TIFF offsets and
    SHORT sensitivity / LONG singleton pointer types are supported.
    """
    tiff = signature.Tiff(data)

    def entries(offset):
        if offset < 8 or offset + 2 > len(data):
            raise ValueError("invalid IFD offset")
        count = tiff.u16(offset)
        if offset + 2 + 12 * count + 4 > len(data):
            raise ValueError("truncated IFD")
        found = {}
        for i in range(count):
            p = offset + 2 + 12 * i
            tag, kind, n = struct.unpack_from(tiff.e + "HHI", data, p)
            if tag in (0x8769, 0x8827):
                if tag in found:
                    raise ValueError("duplicate selected tag")
                found[tag] = (kind, n, p + 8)
        return found

    pointer = entries(tiff.u32(4)).get(0x8769)
    if pointer is None:
        return []
    kind, n, p = pointer
    if kind != 4 or n != 1:
        raise ValueError("invalid ExifIFD pointer type/count")
    tag = entries(tiff.u32(p)).get(0x8827)
    if tag is None:
        return []
    kind, n, p = tag
    if kind != 3 or n == 0:
        raise ValueError("invalid sensitivity type/count")
    if n > 2:
        p = tiff.u32(p)
    if p < 8 or p + 2 * n > len(data):
        raise ValueError("truncated sensitivity values")
    return list(struct.unpack_from(tiff.e + "%dH" % n, data, p))


def measure(sample_id, public_name, path):
    with open(path, "rb") as stream:
        data = stream.read()
    values = sensitivity(data)
    measured = signature.signature(path)
    if measured["sha256"] != hashlib.sha256(data).hexdigest():
        raise ValueError("sample changed while reading metadata")
    measured.pop("file")  # never expose a local filename/path
    return {"pixls_id": sample_id, "pixls_name": public_name,
            "signature": measured, "photographic_sensitivity_raw": values,
            "sensitivity_status": "present" if values else "absent",
            "contains_65535_sentinel": 65535 in values}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", nargs=3, action="append", required=True,
                        metavar=("ID", "PUBLIC_NAME", "PATH"))
    args = parser.parse_args(argv)
    ids = [row[0] for row in args.sample]
    if any(not value or any(c not in "0123456789" for c in value) for value in ids):
        parser.error("sample IDs must contain ASCII decimal digits only")
    if len(set(ids)) != len(ids):
        parser.error("sample IDs must be unique")
    rows, failures = [], []
    for sample_id, public_name, path in args.sample:
        try:
            rows.append(measure(sample_id, public_name, path))
        except (OSError, ValueError, TypeError, struct.error) as error:
            failures.append({"pixls_id": sample_id, "error_type": type(error).__name__})
    hashes = {}
    for name in ("exif_sensitivity_probe.py", "orf_signature.py"):
        with open(os.path.join(os.path.dirname(__file__), name), "rb") as stream:
            hashes[name] = hashlib.sha256(stream.read()).hexdigest()
    print(json.dumps({"source_sha256": hashes, "samples": rows, "failures": failures,
                      "limits": "Raw Exif 0x8827 values only; absent is not ISO zero. "
                      "65535 requires extended tags. No scene, correlation or causality test."},
                     sort_keys=True, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
