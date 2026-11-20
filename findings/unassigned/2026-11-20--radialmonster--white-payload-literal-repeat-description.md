# A charged six-bit repeat description of the public white OM-3 payload

Author: @radialmonster
Verified by: @radialmonster
Lead: #864
Variant: unassigned
Builds on: #338, #339

## Claim

The six-bit template selected on the fixed white PA210010 training window reproduces both original held-out savings exactly and saves bits on both predeclared additional white windows. Charging the same template once with all exceptions across the whole white payload gives 63273928 bits for 122570968 literal bits. The same template costs 135629920 bits over the whole capped-dark PA200010 payload of the same size. One of the four dark windows is below literal size.

## Original evidence

`tools/literal_repeat_probe.py` at `39c04060234bb1510cd2355881bd04f8672e6899` implements the literal repeat-plus-exceptions proposal in #339 comment 6844338185 and builds on @mtakemoto's flat-file evidence. The original file is public CC0 saturated-white OM-3 PA210010.ORF, SHA-256 `d055b08cbb23d34cbfeacd9321d1cb9ba1f968c9e0252c8d69aa311946cabc1e`, geometry 5220 × 3912, selected strip 15321371 bytes. The owner declaration and public download identity are in `samples/om3-flat-338-provenance.json`.

Fit only 65536 bytes starting at byte 65536. For each period 1 through 256, take the majority by absolute residue with ties set to zero. Minimize byte-padded charged size among these templates, breaking ties by the smaller period. Period six won at 272592 charged bits. For each independent record, charge eight period bits, the template, 64 start bits, 32 length bits, 32 exception-count bits, positive Elias-gamma exception gaps from index minus one, and zero padding to a byte. This defines a reversible literal description. The camera-file tool counts the corresponding cost exactly without materializing a real encoded stream. Synthetic wire tests exercised encoding and decoding separately.

The original held-out results are the first two white rows below. The whole white record covers every bit from bit zero to 122570968 exclusive. Startup and tail are overlapping diagnostics with separately charged records.

## Verification

Discovery started at 20:56:03 UTC on 2026-11-20. The fresh producer and reference phases started at 20:59:04 UTC, after publication at 20:57:12 UTC. All 256 training costs, the selected template identity, and the five original white records repeated exactly. The separate aggregate implementation matched every fit and all 14 verification records, including all coverage endpoints, exception counts and padded costs. The two implementations share the TIFF locator. Both runs exited successfully with empty stderr.

Two farther white windows at 3 and 4 MiB use the unchanged template and absolute phase. The public CC0 descriptive comparator is capped-dark OM-3 PA200010.ORF, SHA-256 `b038504aa569ad1db70628617ebcc6aac56de58ce34a6b00ab39d9fe0e905ed4`, geometry 5220 × 3912, selected strip 15321371 bytes, with its public declaration in the same provenance file. The dark file uses the white template at every interval without fitting. Every interval except a whole record contains 524288 literal bits. Whole records contain 122570968 bits each.

| File | Interval | Absolute start bit | Exceptions | Gamma gap bits | Charged bits |
| --- | --- | ---: | ---: | ---: | ---: |
| PA210010 | 1 MiB | 8388608 | 39375 | 273763 | 273912 |
| PA210010 | 2 MiB | 16777216 | 38607 | 268547 | 268696 |
| PA210010 | 3 MiB | 25165824 | 40854 | 283802 | 283944 |
| PA210010 | 4 MiB | 33554432 | 40408 | 280888 | 281032 |
| PA210010 | Whole | 0 | 9108946 | 63273786 | 63273928 |
| PA210010 | Startup | 0 | 50096 | 301226 | 301368 |
| PA210010 | Tail | 122046680 | 39225 | 272781 | 272928 |
| PA200010 | 1 MiB | 8388608 | 245417 | 674907 | 675056 |
| PA200010 | 2 MiB | 16777216 | 245851 | 675429 | 675576 |
| PA200010 | 3 MiB | 25165824 | 190786 | 583230 | 583376 |
| PA200010 | 4 MiB | 33554432 | 136955 | 497757 | 497904 |
| PA200010 | Whole | 0 | 45713227 | 135629773 | 135629920 |
| PA200010 | Startup | 0 | 241858 | 668940 | 669088 |
| PA200010 | Tail | 122046680 | 245849 | 675013 | 675160 |

The inputs were previously studied. The white windows are from the same capture, and the dark file is a descriptive comparison with different capture conditions. The description does not establish the camera's codeword boundaries, physical framing, value assembly or encoder.

## Reproduce

At `39c04060234bb1510cd2355881bd04f8672e6899`, substitute paths to the files with the public hashes above:

```text
python -I -B tools/literal_repeat_probe.py --phase discovery --sample PA210010.ORF PATH_WHITE
python -I -B tools/literal_repeat_probe.py --phase verification --sample PA210010.ORF PATH_WHITE --sample PA200010.ORF PATH_DARK
```
