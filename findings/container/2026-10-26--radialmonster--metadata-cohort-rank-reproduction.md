# Metadata cohort design remains rank deficient after adding a second ORI

Author: @radialmonster
Verified by: @radialmonster
Lead: #318
Variant: container
Builds on: #299, #307
Partial: categorical metadata design rank, aliases, cells and conditional increments

## Claim

The frozen 12-file public manifest cohort has an additive treatment-coded metadata design with 15 columns, rank 11 and nullity 4. Its 11 observed factor cells are saturated by the design. Adding the preselected public ID 1997 yields 13 files but the same 15 columns, rank 11, nullity 4 and 11 cells. The mode label is a width-derived manifest proxy. These are metadata algebra results, not codec, capture-independence or causal claims.

## Original evidence

Lead #318 measured the 12 inputs below using `tools/cohort_design_audit.py` at commit `0dc8abc988844867ee7dff8fd1172ef505773834` and the manifest with SHA-256 `535d99ace97e3424d561ef1ed35cb8003c3cad3fd827c31ee0ac82d96d66db32`. The conditional rank increments for body, recorded mode, geometry and extension were 2, 0, 3 and 1. The original cohort has 11 cells; IDs 1994 and 1996 share its only repeated cell.

- 1799; Olympus - C5060WZ - 12bit (4:3).ORF; 3fc12bc3f6320cfab456111d7805b446e329fdd1907680be55e2e163e5e084bd
- 2151; Olympus - E-400 - 16bit (4:3).ORF; 1354e0ac98ea90820227650031d8215637a2aaabd15de995c5a1e00b1986261b
- 1993; Olympus - E-M1MarkII - 16bit (4:3).ORF; 0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8
- 1994; Olympus - E-M1MarkII - 16bit (4:3).ORF; f8d04ca777b3cd4d1eed4c2971d713d6ac7397bf1254929b4097c4b619f49c23
- 1995; Olympus - E-M1MarkII - 16bit (4:3).ORI; 8af918366ed969c6dddf5a48b8810fec1024858d22c75c5f1ac1a5c750a57a1f
- 1996; Olympus - E-M1MarkII - 16bit (4:3).ORF; eeb589558062114c1f4db00c2341eac6741fb345be871a40f3428600f84a95a2
- 5283; OM System - OM-1 - 16bit (4:3).ORF; bf2eef6becc0851e48231617c3e2eac27a2cdb44c75b93035c561d837952c18b
- 5284; OM System - OM-1 - 16bit (4:3).ORF; f0301e1b49a4ffbb366ec9800ebe9210f421fb25e75dcdf7d63e4b05bc063caf
- 7262; OM System - OM-1 Mark II - 16bit (4:3).orf; d0fe58daf2f0bd749ecb18311e55408f0e7804de8e5e6580e815eae50d834cbd
- 7267; OM System - OM-1 Mark II - 16bit (4:3).orf; 5c4845bcf87d868c1b770d7e92e574e148d82acb2806cddd9df5a7a47d7cd756
- 6343; OM System - OM-5 - 16bit (4:3).ORF; ee0213ee4899d677d9bd538d8cfa4d0f69bdbacd462c1cf3ca3901036cf2fce7
- 6344; OM System - OM-5 - 16bit (4:3).ORF; 42b13fbc10627907881975fb1f617bd7afa90ef448c239ce3ad41a4b9ceca512

## Verification

On 2026-10-26 UTC the finder repeated the analysis as a separate self-verification run using the tool at repository commit `1cf2a0e934e5fc3e997ef363031450b4377699a1` (last tool change `ce56e016d80f4a1fc621588999f8800215448002`) (tool SHA-256 `6af3093ee016bc6c7944b8c0b3aa8f1091d755c501cbb322ac5545413f1f2f1e`). The original manifest was recovered byte-for-byte from the lead's commit and matched its stated SHA-256. The same 12 IDs were also checked against the later public manifest SHA-256 `96fadeca148c9c7db72cdeaa36ac2b534d8eb114312b76e4e866f4971f3a87ed`. Both runs reproduced rank 11/15, nullity 4, 11 cells and increments 2/0/3/1.

