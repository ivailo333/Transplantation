# STEP 26 — HLA Comparison Statistics / Aggregation

Step 26 adds deterministic descriptive statistics over STEP 25 mismatch
summaries.

No SQLite migration is required.

## Architecture

```text
STEP 24 matrix
    ↓
STEP 25 mismatch summary / classification
    ↓
STEP 26 statistics / aggregation
```

STEP 26 does not duplicate STEP 25 classification rules. It consumes the
STEP 25 summary as its source of truth.

## Main commands

One recipient against many donors:

```powershell
python .\main.py stats recipient RECIP-001
```

One donor against many recipients:

```powershell
python .\main.py stats donor DONOR-001
```

Persistent batch:

```powershell
python .\main.py stats batch 3
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
python .\main.py stats recipient RECIP-001 `
    --level G
```

## Locus filtering

```powershell
python .\main.py stats recipient RECIP-001 `
    --locus A `
    --locus DRB1
```

Pair TOTAL statistics are then calculated only from the selected loci.

## Candidate filtering

```powershell
python .\main.py stats recipient RECIP-001 `
    --candidate DONOR-001
```

Repeat `--candidate` to include several candidates.

## Deterministic software ordering

```powershell
python .\main.py stats recipient RECIP-001 `
    --sort-by donor-only
```

```powershell
python .\main.py stats recipient RECIP-001 `
    --sort-by shared `
    --sort-order desc
```

Ordering may affect detail-row order only. Aggregate values are invariant.

## Details

```powershell
python .\main.py stats recipient RECIP-001 `
    --details
```

This adds a compact pair-detail section after the aggregate statistics.

## Numeric statistics

STEP 26 calculates:

```text
count
sum
min
max
mean
median
```

for:

```text
shared_count
donor_only_count
recipient_only_count
```

at:

```text
pair-total level
per-locus level
```

## Classification distributions

STEP 25 descriptive labels are aggregated:

```text
COMPLETE-SOFTWARE-MATCH
PARTIAL-SOFTWARE-MATCH
NO-SOFTWARE-SHARED
```

Each distribution contains:

```text
count
percentage
```

Percentages are descriptive only, not probabilities of clinical
compatibility.

## Empty-set behavior

For no pairs:

```text
count = 0
sum = 0
min = null
max = null
mean = null
median = null
```

All classification percentages are:

```text
0.0
```

No divide-by-zero occurs.

## Single-pair behavior

For one pair:

```text
min = value
max = value
mean = value
median = value
sum = value
```

## Persistent mode

```powershell
python .\main.py stats batch 3
```

Persistent mode follows:

```text
stored batch
    ↓
stored analysis_results
    ↓
STEP 24 persistent matrix
    ↓
STEP 25 persistent summary
    ↓
STEP 26 statistics
```

No py-ard reduction is recalculated.

## Export

```powershell
python .\main.py stats recipient RECIP-001 `
    --export `
    --format both
```

```powershell
python .\main.py stats batch 3 `
    --export `
    --format both
```

Supported:

```text
json
csv
both
```

Default output directory:

```text
exports\stats
```

Optional:

```text
--output-dir PATH
--name NAME
--overwrite
```

### JSON

JSON preserves the complete STEP 26 statistics payload.

### CSV

CSV contains:

```text
one TOTAL row
+
one row per selected locus
```

with explicit statistics and classification distribution fields.

## Routing

`stats` is registered in:

```python
cli.STEP15_COMMAND_GROUPS
```

Regression tests also protect:

```text
summary
matrix
pairs
```

so newer command groups do not fall back to the legacy interactive path.

## Clinical boundary

STEP 26 is strictly descriptive NON-CLINICAL software-comparison
statistics.

It does NOT calculate or infer:

```text
clinical compatibility
clinical risk
virtual crossmatch
DSA
MFI
unacceptable antigens
cPRA
eplet mismatch
PIRCHE
TCE permissiveness
blood-group compatibility
allocation priority
waiting-list priority
graft survival
rejection probability
best donor
worst donor
clinical ranking
transplant suitability
```

## Acceptance criteria

1. `stats recipient` works.
2. `stats donor` works.
3. `stats batch` works.
4. CANONICAL/LGX/G/P remain supported.
5. Locus filtering works.
6. Candidate filtering works.
7. Pair-level count/sum/min/max/mean/median are correct.
8. Locus-level statistics are correct.
9. Pair classification distribution is correct.
10. Locus classification distribution is correct.
11. Percentages are correct.
12. Single-pair behavior is correct.
13. Empty-set behavior is safe.
14. `--details` works.
15. Sorting does not alter aggregate statistics.
16. JSON export works.
17. CSV export works.
18. Overwrite protection works.
19. Persistent mode does not recalculate py-ard.
20. `stats` routes through command-style CLI.
21. `summary`, `matrix`, and `pairs` remain protected.
22. Steps 1–25 remain regression-compatible.
23. No clinical score, risk estimate, or clinical ranking is introduced.
