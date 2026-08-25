# STEP 24 — HLA Comparison Matrix

Step 24 adds a compact multi-pair HLA software-comparison matrix.

No SQLite migration is required.

## Core matrix

One recipient against all eligible donors:

```powershell
python .\main.py matrix recipient RECIP-001
```

One donor against all eligible recipients:

```powershell
python .\main.py matrix donor DONOR-001
```

Default representation level:

```text
LGX
```

Each matrix cell is:

```text
shared_count/donor_only_count/recipient_only_count
```

Example:

```text
1/1/1
```

means:

```text
shared_count=1
donor_only_count=1
recipient_only_count=1
```

## Representation level

```powershell
python .\main.py matrix recipient RECIP-001 `
    --level canonical
```

```powershell
python .\main.py matrix recipient RECIP-001 `
    --level G
```

Supported:

```text
CANONICAL
LGX
G
P
```

## Candidate restriction

```powershell
python .\main.py matrix recipient RECIP-001 `
    --candidate DONOR-001
```

Repeat `--candidate` to include several candidates.

## Locus filtering

```powershell
python .\main.py matrix recipient RECIP-001 `
    --locus A `
    --locus DRB1
```

Supported loci:

```text
A
B
C
DRB1
DQB1
DPB1
```

The matrix preserves canonical HLA locus ordering.

## Deterministic software ordering

```powershell
python .\main.py matrix recipient RECIP-001 `
    --sort-by donor-only
```

```powershell
python .\main.py matrix recipient RECIP-001 `
    --sort-by shared `
    --sort-order desc
```

Supported metrics:

```text
donor-only
shared
recipient-only
```

AUTO order follows STEP 18:

```text
shared          -> DESC
donor-only      -> ASC
recipient-only  -> ASC
```

This is deterministic software ordering only.

## Persistent matrix

A stored STEP 20 batch can be reloaded directly:

```powershell
python .\main.py matrix batch 3
```

Filtered:

```powershell
python .\main.py matrix batch 3 `
    --level lgx `
    --locus DRB1
```

Persistent mode loads the saved `analysis_results` from SQLite and does not
recalculate py-ard reductions.

## Export

```powershell
python .\main.py matrix recipient RECIP-001 `
    --export
```

```powershell
python .\main.py matrix batch 3 `
    --level lgx `
    --export `
    --format both
```

Supported export formats:

```text
json
csv
both
```

Default directory:

```text
exports\matrix
```

Optional:

```text
--output-dir PATH
--name NAME
--overwrite
```

CSV has one row per donor/recipient pair and explicit per-locus columns:

```text
A_shared_count
A_donor_only_count
A_recipient_only_count
...
total_shared_count
total_donor_only_count
total_recipient_only_count
```

## Routing

STEP 24 registers:

```text
matrix
```

in `cli.STEP15_COMMAND_GROUPS`.

STEP 23 `pairs` remains registered as well. Regression tests protect both
routes so the command cannot silently fall back to legacy STEP 13G.

## Acceptance criteria

1. `matrix recipient RECIP-001` works.
2. `matrix donor DONOR-001` works.
3. `matrix batch BATCH_ID` works.
4. CANONICAL/LGX/G/P are supported.
5. One or more locus filters are supported.
6. Candidate restriction works in live mode.
7. Per-row totals equal the sum of selected locus cells.
8. Persistent mode reads stored `analysis_results`.
9. Persistent mode does not recalculate py-ard reductions.
10. STEP 18 deterministic sorting is reusable.
11. JSON export works.
12. CSV export works.
13. Export overwrite protection works.
14. `matrix` routes through command-style CLI.
15. STEP 23 `pairs` routing remains protected.
16. Existing Steps 1–23 remain regression-compatible.
17. No clinical score or clinical ranking is introduced.

## Clinical boundary

STEP 24 is a software-comparison matrix only.

It is NOT:
- an organ-allocation score;
- a virtual crossmatch;
- DSA assessment;
- eplet mismatch analysis;
- cPRA;
- blood-group compatibility;
- transplant eligibility;
- graft-outcome prediction.
