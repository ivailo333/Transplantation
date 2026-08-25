# STEP 16 — Import HLA typings from JSON / CSV

Step 16 adds file import to the modular Step 14 / command-based Step 15 project.

## New command

```powershell
python .\main.py typings import FILE
```

The format is auto-detected from `.json` or `.csv`.

Explicit format:

```powershell
python .\main.py typings import FILE --format json
python .\main.py typings import FILE --format csv
```

Validation-only mode:

```powershell
python .\main.py typings import FILE --dry-run
```

`--dry-run` parses the file, validates all 12 HLA alleles with py-ard,
creates CANONICAL/LGX/G/P representations, but does not change SQLite.

## JSON format

Single typing:

```json
{
  "external_id": "DONOR-002",
  "subject_type": "DONOR",
  "imgthla_version": "3650",
  "hla": {
    "A": ["A*02:01", "A*24:02"],
    "B": ["B*07:02", "B*44:02"],
    "C": ["C*07:02", "C*05:01"],
    "DRB1": ["DRB1*15:01", "DRB1*04:01"],
    "DQB1": ["DQB1*06:02", "DQB1*03:02"],
    "DPB1": ["DPB1*04:01", "DPB1*02:01"]
  }
}
```

The `imgthla_version` field is optional. If supplied, it must equal
the active py-ard/IPD-IMGT/HLA version.

JSON also supports a list:

```json
[
  { "...": "..." },
  { "...": "..." }
]
```

or:

```json
{
  "typings": [
    { "...": "..." },
    { "...": "..." }
  ]
}
```

## CSV format

One row = one complete HLA typing.

Required columns:

```text
external_id
subject_type
A1
A2
B1
B2
C1
C2
DRB1_1
DRB1_2
DQB1_1
DQB1_2
DPB1_1
DPB1_2
```

Optional:

```text
imgthla_version
```

Example:

```text
external_id,subject_type,imgthla_version,A1,A2,B1,B2,C1,C2,DRB1_1,DRB1_2,DQB1_1,DQB1_2,DPB1_1,DPB1_2
DONOR-002,DONOR,3650,A*02:01,A*24:02,B*07:02,B*44:02,C*07:02,C*05:01,DRB1*15:01,DRB1*04:01,DQB1*06:02,DQB1*03:02,DPB1*04:01,DPB1*02:01
```

## Sample files

The project root contains:

```text
  import_typing.json
  import_typing.csv
  import_typings_batch.json
```

Try validation first:

```powershell
python .\main.py typings import .\import_typing.json --dry-run
python .\main.py typings import .\import_typings_batch.json --dry-run
```

Then import:

```powershell
python .\main.py typings import .\import_typing.json
python .\main.py typings import .\import_typings_batch.json
```

Verify:

```powershell
python .\main.py subjects list
python .\main.py typings history DONOR-IMPORT-001
python .\main.py typings show DONOR-IMPORT-001
```

## Atomic batch behavior

All records in a JSON list/wrapper or multi-row CSV are:

1. parsed,
2. structurally validated,
3. allele-validated with py-ard,
4. reduced to CANONICAL/LGX/G/P,

before the first SQL write.

The SQL batch is then saved in one transaction. If one database record
fails, all records from that file are rolled back.

## Backward compatibility

All Step 15 commands remain unchanged.

## Tests

Run:

```powershell
python -m unittest discover -s tests -v
```

Step 15 total: 147 tests  
Step 16 new tests: 26  
Expected total: 173 tests

On the project Windows environment with py-ard installed, all 173 tests
should execute. In an environment without py-ard, the pre-existing 15
py-ard integration tests are expected to be skipped.
