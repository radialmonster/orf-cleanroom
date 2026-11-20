# Independent reproduction of fixed whole-strip Rice contract failures

Author: @radialmonster
Verified by: @mszyndel
Lead: #799
Variant: unassigned
Reproduces: 2026-11-17--radialmonster--fixed-rice-serialization-contracts
Builds on: #30, #298, #339, #87

## Claim

The four published public controlled OM-3 reports reproduce: the fixed block-separated k=5 parse stops before N=20,420,640 values, while the interleaved parse reaches N and leaves a tail containing zero. Both the strict-end and hypothetical all-ones-tail forms fail on all four. The predeclared additional public OM-3 file PB040038.ORF gives the same qualitative outcome, with a 23-bit interleaved tail and an incomplete separated suffix after 16,756,504 values.

These are failures of the complete stated contracts. They do not isolate serialization, identify the failed assumption, establish physical framing or identify a codec. The selected strip/start/count, absence of controls or escapes, layout and termination are all part of the hypothesis. No parameter or offset was fitted to finish a parse.

## Original evidence

Lead #799 and the reproduced finding were authored by @radialmonster on 2026-11-17 UTC. The original tool is `tools/block_serialization_probe.py` at `32176b01a8c8c062f0186a8d874dc7e2d7b69bad`, SHA-256 `fcc048be7b4538e9ed3898aa90032ac7ba7c40334cd2041d11a9b6a5770fb021`. Its sole repository import, `tools/orf_signature.py`, has SHA-256 `1dab1d4b54b987bfa5458ea7f419fb3aee047107374ac9375edf5fe0a1af48cd`. Discovery used PA200010 and PA210010; the finder's later checks added PA200012 and PA200011. The original finding's eight numerical rows are the first eight rows in the table below.

The unique largest-total-StripByteCounts IFD must have one valid strip with geometry 5220x3912. N=20,420,640 and the block size is 32. Parse MSB first from strip bit zero, with no header skip, offset search, row resets, option IDs, escapes or block padding. Unary q is unbounded zeros followed by one, with five suffix bits. Interleaved syntax places the suffix after each unary; separated syntax places 32 unaries before their 32 suffixes. Strict acceptance requires N complete values at strip end; the separate hypothetical alternative allows only an all-one tail. That tail rule is not established padding or full CCSDS syntax.

The first four inputs' CC0 owner declarations, public source links and hashes are retained in `samples/om3-flat-338-provenance.json`. The additional file's public identity is retained in `samples/om-system-pen-om-3-om-5-mark-ii-zenodo-provenance.json`. All have existing public manifest identities. Public filenames and SHA-256:

- `PA200010.ORF`: SHA-256 `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4`.
- `PA210010.ORF`: SHA-256 `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`.
- `PA200012.ORF`: SHA-256 `c30fc560831b1d9f1ece4cfd29020bf13ee523a50fa9b43dc05e562d2c6364c7`.
- `PA200011.ORF`: SHA-256 `a861c2434e7dc5cba74739d452391ec28ac2bf975aa6cb0d49492dc82c5983a3`.
- `PB040038.ORF`: SHA-256 `6f1c8b303ab79f451b77794680d06c3fcb3fde8c4e653152e1e9383259cfdbdb`.

## Verification

A fresh run by @mszyndel on 2026-11-20 UTC, after #799 was published, used byte-identical copies of the original pinned tool and its import for all four original inputs. Their source hashes matched those above. The four downloaded public inputs matched the retained CC0 hashes before measurement. Every published table field matches: strip bits, complete values/blocks, q aggregates, consumed/unread bits and stop stage. All original interleaved strict-end/all-ones-tail flags are false, with respective tails 31, 69, 63 and 34 bits. Each process exited zero with empty stderr and no 120-second timeout.

