# STEP 27 — HLA Analytical Reporting

Step 27 is the reporting layer above the existing non-clinical comparison
pipeline.

```text
STEP 24 matrix
    ↓
STEP 25 mismatch summary / classification
    ↓
STEP 26 descriptive statistics
    ↓
STEP 27 analytical report
```

No SQLite migration is required.

## Core design rule

STEP 27 must not implement a second HLA engine.

It composes one STEP 24 matrix, derives STEP 25 and STEP 26 data from that
same scope, validates consistency, and renders one reproducible report.

It does NOT recalculate py-ard reductions and does NOT create
`analysis_runs`.

## Commands

Live recipient report:

```powershell
python .\main.py report recipient RECIP-001
```

Live donor report:

```powershell
python .\main.py report donor DONOR-001
```

Persistent batch report:

```powershell
python .\main.py report batch 3
```

## Representation level

Default:

```text
LGX
```

Supported:

```text
CANONICAL
LGX
G
P
```

Example:

```powershell
python .\main.py report recipient RECIP-001 `
    --level G
```

## Locus filter

```powershell
python .\main.py report recipient RECIP-001 `
    --level lgx `
    --locus A `
    --locus DRB1
```

All report totals and statistics are then based on the selected locus
scope.

## Candidate filter

```powershell
python .\main.py report recipient RECIP-001 `
    --candidate DONOR-001
```

Repeat `--candidate` to include several candidates.

## Deterministic software ordering

```powershell
python .\main.py report recipient RECIP-001 `
    --sort-by donor-only
```

```powershell
python .\main.py report recipient RECIP-001 `
    --sort-by shared `
    --sort-order desc
```

The report calls this `Software ordering`. It is not clinical ranking.

## Report sections

The terminal report contains:

```text
PAIR OVERVIEW
LOCUS OVERVIEW
LOCUS CLASSIFICATION DISTRIBUTION
DESCRIPTIVE PAIR STATISTICS
REPORT PROVENANCE / INTEGRITY
NON-CLINICAL disclaimer
```

## Consistency validation

STEP 27 validates that STEP 24, STEP 25, and STEP 26 describe the same:

```text
source
batch_id
direction
anchor
typing_id
IPD-IMGT/HLA version
representation level
loci
pair count
candidate order
```

It also validates:

```text
matrix pair totals == summary pair totals
summary totals == STEP 26 aggregate statistics
STEP 25 classifications == STEP 26 distributions
locus statistics == recomputed descriptive aggregates
represented locus observations == pair_count × locus_count
```

These are integrity checks only. They do not perform new HLA reduction.

## Export

Bare `--export` means both JSON and CSV:

```powershell
python .\main.py report recipient RECIP-001 `
    --export
```

Explicit format:

```powershell
python .\main.py report recipient RECIP-001 `
    --export json
```

```powershell
python .\main.py report batch 3 `
    --export both
```

Default directory:

```text
exports\reports
```

Optional:

```text
--output-dir PATH
--name NAME
--overwrite
```

## JSON

JSON is the canonical machine-readable STEP 27 report. It contains:

```text
report metadata
anchor
HLA reference/version/level/loci
pair overview rows
locus overview rows
pair classification distribution
locus classification distribution
pair descriptive statistics
software ordering metadata
provenance / integrity flags
```

## CSV

CSV uses a `record_type` column and contains:

```text
PAIR
LOCUS
```

records in one export file.

## Routing

STEP 27 registers:

```text
report
```

in `cli.STEP15_COMMAND_GROUPS`.

Regression tests retain routing protection for:

```text
stats
summary
matrix
pairs
```

## Clinical boundary

STEP 27 is a deterministic NON-CLINICAL analytical software report.

It is NOT:

```text
organ-allocation report
clinical compatibility score
clinical risk score
virtual crossmatch
DSA assessment
MFI interpretation
unacceptable-antigen assessment
cPRA calculation
eplet mismatch analysis
PIRCHE
blood-group compatibility
waiting-list priority
best-donor ranking
transplant-suitability decision
graft-outcome prediction
```

## Acceptance criteria

1. `report recipient` works.
2. `report donor` works.
3. `report batch` works.
4. CANONICAL/LGX/G/P remain supported.
5. Locus filtering works.
6. Candidate filtering works.
7. Deterministic software ordering works.
8. STEP 24 matrix is reused as the source comparison scope.
9. STEP 25 classifications are derived from that matrix.
10. STEP 26 statistics are derived from that summary.
11. Scope consistency is validated.
12. Pair aggregates are validated.
13. Classification distributions are validated.
14. Locus aggregates are validated.
15. JSON export works.
16. CSV export works.
17. Bare `--export` means BOTH.
18. Explicit `--export json|csv|both` works.
19. Overwrite protection works.
20. Persistent mode reuses stored analysis results.
21. No py-ard reduction is recalculated by STEP 27.
22. No analysis_run is created by STEP 27.
23. `report` routes through command-style CLI.
24. `stats`, `summary`, `matrix`, and `pairs` remain protected.
25. Steps 1–26 remain regression-compatible.
26. No clinical score, risk estimate, or clinical ranking is introduced.
