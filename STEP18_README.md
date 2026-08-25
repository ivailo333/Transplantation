# STEP 18 — Software ordering of batch HLA comparison results

Step 18 builds on Step 17 batch analysis and adds deterministic sorting of
the already calculated batch summaries.

It does **not** create a clinical compatibility score.

## Basic usage

The old Step 17 command remains unchanged:

```powershell
python .\main.py batch recipient RECIP-001
```

This still shows the batch in its normal candidate order.

Software ordering is enabled only when `--sort-by` is supplied.

Example:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --sort-level lgx
```

## Supported representation levels

```text
canonical
lgx
G
P
```

If `--sort-by` is used without `--sort-level`, Step 18 defaults to:

```text
lgx
```

## Supported metrics

```text
donor-only
shared
recipient-only
```

These map directly to the Step 17 totals:

```text
donor_only_count
shared_count
recipient_only_count
```

There is no weighted formula and no combined compatibility score.

## AUTO sort direction

The default is:

```text
--sort-order auto
```

AUTO means:

```text
shared         -> DESC
donor-only     -> ASC
recipient-only -> ASC
```

This is only a software ordering convention.

Explicit order is also supported:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --sort-order desc
```

## Examples

Order donors for one recipient by LGX donor_only_count:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --sort-level lgx
```

Order by G shared_count:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by shared `
    --sort-level G
```

Order recipients for one donor:

```powershell
python .\main.py batch donor DONOR-001 `
    --sort-by recipient-only `
    --sort-level canonical
```

## Ties

Equal criterion values are ties and receive the same `software_rank`.

Example:

```text
position=1 | software_rank=1 | donor_only_count=2
position=2 | software_rank=1 | donor_only_count=2
position=3 | software_rank=3 | donor_only_count=4
```

Within a tie, external_id / typing_id is used only to produce stable,
repeatable display order. It has no medical meaning.

## Display limit

You can limit the ordered output:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --limit 5
```

`--display-limit` is an alias:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --display-limit 5
```

Important: the limit affects **display only**.

If `--save` is also used, Step 17 first atomically saves **all eligible
pairs**, and Step 18 then orders/limits only what is printed.

Therefore:

```powershell
python .\main.py batch recipient RECIP-001 `
    --sort-by donor-only `
    --limit 5 `
    --save
```

does **not** mean "save only five". It means:

```text
save all eligible pairs
then display five ordered rows
```

This design avoids selectively persisting pairs based on a non-clinical
software count.

## Backward compatibility

Without `--sort-by`, Step 17 behavior is unchanged.

For example:

```powershell
python .\main.py batch recipient RECIP-001
python .\main.py batch donor DONOR-001
python .\main.py batch recipient RECIP-001 --candidate DONOR-001 --save
```

continue to work as before.

No SQLite schema migration is required for Step 18.

## Interpretation warning

Step 18 does **not** rank transplant suitability.

The selected values remain copy-sensitive software comparison counts across:

```text
A
B
C
DRB1
DQB1
DPB1
```

The ordering is not:

```text
a clinical organ-allocation ranking
a virtual crossmatch
DSA assessment
eplet mismatch scoring
cPRA
a transplant eligibility decision
a prediction of graft outcome
```

A smaller `donor_only_count` or a larger `shared_count` must not be treated
as proof that a donor is clinically preferable.

## Tests

Run:

```powershell
python -m unittest discover -s tests -v
```

The generated Step 18 package preserves all 198 Step 17 tests and adds
new normalization, ordering, tie, CLI, display-limit, persistence-scope,
and backward-compatibility tests.

Expected total in this generated package: **232 tests**.
