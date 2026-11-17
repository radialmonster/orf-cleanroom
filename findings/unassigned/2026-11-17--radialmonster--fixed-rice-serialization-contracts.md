# Fixed whole-strip Rice serializations on controlled OM-3 files

Author: @radialmonster
Verified by: @radialmonster
Lead: #799
Variant: unassigned
Builds on: #30, #298, #339, #87

## Claim

On two public controlled OM-3 files, the fixed block-separated k=5 candidate
stops before N values; the interleaved control reaches N but leaves a tail that
contains a zero. Both the strict-end and hypothetical all-ones-tail forms of
these full contracts fail. A fresh post-lead run reproduces both original
reports, and two predeclared additional files give the same outcome. These
failures concern the entire fixed contract; they do not identify the failed
assumption, establish physical framing or identify a codec.

## Original evidence

Lead #799 used `tools/block_serialization_probe.py` at commit
`32176b01a8c8c062f0186a8d874dc7e2d7b69bad`, source SHA-256
`fcc048be7b4538e9ed3898aa90032ac7ba7c40334cd2041d11a9b6a5770fb021`;
its `tools/orf_signature.py` import has SHA-256
`1dab1d4b54b987bfa5458ea7f419fb3aee047107374ac9375edf5fe0a1af48cd`.
Discovery inputs were public CC0 PA200010.ORF (dark ISO 200, SHA-256
`b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4`)
and PA210010.ORF (saturated white ISO 200, SHA-256
`d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`).
The first four table rows are the lead's original results. #339 already reports
N+5 and N+11 interleaved whole-stream words on these files, respectively;
the N/strict-end failures are expected controls.

## Verification

Fresh post-lead runs on 2026-11-17 UTC reproduced the original reports and
applied the identical full checks to the predeclared public CC0 extensions
PA200012.ORF (dark ISO 800, SHA-256
`c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7`)
and PA200011.ORF (dark ISO 200, SHA-256
`a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3`).
Public identity and CC0 owner declarations are retained in
`samples/om3-flat-338-provenance.json`, with matching manifest rows. All files
were previously studied; this is same-account self-verification.

The original-file stdout reports reproduce discovery byte-for-byte. All four
producer runs exited zero with empty stderr and no timeout. A separately written
reference with its own TIFF locator and 4-KiB bit-string chunk unary scanner
matched the aggregate fields for both serializations on all four files; its
four processes exited zero with empty stderr. The reference shares the declared
grammar and human account, so its agreement checks implementation rather than
providing independent-human verification.

Every interleaved run completes N values, then leaves a tail containing at
least one zero; strict end and all-ones tail both fail. Every separated run
stops before N. In incomplete separated blocks sum q includes all completed
unaries read, and consumed is a stop position rather than an N-value endpoint.

File | Grammar | Strip bits | Values | Blocks | sum q | max q | Consumed | Unread | Status
--- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---
PA200010 | interleaved | 122570968 | 20420640 | 638145 | 47097 | 39 | 122570937 | 31 | tail contains zero
PA200010 | separated | 122570968 | 16740973 | 523155 | 22125108 | 39 | 122570965 | 3 | suffix incomplete
PA210010 | interleaved | 122570968 | 20420640 | 638145 | 47059 | 39 | 122570899 | 69 | tail contains zero
PA210010 | separated | 122570968 | 13353696 | 417303 | 42448774 | 39 | 122570968 | 0 | unary incomplete
PA200012 | interleaved | 122640304 | 20420640 | 638145 | 116401 | 39 | 122640241 | 63 | tail contains zero
PA200012 | separated | 122640304 | 16999099 | 531221 | 20645704 | 39 | 122640303 | 1 | suffix incomplete
PA200011 | interleaved | 122570960 | 20420640 | 638145 | 47086 | 39 | 122570926 | 34 | tail contains zero
PA200011 | separated | 122570960 | 16741384 | 523168 | 22122629 | 39 | 122570957 | 3 | suffix incomplete

Each file's uniquely selected largest-strip IFD has a single strip and geometry
5220x3912, giving N=20,420,640 and 638,145 blocks of 32. The entire strip is
read MSB first from bit zero, with no header, offset search, row reset, option
ID, escape or block padding. Unary q has no cap: q zeros then a one, with five
suffix bits. Interleaved emits one unary and suffix per value; separated emits
32 unaries followed by 32 suffixes. The strict form requires an exact end
after N; the alternative requires every remaining bit to be one. The latter
is a hypothetical termination rule: #87 does not establish padding. For a
complete N-value parse, its data endpoint is 6N+sum(q), and strip length is
that endpoint plus the tail length. A wrong extent, start, count, syntax or
termination could each explain failure. This simplified rival is not full CCSDS
syntax, and results do not establish samples, rows, values or a codec.

## Reproduce

After reviewing the tool and import and matching each local input to the
retained CC0 identity and hash, run at the named commit under a hard 120-second
per-file limit, preserving stdout, stderr, exit status and timeout:

    python -I -B tools/block_serialization_probe.py PA200010.ORF PATH_TO_CC0_FILE
    python -I -B tools/block_serialization_probe.py PA210010.ORF PATH_TO_CC0_FILE
    python -I -B tools/block_serialization_probe.py PA200012.ORF PATH_TO_CC0_FILE
    python -I -B tools/block_serialization_probe.py PA200011.ORF PATH_TO_CC0_FILE

Timeouts, incomplete reads, process errors and incompatible container metadata
are unknown, not failures or silent exclusions.
