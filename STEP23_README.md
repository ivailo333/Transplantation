# STEP 23 — Pair Comparison Profiles

Step 23 adds detailed one-pair HLA software-comparison profiles.

No SQLite migration is required.

Commands:

```powershell
python .\main.py pairs show DONOR-001 RECIP-001
python .\main.py pairs show DONOR-001 RECIP-001 --level lgx
python .\main.py pairs show DONOR-001 RECIP-001 --locus DRB1
python .\main.py pairs show DONOR-001 RECIP-001 --level lgx --locus DRB1

python .\main.py pairs show-run 10

python .\main.py pairs export DONOR-001 RECIP-001 --format both
python .\main.py pairs export-run 10 --format both
```

Specific typing rounds:

```powershell
python .\main.py pairs show DONOR-001 RECIP-001 `
    --donor-typing-id 1 `
    --recipient-typing-id 2
```

Supported levels: CANONICAL, LGX, G, P.

Supported loci: A, B, C, DRB1, DQB1, DPB1.

Full profile = 24 level/locus rows.
`--level` = 6 rows.
`--locus` = 4 rows.
`--level` + `--locus` = 1 row.

`pairs show` compares exact representations already stored in SQLite.
`pairs show-run` loads exact saved `analysis_results`.
Neither path recalculates py-ard reductions.

Default export directory:

```text
exports\pairs
```

Step 23 remains NON-CLINICAL software-comparison output. It is not an
organ-allocation score, virtual crossmatch, DSA assessment, eplet score, cPRA,
transplant eligibility decision, or graft-outcome prediction.
