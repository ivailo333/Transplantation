# STEP 19 — JSON / CSV export of batch and software-ordered results

Step 19 adds portable file export for Step 17 batch analyses and Step 18
software-ordered batch views.

No SQLite schema migration is required.

## 1. Basic batch export

Export one recipient against all eligible donors:

```powershell
python .\main.py batch recipient RECIP-001 --export
```

Default format:

```text
both
```

so the command creates JSON and CSV files.

Default directory:

```text
exports\batch\
```

## 2. Choose a format

JSON only:

```powershell
python .\main.py batch recipient RECIP-001 `
    --export `
    --export-format json
```

CSV only:

```powershell
python .\main.py batch recipient RECIP-001 `
    --export `
    --export-format csv
```

Both:

```powershell
python .\main.py batch recipient RECIP-001 `
    --export `
    --export-format both
```

## 3. Export Step 18 software ordering

Example:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --sort-level lgx `
    --export
```

The JSON and CSV preserve:

```text
software_position
software_rank
sort level
sort metric
sort order
criterion value
```

for each ordered pair.

## 4. Display limit does NOT truncate export

This is intentional:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --limit 5 `
    --export
```

means:

```text
compute all eligible pairs
order all pairs
display only 5
export ALL ordered pairs
```

This prevents accidental loss of data merely because the terminal output
was shortened.

The same rule applies with `--save`:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --limit 5 `
    --save `
    --export
```

means:

```text
save ALL eligible pairs atomically
export ALL ordered pairs
display only 5
```

## 5. NO SAVE export is supported

You do not need to create analysis_runs in order to export:

```powershell
python .\main.py batch recipient RECIP-001 `
    --export
```

In this case:

```text
run_id = null
```

in JSON and blank in CSV.

Export itself never creates analysis_runs.

## 6. SAVE + export

You may persist the batch and export it in the same command:

```powershell
python .\main.py batch recipient RECIP-001 `
    --save `
    --export
```

The exported pairs then contain their generated `run_id` values.

## 7. Output directory

Custom directory:

```powershell
python .\main.py batch recipient RECIP-001 `
    --export `
    --export-dir .\my_exports
```

## 8. Custom filename

```powershell
python .\main.py batch recipient RECIP-001 `
    --export `
    --export-name recipient_001_donors
```

The extensions are added automatically:

```text
recipient_001_donors.json
recipient_001_donors.csv
```

## 9. Overwrite protection

Existing files are not replaced by default.

To replace them deliberately:

```powershell
python .\main.py batch recipient RECIP-001 `
    --export `
    --overwrite
```

JSON and CSV writes are atomic through temporary files followed by replace.

## 10. JSON structure

The JSON schema identifier is:

```text
hla-batch-export-v1
```

The document contains:

```text
batch metadata
ordering metadata, when Step 18 ordering is active
skipped candidates
all exported pairs
donor / recipient typing IDs
run_id, when saved
summary counts
full 24 per-pair comparison results
non-clinical interpretation warning
```

## 11. CSV structure

CSV uses one row per:

```text
pair × representation × locus
```

Therefore:

```text
24 data rows per pair
```

because:

```text
4 representations × 6 loci = 24
```

For example:

```text
2 pairs -> 48 CSV data rows
10 pairs -> 240 CSV data rows
```

The CSV includes identifiers, run_id, software-order metadata when present,
counts, and JSON-encoded value lists.

UTF-8 with BOM is used to make opening the file in Excel on Windows easier.

## 12. Backward compatibility

All previous commands continue to work:

```powershell
python .\main.py batch recipient RECIP-001
python .\main.py batch donor DONOR-001
python .\main.py batch recipient RECIP-001 --sort-by donor-only
python .\main.py batch recipient RECIP-001 --candidate DONOR-001 --save
```

Step 19 is enabled only by:

```text
--export
```

## 13. Interpretation

The exported ordering and counts are software-comparison data only.

They are NOT:

```text
a clinical donor ranking
an organ-allocation score
a virtual crossmatch
a DSA assessment
an eplet mismatch score
cPRA
a transplant eligibility decision
a graft-outcome prediction
```

Exporting a Step 18 software rank does not turn it into a clinical rank.

## 14. Tests

Run:

```powershell
python -m unittest discover -s tests -v
```

The generated package preserves all Step 18 regression tests and adds
Step 19 tests for JSON, CSV, ordering metadata, display-limit separation,
NO SAVE/SAVE semantics, overwrite protection, atomic file creation and CLI
backward compatibility.

Expected total in this generated package: **264 tests**.
