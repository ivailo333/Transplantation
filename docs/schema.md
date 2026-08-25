# Database Schema

This document summarizes the SQLite schema used by the non-clinical HLA comparison CLI.

The current schema version is 3. Migrations are tracked in `schema_migrations` and are applied through `database.migrate_database()`.

## Core Tables

### `subjects`

Stores pseudonymous subject identity.

- `id`: integer primary key.
- `external_id`: unique pseudonymous identifier such as `DONOR-001` or `RECIP-001`.
- `subject_type`: `DONOR` or `RECIPIENT`.
- `created_at`: SQLite timestamp.

### `hla_typings`

Stores one HLA typing event for one subject.

- `id`: integer primary key.
- `subject_id`: references `subjects.id`.
- `imgthla_version`: IPD-IMGT/HLA version, for example `3650`.
- `created_at`: SQLite timestamp.

A subject can have multiple typings. CLI commands default to the latest typing unless a `--typing-id` is supplied.

### `hla_alleles`

Stores two allele rows per locus for each typing.

- `typing_id`: references `hla_typings.id`.
- `locus`: one of `A`, `B`, `C`, `DRB1`, `DQB1`, `DPB1`.
- `allele_number`: `1` or `2`.
- `raw_value`: original value as supplied.
- `canonical_value`: validated canonical value.
- `lgx_value`: py-ard LGX reduction.
- `g_value`: py-ard G-group reduction.
- `p_value`: py-ard P-group reduction.

The unique key is `(typing_id, locus, allele_number)`.

### `analysis_runs`

Stores one donor-recipient analysis request.

- `donor_typing_id`: references the donor typing.
- `recipient_typing_id`: references the recipient typing.
- `imgthla_version`: version shared by both typings.
- `created_at`: SQLite timestamp.

### `analysis_results`

Stores deterministic software comparison results for each run, representation level, and locus.

- `run_id`: references `analysis_runs.id`.
- `level`: `CANONICAL`, `LGX`, `G`, or `P`.
- `locus`: one configured HLA locus.
- `shared_count`: copy-sensitive shared allele count.
- `donor_only_count`: donor-only copy count.
- `recipient_only_count`: recipient-only copy count.
- `shared_values`, `donor_only_values`, `recipient_only_values`: JSON arrays.

The migration-managed unique key is `(run_id, level, locus)`.

## Batch History Tables

### `batch_runs`

Stores metadata for one persistent one-to-many comparison batch.

- `direction`: `recipient` or `donor`.
- `anchor_typing_id`: the fixed subject typing.
- `imgthla_version`: IPD-IMGT/HLA version.
- `pair_count`: number of stored comparison pairs.
- `skipped_count`, `skipped_json`: skipped candidate metadata.
- `sort_level`, `sort_metric`, `sort_order`, `requested_sort_order`: deterministic software ordering metadata.
- `display_limit`: optional presentation limit.
- `created_at`: SQLite timestamp.

### `batch_run_items`

Maps persistent batch rows to stored analysis runs.

- `batch_id`: references `batch_runs.id`.
- `analysis_run_id`: references `analysis_runs.id` and is unique.
- `candidate_typing_id`: candidate typing for this row.
- `item_position`: original batch position.
- `software_position`, `software_rank`, `criterion_value`: optional deterministic ordering metadata.

## Derived Views

The later CLI layers reuse stored typings and/or stored analysis results:

- STEP 23 pair profiles.
- STEP 24 matrices.
- STEP 25 mismatch summaries.
- STEP 26 descriptive statistics.
- STEP 27 analytical reports.
- STEP 28 report comparisons.

These layers are deterministic software views. They do not introduce clinical scoring or transplant suitability decisions.
