# HLA Transplantation Simulation

Non-clinical HLA donor/recipient comparison CLI prototype.

The project validates and stores HLA typings, computes deterministic software
comparisons across CANONICAL / LGX / G / P representations, persists analysis
and batch history in SQLite, and renders matrix, summary, statistics, report,
and report-comparison views.

This software is strictly non-clinical. It does not calculate transplant
compatibility, clinical risk, allocation priority, virtual crossmatch, DSA,
MFI, unacceptable antigens, cPRA, eplet mismatch, PIRCHE, blood-group
compatibility, graft outcome, or transplant suitability.

## Requirements

- Python 3.10 or newer
- `py-ard`
- Local IPD-IMGT/HLA py-ard data under `pyard-data/`

Install runtime dependencies:

```powershell
python -m pip install -r requirements.txt
```

Install FastAPI backend dependencies:

```powershell
python -m pip install -e .[api]
# or
python -m pip install -r requirements-api.txt
```

Copy `backend.env.example` to `backend.env` for local backend runtime settings.

For development tools:

```powershell
python -m pip install -e .[dev]
```

## Quick Start

Run project health checks:

```powershell
python .\main.py doctor
python .\main.py doctor --json
```

Check the database and migrations:

```powershell
python .\main.py db status
```

List saved subjects:

```powershell
python .\main.py subjects list
```

Show a non-clinical analytical report:

```powershell
python .\main.py report recipient RECIP-001
```

Compare representation levels:

```powershell
python .\main.py compare levels recipient RECIP-001 --level canonical --level lgx
```

Compare persisted batches:

```powershell
python .\main.py compare batches 1 3
```

Export browser-readable reports, or all supported export formats at once:

```powershell
python .\main.py report recipient RECIP-001 --export html
python .\main.py compare levels recipient RECIP-001 --export html
python .\main.py report recipient RECIP-001 --export all
```

Create a reproducible audit bundle:

```powershell
python .\main.py audit recipient RECIP-001 --zip
python .\main.py audit batches 1 3 --level lgx
```

Show command-style help:

```powershell
python .\main.py --help
```

Start the backend API component for a larger application:

```powershell
hla-api
# or
python -m backend_app
```

The default API URL is `http://127.0.0.1:8000`. New integrations should use `/v1` endpoints; OpenAPI is available at `/openapi.json` and interactive docs at `/docs`.

Probe the backend component:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/live
Invoke-RestMethod http://127.0.0.1:8000/v1/ready
```

Legacy flags such as `--db-status`, `--list-subjects`, `--show-results`, and
`--export-analysis` are still supported for backward compatibility.

## Main Commands

- `doctor`: run project health checks without modifying data; `--json` emits machine-readable output.
- `db status` / `db migrate`: inspect and apply SQLite migrations.
- `subjects list`: list saved DONOR / RECIPIENT subjects.
- `typings history/show/import`: inspect or import HLA typings.
- `analyses create/run/results/export`: manage one donor-recipient analysis.
- `batch recipient|donor`: run one-to-many software comparisons.
- `batches list/search/show/results/export`: inspect persistent batch history.
- `pairs`: render one-pair comparison profiles.
- `matrix`: render STEP 24 comparison matrices.
- `summary`: render STEP 25 mismatch summaries.
- `stats`: render STEP 26 descriptive statistics.
- `report`: render STEP 27 analytical reports.
- `compare`: render STEP 28 report comparisons.
- `audit`: create a reproducible bundle with doctor output, schema status, STEP 27/28 artifacts, and metadata.

Use another SQLite database with the global `--db PATH` option:

```powershell
python .\main.py --db .\other.db report recipient RECIP-001
```

## Tests

Run the full unittest suite:

```powershell
python -m unittest discover -s tests
```

If `pytest` is installed, the project metadata also points it at `tests/`:

```powershell
python -m pytest
```

## Continuous Integration

The GitHub Actions workflow in `.github/workflows/ci.yml` runs on Windows and checks:

- whitespace with `git diff --check`
- Python compilation with `compileall`
- the full unittest suite
- CLI smoke tests for `--help` and `doctor --json`
- FastAPI backend app and OpenAPI contract smoke test
- source and wheel builds with `python -m build`
- installed console-script metadata for `hla-match` and `hla-api`
- the installed `hla-match` console script

## Packaging

Build release artifacts locally with:

```powershell
python -m build
```

The project exposes console scripts for CLI and API use:

```powershell
hla-match --help
hla-api
```

## Project Layout

- `main.py`: minimal executable entry point.
- `cli.py`: legacy-compatible CLI entry and command-style routing.
- `command_cli.py`: command-style parser and dispatch.
- `backend_app.py`: FastAPI component exposing reports, comparisons, doctor checks, and audit bundles.
- `backend_config.py` and `backend_services.py`: backend settings, .env loading, probes, and service envelope layer.
- `Dockerfile` and `.dockerignore`: container runtime packaging for the backend service.
- `config.py`: shared HLA loci, representation levels, and data paths.
- `hla_validation.py`: py-ard initialization and allele validation.
- `hla_reduction.py`: CANONICAL to LGX / G / P reductions.
- `hla_comparison.py`: copy-sensitive multiset comparison.
- `database.py` and `migrations.py`: SQLite schema and migration helpers.
- `subjects.py` and `typings.py`: subject and typing persistence.
- `analyses.py`: analysis run and result persistence.
- `batch_*.py`: one-to-many batch execution, ranking, selection, export, history.
- `hla_matrix.py`, `mismatch_summary.py`, `comparison_statistics.py`: STEP 24-26 views.
- `step27_reporting.py`: analytical report layer.
- `step28_report_comparison.py`: multi-report comparison layer.
- `tests/`: unittest coverage for CLI, persistence, import/export, and STEP behavior.

## Documentation

- [Backend API component](docs/backend.md)
- [Backend integration guide](docs/backend-integration.md)
- [Clinical intended use draft](docs/clinical/intended-use.md)
- [Clinical regulatory classification draft](docs/clinical/regulatory-classification.md)
- [Database schema](docs/schema.md)
- [Data policy](docs/data.md)

## Data And Exports

The default SQLite database is `transplant.db`. Export commands write under
`exports/` unless another output directory is supplied.

JSON, CSV, and HTML exports are deterministic software artifacts. `--export all` writes JSON, CSV, and HTML together; `both` remains JSON + CSV for backward compatibility. Audit bundles collect these artifacts with doctor output, schema status, and metadata for reproducibility, not clinical decision-making.



