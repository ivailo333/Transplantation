# STEP 22 — Batch Filtering & Selection

Step 22 adds an explicit non-clinical selection view over the already computed
Step 17 batch results.

No SQLite schema migration is required.

## Selection criteria

Supported representation levels:

```text
canonical
lgx
G
P
```

Default when a Step 22 filter is used:

```text
lgx
```

Supported predicates:

```text
--max-donor-only N
--min-shared N
--max-recipient-only N
--exclude-candidate EXTERNAL_ID
```

Multiple predicates are combined with logical AND.

## Examples

Select rows with LGX donor_only_count <= 10:

```powershell
python .\main.py batch recipient RECIP-001 `
    --filter-level lgx `
    --max-donor-only 10
```

Require at least 3 shared LGX copies:

```powershell
python .\main.py batch recipient RECIP-001 `
    --min-shared 3
```

Combine predicates:

```powershell
python .\main.py batch recipient RECIP-001 `
    --max-donor-only 10 `
    --min-shared 2
```

Exclude a candidate:

```powershell
python .\main.py batch recipient RECIP-001 `
    --exclude-candidate DONOR-002
```

## Interaction with Step 18 ordering

Step 18 ordering happens first, then Step 22 selects rows while preserving
the Step 18 order.

Example:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --sort-level lgx `
    --max-donor-only 10
```

## Persistence safety

Step 22 is a selected VIEW.

With:

```powershell
python .\main.py batch recipient RECIP-001 `
    --max-donor-only 10 `
    --save
```

Step 20 still persists ALL eligible computed pairs atomically.

The Step 22 software filter does not silently truncate persistent audit
history.

## Export semantics

Ordinary export remains backward compatible and exports the full computed
batch:

```powershell
python .\main.py batch recipient RECIP-001 `
    --max-donor-only 10 `
    --export
```

To deliberately export only the selected view:

```powershell
python .\main.py batch recipient RECIP-001 `
    --max-donor-only 10 `
    --export `
    --export-selection
```

This explicit flag makes the selected-subset behavior visible and auditable.

## Display limit

`--limit` remains display-only and belongs to Step 18 ordering.

Step 22 selection and Step 18 display limiting are separate concepts.

## Acceptance criteria

1. Existing Steps 1–21 remain regression-compatible.
2. No migration is required.
3. Thresholds are validated as non-negative integers.
4. Multiple predicates use AND.
5. Step 18 order is preserved after selection.
6. `--save` persists the full eligible batch.
7. ordinary `--export` exports the full computed batch.
8. `--export-selection` explicitly exports only selected pairs.
9. No clinical score is introduced.

## Interpretation warning

Step 22 is a software data-selection tool only.

A selected pair is not thereby clinically compatible, preferred, suitable,
eligible, crossmatch-negative, DSA-negative, or appropriate for organ
allocation.

The selected counts remain copy-sensitive software-comparison data.
