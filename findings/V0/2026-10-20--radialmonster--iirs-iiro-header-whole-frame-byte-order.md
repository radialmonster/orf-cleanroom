# Header IIRS vs IIRO: whole-frame byte order agrees on 7 of 7 CC0 packed-12 files tested (and 4 of 4 further)

Author: @radialmonster
Verified by: @radialmonster
Lead: #78
Variant: V0
Builds on: #77, #75
Partial: whole-frame byte order versus header and strip gap, on 7 of the 9 CC0 packed-12 files (XZ-10 and SH-2 not re-run); the "candidate rule" status, the packed-16 byte-order claim and the confound with camera generation are not settled.

## Claim

On packed-12 files the first four bytes (`IIRS` or `IIRO`) pair with the byte order that is smoother over the whole frame: every `IIRS` file is smoother in the plain byte order (and has exactly one strip gap), the `IIRO` file is smoother with the bytes of each 4-byte word reversed (and has one strip, no gap). The pairing is still confounded with camera generation.

## Original evidence

Lead #78 (@radialmonster, 2026-10-18): 9 CC0 packed-12 files, 6 `IIRS` and 3 `IIRO`, via `tools/layout_probe.py` and the decoder. A comment on the lead reported a prefix-window re-run (48 rows) with the same pairing, 13 of 13 including 4 non-CC0 files.

## Verification

New run on 2026-10-20 UTC by @radialmonster, after the lead and its comment, with a new script (listing below, stdlib plus `tools/orf_signature.py` for TIFF parsing; `decoder/` not used). Roughness is sum |v[x]-v[x+2]| over all `height` rows divided by the mean level, once for the plain 12-bit MSB-first unpack and once after reversing the bytes of every 4-byte word. This is a wider run than the earlier 48-row window.

CC0 raw.pixls.us (header, size, strips, strip gap in bytes, plain, reversed):
- IIRS 3088x2309, 146 strips, gap 1464: plain 0.135 / 0.111 / 0.149, reversed 0.780 / 1.053 / 0.924 (three files)
- IIRS 2608x1949, 122 strips, gap 1224: plain 0.069, reversed 0.836
- IIRS 3664x2741, 172 strips, gap 1624: plain 0.044 / 0.095, reversed 0.838 / 0.922 (two files)
- IIRO 3984x2986, 1 strip, no gap: plain 0.940, reversed 0.033

Non-CC0 files (private, aggregates only): 4 `IIRS` packed-12 files (2576x1925, 2832x2117, 3280x2453 twice) smoother in the plain order (plain 0.045 to 0.077, reversed 0.889 to 0.929), one strip gap each (184, 824, 664, 664 bytes). Two non-CC0 files are `IIRO` compressed and one `MMOR` packed-16; none broke the pairing.

So 7 of 7 CC0 packed-12 files re-run and 4 of 4 further files fit. XZ-10 and SH-2 (the other two CC0 `IIRO` packed-12 files) were not available locally and were not re-run, so the `IIRO` side rests on one file here (the earlier comment covered all three on a prefix). No file not already counted in the lead's census was a new CC0 body; this is a wider run, not a new-body test. Nothing here separates the header from the strip table: every file has both.

## Reproduce

    python -I hdr_whole.py PATH_TO_REPO/tools FILE [FILE ...]

where `hdr_whole.py`:

    import sys
    sys.path.insert(0, sys.argv[1])
    import orf_signature as S
    def unpack12(b, w):
        o = []
        for i in range(0, len(b) - 2, 3):
            o.append(b[i] << 4 | b[i+1] >> 4); o.append((b[i+1] & 15) << 8 | b[i+2])
        return o[:w]
    def rev4(b):
        b = bytearray(b)
        for i in range(0, len(b) // 4 * 4, 4): b[i:i+4] = b[i:i+4][::-1]
        return bytes(b)
    def rough(rows):
        s = t = 0
        for r in rows:
            for x in range(len(r) - 2):
                s += abs(r[x] - r[x+2]); t += r[x] + r[x+2]
        return s / (t / 2) if t else 0
    for p in sys.argv[2:]:
        data = open(p, 'rb').read(); t = S.Tiff(data)
        best = max(t.all_ifds(), key=lambda d: sum(d.get(0x117) or [0]))
        sig = S.signature(p)
        offs, cnts = best.get(0x111) or [], best.get(0x117) or []
        gaps = [g for g in (offs[i+1]-offs[i]-cnts[i] for i in range(len(offs)-1)) if g]
        L = [sig['sha256'][:12], data[:4].decode('latin1'), sig['size_class'], 'strips=%d' % len(offs), 'gaps=%s' % gaps[:3]]
        if sig['size_class'] == 'packed-12':
            w, h = sig['payload_w'], sig['payload_h']; rb = w*3//2
            pay = b''.join(data[o:o+c] for o, c in zip(offs, cnts))
            rows = [pay[y*rb:(y+1)*rb] for y in range(h)]
            a = rough([unpack12(r, w) for r in rows]); b = rough([unpack12(rev4(r), w) for r in rows])
            L += ['plain=%.3f' % a, 'rev=%.3f' % b]
        print(*L)

Files: the 6 CC0 `IIRS` packed-12 files and the CC0 XZ-2 file of the lead (the 9-file list in #75), recognised by header, size and the strip gaps above; run `pixls_samples.py check` on each first.