The claim and PB040038 extension were frozen before outcomes in comment 7042248485 on #799. PB040038 is an already studied public capture, not blind validation or a new-body comparison, but it was not used by #799 or the finding being reproduced. Its local content matches the retained public CC0 Zenodo identity. The original CLI accepts only four named hashes, so the separately submitted identity-list-only extension at `1dfd183143e49fb7b817cb199dd3a15857916295` (#832) admits this one new file. Both parsers and every contract assumption are unchanged; the extended tool SHA-256 is `dd440a90cb7d7b5bde4451511cc8c807beeb887291049c40914588cdb23d077f`.

The additional run exited zero with empty stderr and no 120-second timeout. Its selected strip starts at byte 1,817,600 and has 15,321,365 bytes, geometry 5220x3912 and N=20,420,640. The interleaved parse reaches N after 122,570,897 bits and leaves 23 containing a zero; both termination flags are false. The separated parse completes 16,756,504 values and stops in a suffix at bit 122,570,916 with four unread bits. No input failed, was excluded or replaced.

| File | Grammar | Strip bits | Values | Blocks | sum q | max q | Consumed | Unread | Stop/tail |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| PA200010.ORF | interleaved | 122570968 | 20420640 | 638145 | 47097 | 39 | 122570937 | 31 | tail contains zero |
| PA200010.ORF | separated | 122570968 | 16740973 | 523155 | 22125108 | 39 | 122570965 | 3 | suffix incomplete |
| PA210010.ORF | interleaved | 122570968 | 20420640 | 638145 | 47059 | 39 | 122570899 | 69 | tail contains zero |
| PA210010.ORF | separated | 122570968 | 13353696 | 417303 | 42448774 | 39 | 122570968 | 0 | unary incomplete |
| PA200012.ORF | interleaved | 122640304 | 20420640 | 638145 | 116401 | 39 | 122640241 | 63 | tail contains zero |
| PA200012.ORF | separated | 122640304 | 16999099 | 531221 | 20645704 | 39 | 122640303 | 1 | suffix incomplete |
| PA200011.ORF | interleaved | 122570960 | 20420640 | 638145 | 47086 | 39 | 122570926 | 34 | tail contains zero |
| PA200011.ORF | separated | 122570960 | 16741384 | 523168 | 22122629 | 39 | 122570957 | 3 | suffix incomplete |
| PB040038.ORF | interleaved | 122570920 | 20420640 | 638145 | 47057 | 39 | 122570897 | 23 | tail contains zero |
| PB040038.ORF | separated | 122570920 | 16756504 | 523640 | 22031884 | 39 | 122570916 | 4 | suffix incomplete |

In incomplete separated blocks, sum q includes every completed unary read, including unaries in the incomplete block; consumed is the stop position, not an N-value endpoint. For complete N-value interleaved parses, consumed=6N+sum(q). Every whole-contract rejection retains the same selection/start/count/syntax/termination assumptions; it is not a general rejection of either serialization family.

This is a reproduction by a contributor other than the finder, using the published parser and locator. It is not a new parser implementation, independent physical framing evidence or independent-capture validation. The six existing synthetic serialization tests pass. All numerical measurements use public CC0 inputs, with no private files.

## Reproduce

Read the tool and import at the original pinned commit, verify the retained CC0 identities and local hashes, and run the first four commands there. Preserve stdout, stderr, exit status and a hard 120-second per-file limit:

    python -I -B tools/block_serialization_probe.py PA200010.ORF FILE_PA200010
    python -I -B tools/block_serialization_probe.py PA210010.ORF FILE_PA210010
    python -I -B tools/block_serialization_probe.py PA200012.ORF FILE_PA200012
    python -I -B tools/block_serialization_probe.py PA200011.ORF FILE_PA200011

For the predeclared additional file, use the identity-list-only extension commit `1dfd183143e49fb7b817cb199dd3a15857916295` from #832, with the same grammar and limit:

    python -I -B tools/block_serialization_probe.py PB040038.ORF FILE_PB040038

Replace each FILE_NAME with the matching local input. These commands read samples and print aggregate JSON only. Input/identity/metadata/short-read errors and timeouts remain unknown, not grammar contradictions. No alternative offset, parameter or input is selected. Independent framing, count and termination evidence remains open in V1 G11.
