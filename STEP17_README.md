# STEP 17 — Batch DONOR↔RECIPIENT analysis

Step 17 adds one-to-many HLA software comparisons on top of the
Step 16 import / Step 15 command CLI / Step 14 modular architecture.

The batch engine uses the RAW/CANONICAL/LGX/G/P representations already
stored in SQLite. It does **not** call py-ard again when comparing saved
typings.

## 1. One recipient against all donors

Compute only — no new database rows:

```powershell
python .\main.py batch recipient RECIP-001
```

Persist all generated pairs:

```powershell
python .\main.py batch recipient RECIP-001 --save
```

Use a specific recipient typing:

```powershell
python .\main.py batch recipient RECIP-001 --typing-id 2
```

Restrict the batch to selected donors:

```powershell
python .\main.py batch recipient RECIP-001 --candidate DONOR-001
```

Multiple candidates:

```powershell
python .\main.py batch recipient RECIP-001 `
    --candidate DONOR-001 `
    --candidate DONOR-002
```

## 2. One donor against all recipients

Compute only:

```powershell
python .\main.py batch donor DONOR-001
```

Persist:

```powershell
python .\main.py batch donor DONOR-001 --save
```

Restrict to selected recipients:

```powershell
python .\main.py batch donor DONOR-001 `
    --candidate RECIP-001 `
    --candidate RECIP-002
```

## 3. Default NO SAVE behavior

The default is intentionally read-only:

```text
Mode: NO SAVE
```

The program loads the existing stored HLA representations, computes every
pair, prints a batch summary, and does not create `analysis_runs` or
`analysis_results`.

Use `--save` only when the batch should become part of the analysis history.

## 4. Atomic SAVE behavior

With:

```powershell
python .\main.py batch recipient RECIP-001 --save
```

the whole persisted batch is one SQLite transaction:

```text
pair 1 -> analysis_run + 24 results
pair 2 -> analysis_run + 24 results
pair 3 -> analysis_run + 24 results
...
COMMIT
```

If one pair fails while saving:

```text
ROLLBACK
```

so analysis rows from the earlier pairs in that same batch are not left
partially stored.

## 5. Candidate selection

Without `--candidate`, the latest saved typing is selected for every subject
with the opposite role:

```text
recipient mode -> all DONOR subjects
donor mode     -> all RECIPIENT subjects
```

With repeated `--candidate`, only those subjects are compared.

A candidate with a different IPD-IMGT/HLA version is skipped and reported.
An explicitly selected candidate with the wrong role or unknown external_id
is rejected.

## 6. Summary levels

Every pair still produces the same full 24-result structure:

```text
4 representations × 6 loci = 24
```

Representations:

```text
CANONICAL
LGX
G
P
```

Loci:

```text
A
B
C
DRB1
DQB1
DPB1
```

The Step 17 batch summary additionally totals:

```text
shared_count
donor_only_count
recipient_only_count
```

across the six loci for each representation.

## 7. Important interpretation

These totals remain **copy-sensitive software-comparison counts**.

They are **not**:

```text
a clinical organ-allocation score
a virtual crossmatch
a DSA assessment
an eplet mismatch score
cPRA
a transplant eligibility decision
```

The batch output therefore must not be interpreted as a clinical ranking of
donors or recipients.

## 8. Step 16 import files remain in project root

The current project convention remains:

```text
import_typing.json
import_typing.csv
import_typings_batch.json
```

For example:

```powershell
python .\main.py typings import .\import_typing.json --dry-run
```

## 9. Tests

Run the complete suite:

```powershell
python -m unittest discover -s tests -v
```

The package preserves the 173 Step 16 regression tests and adds the
Step 17 batch-analysis tests.

Expected total in this package: **198 tests**.
