# STEP 15 — Command-based CLI

Step 15 changes the command-line interface without changing HLA,
SQLite, migration, analysis, or export logic.

## Preferred new commands

### Database

```powershell
python .\main.py db status
python .\main.py db migrate
```

### Subjects

```powershell
python .\main.py subjects list
```

### Typings

```powershell
python .\main.py typings history DONOR-001
python .\main.py typings show DONOR-001
python .\main.py typings show DONOR-001 --typing-id 1
```

### Analyses

```powershell
python .\main.py analyses list
python .\main.py analyses create DONOR-001 RECIP-001
python .\main.py analyses show 1
python .\main.py analyses run 1
python .\main.py analyses results 1
python .\main.py analyses export 1
python .\main.py analyses export 1 --format json --overwrite
```

### Interactive workflow

```powershell
python .\main.py workflow interactive
python .\main.py workflow demo
```

Use another database with:

```powershell
python .\main.py --db .\other.db db status
```

## Backward compatibility

All Step 13/14 flag commands remain supported:

```powershell
python .\hla_match.py --db-status
python .\hla_match.py --list-subjects
python .\hla_match.py --list-analyses
python .\hla_match.py --show-results 1
python .\hla_match.py --export-analysis 1 --overwrite
```

## Tests

Run:

```powershell
python -m unittest discover -s tests -v
```

Step 14 regression tests: 126  
Step 15 new CLI tests: 21  
Expected total: 147

On an environment without py-ard, 15 integration tests are expected to be
skipped. On the project Windows environment where py-ard is installed,
all 147 should execute.
