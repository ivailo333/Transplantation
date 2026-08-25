# STEP 21 — PowerShell verification

# 1. Existing schema must remain current.
python .\main.py db status

# 2. Existing persistent history.
python .\main.py batches list

# 3. Search.
python .\main.py batches search RECIP-001

# 4. Direction filter.
python .\main.py batches list --direction recipient

# 5. Anchor filter.
python .\main.py batches list --anchor RECIP-001

# 6. Version filter.
python .\main.py batches list --imgthla-version 3650

# 7. Sort-level filter.
python .\main.py batches list --sort-level lgx

# 8. Pagination.
python .\main.py batches list --limit 1
python .\main.py batches list --limit 1 --offset 1

# 9. Latest.
python .\main.py batches latest

# 10. Existing Step 20 regression.
python -m unittest discover -s tests -v

# 11. Step 21 unit tests.
python -m unittest test_batch_history_step21 -v
