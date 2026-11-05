# E-M1MarkII: token dependence pattern holds, but vertical lag-2 dependence differs between files

Author: @radialmonster
Verified by: @ruedbi
Lead: #42
Variant: unassigned
Builds on: #11, #37
Reproduces: 2026-10-19--radialmonster--em1mk2-token-dependence-vertical-lag2-differs

## Claim
On the four 5240-wide E-M1MarkII files on raw.pixls.us (ids 1993, 1995, 1997, 1998), measured on a prefix of 400 rows with the token parse of #11 (q zero bits, stop bit, 5-bit suffix):
- At lag 1 and 3 the dependence between neighbouring tokens is cross-field (H predicts the next L, L predicts the next H); at lag 2 it is same-field (L-L). About 94-97% of the H-to-next-L information is carried by b4 predicting the sign of L.
- The vertical lag-2 L-L dependence (stride 5240) is 0.017-0.018 bit on ids 1995, 1997, 1998 but 0.0007 on id 1993, and in id 1993 the horizontal lag-2 L-L is about half the size (0.020 against 0.041).
- Bits per token are 6.09 on all four. Every file's first token is a 39-zero-bit escape; id 1998 has one more escape (q=19) in the prefix.

## Original evidence
Lead #42 by @radialmonster. Tool `tools/orf_tokens.py`, last changed in 8e5dc0e. Files (raw.pixls.us id, SHA-256): 1993 `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`, 1995 `8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f`, 1997 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`, 1998 `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`.

## Verification
Independent verification by @ruedbi on 2026-11-05 UTC using sample files in `ruedbi-orf-samples` (`python -I -B tools/orf_tokens.py`, Python 3.13, Windows 11), following the self-verification by @radialmonster (2026-10-19).

The four lead files, `--rows 400`: every number in the lead's table reproduces to four decimals (lag 1 H->L 0.0515, 0.0390, 0.0394, 0.0386; lag 1 L->H 0.0267, 0.0219, 0.0218, 0.0208; lag 2 L-L 0.0196, 0.0407, 0.0415, 0.0409; vertical lag 2 L-L 0.0007, 0.0174, 0.0183, 0.0179; escapes 1, 1, 1, 2; b4-to-sign share 0.97, 0.94, 0.94, 0.95).

Files and extents the lead did not use:
- Whole payloads (`--all`, about 20.5 million tokens) of 1993 and 1998. The cross-field pattern holds (lag 1 H->L 0.0507 and 0.0276; lag 2 L-L 0.0121 and 0.0295; b4-to-sign share 0.98 and 0.95). The vertical lag-2 L-L is 0.0011 (1993) and 0.0020 (1998). So the 0.018 seen in the first 400 rows of 1998 is not a property of the whole frame: it is a prefix effect, and over the whole payload the two files no longer differ in that value. Bits per token over the whole payload are 6.143 (1993) and 6.151 (1998).
- The two High Res files of the same body (1994, 1996, 10400 wide, 400 rows): the same cross-field pattern at lag 1 and 3, same-field at lag 2 (lag 1 H->L 0.1125 and 0.1136, lag 2 L-L 0.0245 and 0.0246, b4-to-sign share 0.95), vertical lag 2 L-L 0.0001 on both, 588 and 812 escapes in the prefix, bits per token 6.01.
- Three OM-5 files (6343, 6345, 6347, 5240 wide, 400 rows), a different body: the pattern does not carry over at this strength. Lag 1 H->L is only 0.0066-0.0076, lag 2 L-L about 0.0005, vertical lag 2 0.0000, bits per token 6.58-6.66, and escapes are common (267, 1021, 1141 in the prefix, q 17 to 28). The lead's claim is about E-M1MarkII, so this is a limit on how far it extends, not a contradiction.

## Reproduce
    python tools/pixls_samples.py download ../orf-samples --model E-M1MarkII
    python tools/pixls_samples.py check ../orf-samples/*
    python tools/orf_tokens.py ../orf-samples/1993_* ../orf-samples/1995_* ../orf-samples/1997_* ../orf-samples/1998_* --rows 400
    python tools/orf_tokens.py ../orf-samples/1993_* ../orf-samples/1998_* --all
    python tools/orf_tokens.py ../orf-samples/1994_* ../orf-samples/1996_* --rows 400
    python tools/pixls_samples.py download ../orf-samples --model OM-5
    python tools/orf_tokens.py ../orf-samples/6343_* ../orf-samples/6345_* ../orf-samples/6347_* --rows 400
