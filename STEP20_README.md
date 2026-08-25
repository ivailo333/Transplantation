# STEP 20 — Persistent Batch Runs / Batch History

Step 20 adds a persistent identity for every saved CLI batch.

Until Step 19, `--save` created the individual `analysis_runs`, but there was
no SQLite object saying that those runs were created together as one batch.
Step 20 adds that missing traceability layer.

## New schema version

Step 20 raises the SQLite schema version from:

```text
2 -> 3
```

New tables:

```text
batch_runs
batch_run_items
```

Before using normal commands after copying Step 20, back up the database and
apply the migration:

```powershell
Copy-Item .\transplant.db .\transplant_before_step20.db
python .\main.py db status
python .\main.py db migrate
python .\main.py db status
```

Expected status:

```text
Schema version: 3 / 3
Current: True
STEP 20 batch history schema: True
Pending migrations: none
```

## What is saved

A saved batch now has its own:

```text
batch_id
```

The structure is conceptually:

```text
batch_run
  -> analysis_run 1 -> 24 analysis_results
  -> analysis_run 2 -> 24 analysis_results
  -> analysis_run 3 -> 24 analysis_results
```

`batch_runs` stores:

```text
direction
exact anchor_typing_id
IPD-IMGT/HLA version
pair_count
skipped-candidate metadata
Step 18 sort level / metric / order, when used
original display limit, when used
created_at
```

`batch_run_items` stores:

```text
analysis_run_id
exact candidate_typing_id
item_position
software_position
software_rank
criterion_value
```

The software-order fields are nullable when Step 18 ordering was not used.

## Atomic persistence

For the command CLI, Step 20 now makes one saved batch a single transaction:

```text
batch_runs row
+ N analysis_runs
+ N × 24 analysis_results
+ N batch_run_items
-> COMMIT
```

If any pair fails during the transaction:

```text
ROLLBACK
```

so neither the persistent batch nor partial analysis runs remain.

## Existing batch command

The normal command remains:

```powershell
python .\main.py batch recipient RECIP-001 --save
```

but the output now also includes:

```text
Persistent batch_id: ...
```

Step 18 ordering is preserved:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --sort-level lgx `
    --limit 5 `
    --save
```

All eligible pairs are saved, while the original terminal display limit is
stored only as batch metadata.

## New `batches` command group

List persistent batches:

```powershell
python .\main.py batches list
```

Show metadata and linked analysis runs:

```powershell
python .\main.py batches show 1
```

Reload the exact saved analysis results:

```powershell
python .\main.py batches results 1
```

This reads the already stored `analysis_results`; it does not re-run py-ard.

## Re-export from history

A persistent batch can be exported later without recomputing HLA reductions:

```powershell
python .\main.py batches export 1
```

JSON only:

```powershell
python .\main.py batches export 1 --format json
```

Custom directory:

```powershell
python .\main.py batches export 1 `
    --format both `
    --output-dir .\exports\batch_history
```

Custom name:

```powershell
python .\main.py batches export 1 `
    --name recipient_001_saved_batch
```

Overwrite protection remains active:

```powershell
python .\main.py batches export 1 --overwrite
```

The default re-export name is:

```text
batch_run_<batch_id>.json
batch_run_<batch_id>.csv
```

## Step 19 export compatibility

A batch can still be saved and exported immediately:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --limit 1 `
    --save `
    --export `
    --export-format both
```

The JSON/CSV now also contains the persistent `batch_id` when the source batch
was saved.

CSV adds:

```text
batch_id
batch_created_at
```

## Important interpretation

Step 20 is a data-management and reproducibility feature.

It does not introduce a clinical score. Stored `software_rank` values remain
only deterministic ordering metadata from Step 18 and are not:

```text
an organ-allocation rank
a virtual crossmatch
a DSA assessment
an eplet mismatch score
cPRA
a transplant eligibility decision
a graft-outcome prediction
```

## Tests

Run the complete regression suite after migration:

```powershell
python -m unittest discover -s tests -v
```

The Step 20 package includes migration, atomic persistence, history loading,
SQLite re-export, CLI and backward-compatibility tests.

Expected total in this generated package: **293 tests**.
