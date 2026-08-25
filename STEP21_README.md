# STEP 21 — Ready command_cli.py integration

This package is built from the complete STEP 20 code-only package and
integrates `step21_batch_history.py` directly into the current STEP 20
`command_cli.py`.

New commands:

```powershell
python .\main.py batches list
python .\main.py batches list --direction recipient
python .\main.py batches list --anchor RECIP-001
python .\main.py batches list --imgthla-version 3650
python .\main.py batches list --sort-level lgx
python .\main.py batches list --limit 10 --offset 10

python .\main.py batches search RECIP-001
python .\main.py batches latest
python .\main.py batches summary
```

Existing STEP 20 commands remain:

```powershell
python .\main.py batches show 1
python .\main.py batches results 1
python .\main.py batches export 1 --overwrite
```

No SQLite migration is required for STEP 21.

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected generated total: 318 tests.

STEP 21 remains read-only administrative history management. It does not
recalculate py-ard reductions and does not introduce a clinical compatibility
ranking.
