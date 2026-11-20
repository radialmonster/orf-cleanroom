#!/usr/bin/env python3
"""Compare fixed interleaved and block-separated k=5 contracts, aggregates only.

Candidate from #298 comment 6844338899; #30 is related framing context.
The all-ones tail is hypothetical, not established padding. EOF is tested
against the selected complete strip. No decoding or values are printed.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orf_signature import Tiff

N = 5220 * 3912
BLOCK = 32
IDENTITIES = {
    "PA200010.ORF": "b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4",
    "PA210010.ORF": "d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e",
    "PA200012.ORF": "c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7",
    "PA200011.ORF": "a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3",
    "PB040038.ORF": "6f1c8b303ab79f451b77794680d06c3fcb3fde8c4e653152e1e9383259cfdbdb",
}


def locate(data):
    ifds = list(Tiff(data).all_ifds())
    candidates = []
    for tags in ifds:
        counts = tags.get(0x117)
        if 0x117 in tags and (not isinstance(counts, list) or not counts or
                              any(type(c) is not int or c <= 0 for c in counts)):
            raise ValueError("invalid strip byte counts")
        if counts:
            candidates.append((sum(counts), tags))
    if not candidates:
        raise ValueError("no eligible strip IFD")
    largest = max(item[0] for item in candidates)
    winners = [tags for size, tags in candidates if size == largest]
    if len(winners) != 1:
        raise ValueError("largest strip IFD is not unique")
    tags = winners[0]
    offsets, counts = tags.get(0x111), tags.get(0x117)
    if not isinstance(offsets, list) or len(offsets) != 1 or len(counts) != 1:
        raise ValueError("expected one strip")
    if tags.get(0x100) != [5220] or tags.get(0x101) != [3912]:
        raise ValueError("incompatible dimensions")
    off, size = offsets[0], counts[0]
    if type(off) is not int or off < 0 or off + size > len(data):
        raise ValueError("invalid strip extent")
    return memoryview(data)[off:off + size], off


def scan(payload, count, separated):
    """Parse only q/positions; return aggregates, never reconstructed values."""
    if count <= 0 or count % BLOCK:
        raise ValueError("count must be a positive multiple of 32")
    size = len(payload) * 8
    if size < 6 * count:
        return {"status": "contradiction_minimum_length", "payload_bits": size,
                "minimum_bits": 6 * count}
    pos = total_q = maximum_q = complete = blocks = 0
    stage = None
    for _ in range(count // BLOCK):
        for _ in range(BLOCK):
            begin = pos
            while pos < size:
                available = min(8 - (pos & 7), size - pos)
                chunk = payload[pos >> 3] & ((1 << available) - 1)
                if chunk:
                    pos += available - chunk.bit_length() + 1
                    break
                pos += available
            else:
                stage = "unary"
                break
            q = pos - begin - 1
            total_q += q
            maximum_q = max(maximum_q, q)
            if not separated:
                if pos + 5 > size:
                    stage = "suffix"
                    break
                pos += 5
                complete += 1
        if stage:
            break
        if separated:
            available_suffixes = min(BLOCK, (size - pos) // 5)
            pos += 5 * available_suffixes
            complete += available_suffixes
            if available_suffixes != BLOCK:
                stage = "suffix"
                break
        blocks += 1
    out = {"payload_bits": size, "consumed_bits": pos, "unread_bits": size - pos,
           "complete_values": complete, "complete_blocks": blocks,
           "sum_q_read": total_q, "max_q_read": maximum_q, "incomplete_stage": stage}
    if stage:
        out["status"] = "contradiction_truncated_" + stage
        return out
    if pos != 6 * count + total_q:
        raise AssertionError("data endpoint invariant")
    remaining = size - pos
    prefix_end = min(size, (pos + 7) & ~7)
    tail_ones = (all((payload[p >> 3] >> (7 - (p & 7))) & 1
                     for p in range(pos, prefix_end))
                 and all(b == 255 for b in payload[prefix_end >> 3:]))
    out.update({"status": "complete", "strict_end": remaining == 0,
                "hypothetical_all_ones_tail": tail_ones,
                "tail_bits": remaining})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", choices=sorted(IDENTITIES))
    parser.add_argument("file")
    args = parser.parse_args()
    try:
        with open(args.file, "rb") as f:
            data = f.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != IDENTITIES[args.name]:
            raise ValueError("hash differs from retained CC0 identity")
        payload, offset = locate(data)
        result = {"status": "measured", "name": args.name, "sha256": digest,
                  "payload_offset": offset, "payload_bytes": len(payload), "N": N,
                  "interleaved": scan(payload, N, False),
                  "separated": scan(payload, N, True)}
    except OSError as exc:
        result = {"status": "unknown_metadata_or_read", "name": args.name,
                  "reason": "read_" + type(exc).__name__}
    except (ValueError, TypeError, IndexError, struct.error) as exc:
        result = {"status": "unknown_metadata_or_read", "name": args.name,
                  "reason": type(exc).__name__}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "measured" else 1


if __name__ == "__main__":
    sys.exit(main())
