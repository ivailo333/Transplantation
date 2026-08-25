# Step 14 — Modular refactor

This directory is the refactored version of the Step 13G prototype.

## Goal

No HLA mathematics, SQLite data model, migration version, CLI command, or
export format is intentionally changed. The main change is code organization.

## Modules

- `config.py` — shared constants.
- `hla_validation.py` — py-ard initialization and HLA validation/canonicalization.
- `hla_reduction.py` — LGX/G/P reductions and reduction display helpers.
- `hla_comparison.py` — copy-sensitive Counter comparison.
- `database.py` — SQLite core, schema, migrations, compatibility facade.
- `subjects.py` — subject identity/read logic.
- `typings.py` — HLA typing persistence and loading.
- `analyses.py` — analysis_run and analysis_results persistence.
- `migrations.py` — schema migration engine.
- `exporters.py` — JSON/CSV export.
- `cli.py` — console UI and orchestration.
- `main.py` — minimal entry point.
- `hla_match.py` — compatibility facade for old commands/imports.

## Tests

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected regression baseline:

```text
Ran 126 tests in ...
OK
```

When py-ard is unavailable, the py-ard integration group is skipped.

## Compatibility

Existing commands remain available:

```powershell
python .\hla_match.py --db-status
python .\hla_match.py --list-subjects
python .\hla_match.py --list-analyses
python .\hla_match.py --show-results 1
python .\hla_match.py --export-analysis 1 --overwrite
```

`main.py` can also be used:

```powershell
python .\main.py --db-status
```

## Safety

Before replacing the current project, keep a copy of:
- `transplant.db`
- the existing Step 13G source files
- `pyard-data`
- `exports`

The supplied `archive/step13g/` directory contains the source files used for
this refactor, but it does not include your local database.
