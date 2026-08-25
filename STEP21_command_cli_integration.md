# STEP 21 — command_cli.py integration patch

The exact Step 20 `command_cli.py` in the local project is not present in the
current working files, so this document gives the minimal integration blocks
without guessing its surrounding implementation.

## 1. Import

Near the existing imports add:

```python
import batch_history
import step21_batch_history
```

## 2. Add arguments to the existing `batches` parser

For `batches list`, add:

```python
batches_list.add_argument("--query", default=None)
batches_list.add_argument("--direction", choices=("recipient", "donor"))
batches_list.add_argument("--anchor", default=None)
batches_list.add_argument("--imgthla-version", default=None)
batches_list.add_argument(
    "--sort-level",
    choices=("canonical", "lgx", "G", "P"),
)
batches_list.add_argument("--limit", type=int, default=None)
batches_list.add_argument("--offset", type=int, default=0)
```

Add a new command:

```python
batches_search = batch_commands.add_parser(
    "search",
    add_help=False,
    help="Search persistent batch history.",
)
batches_search.add_argument("query")
batches_search.add_argument("--limit", type=int, default=None)
batches_search.add_argument("--offset", type=int, default=0)
batches_search.add_argument("-h", "--help", action="store_true")
```

Add:

```python
batches_latest = batch_commands.add_parser(
    "latest",
    add_help=False,
    help="Show the newest persistent batch.",
)
batches_latest.add_argument("-h", "--help", action="store_true")
```

## 3. Dispatch: list

In the existing `batches list` branch:

```python
records = batch_history.list_batch_runs(database_path)

records = step21_batch_history.search_batch_history(
    records,
    query=args.query,
    direction=args.direction,
    anchor=args.anchor,
    imgthla_version=args.imgthla_version,
    sort_level=args.sort_level,
)

records = step21_batch_history.paginate_batch_history(
    records,
    limit=args.limit,
    offset=args.offset,
)

output_func(
    step21_batch_history.render_batch_history(
        records,
        title="STEP 21 — BATCH HISTORY",
    )
)
return 0
```

## 4. Dispatch: search

```python
records = batch_history.list_batch_runs(database_path)

records = step21_batch_history.search_batch_history(
    records,
    query=args.query,
)

records = step21_batch_history.paginate_batch_history(
    records,
    limit=args.limit,
    offset=args.offset,
)

output_func(
    step21_batch_history.render_batch_history(
        records,
        title="STEP 21 — BATCH HISTORY SEARCH",
    )
)
return 0
```

## 5. Dispatch: latest

```python
records = batch_history.list_batch_runs(database_path)
latest = step21_batch_history.latest_batch(records)

if latest is None:
    output_func("No persistent batches found.")
    return 0

output_func(
    step21_batch_history.render_batch_history(
        [latest],
        title="STEP 21 — LATEST PERSISTENT BATCH",
    )
)
return 0
```

## 6. Help text

Add:

```text
batches list [--query TEXT] [--direction recipient|donor]
             [--anchor EXTERNAL_ID] [--imgthla-version VERSION]
             [--sort-level canonical|lgx|G|P]
             [--limit N] [--offset N]

batches search QUERY [--limit N] [--offset N]

batches latest
```

The existing Step 20 commands must remain unchanged.
