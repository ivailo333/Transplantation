# STEP 28 — HLA Report Comparison / Multi-Report Analysis

STEP 28 compares validated STEP 27 reports without introducing a new HLA
calculation engine.

```text
STEP 24 matrix
    ↓
STEP 25 mismatch summary / classification
    ↓
STEP 26 statistics
    ↓
STEP 27 analytical report
    ↓
STEP 28 report comparison
```

No SQLite migration is required.

## Modes

### 1. Compare representation levels

Compare the same live scope across CANONICAL / LGX / G / P:

```powershell
python .\main.py compare levels recipient RECIP-001
```

or:

```powershell
python .\main.py compare levels donor DONOR-001
```

Default level set:

```text
CANONICAL
LGX
G
P
```

Choose only selected levels:

```powershell
python .\main.py compare levels recipient RECIP-001 `
    --level canonical `
    --level lgx
```

At least two distinct levels are required.

### 2. Compare persistent batches

```powershell
python .\main.py compare batches 1 3
```

Select a representation:

```powershell
python .\main.py compare batches 1 3 `
    --level lgx
```

The two batches must have the same:

```text
direction
anchor external_id
selected locus scope
representation level
```

Anchor typing ID, IPD-IMGT/HLA version, and candidate membership may differ.
Those context changes are displayed explicitly.

## Level comparison output

STEP 28 shows:

```text
LEVEL OVERVIEW
PAIR DELTAS FROM REFERENCE LEVEL
CROSS-LEVEL STABILITY
LOCUS AGGREGATE DELTAS
```

The first requested level is the reference level.

For every common candidate the software deltas are:

```text
d_shared
d_donor
d_recipient
classification_changed
```

These are software-representation deltas only.

## Batch comparison output

STEP 28 shows:

```text
CANDIDATE MEMBERSHIP
COMMON-CANDIDATE DELTAS
CONTEXT CHANGES
LOCUS AGGREGATE DELTAS
```

Candidate membership is separated into:

```text
common
only left
only right
```

Context changes include:

```text
anchor typing changed
IPD-IMGT/HLA version changed
candidate membership changed
```

## Filters

Candidate:

```powershell
python .\main.py compare levels recipient RECIP-001 `
    --candidate DONOR-001
```

Locus:

```powershell
python .\main.py compare levels recipient RECIP-001 `
    --locus DRB1
```

Multiple loci:

```powershell
python .\main.py compare levels recipient RECIP-001 `
    --locus A `
    --locus DRB1
```

Deterministic software ordering:

```powershell
python .\main.py compare levels recipient RECIP-001 `
    --sort-by shared `
    --sort-order desc
```

Ordering affects presentation scope only; it is not a clinical ranking.

## Export

Bare export means JSON + CSV:

```powershell
python .\main.py compare levels recipient RECIP-001 `
    --level lgx `
    --level G `
    --export
```

Explicit:

```powershell
python .\main.py compare batches 1 3 `
    --export json
```

Supported:

```text
json
csv
both
```

Default directory:

```text
exports\comparisons
```

Optional:

```text
--output-dir PATH
--name NAME
--overwrite
```

## JSON

The JSON export preserves the complete comparison payload, including:

```text
mode
scope
levels/batches
level summaries
pair deltas
locus deltas
candidate membership
context changes
stability
provenance
```

## CSV

CSV contains record types:

```text
LEVEL
PAIR_DELTA
LOCUS_DELTA
MEMBERSHIP
```

`MEMBERSHIP` records apply to batch comparisons when candidates exist only
on one side.

## Cross-level stability

For a level comparison STEP 28 reports:

```text
candidate_count
identical_total_counts_across_levels
stable_pair_classification_across_levels
```

This is a deterministic software-stability description, not a clinical
stability or risk measure.

## Clinical boundary

STEP 28 is strictly NON-CLINICAL.

It does NOT calculate or infer:

```text
clinical compatibility
clinical risk
organ-allocation priority
virtual crossmatch
DSA
MFI
unacceptable antigens
cPRA
eplet mismatch
PIRCHE
TCE permissiveness
blood-group compatibility
waiting-list priority
best donor
worst donor
graft survival
rejection probability
transplant suitability
```

A positive or negative delta must not be interpreted as clinical
improvement or deterioration.

## No recalculation / persistence side effects

STEP 28:

```text
does NOT recalculate py-ard reductions
does NOT create analysis_runs
does NOT create analysis_results
does NOT modify persistent batches
```

It consumes STEP 27 reports only.

## Acceptance criteria

1. `compare levels recipient` works.
2. `compare levels donor` works.
3. Default CANONICAL/LGX/G/P comparison works.
4. Explicit repeated `--level` works.
5. At least two levels are required.
6. Candidate filtering works.
7. Locus filtering works.
8. Software ordering works.
9. Level overview is deterministic.
10. Pair deltas are computed relative to the first level.
11. Locus aggregate deltas are computed.
12. Cross-level count stability is reported.
13. Cross-level classification stability is reported.
14. Level comparison scope mismatches are rejected.
15. `compare batches LEFT RIGHT` works.
16. Same batch ID on both sides is rejected.
17. Common candidates are identified.
18. Left-only candidates are identified.
19. Right-only candidates are identified.
20. Batch pair deltas are computed for common candidates.
21. Batch locus deltas are computed.
22. Anchor typing changes are reported.
23. IPD-IMGT/HLA version changes are reported.
24. Candidate membership changes are reported.
25. JSON export works.
26. CSV export works.
27. Bare `--export` means BOTH.
28. Explicit json/csv/both works.
29. Overwrite protection works.
30. `compare` routes through command-style CLI.
31. `report`, `stats`, `summary`, `matrix`, and `pairs` remain protected.
32. Steps 1–27 remain regression-compatible.
33. No py-ard reduction is recalculated by STEP 28.
34. No analysis_run is created by STEP 28.
35. No clinical score/risk/ranking is introduced.