The predeclared additional input was raw.pixls.us ID 1997; Olympus - E-M1MarkII - 16bit (4:3).ORI; SHA-256 `89138ccc958509ca1beb7028452400ab7f42061c0fc56e35c8a7d7a4a808dd0a` (CC0). The retained licence record and local content hash matched. Adding it preserved the same rank, nullity and increments, and introduced no new factor cell: IDs 1995 and 1997 share the normal 5240x3912 ORI cell. Unlike the original cohort, its extension contrast has two ORI files; their capture or scene independence is not established. Residual row dimension is 1 for the 12-file cohort and 2 for the 13-file cohort, algebraic counts only.

An independently structured exact rational forward elimination reproduced each rank and each conditional increment. All four reported null vectors are independent and evaluate to zero on every row of all three matrices. The current tool's eight synthetic tests passed. This is self-verification by the original finder, not verification by a different person. No raw metadata was newly measured, and no image or preview was used.

## Reproduce

From commit `1cf2a0e934e5fc3e997ef363031450b4377699a1`, using its public `samples/manifest.csv`:

```sh
python -I -B tools/test_cohort_design_audit.py
python -I -B tools/cohort_design_audit.py --manifest samples/manifest.csv --ids 1799 2151 1993 1994 1995 1996 5283 5284 7262 7267 6343 6344
python -I -B tools/cohort_design_audit.py --manifest samples/manifest.csv --ids 1799 2151 1993 1994 1995 1996 5283 5284 7262 7267 6343 6344 1997
```

The commands use public repository metadata and print the input identities, matrix summaries and nullspace vectors. The lead's original manifest is available at its cited commit.

For a separate forward-elimination check, save the JSON printed by a command above in your own scratch folder. The following one-off checker reads report paths passed as arguments, reconstructs the matrix, checks each alias by substitution and recomputes conditional increments. It only reads reports and prints counts.

```python
"""Independent forward elimination and alias substitution over audit JSON output."""
import json
from fractions import Fraction
from pathlib import Path
import sys




def rank(rows):
    rows = [[Fraction(x) for x in row] for row in rows]
    n = 0
    for col in range(len(rows[0])):
        pivot = next((i for i in range(n, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[n], rows[pivot] = rows[pivot], rows[n]
        for i in range(n + 1, len(rows)):
            if rows[i][col]:
                scale = rows[i][col] / rows[n][col]
                rows[i] = [x - scale * y for x, y in zip(rows[i], rows[n])]
        n += 1
        if n == len(rows):
            break
    return n


for name in sys.argv[1:]:
    raw = Path(name).read_bytes()
    report = json.loads(raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig"))
    labels = report["columns"]
    matrix = []
    for record in report["inputs"]:
        factors = {"body": json.dumps([record["make"], record["model"]], ensure_ascii=True),
                   "recorded_mode": record["mode"],
                   "geometry": "%sx%s" % (int(record["payload_w"]), int(record["payload_h"])),
                   "extension": Path(record["pixls_name"]).suffix.lower()}
        matrix.append([1] + [int(factors[label.split("=", 1)[0]] == label.split("=", 1)[1])
                             for label in labels[1:]])
    independent_rank = rank(matrix)
    substitutions = [sum(sum(Fraction(alias.get(label, "0")) * x for x, label in zip(row, labels)) != 0
                         for row in matrix) for alias in report["nullspace"]]
    print(name, "rows", len(matrix), "columns", len(labels), "rank", independent_rank,
          "nullity", len(labels) - independent_rank, "cells", len(report["cells"]),
          "conditional", report["conditional_rank_increment"], "alias_nonzero_rows", substitutions)
    assert independent_rank == report["rank"]
    assert not any(substitutions)
    vectors = [[Fraction(alias.get(label, "0")) for label in labels] for alias in report["nullspace"]]
    assert rank(vectors) == len(vectors)
    print("alias vectors independent:", rank(vectors))
    for factor in ("body", "recorded_mode", "geometry", "extension"):
        keep = [i for i, label in enumerate(labels) if not label.startswith(factor + "=")]
        smaller = [[row[i] for i in keep] for row in matrix]
        assert independent_rank - rank(smaller) == report["conditional_rank_increment"][factor]
    if report["files"] == 13:
        print("new identity:", next(x for x in report["inputs"] if x["pixls_id"] == "1997"))
        print("repeated cells:", [cell for cell in report["cells"] if cell["files"] > 1])
```
