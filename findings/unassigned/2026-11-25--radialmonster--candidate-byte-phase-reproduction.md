# Candidate word-start byte-phase association does not transfer consistently

Author: @radialmonster
Verified by: @radialmonster
Lead: #1039
Variant: unassigned
Builds on: #11

## Claim

For a fixed literal stop-1/five-bit candidate walk on three public E-M1 Mark II files, only the b4 comparison on id 1993 exceeds all three fixed phase-rotation controls in both tested windows. Its prefix-selected rate contrast also remains positive later. Seven of nine prefix-selected directions are retained, but that is a separate comparison. This is a bounded follow-up, not a reproduction of #11's unspecified private byte-alignment analysis. It does not determine physical byte alignment or true codeword starts.

## Original evidence

Lead #1039 used `tools/candidate_byte_phase.py` at `57deeea9438e4cd48874c95f53ee54146066c058` on public ids 1993 and 1997. From declared strip bit zero, the candidate MSB-first walk advances by q+6 bits per complete word with no extra skip, including q>=17. Phase means word-start bit offset modulo eight. The windows are [0,262144) and [1048576,1310720) in the same uninterrupted walk. The q bins are 0, 1, 2, 3–7, 8–16, and 17+, while b4/b2 use only q<17 words. The three fixed controls pair each outcome with the phase 257, 4093 or 16381 positions forward modulo the window, keeping the original outcome's eligibility. These are descriptive controls, not calibrated p-values.

## Verification

After the lead was published at 20:28:18 UTC on 2026-11-25, the complete discovery aggregates matched at 20:29:24 UTC. Reserved public id 1998 was then run separately at 20:29:38 UTC, with the same method. All three identities passed the full hash and CC0 manifest checks. Five generated tests passed. A separate bit cursor and joint-table implementation with the same declared-strip reader agreed on the reserved tables, endpoints and fit choices, with MI agreeing to within 1e-12 bit. This is same-finder verification, not a different person's verification.

| Raw id | Field | Prefix MI / maximum rotation | Later MI / maximum rotation | Prefix high-minus-low stays positive later |
| --- | --- | --- | --- | --- |
| 1993 | q bins | 7.64e-5 / 1.11e-4 | 4.65e-4 / 2.70e-4 | No (q=0) |
| 1993 | b4 | 4.71e-5 / 4.22e-5 | 3.83e-4 / 3.32e-4 | Yes |
| 1993 | b2 | 1.64e-5 / 3.91e-5 | 8.26e-5 / 9.20e-5 | Yes |
| 1997 | q bins | 1.01e-4 / 1.50e-4 | 1.06e-4 / 8.78e-5 | Yes (q=0) |
| 1997 | b4 | 4.59e-5 / 5.73e-5 | 4.00e-5 / 3.07e-5 | Yes |
| 1997 | b2 | 2.01e-5 / 6.22e-5 | 3.14e-5 / 4.27e-5 | Yes |
| 1998 reserved | q bins | 6.94e-5 / 8.71e-5 | 6.39e-5 / 9.21e-5 | Yes (q=0) |
| 1998 reserved | b4 | 1.75e-5 / 3.25e-5 | 4.08e-5 / 1.80e-5 | Yes |
| 1998 reserved | b2 | 1.45e-5 / 3.93e-5 | 1.53e-5 / 6.73e-5 | No |

MI in bits, rounded. In 1993 the b4=1 contrast uses phases 5 and 2, with rates 9582/32931 versus 9172/32493 in the prefix and 8258/30113 versus 8802/35391 later. On reserved 1998 the b2=1 contrast uses phases 1 and 5, with rates 10542/32441 versus 10321/32501 in the prefix and 10474/32199 versus 10584/32291 later. The reserved cursor uses exact bit intervals [0,1595500) and [6383452,7979955). None of the reserved field comparisons exceeds the strongest rotation in both windows. The data do not decide whether the codec is physically byte aligned. All three captures are from the same model.

## Reproduce

At `57deeea9438e4cd48874c95f53ee54146066c058`, substitute local paths for A, B and C. Exact raw.pixls.us public identities and CC0 hashes are in `samples/manifest.csv`.

    python -I -B tools/test_candidate_byte_phase.py
    python -I -B tools/candidate_byte_phase.py --sample 1993 A --sample 1997 B
    python -I -B tools/candidate_byte_phase.py --cohort repeat --sample 1998 C

- 1993, Olympus - E-M1MarkII - 16bit (4:3).ORF, `0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`.
- 1997, Olympus - E-M1MarkII - 16bit (4:3).ORI, `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a`.
- 1998, Olympus - E-M1MarkII - 16bit (4:3).ORF, `4bc52d99e4fbf2f09335a3301a4634bc261a98441edb824434ec069f7026cd71`.

Compare exact phase tables, bit endpoints, selected residues and counts, and the original and rotated MI. No private files were used.
