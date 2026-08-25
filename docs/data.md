# Data Policy

This repository intentionally keeps a small local demo/runtime data set so the CLI can be exercised immediately after checkout.

## Versioned Data

### `transplant.db`

The default SQLite database used by quick-start commands. It contains pseudonymous demo subjects, typings, analysis runs, and persistent batch history.

Keep this file small and non-clinical. Do not store real patient, donor, recipient, or operational transplant data in this repository.

### `pyard-data/pyard-3650.sqlite3`

Local py-ard data for IPD-IMGT/HLA version `3650`. The code points at this directory through `config.PYARD_DATA_DIR`.

The file is versioned to make the project runnable without a separate py-ard data bootstrap step.

### Import Samples

- `import_typing.json`
- `import_typing.csv`
- `import_typings_batch.json`

These are small sample import payloads for the `typings import` command.

### Step Notes And Test Results

`STEP*_README.md` and `STEP*_TEST_RESULTS.txt` files are retained as project history and acceptance evidence for the incremental STEP development process.

## Ignored Generated Data

`exports/` is ignored. Export commands can recreate JSON/CSV artifacts as needed.

Python bytecode caches, temporary files, test caches, and build outputs are also ignored through `.gitignore`.

## Rules For Future Data

- Keep committed examples pseudonymous and minimal.
- Do not commit real clinical data.
- Do not commit generated exports unless they are intentionally promoted to fixtures.
- Prefer creating reproducible fixtures under `tests/` for automated tests.
- If a future py-ard data bundle becomes too large for Git, replace it with documented bootstrap instructions.
