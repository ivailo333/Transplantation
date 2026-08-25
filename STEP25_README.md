# STEP 25 — HLA Mismatch Summary / Classification Layer

Step 25 summarizes STEP 24 matrix counts into deterministic, descriptive **NON-CLINICAL** software classes. No SQLite migration is required.

## Classification rules

`COMPLETE-SOFTWARE-MATCH`: `donor_only_count == 0` and `recipient_only_count == 0`.

`PARTIAL-SOFTWARE-MATCH`: `shared_count > 0` and at least one unmatched copy exists.

`NO-SOFTWARE-SHARED`: `shared_count == 0`.

These labels are software descriptions only. They are not clinical histocompatibility risk categories.

## Commands

```powershell
python .\main.py summary recipient RECIP-001
python .\main.py summary donor DONOR-001
python .\main.py summary batch 3
```

Level/locus filtering:

```powershell
python .\main.py summary recipient RECIP-001 `
    --level lgx `
    --locus DRB1
```

Candidate restriction:

```powershell
python .\main.py summary recipient RECIP-001 `
    --candidate DONOR-001
```

Deterministic software ordering reuses STEP 18:

```powershell
python .\main.py summary recipient RECIP-001 `
    --sort-by donor-only
```

Persistent batch mode:

```powershell
python .\main.py summary batch 3 `
    --level lgx `
    --locus A `
    --locus DRB1
```

Export:

```powershell
python .\main.py summary recipient RECIP-001 `
    --export `
    --format both
```

Default output directory:

```text
exports\summary
```

Supported export formats are `json`, `csv`, and `both`; `--overwrite`, `--output-dir`, and `--name` are supported.

## Architecture

STEP 25 consumes STEP 24 matrix output. It reuses already stored HLA representations/results and does **not** recalculate py-ard reductions.

Routing adds `summary` to `cli.STEP15_COMMAND_GROUPS`, while preserving `matrix` and `pairs`.

## Clinical boundary

STEP 25 does **not** calculate virtual crossmatch, DSA, unacceptable antigens, cPRA, eplet mismatch, PIRCHE, allocation priority, blood-group compatibility, waiting-list priority, transplant eligibility, or graft outcome.

## Acceptance criteria

1. `summary recipient`, `summary donor`, and `summary batch` work.
2. CANONICAL/LGX/G/P remain available through STEP 24.
3. Locus and candidate filtering work.
4. Per-locus and pair-total descriptive classifications are deterministic.
5. Persistent mode reuses saved results without py-ard recalculation.
6. JSON/CSV export and overwrite protection work.
7. `summary` routes through command-style CLI.
8. STEP 24 `matrix` and STEP 23 `pairs` routing remain intact.
9. Steps 1–24 remain regression compatible.
10. No clinical score or clinical risk category is introduced.
