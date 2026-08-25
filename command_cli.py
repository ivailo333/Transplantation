"""
STEP 15 — command-based CLI.

New interface examples:

    python main.py db status
    python main.py db migrate

    python main.py subjects list

    python main.py typings history DONOR-001
    python main.py typings show DONOR-001
    python main.py typings show DONOR-001 --typing-id 3

    python main.py analyses list
    python main.py analyses create DONOR-001 RECIP-001
    python main.py analyses show 1
    python main.py analyses run 1
    python main.py analyses results 1
    python main.py analyses export 1 --format json --overwrite

    python main.py workflow interactive
    python main.py workflow demo

The old flag-based CLI remains supported by cli.legacy_main().
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import database
import exporters
import importers
import batch_analysis
import batch_ranking
import batch_selection
import batch_exporters
import batch_history
import step21_batch_history
import pair_profiles
import hla_matrix
import mismatch_summary
import comparison_statistics
import step27_reporting
import step28_report_comparison


COMMAND_GROUPS = frozenset({
    "db",
    "subjects",
    "typings",
    "analyses",
    "workflow",
    "batch",
    "batches",
    "pairs",
    "matrix",
    "summary",
    "stats",
    "report",
    "compare",
})


class CommandCLIError(ValueError):
    """Невалидна STEP 15 command-line команда."""


class SafeArgumentParser(argparse.ArgumentParser):
    """
    ArgumentParser variant that does not terminate the interpreter.

    This makes the CLI easy to unit-test and lets main() return
    conventional exit codes instead of raising SystemExit.
    """

    def error(self, message):
        raise CommandCLIError(message)


def _add_db_option(parser):
    parser.add_argument(
        "--db",
        type=Path,
        default=database.DEFAULT_DATABASE_PATH,
        help=(
            "Path to SQLite database. "
            f"Default: {database.DEFAULT_DATABASE_PATH}"
        ),
    )


def build_parser():
    parser = SafeArgumentParser(
        prog="hla-match",
        description=(
            "HLA donor/recipient comparison prototype — "
            "STEP 28 HLA report comparison / multi-report analysis"
        ),
        add_help=False,
    )

    _add_db_option(parser)
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_root_help",
        help="Show this help message.",
    )

    groups = parser.add_subparsers(dest="group")

    # ------------------------------------------------------------
    # db
    # ------------------------------------------------------------
    db_parser = groups.add_parser(
        "db",
        add_help=False,
        help="Database schema and migration commands.",
    )
    db_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    db_commands = db_parser.add_subparsers(dest="command")

    db_status = db_commands.add_parser(
        "status",
        add_help=False,
        help="Show schema version and pending migrations.",
    )
    db_status.add_argument("-h", "--help", action="store_true")

    db_migrate = db_commands.add_parser(
        "migrate",
        add_help=False,
        help="Apply pending database migrations.",
    )
    db_migrate.add_argument("-h", "--help", action="store_true")

    # ------------------------------------------------------------
    # subjects
    # ------------------------------------------------------------
    subjects_parser = groups.add_parser(
        "subjects",
        add_help=False,
        help="Saved DONOR/RECIPIENT subjects.",
    )
    subjects_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    subject_commands = subjects_parser.add_subparsers(dest="command")

    subjects_list = subject_commands.add_parser(
        "list",
        add_help=False,
        help="List saved subjects.",
    )
    subjects_list.add_argument("-h", "--help", action="store_true")

    # ------------------------------------------------------------
    # typings
    # ------------------------------------------------------------
    typings_parser = groups.add_parser(
        "typings",
        add_help=False,
        help="Saved HLA typing commands.",
    )
    typings_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    typing_commands = typings_parser.add_subparsers(dest="command")

    typing_history = typing_commands.add_parser(
        "history",
        add_help=False,
        help="Show typing history for a subject.",
    )
    typing_history.add_argument("external_id")
    typing_history.add_argument("-h", "--help", action="store_true")

    typing_show = typing_commands.add_parser(
        "show",
        add_help=False,
        help="Load one saved HLA typing.",
    )
    typing_show.add_argument("external_id")
    typing_show.add_argument(
        "--typing-id",
        type=int,
        default=None,
        help="Load a specific typing_id instead of the latest.",
    )
    typing_show.add_argument("-h", "--help", action="store_true")

    typing_import = typing_commands.add_parser(
        "import",
        add_help=False,
        help="Import one or more HLA typings from JSON/CSV.",
    )
    typing_import.add_argument(
        "input_path",
        type=Path,
        help="JSON or CSV file containing HLA typings.",
    )
    typing_import.add_argument(
        "--format",
        choices=importers.SUPPORTED_IMPORT_FORMATS,
        default="auto",
        dest="import_format",
        help="auto (default), json or csv.",
    )
    typing_import.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse, validate and reduce, but do not write to SQLite.",
    )
    typing_import.add_argument("-h", "--help", action="store_true")

    # ------------------------------------------------------------
    # analyses
    # ------------------------------------------------------------
    analyses_parser = groups.add_parser(
        "analyses",
        add_help=False,
        help="DONOR↔RECIPIENT analysis commands.",
    )
    analyses_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    analysis_commands = analyses_parser.add_subparsers(dest="command")

    analyses_list = analysis_commands.add_parser(
        "list",
        add_help=False,
        help="List saved analysis runs.",
    )
    analyses_list.add_argument("-h", "--help", action="store_true")

    analyses_create = analysis_commands.add_parser(
        "create",
        add_help=False,
        help="Create an analysis_run linking DONOR and RECIPIENT typings.",
    )
    analyses_create.add_argument("donor_external_id")
    analyses_create.add_argument("recipient_external_id")
    analyses_create.add_argument(
        "--donor-typing-id",
        type=int,
        default=None,
    )
    analyses_create.add_argument(
        "--recipient-typing-id",
        type=int,
        default=None,
    )
    analyses_create.add_argument("-h", "--help", action="store_true")

    analyses_show = analysis_commands.add_parser(
        "show",
        add_help=False,
        help="Show analysis_run metadata.",
    )
    analyses_show.add_argument("run_id", type=int)
    analyses_show.add_argument("-h", "--help", action="store_true")

    analyses_run = analysis_commands.add_parser(
        "run",
        add_help=False,
        help="Compute and save the 24 comparison result rows.",
    )
    analyses_run.add_argument("run_id", type=int)
    analyses_run.add_argument("-h", "--help", action="store_true")

    analyses_results = analysis_commands.add_parser(
        "results",
        add_help=False,
        help="Show the 24 saved comparison result rows.",
    )
    analyses_results.add_argument("run_id", type=int)
    analyses_results.add_argument("-h", "--help", action="store_true")

    analyses_export = analysis_commands.add_parser(
        "export",
        add_help=False,
        help="Export saved analysis results to JSON/CSV.",
    )
    analyses_export.add_argument("run_id", type=int)
    analyses_export.add_argument(
        "--format",
        choices=exporters.VALID_FORMATS,
        default="both",
    )
    analyses_export.add_argument(
        "--output-dir",
        type=Path,
        default=exporters.DEFAULT_EXPORT_DIR,
    )
    analyses_export.add_argument(
        "--overwrite",
        action="store_true",
    )
    analyses_export.add_argument("-h", "--help", action="store_true")

    # ------------------------------------------------------------
    # pairs — STEP 23
    # ------------------------------------------------------------
    pairs_parser = groups.add_parser("pairs", add_help=False, help="Detailed one-pair HLA software-comparison profiles.")
    pairs_parser.add_argument("-h", "--help", action="store_true", dest="_group_help")
    pair_commands = pairs_parser.add_subparsers(dest="command")

    pairs_show = pair_commands.add_parser("show", add_help=False)
    pairs_show.add_argument("donor_external_id")
    pairs_show.add_argument("recipient_external_id")
    pairs_show.add_argument("--donor-typing-id", type=int, default=None)
    pairs_show.add_argument("--recipient-typing-id", type=int, default=None)
    pairs_show.add_argument("--level", default=None)
    pairs_show.add_argument("--locus", default=None)
    pairs_show.add_argument("-h", "--help", action="store_true")

    pairs_show_run = pair_commands.add_parser("show-run", add_help=False)
    pairs_show_run.add_argument("run_id", type=int)
    pairs_show_run.add_argument("--level", default=None)
    pairs_show_run.add_argument("--locus", default=None)
    pairs_show_run.add_argument("-h", "--help", action="store_true")

    pairs_export = pair_commands.add_parser("export", add_help=False)
    pairs_export.add_argument("donor_external_id")
    pairs_export.add_argument("recipient_external_id")
    pairs_export.add_argument("--donor-typing-id", type=int, default=None)
    pairs_export.add_argument("--recipient-typing-id", type=int, default=None)
    pairs_export.add_argument("--level", default=None)
    pairs_export.add_argument("--locus", default=None)
    pairs_export.add_argument("--format", choices=pair_profiles.VALID_EXPORT_FORMATS, default="both")
    pairs_export.add_argument("--output-dir", type=Path, default=pair_profiles.DEFAULT_EXPORT_DIR)
    pairs_export.add_argument("--name", default=None)
    pairs_export.add_argument("--overwrite", action="store_true")
    pairs_export.add_argument("-h", "--help", action="store_true")

    pairs_export_run = pair_commands.add_parser("export-run", add_help=False)
    pairs_export_run.add_argument("run_id", type=int)
    pairs_export_run.add_argument("--level", default=None)
    pairs_export_run.add_argument("--locus", default=None)
    pairs_export_run.add_argument("--format", choices=pair_profiles.VALID_EXPORT_FORMATS, default="both")
    pairs_export_run.add_argument("--output-dir", type=Path, default=pair_profiles.DEFAULT_EXPORT_DIR)
    pairs_export_run.add_argument("--name", default=None)
    pairs_export_run.add_argument("--overwrite", action="store_true")
    pairs_export_run.add_argument("-h", "--help", action="store_true")

    # ------------------------------------------------------------
    # compare — STEP 28
    # ------------------------------------------------------------
    compare_parser = groups.add_parser(
        "compare",
        add_help=False,
        help="Compare STEP 27 reports across levels or persistent batches.",
    )
    compare_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    compare_commands = compare_parser.add_subparsers(dest="command")

    # compare levels recipient|donor
    compare_levels = compare_commands.add_parser(
        "levels",
        add_help=False,
    )
    compare_levels.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_command_help",
    )
    compare_level_directions = compare_levels.add_subparsers(
        dest="direction"
    )

    def _add_compare_level_options(subparser):
        subparser.add_argument("external_id")
        subparser.add_argument("--typing-id", type=int, default=None)
        subparser.add_argument(
            "--candidate",
            action="append",
            default=None,
        )
        subparser.add_argument(
            "--level",
            action="append",
            default=None,
            help=(
                "Representation level to include. Repeat for multiple "
                "levels. Default: canonical, lgx, G, P."
            ),
        )
        subparser.add_argument(
            "--locus",
            action="append",
            default=None,
        )
        subparser.add_argument(
            "--sort-by",
            choices=batch_ranking.SORT_METRICS,
            default=None,
        )
        subparser.add_argument(
            "--sort-order",
            choices=batch_ranking.SORT_ORDERS,
            default="auto",
        )
        subparser.add_argument(
            "--export",
            nargs="?",
            const="both",
            choices=step28_report_comparison.VALID_EXPORT_FORMATS,
            default=None,
        )
        subparser.add_argument(
            "--output-dir",
            type=Path,
            default=step28_report_comparison.DEFAULT_EXPORT_DIR,
        )
        subparser.add_argument("--name", default=None)
        subparser.add_argument("--overwrite", action="store_true")
        subparser.add_argument("-h", "--help", action="store_true")

    compare_levels_recipient = compare_level_directions.add_parser(
        "recipient",
        add_help=False,
    )
    _add_compare_level_options(compare_levels_recipient)

    compare_levels_donor = compare_level_directions.add_parser(
        "donor",
        add_help=False,
    )
    _add_compare_level_options(compare_levels_donor)

    # compare batches LEFT RIGHT
    compare_batches = compare_commands.add_parser(
        "batches",
        add_help=False,
    )
    compare_batches.add_argument("left_batch_id", type=int)
    compare_batches.add_argument("right_batch_id", type=int)
    compare_batches.add_argument(
        "--level",
        default=hla_matrix.DEFAULT_LEVEL,
    )
    compare_batches.add_argument(
        "--locus",
        action="append",
        default=None,
    )
    compare_batches.add_argument(
        "--sort-by",
        choices=batch_ranking.SORT_METRICS,
        default=None,
    )
    compare_batches.add_argument(
        "--sort-order",
        choices=batch_ranking.SORT_ORDERS,
        default="auto",
    )
    compare_batches.add_argument(
        "--export",
        nargs="?",
        const="both",
        choices=step28_report_comparison.VALID_EXPORT_FORMATS,
        default=None,
    )
    compare_batches.add_argument(
        "--output-dir",
        type=Path,
        default=step28_report_comparison.DEFAULT_EXPORT_DIR,
    )
    compare_batches.add_argument("--name", default=None)
    compare_batches.add_argument("--overwrite", action="store_true")
    compare_batches.add_argument("-h", "--help", action="store_true")

    # ------------------------------------------------------------
    # report — STEP 27
    # ------------------------------------------------------------
    report_parser = groups.add_parser(
        "report",
        add_help=False,
        help="Validated NON-CLINICAL HLA analytical report.",
    )
    report_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    report_commands = report_parser.add_subparsers(dest="command")

    def _add_report_common_options(
        subparser,
        include_candidates=False,
    ):
        subparser.add_argument(
            "--level",
            default=hla_matrix.DEFAULT_LEVEL,
        )
        subparser.add_argument(
            "--locus",
            action="append",
            default=None,
        )
        if include_candidates:
            subparser.add_argument(
                "--candidate",
                action="append",
                default=None,
            )
        subparser.add_argument(
            "--sort-by",
            choices=batch_ranking.SORT_METRICS,
            default=None,
        )
        subparser.add_argument(
            "--sort-order",
            choices=batch_ranking.SORT_ORDERS,
            default="auto",
        )
        subparser.add_argument(
            "--export",
            nargs="?",
            const="both",
            choices=step27_reporting.VALID_EXPORT_FORMATS,
            default=None,
            help=(
                "Export report as json, csv, or both. "
                "Bare --export means both."
            ),
        )
        subparser.add_argument(
            "--output-dir",
            type=Path,
            default=step27_reporting.DEFAULT_EXPORT_DIR,
        )
        subparser.add_argument("--name", default=None)
        subparser.add_argument("--overwrite", action="store_true")
        subparser.add_argument("-h", "--help", action="store_true")

    report_recipient = report_commands.add_parser(
        "recipient",
        add_help=False,
    )
    report_recipient.add_argument("external_id")
    report_recipient.add_argument(
        "--typing-id",
        type=int,
        default=None,
    )
    _add_report_common_options(
        report_recipient,
        include_candidates=True,
    )

    report_donor = report_commands.add_parser(
        "donor",
        add_help=False,
    )
    report_donor.add_argument("external_id")
    report_donor.add_argument(
        "--typing-id",
        type=int,
        default=None,
    )
    _add_report_common_options(
        report_donor,
        include_candidates=True,
    )

    report_batch = report_commands.add_parser(
        "batch",
        add_help=False,
    )
    report_batch.add_argument("batch_id", type=int)
    _add_report_common_options(
        report_batch,
        include_candidates=False,
    )

    # ------------------------------------------------------------
    # stats — STEP 26
    # ------------------------------------------------------------
    stats_parser = groups.add_parser(
        "stats",
        add_help=False,
        help="Aggregated NON-CLINICAL HLA comparison statistics.",
    )
    stats_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    stats_commands = stats_parser.add_subparsers(dest="command")

    def _add_stats_common_options(subparser, include_candidates=False):
        subparser.add_argument(
            "--level",
            default=hla_matrix.DEFAULT_LEVEL,
        )
        subparser.add_argument(
            "--locus",
            action="append",
            default=None,
        )
        if include_candidates:
            subparser.add_argument(
                "--candidate",
                action="append",
                default=None,
            )
        subparser.add_argument(
            "--sort-by",
            choices=batch_ranking.SORT_METRICS,
            default=None,
        )
        subparser.add_argument(
            "--sort-order",
            choices=batch_ranking.SORT_ORDERS,
            default="auto",
        )
        subparser.add_argument(
            "--details",
            action="store_true",
            help="Include per-pair detail rows.",
        )
        subparser.add_argument(
            "--export",
            action="store_true",
        )
        subparser.add_argument(
            "--format",
            choices=comparison_statistics.VALID_EXPORT_FORMATS,
            default="both",
        )
        subparser.add_argument(
            "--output-dir",
            type=Path,
            default=comparison_statistics.DEFAULT_EXPORT_DIR,
        )
        subparser.add_argument("--name", default=None)
        subparser.add_argument("--overwrite", action="store_true")
        subparser.add_argument("-h", "--help", action="store_true")

    stats_recipient = stats_commands.add_parser(
        "recipient",
        add_help=False,
    )
    stats_recipient.add_argument("external_id")
    stats_recipient.add_argument("--typing-id", type=int, default=None)
    _add_stats_common_options(
        stats_recipient,
        include_candidates=True,
    )

    stats_donor = stats_commands.add_parser(
        "donor",
        add_help=False,
    )
    stats_donor.add_argument("external_id")
    stats_donor.add_argument("--typing-id", type=int, default=None)
    _add_stats_common_options(
        stats_donor,
        include_candidates=True,
    )

    stats_batch = stats_commands.add_parser(
        "batch",
        add_help=False,
    )
    stats_batch.add_argument("batch_id", type=int)
    _add_stats_common_options(
        stats_batch,
        include_candidates=False,
    )

    # ------------------------------------------------------------
    # summary — STEP 25
    # ------------------------------------------------------------
    summary_parser = groups.add_parser(
        "summary", add_help=False,
        help="HLA mismatch summary / descriptive software classification.",
    )
    summary_parser.add_argument("-h", "--help", action="store_true", dest="_group_help")
    summary_commands = summary_parser.add_subparsers(dest="command")

    def _add_summary_common_options(subparser, include_candidates=False):
        subparser.add_argument("--level", default=hla_matrix.DEFAULT_LEVEL)
        subparser.add_argument("--locus", action="append", default=None)
        if include_candidates:
            subparser.add_argument("--candidate", action="append", default=None)
        subparser.add_argument("--sort-by", choices=batch_ranking.SORT_METRICS, default=None)
        subparser.add_argument("--sort-order", choices=batch_ranking.SORT_ORDERS, default="auto")
        subparser.add_argument("--export", action="store_true")
        subparser.add_argument("--format", choices=mismatch_summary.VALID_EXPORT_FORMATS, default="both")
        subparser.add_argument("--output-dir", type=Path, default=mismatch_summary.DEFAULT_EXPORT_DIR)
        subparser.add_argument("--name", default=None)
        subparser.add_argument("--overwrite", action="store_true")
        subparser.add_argument("-h", "--help", action="store_true")

    summary_recipient = summary_commands.add_parser("recipient", add_help=False)
    summary_recipient.add_argument("external_id")
    summary_recipient.add_argument("--typing-id", type=int, default=None)
    _add_summary_common_options(summary_recipient, include_candidates=True)

    summary_donor = summary_commands.add_parser("donor", add_help=False)
    summary_donor.add_argument("external_id")
    summary_donor.add_argument("--typing-id", type=int, default=None)
    _add_summary_common_options(summary_donor, include_candidates=True)

    summary_batch = summary_commands.add_parser("batch", add_help=False)
    summary_batch.add_argument("batch_id", type=int)
    _add_summary_common_options(summary_batch, include_candidates=False)

    # ------------------------------------------------------------
    # matrix — STEP 24
    # ------------------------------------------------------------
    matrix_parser = groups.add_parser(
        "matrix",
        add_help=False,
        help="Multi-pair HLA software-comparison matrix.",
    )
    matrix_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    matrix_commands = matrix_parser.add_subparsers(dest="command")

    def _add_matrix_common_options(subparser, include_candidates=False):
        subparser.add_argument(
            "--level",
            default=hla_matrix.DEFAULT_LEVEL,
            help="canonical, lgx, G or P. Default: lgx.",
        )
        subparser.add_argument(
            "--locus",
            action="append",
            default=None,
            help=(
                "Restrict matrix to one HLA locus. "
                "Repeat for multiple loci."
            ),
        )
        if include_candidates:
            subparser.add_argument(
                "--candidate",
                action="append",
                default=None,
                help=(
                    "Restrict to one candidate external_id. "
                    "Repeat for multiple candidates."
                ),
            )
        subparser.add_argument(
            "--sort-by",
            choices=batch_ranking.SORT_METRICS,
            default=None,
        )
        subparser.add_argument(
            "--sort-order",
            choices=batch_ranking.SORT_ORDERS,
            default="auto",
        )
        subparser.add_argument(
            "--export",
            action="store_true",
            help="Export matrix after displaying it.",
        )
        subparser.add_argument(
            "--format",
            choices=hla_matrix.VALID_EXPORT_FORMATS,
            default="both",
        )
        subparser.add_argument(
            "--output-dir",
            type=Path,
            default=hla_matrix.DEFAULT_EXPORT_DIR,
        )
        subparser.add_argument("--name", default=None)
        subparser.add_argument("--overwrite", action="store_true")
        subparser.add_argument("-h", "--help", action="store_true")

    matrix_recipient = matrix_commands.add_parser(
        "recipient",
        add_help=False,
        help="One RECIPIENT against many DONOR subjects.",
    )
    matrix_recipient.add_argument("external_id")
    matrix_recipient.add_argument("--typing-id", type=int, default=None)
    _add_matrix_common_options(
        matrix_recipient,
        include_candidates=True,
    )

    matrix_donor = matrix_commands.add_parser(
        "donor",
        add_help=False,
        help="One DONOR against many RECIPIENT subjects.",
    )
    matrix_donor.add_argument("external_id")
    matrix_donor.add_argument("--typing-id", type=int, default=None)
    _add_matrix_common_options(
        matrix_donor,
        include_candidates=True,
    )

    matrix_batch = matrix_commands.add_parser(
        "batch",
        add_help=False,
        help="Matrix from a persistent STEP 20 batch_id.",
    )
    matrix_batch.add_argument("batch_id", type=int)
    _add_matrix_common_options(
        matrix_batch,
        include_candidates=False,
    )

    # ------------------------------------------------------------
    # batch — STEP 17
    # ------------------------------------------------------------
    batch_parser = groups.add_parser(
        "batch",
        add_help=False,
        help="One-to-many DONOR↔RECIPIENT software comparisons.",
    )
    batch_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    batch_commands = batch_parser.add_subparsers(dest="command")

    batch_recipient = batch_commands.add_parser(
        "recipient",
        add_help=False,
        help="Compare one RECIPIENT against many DONOR subjects.",
    )
    batch_recipient.add_argument("external_id")
    batch_recipient.add_argument(
        "--typing-id",
        type=int,
        default=None,
        help="Use a specific RECIPIENT typing_id instead of latest.",
    )
    batch_recipient.add_argument(
        "--candidate",
        action="append",
        default=None,
        help=(
            "Restrict to one DONOR external_id. "
            "Repeat --candidate for multiple donors."
        ),
    )
    batch_recipient.add_argument(
        "--save",
        action="store_true",
        help=(
            "Persist all pair runs/results atomically. "
            "Default is compute-only NO SAVE."
        ),
    )
    batch_recipient.add_argument(
        "--sort-by",
        default=None,
        help=(
            "STEP 18 software ordering metric: "
            "donor-only, shared, recipient-only."
        ),
    )
    batch_recipient.add_argument(
        "--sort-level",
        default=None,
        help=(
            "Representation used for software ordering: "
            "canonical, lgx, G or P. Default with --sort-by: lgx."
        ),
    )
    batch_recipient.add_argument(
        "--sort-order",
        default="auto",
        help=(
            "auto, asc or desc. AUTO uses shared=desc and "
            "donor-only/recipient-only=asc."
        ),
    )
    batch_recipient.add_argument(
        "--limit",
        "--display-limit",
        dest="display_limit",
        type=int,
        default=None,
        help=(
            "Limit DISPLAYED ordered pairs only. "
            "With --save, all eligible pairs are still persisted."
        ),
    )
    batch_recipient.add_argument(
        "--export",
        action="store_true",
        help=(
            "STEP 19 export of the FULL computed batch. "
            "Works in NO SAVE and SAVE modes."
        ),
    )
    batch_recipient.add_argument(
        "--export-format",
        choices=batch_exporters.VALID_BATCH_EXPORT_FORMATS,
        default="both",
        help="json, csv or both. Default: both.",
    )
    batch_recipient.add_argument(
        "--export-dir",
        type=Path,
        default=batch_exporters.DEFAULT_BATCH_EXPORT_DIR,
        help="Batch export output directory.",
    )
    batch_recipient.add_argument(
        "--export-name",
        default=None,
        help=(
            "Optional export base filename without extension. "
            "Default is generated from direction/anchor/sort."
        ),
    )
    batch_recipient.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing existing STEP 19 export files.",
    )
    batch_recipient.add_argument(
        "--filter-level",
        default=None,
        help=(
            "STEP 22 selection representation: canonical, lgx, G or P. "
            "Default when filtering: lgx."
        ),
    )
    batch_recipient.add_argument(
        "--max-donor-only",
        type=int,
        default=None,
        help=(
            "STEP 22 select rows with donor_only_count <= N "
            "at --filter-level."
        ),
    )
    batch_recipient.add_argument(
        "--min-shared",
        type=int,
        default=None,
        help=(
            "STEP 22 select rows with shared_count >= N "
            "at --filter-level."
        ),
    )
    batch_recipient.add_argument(
        "--max-recipient-only",
        type=int,
        default=None,
        help=(
            "STEP 22 select rows with recipient_only_count <= N "
            "at --filter-level."
        ),
    )
    batch_recipient.add_argument(
        "--exclude-candidate",
        action="append",
        default=None,
        help=(
            "STEP 22 exclude one candidate external_id from the selected "
            "view. Repeat for multiple IDs."
        ),
    )
    batch_recipient.add_argument(
        "--export-selection",
        action="store_true",
        help=(
            "With --export, export only the STEP 22 selected view. "
            "Default --export still exports the FULL computed batch."
        ),
    )
    batch_recipient.add_argument("-h", "--help", action="store_true")

    batch_donor = batch_commands.add_parser(
        "donor",
        add_help=False,
        help="Compare one DONOR against many RECIPIENT subjects.",
    )
    batch_donor.add_argument("external_id")
    batch_donor.add_argument(
        "--typing-id",
        type=int,
        default=None,
        help="Use a specific DONOR typing_id instead of latest.",
    )
    batch_donor.add_argument(
        "--candidate",
        action="append",
        default=None,
        help=(
            "Restrict to one RECIPIENT external_id. "
            "Repeat --candidate for multiple recipients."
        ),
    )
    batch_donor.add_argument(
        "--save",
        action="store_true",
        help=(
            "Persist all pair runs/results atomically. "
            "Default is compute-only NO SAVE."
        ),
    )
    batch_donor.add_argument(
        "--sort-by",
        default=None,
        help=(
            "STEP 18 software ordering metric: "
            "donor-only, shared, recipient-only."
        ),
    )
    batch_donor.add_argument(
        "--sort-level",
        default=None,
        help=(
            "Representation used for software ordering: "
            "canonical, lgx, G or P. Default with --sort-by: lgx."
        ),
    )
    batch_donor.add_argument(
        "--sort-order",
        default="auto",
        help=(
            "auto, asc or desc. AUTO uses shared=desc and "
            "donor-only/recipient-only=asc."
        ),
    )
    batch_donor.add_argument(
        "--limit",
        "--display-limit",
        dest="display_limit",
        type=int,
        default=None,
        help=(
            "Limit DISPLAYED ordered pairs only. "
            "With --save, all eligible pairs are still persisted."
        ),
    )
    batch_donor.add_argument(
        "--export",
        action="store_true",
        help=(
            "STEP 19 export of the FULL computed batch. "
            "Works in NO SAVE and SAVE modes."
        ),
    )
    batch_donor.add_argument(
        "--export-format",
        choices=batch_exporters.VALID_BATCH_EXPORT_FORMATS,
        default="both",
        help="json, csv or both. Default: both.",
    )
    batch_donor.add_argument(
        "--export-dir",
        type=Path,
        default=batch_exporters.DEFAULT_BATCH_EXPORT_DIR,
        help="Batch export output directory.",
    )
    batch_donor.add_argument(
        "--export-name",
        default=None,
        help=(
            "Optional export base filename without extension. "
            "Default is generated from direction/anchor/sort."
        ),
    )
    batch_donor.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing existing STEP 19 export files.",
    )
    batch_donor.add_argument(
        "--filter-level",
        default=None,
        help=(
            "STEP 22 selection representation: canonical, lgx, G or P. "
            "Default when filtering: lgx."
        ),
    )
    batch_donor.add_argument(
        "--max-donor-only",
        type=int,
        default=None,
        help=(
            "STEP 22 select rows with donor_only_count <= N "
            "at --filter-level."
        ),
    )
    batch_donor.add_argument(
        "--min-shared",
        type=int,
        default=None,
        help=(
            "STEP 22 select rows with shared_count >= N "
            "at --filter-level."
        ),
    )
    batch_donor.add_argument(
        "--max-recipient-only",
        type=int,
        default=None,
        help=(
            "STEP 22 select rows with recipient_only_count <= N "
            "at --filter-level."
        ),
    )
    batch_donor.add_argument(
        "--exclude-candidate",
        action="append",
        default=None,
        help=(
            "STEP 22 exclude one candidate external_id from the selected "
            "view. Repeat for multiple IDs."
        ),
    )
    batch_donor.add_argument(
        "--export-selection",
        action="store_true",
        help=(
            "With --export, export only the STEP 22 selected view. "
            "Default --export still exports the FULL computed batch."
        ),
    )
    batch_donor.add_argument("-h", "--help", action="store_true")

    # ------------------------------------------------------------
    # batches — STEP 20 persistent history
    # ------------------------------------------------------------
    batches_parser = groups.add_parser(
        "batches",
        add_help=False,
        help="Persistent STEP 20 batch history.",
    )
    batches_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    batches_commands = batches_parser.add_subparsers(dest="command")

    batches_list = batches_commands.add_parser(
        "list",
        add_help=False,
        help="List/filter saved persistent batch runs.",
    )
    batches_list.add_argument(
        "--query",
        default=None,
        help="Free-text search across stored batch metadata.",
    )
    batches_list.add_argument(
        "--direction",
        choices=("recipient", "donor"),
        default=None,
        help="Filter by batch direction.",
    )
    batches_list.add_argument(
        "--anchor",
        default=None,
        help="Filter by anchor external_id (case-insensitive substring).",
    )
    batches_list.add_argument(
        "--imgthla-version",
        dest="imgthla_version",
        default=None,
        help="Filter by exact IPD-IMGT/HLA version.",
    )
    batches_list.add_argument(
        "--sort-level",
        choices=("canonical", "lgx", "G", "P"),
        default=None,
        help="Filter by stored STEP 18 sort level.",
    )
    batches_list.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of history rows to display.",
    )
    batches_list.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Number of matching history rows to skip.",
    )
    batches_list.add_argument("-h", "--help", action="store_true")

    batches_search = batches_commands.add_parser(
        "search",
        add_help=False,
        help="Search persistent batch history.",
    )
    batches_search.add_argument("query")
    batches_search.add_argument(
        "--direction",
        choices=("recipient", "donor"),
        default=None,
    )
    batches_search.add_argument("--anchor", default=None)
    batches_search.add_argument(
        "--imgthla-version",
        dest="imgthla_version",
        default=None,
    )
    batches_search.add_argument(
        "--sort-level",
        choices=("canonical", "lgx", "G", "P"),
        default=None,
    )
    batches_search.add_argument("--limit", type=int, default=None)
    batches_search.add_argument("--offset", type=int, default=0)
    batches_search.add_argument("-h", "--help", action="store_true")

    batches_latest = batches_commands.add_parser(
        "latest",
        add_help=False,
        help="Show the newest persistent batch.",
    )
    batches_latest.add_argument("-h", "--help", action="store_true")

    batches_summary = batches_commands.add_parser(
        "summary",
        add_help=False,
        help="Show administrative statistics for persistent batch history.",
    )
    batches_summary.add_argument("-h", "--help", action="store_true")

    batches_show = batches_commands.add_parser(
        "show",
        add_help=False,
        help="Show persistent batch metadata and linked analysis runs.",
    )
    batches_show.add_argument("batch_id", type=int)
    batches_show.add_argument("-h", "--help", action="store_true")

    batches_results = batches_commands.add_parser(
        "results",
        add_help=False,
        help="Reload saved batch results without py-ard recalculation.",
    )
    batches_results.add_argument("batch_id", type=int)
    batches_results.add_argument("-h", "--help", action="store_true")

    batches_export = batches_commands.add_parser(
        "export",
        add_help=False,
        help="Re-export one persistent batch directly from SQLite.",
    )
    batches_export.add_argument("batch_id", type=int)
    batches_export.add_argument(
        "--format",
        choices=batch_exporters.VALID_BATCH_EXPORT_FORMATS,
        default="both",
    )
    batches_export.add_argument(
        "--output-dir",
        type=Path,
        default=batch_exporters.DEFAULT_BATCH_EXPORT_DIR,
    )
    batches_export.add_argument(
        "--name",
        default=None,
        help="Optional export base filename without extension.",
    )
    batches_export.add_argument(
        "--overwrite",
        action="store_true",
    )
    batches_export.add_argument("-h", "--help", action="store_true")

    # ------------------------------------------------------------
    # workflow
    # ------------------------------------------------------------
    workflow_parser = groups.add_parser(
        "workflow",
        add_help=False,
        help="Interactive/demo HLA input workflows.",
    )
    workflow_parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="_group_help",
    )
    workflow_commands = workflow_parser.add_subparsers(dest="command")

    interactive = workflow_commands.add_parser(
        "interactive",
        add_help=False,
        help="Interactive DONOR/RECIPIENT HLA input.",
    )
    interactive.add_argument(
        "--no-save",
        action="store_true",
        help="Do not persist the entered profiles to SQLite.",
    )
    interactive.add_argument("-h", "--help", action="store_true")

    demo = workflow_commands.add_parser(
        "demo",
        add_help=False,
        help="Run the built-in demo profiles.",
    )
    demo.add_argument(
        "--no-save",
        action="store_true",
        help="Do not persist demo profiles to SQLite.",
    )
    demo.add_argument("-h", "--help", action="store_true")

    return parser


def command_help_text():
    return """\
HLA donor/recipient comparison CLI

Quick start:
  python main.py db status
  python main.py subjects list
  python main.py report recipient RECIP-001
  python main.py compare levels recipient RECIP-001 --level canonical --level lgx

Help:
  python main.py --help
  python main.py GROUP --help
  python main.py --db PATH GROUP COMMAND

Project docs:
  README.md
  docs/schema.md
  docs/data.md

Current layer: STEP 28 report comparison / multi-report analysis.
Built on STEP 27 reporting / STEP 26 statistics / STEP 25 summary / STEP 24 matrix / STEP 23 pair profiles / STEP 22 selection / STEP 21 history management / STEP 20 persistent history / STEP 19 export / STEP 18 ordering / STEP 17 batch analysis / STEP 16 import / STEP 15 CLI.

Command examples:

Database:
  python main.py db status
  python main.py db migrate

Subjects:
  python main.py subjects list

Typings:
  python main.py typings history DONOR-001
  python main.py typings show DONOR-001
  python main.py typings show DONOR-001 --typing-id 1
  python main.py typings import .\\import_typing.json
  python main.py typings import .\\import_typing.csv
  python main.py typings import FILE --dry-run

Analyses:
  python main.py analyses list
  python main.py analyses create DONOR-001 RECIP-001
  python main.py analyses create DONOR-001 RECIP-001 --donor-typing-id 1 --recipient-typing-id 2
  python main.py analyses show 1
  python main.py analyses run 1
  python main.py analyses results 1
  python main.py analyses export 1
  python main.py analyses export 1 --format json --overwrite


Pair profiles (STEP 23):
  python main.py pairs show DONOR-001 RECIP-001
  python main.py pairs show DONOR-001 RECIP-001 --level lgx
  python main.py pairs show DONOR-001 RECIP-001 --level lgx --locus DRB1
  python main.py pairs show-run 10
  python main.py pairs export DONOR-001 RECIP-001 --format both
  python main.py pairs export-run 10 --format json

HLA comparison matrix (STEP 24):
  python main.py matrix recipient RECIP-001
  python main.py matrix recipient RECIP-001 --level lgx
  python main.py matrix donor DONOR-001 --level G
  python main.py matrix recipient RECIP-001 --candidate DONOR-001
  python main.py matrix recipient RECIP-001 --locus A --locus DRB1
  python main.py matrix recipient RECIP-001 --sort-by donor-only
  python main.py matrix batch 3 --level lgx
  python main.py matrix batch 3 --export --format both

Mismatch summary / classification (STEP 25):
  python main.py summary recipient RECIP-001
  python main.py summary donor DONOR-001
  python main.py summary recipient RECIP-001 --level lgx --locus DRB1
  python main.py summary recipient RECIP-001 --candidate DONOR-001
  python main.py summary recipient RECIP-001 --sort-by donor-only
  python main.py summary batch 3 --level lgx
  python main.py summary batch 3 --export --format both

Comparison statistics / aggregation (STEP 26):
  python main.py stats recipient RECIP-001
  python main.py stats donor DONOR-001
  python main.py stats recipient RECIP-001 --level lgx --locus DRB1
  python main.py stats recipient RECIP-001 --candidate DONOR-001
  python main.py stats recipient RECIP-001 --details
  python main.py stats recipient RECIP-001 --sort-by donor-only
  python main.py stats batch 3 --level lgx
  python main.py stats batch 3 --export --format both

Analytical reporting (STEP 27):
  python main.py report recipient RECIP-001
  python main.py report donor DONOR-001
  python main.py report recipient RECIP-001 --level lgx --locus DRB1
  python main.py report recipient RECIP-001 --candidate DONOR-001
  python main.py report recipient RECIP-001 --sort-by shared --sort-order desc
  python main.py report batch 3
  python main.py report recipient RECIP-001 --export both
  python main.py report batch 3 --export json

Report comparison / multi-report analysis (STEP 28):
  python main.py compare levels recipient RECIP-001
  python main.py compare levels donor DONOR-001
  python main.py compare levels recipient RECIP-001 --level canonical --level lgx
  python main.py compare levels recipient RECIP-001 --locus DRB1
  python main.py compare levels recipient RECIP-001 --candidate DONOR-001
  python main.py compare batches 1 3 --level lgx
  python main.py compare levels recipient RECIP-001 --export both
  python main.py compare batches 1 3 --export json

Batch:
  python main.py batch recipient RECIP-001
  python main.py batch recipient RECIP-001 --candidate DONOR-001
  python main.py batch recipient RECIP-001 --save
  python main.py batch donor DONOR-001
  python main.py batch donor DONOR-001 --candidate RECIP-001 --save

STEP 18 software ordering:
  python main.py batch recipient RECIP-001 --sort-by donor-only --sort-level lgx
  python main.py batch recipient RECIP-001 --sort-by shared --sort-level G
  python main.py batch donor DONOR-001 --sort-by recipient-only --sort-order asc
  python main.py batch recipient RECIP-001 --sort-by donor-only --limit 5

STEP 19 batch export:
  python main.py batch recipient RECIP-001 --export
  python main.py batch recipient RECIP-001 --sort-by donor-only --export
  python main.py batch recipient RECIP-001 --sort-by donor-only --limit 5 --export
  python main.py batch donor DONOR-001 --export --export-format json
  python main.py batch recipient RECIP-001 --export --overwrite

STEP 22 batch filtering / selection:
  python main.py batch recipient RECIP-001 --max-donor-only 10
  python main.py batch recipient RECIP-001 --filter-level lgx --min-shared 3
  python main.py batch recipient RECIP-001 --max-donor-only 10 --min-shared 2
  python main.py batch recipient RECIP-001 --exclude-candidate DONOR-002
  python main.py batch recipient RECIP-001 --max-donor-only 10 --export --export-selection

Persistent batch history (STEP 20 + STEP 21):
  python main.py batches list
  python main.py batches list --direction recipient
  python main.py batches list --anchor RECIP-001 --limit 10
  python main.py batches search RECIP-001
  python main.py batches latest
  python main.py batches summary
  python main.py batches show 1
  python main.py batches results 1
  python main.py batches export 1 --format both

Workflow:
  python main.py workflow interactive
  python main.py workflow demo

Global:
  --db PATH      Use another SQLite database.

Backward compatibility:
  Legacy flags such as --db-status, --list-subjects,
  --show-results and --export-analysis are still supported.
"""


def _group_help(group):
    messages = {
        "db": """\
Database commands:
  db status
  db migrate
""",
        "subjects": """\
Subject commands:
  subjects list
""",
        "typings": """\
Typing commands:
  typings history EXTERNAL_ID
  typings show EXTERNAL_ID [--typing-id N]
  typings import FILE [--format auto|json|csv] [--dry-run]
""",
        "analyses": """\
Analysis commands:
  analyses list
  analyses create DONOR_ID RECIPIENT_ID
  analyses show RUN_ID
  analyses run RUN_ID
  analyses results RUN_ID
  analyses export RUN_ID [--format json|csv|both] [--overwrite]
""",
        "pairs": """\
Pair comparison profiles (STEP 23):
  pairs show DONOR_ID RECIPIENT_ID [--donor-typing-id ID] [--recipient-typing-id ID]
             [--level canonical|lgx|G|P] [--locus A|B|C|DRB1|DQB1|DPB1]
  pairs show-run RUN_ID [--level canonical|lgx|G|P] [--locus LOCUS]
  pairs export DONOR_ID RECIPIENT_ID [--level LEVEL] [--locus LOCUS]
               [--format json|csv|both] [--output-dir PATH] [--name NAME] [--overwrite]
  pairs export-run RUN_ID [--level LEVEL] [--locus LOCUS]
                   [--format json|csv|both] [--output-dir PATH] [--name NAME] [--overwrite]

Live profiles compare exact representations already stored in SQLite.
Stored-run profiles load exact saved analysis_results.
Neither path recalculates py-ard reductions.
""",
        "compare": """\
Report comparison / multi-report analysis (STEP 28):
  compare levels recipient RECIPIENT_ID
                 [--typing-id ID] [--candidate DONOR_ID]
                 [--level canonical|lgx|G|P]...
                 [--locus LOCUS]
                 [--sort-by donor-only|shared|recipient-only]
                 [--sort-order auto|asc|desc]
                 [--export [json|csv|both]]
                 [--output-dir PATH] [--name NAME] [--overwrite]

  compare levels donor DONOR_ID
                 [--typing-id ID] [--candidate RECIPIENT_ID] ...

  compare batches LEFT_BATCH_ID RIGHT_BATCH_ID
                  [--level canonical|lgx|G|P]
                  [--locus LOCUS]
                  [--sort-by donor-only|shared|recipient-only]
                  [--sort-order auto|asc|desc]
                  [--export [json|csv|both]]
                  [--output-dir PATH] [--name NAME] [--overwrite]

LEVELS compares the same live scope across stored representation levels.
BATCHES compares two persistent historical STEP 27 report scopes.
All deltas are NON-CLINICAL software differences.
""",

        "report": """\
Analytical reporting (STEP 27):
  report recipient RECIPIENT_ID [--typing-id ID]
                   [--candidate DONOR_ID]
                   [--level canonical|lgx|G|P]
                   [--locus LOCUS]
                   [--sort-by donor-only|shared|recipient-only]
                   [--sort-order auto|asc|desc]
                   [--export [json|csv|both]]
                   [--output-dir PATH] [--name NAME] [--overwrite]

  report donor DONOR_ID [--typing-id ID]
               [--candidate RECIPIENT_ID] ...

  report batch BATCH_ID [--level canonical|lgx|G|P]
                        [--locus LOCUS]
                        [--sort-by donor-only|shared|recipient-only]
                        [--sort-order auto|asc|desc]
                        [--export [json|csv|both]]
                        [--output-dir PATH] [--name NAME] [--overwrite]

STEP 27 composes and validates STEP 24 + STEP 25 + STEP 26 data.
It does not recalculate py-ard reductions and does not create analysis_runs.
The report is NON-CLINICAL.
""",

        "stats": """\
Comparison statistics / aggregation (STEP 26):
  stats recipient RECIPIENT_ID [--typing-id ID] [--candidate DONOR_ID]
                  [--level canonical|lgx|G|P] [--locus LOCUS]
                  [--sort-by donor-only|shared|recipient-only]
                  [--sort-order auto|asc|desc]
                  [--details] [--export]
                  [--format json|csv|both]
                  [--output-dir PATH] [--name NAME] [--overwrite]

  stats donor DONOR_ID [--typing-id ID] [--candidate RECIPIENT_ID] ...

  stats batch BATCH_ID [--level canonical|lgx|G|P]
                       [--locus LOCUS]
                       [--sort-by donor-only|shared|recipient-only]
                       [--sort-order auto|asc|desc]
                       [--details] [--export]
                       [--format json|csv|both]
                       [--output-dir PATH] [--name NAME] [--overwrite]

Statistics:
  count / sum / min / max / mean / median
  pair classification distribution
  locus classification distribution

All results are descriptive NON-CLINICAL software-comparison data.
""",

        "summary": """\
Mismatch summary / classification (STEP 25):
  summary recipient RECIPIENT_ID [--typing-id ID] [--candidate DONOR_ID]
                    [--level canonical|lgx|G|P] [--locus LOCUS]
                    [--sort-by donor-only|shared|recipient-only]
                    [--sort-order auto|asc|desc] [--export]
                    [--format json|csv|both] [--output-dir PATH]
                    [--name NAME] [--overwrite]
  summary donor DONOR_ID [--typing-id ID] [--candidate RECIPIENT_ID] ...
  summary batch BATCH_ID [--level canonical|lgx|G|P] [--locus LOCUS] ...

Descriptive NON-CLINICAL software classes:
  COMPLETE-SOFTWARE-MATCH
  PARTIAL-SOFTWARE-MATCH
  NO-SOFTWARE-SHARED
""",

        "matrix": """\
HLA comparison matrix (STEP 24):
  matrix recipient RECIPIENT_ID [--typing-id ID] [--candidate DONOR_ID]
                   [--level canonical|lgx|G|P]
                   [--locus LOCUS]
                   [--sort-by donor-only|shared|recipient-only]
                   [--sort-order auto|asc|desc]
                   [--export] [--format json|csv|both]
                   [--output-dir PATH] [--name NAME] [--overwrite]

  matrix donor DONOR_ID [--typing-id ID] [--candidate RECIPIENT_ID]
               [--level canonical|lgx|G|P]
               [--locus LOCUS]
               [--sort-by donor-only|shared|recipient-only]
               [--sort-order auto|asc|desc]
               [--export] [--format json|csv|both]
               [--output-dir PATH] [--name NAME] [--overwrite]

  matrix batch BATCH_ID
               [--level canonical|lgx|G|P]
               [--locus LOCUS]
               [--sort-by donor-only|shared|recipient-only]
               [--sort-order auto|asc|desc]
               [--export] [--format json|csv|both]
               [--output-dir PATH] [--name NAME] [--overwrite]

Cell format:
  shared_count/donor_only_count/recipient_only_count

Default level:
  LGX

Persistent batch mode loads saved analysis_results from SQLite.
No py-ard reductions are recalculated.
Sorting is deterministic software ordering, NOT clinical ranking.
""",

        "batch": """\
Batch commands:
  batch recipient RECIPIENT_ID [--typing-id N] [--candidate DONOR_ID] [--save]
  batch donor DONOR_ID [--typing-id N] [--candidate RECIPIENT_ID] [--save]

STEP 18 software ordering:
  --sort-by donor-only|shared|recipient-only
  --sort-level canonical|lgx|G|P
  --sort-order auto|asc|desc
  --limit N / --display-limit N

STEP 19 export:
  --export
  --export-format json|csv|both
  --export-dir PATH
  --export-name NAME
  --overwrite

Export scope is always the FULL computed batch by default.
--limit changes CLI display only and never truncates export.

STEP 22 filtering / selection:
  --filter-level canonical|lgx|G|P
  --max-donor-only N
  --min-shared N
  --max-recipient-only N
  --exclude-candidate EXTERNAL_ID
  --export-selection

Threshold predicates are combined with AND.
--save always persists ALL eligible computed pairs.
Ordinary --export still exports the FULL computed batch.
--export-selection explicitly exports only the selected STEP 22 view.

Default is NO SAVE and no ordering. AUTO ordering is:
  shared -> descending
  donor-only / recipient-only -> ascending

--limit changes display only. With --save, all eligible pairs are saved.
This is deterministic software ordering, NOT a clinical compatibility ranking.
""",
        "batches": """\
Persistent batch history commands (STEP 20 + STEP 21):
  batches list [--query TEXT] [--direction recipient|donor]
               [--anchor EXTERNAL_ID] [--imgthla-version VERSION]
               [--sort-level canonical|lgx|G|P]
               [--limit N] [--offset N]
  batches search QUERY [--direction recipient|donor]
                       [--anchor EXTERNAL_ID]
                       [--imgthla-version VERSION]
                       [--sort-level canonical|lgx|G|P]
                       [--limit N] [--offset N]
  batches latest
  batches summary
  batches show BATCH_ID
  batches results BATCH_ID
  batches export BATCH_ID [--format json|csv|both] [--output-dir PATH] [--name NAME] [--overwrite]

STEP 21 operations are read-only management of stored STEP 20 metadata.
They do not re-run py-ard and do not create analysis_runs.
A saved STEP 17/18 CLI batch keeps its persistent batch_id.
""",
        "workflow": """\
Workflow commands:
  workflow interactive [--no-save]
  workflow demo [--no-save]
""",
    }
    return messages[group]


def _normal_db_guard(database_path):
    database.migrate_database(database_path)
    database.verify_database_is_current(database_path)


def _cli_module():
    # Lazy import prevents an import cycle when cli.main() dispatches here.
    import cli
    return cli


def _dispatch(args, input_func, output_func):
    cli = _cli_module()
    database_path = args.db

    # ------------------------------------------------------------
    # Help
    # ------------------------------------------------------------
    if args._root_help or args.group is None:
        output_func(command_help_text().rstrip())
        return 0

    if getattr(args, "_group_help", False) and args.command is None:
        output_func(_group_help(args.group).rstrip())
        return 0

    if getattr(args, "help", False):
        output_func(_group_help(args.group).rstrip())
        return 0

    if args.command is None:
        output_func(
            f"ERROR: missing command for group {args.group!r}."
        )
        output_func(_group_help(args.group).rstrip())
        return 2

    # ------------------------------------------------------------
    # Database
    # ------------------------------------------------------------
    if args.group == "db":
        if args.command == "status":
            status = database.get_database_schema_status(database_path)
            cli.print_database_schema_status(
                status,
                output_func=output_func,
            )
            return 0

        if args.command == "migrate":
            info = database.migrate_database(database_path)
            cli.print_migration_summary(
                info,
                output_func=output_func,
            )
            return 0

    # All remaining commands operate on a current database.
    _normal_db_guard(database_path)

    # ------------------------------------------------------------
    # Subjects
    # ------------------------------------------------------------
    if args.group == "subjects":
        subjects = database.list_subjects(database_path)
        cli.print_subject_list(
            subjects,
            output_func=output_func,
        )
        return 0

    # ------------------------------------------------------------
    # Typings
    # ------------------------------------------------------------
    if args.group == "typings":
        if args.command == "history":
            history = database.list_subject_typings(
                database_path,
                args.external_id,
            )
            cli.print_subject_typing_history(
                history,
                output_func=output_func,
            )
            return 0

        if args.command == "show":
            loaded = database.load_subject_typing(
                database_path=database_path,
                external_id=args.external_id,
                typing_id=args.typing_id,
            )
            cli.print_saved_typing(
                loaded,
                output_func=output_func,
            )
            return 0

        if args.command == "import":
            import_info = importers.import_typings(
                database_path=database_path,
                input_path=args.input_path,
                import_format=args.import_format,
                dry_run=args.dry_run,
            )
            cli.print_import_summary(
                import_info,
                output_func=output_func,
            )
            return 0

    # ------------------------------------------------------------
    # Analyses
    # ------------------------------------------------------------
    if args.group == "analyses":
        if args.command == "list":
            runs = database.list_analysis_runs(database_path)
            cli.print_analysis_run_list(
                runs,
                output_func=output_func,
            )
            return 0

        if args.command == "create":
            run = database.create_analysis_run_for_subjects(
                database_path=database_path,
                donor_external_id=args.donor_external_id,
                recipient_external_id=args.recipient_external_id,
                donor_typing_id=args.donor_typing_id,
                recipient_typing_id=args.recipient_typing_id,
            )
            cli.print_analysis_run_summary(
                run,
                output_func=output_func,
            )
            return 0

        if args.command == "show":
            run = database.load_analysis_run(
                database_path,
                args.run_id,
            )
            cli.print_loaded_analysis_run(
                run,
                output_func=output_func,
            )
            return 0

        if args.command == "run":
            analyzed = cli.analyze_and_save_existing_run(
                database_path,
                args.run_id,
            )
            cli.print_analysis_results_save_summary(
                analyzed,
                output_func=output_func,
            )
            return 0

        if args.command == "results":
            loaded = database.load_analysis_results(
                database_path,
                args.run_id,
            )
            cli.print_loaded_analysis_results(
                loaded,
                output_func=output_func,
            )
            return 0

        if args.command == "export":
            export_info = exporters.export_analysis(
                database_path=database_path,
                run_id=args.run_id,
                output_dir=args.output_dir,
                export_format=args.format,
                overwrite=args.overwrite,
            )
            cli.print_export_summary(
                export_info,
                output_func=output_func,
            )
            return 0

    # ------------------------------------------------------------
    # STEP 28 HLA report comparison / multi-report analysis
    # ------------------------------------------------------------
    if args.group == "compare":
        if args.command == "levels":
            if args.direction not in ("recipient", "donor"):
                raise CommandCLIError(
                    "Липсва compare levels direction. "
                    "Използвайте recipient или donor."
                )

            comparison = (
                step28_report_comparison.build_live_level_comparison(
                    database_path=database_path,
                    direction=args.direction,
                    anchor_external_id=args.external_id,
                    anchor_typing_id=args.typing_id,
                    candidate_external_ids=args.candidate,
                    levels=args.level,
                    loci=args.locus,
                    sort_by=args.sort_by,
                    sort_order=args.sort_order,
                )
            )
        elif args.command == "batches":
            comparison = (
                step28_report_comparison.build_persistent_batch_comparison(
                    database_path=database_path,
                    left_batch_id=args.left_batch_id,
                    right_batch_id=args.right_batch_id,
                    level=args.level,
                    loci=args.locus,
                    sort_by=args.sort_by,
                    sort_order=args.sort_order,
                )
            )
        else:
            raise CommandCLIError(
                "Липсва compare subcommand. "
                "Използвайте levels или batches."
            )

        output_func(
            step28_report_comparison.render_comparison(
                comparison
            )
        )

        if args.export is not None:
            info = step28_report_comparison.export_comparison(
                comparison,
                output_dir=args.output_dir,
                export_format=args.export,
                export_name=args.name,
                overwrite=args.overwrite,
            )
            output_func(
                step28_report_comparison.render_export_summary(
                    info
                )
            )

        return 0

    # ------------------------------------------------------------
    # STEP 27 HLA analytical reporting
    # ------------------------------------------------------------
    if args.group == "report":
        if args.command in ("recipient", "donor"):
            report = step27_reporting.build_live_report(
                database_path=database_path,
                direction=args.command,
                anchor_external_id=args.external_id,
                anchor_typing_id=args.typing_id,
                candidate_external_ids=args.candidate,
                level=args.level,
                loci=args.locus,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
            )
        elif args.command == "batch":
            report = step27_reporting.build_persistent_report(
                database_path=database_path,
                batch_id=args.batch_id,
                level=args.level,
                loci=args.locus,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
            )
        else:
            raise CommandCLIError(
                "Липсва report subcommand. "
                "Използвайте recipient, donor или batch."
            )

        output_func(
            step27_reporting.render_report(report)
        )

        if args.export is not None:
            info = step27_reporting.export_report(
                report,
                output_dir=args.output_dir,
                export_format=args.export,
                export_name=args.name,
                overwrite=args.overwrite,
            )
            output_func(
                step27_reporting.render_export_summary(
                    info
                )
            )

        return 0

    # ------------------------------------------------------------
    # STEP 26 HLA comparison statistics / aggregation
    # ------------------------------------------------------------
    if args.group == "stats":
        if args.command in ("recipient", "donor"):
            stats = comparison_statistics.build_live_statistics(
                database_path=database_path,
                direction=args.command,
                anchor_external_id=args.external_id,
                anchor_typing_id=args.typing_id,
                candidate_external_ids=args.candidate,
                level=args.level,
                loci=args.locus,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
                details=args.details,
            )
        elif args.command == "batch":
            stats = comparison_statistics.build_persistent_statistics(
                database_path=database_path,
                batch_id=args.batch_id,
                level=args.level,
                loci=args.locus,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
                details=args.details,
            )
        else:
            raise CommandCLIError(
                "Липсва stats subcommand. "
                "Използвайте recipient, donor или batch."
            )

        output_func(
            comparison_statistics.render_statistics(stats)
        )

        if args.export:
            info = comparison_statistics.export_statistics(
                stats,
                output_dir=args.output_dir,
                export_format=args.format,
                export_name=args.name,
                overwrite=args.overwrite,
            )
            output_func(
                comparison_statistics.render_export_summary(info)
            )

        return 0

    # ------------------------------------------------------------
    # STEP 25 HLA mismatch summary / classification
    # ------------------------------------------------------------
    if args.group == "summary":
        if args.command in ("recipient", "donor"):
            summary = mismatch_summary.build_live_summary(
                database_path=database_path, direction=args.command,
                anchor_external_id=args.external_id, anchor_typing_id=args.typing_id,
                candidate_external_ids=args.candidate, level=args.level, loci=args.locus,
                sort_by=args.sort_by, sort_order=args.sort_order,
            )
        elif args.command == "batch":
            summary = mismatch_summary.build_persistent_summary(
                database_path=database_path, batch_id=args.batch_id, level=args.level,
                loci=args.locus, sort_by=args.sort_by, sort_order=args.sort_order,
            )
        else:
            raise CommandCLIError("Липсва summary subcommand. Използвайте recipient, donor или batch.")

        output_func(mismatch_summary.render_summary(summary))
        if args.export:
            info = mismatch_summary.export_summary(
                summary, output_dir=args.output_dir, export_format=args.format,
                export_name=args.name, overwrite=args.overwrite,
            )
            output_func(mismatch_summary.render_export_summary(info))
        return 0

    # ------------------------------------------------------------
    # STEP 24 HLA comparison matrix
    # ------------------------------------------------------------
    if args.group == "matrix":
        if args.command in ("recipient", "donor"):
            matrix = hla_matrix.build_live_matrix(
                database_path=database_path,
                direction=args.command,
                anchor_external_id=args.external_id,
                anchor_typing_id=args.typing_id,
                candidate_external_ids=args.candidate,
                level=args.level,
                loci=args.locus,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
            )
        elif args.command == "batch":
            matrix = hla_matrix.build_persistent_matrix(
                database_path=database_path,
                batch_id=args.batch_id,
                level=args.level,
                loci=args.locus,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
            )
        else:
            raise CommandCLIError(
                "Липсва matrix subcommand. "
                "Използвайте recipient, donor или batch."
            )

        output_func(
            hla_matrix.render_matrix(matrix)
        )

        if args.export:
            info = hla_matrix.export_matrix(
                matrix,
                output_dir=args.output_dir,
                export_format=args.format,
                export_name=args.name,
                overwrite=args.overwrite,
            )
            output_func(
                hla_matrix.render_export_summary(info)
            )

        return 0

    # ------------------------------------------------------------
    # STEP 23 Pair comparison profiles
    # ------------------------------------------------------------
    if args.group == "pairs":
        if args.command == "show":
            profile = pair_profiles.build_live_pair_profile(
                database_path, args.donor_external_id, args.recipient_external_id,
                donor_typing_id=args.donor_typing_id, recipient_typing_id=args.recipient_typing_id,
                level=args.level, locus=args.locus,
            )
            output_func(pair_profiles.render_pair_profile(profile))
            return 0

        if args.command == "show-run":
            profile = pair_profiles.build_stored_run_profile(
                database_path, args.run_id, level=args.level, locus=args.locus,
            )
            output_func(pair_profiles.render_pair_profile(profile))
            return 0

        if args.command == "export":
            profile = pair_profiles.build_live_pair_profile(
                database_path, args.donor_external_id, args.recipient_external_id,
                donor_typing_id=args.donor_typing_id, recipient_typing_id=args.recipient_typing_id,
                level=args.level, locus=args.locus,
            )
            info = pair_profiles.export_pair_profile(
                profile, output_dir=args.output_dir, export_format=args.format,
                export_name=args.name, overwrite=args.overwrite,
            )
            output_func(pair_profiles.render_export_summary(info))
            return 0

        if args.command == "export-run":
            profile = pair_profiles.build_stored_run_profile(
                database_path, args.run_id, level=args.level, locus=args.locus,
            )
            info = pair_profiles.export_pair_profile(
                profile, output_dir=args.output_dir, export_format=args.format,
                export_name=args.name, overwrite=args.overwrite,
            )
            output_func(pair_profiles.render_export_summary(info))
            return 0

        raise CommandCLIError("Липсва pairs subcommand. Използвайте show, show-run, export или export-run.")

    # ------------------------------------------------------------
    # STEP 17-22 Batch analysis / ordering / export / persistence / selection
    # ------------------------------------------------------------
    if args.group == "batch":
        ranking_requested = args.sort_by is not None

        ranking_only_options = (
            args.sort_level is not None
            or args.sort_order != "auto"
            or args.display_limit is not None
        )

        if not ranking_requested and ranking_only_options:
            raise batch_ranking.BatchRankingError(
                "--sort-level, --sort-order and --limit require --sort-by."
            )

        export_only_options = (
            args.export_format != "both"
            or args.export_dir
            != batch_exporters.DEFAULT_BATCH_EXPORT_DIR
            or args.export_name is not None
            or args.overwrite
        )

        if not args.export and export_only_options:
            raise batch_exporters.BatchExportError(
                "--export-format, --export-dir, --export-name and "
                "--overwrite require --export."
            )

        step22_requested = batch_selection.selection_requested(
            exclude_candidate_ids=args.exclude_candidate,
            max_donor_only=args.max_donor_only,
            min_shared=args.min_shared,
            max_recipient_only=args.max_recipient_only,
        )

        if args.filter_level is not None and not step22_requested:
            raise batch_selection.BatchSelectionError(
                "--filter-level requires at least one STEP 22 selection "
                "predicate."
            )

        if args.export_selection and not args.export:
            raise batch_selection.BatchSelectionError(
                "--export-selection requires --export."
            )

        if args.export_selection and not step22_requested:
            raise batch_selection.BatchSelectionError(
                "--export-selection requires a STEP 22 selection predicate."
            )

        # Compute the complete eligible batch first.
        base_batch = batch_analysis.run_batch_analysis(
            database_path=database_path,
            direction=args.command,
            anchor_external_id=args.external_id,
            anchor_typing_id=args.typing_id,
            candidate_external_ids=args.candidate,
            save=False,
        )

        full_batch_view = base_batch
        selected_level = None

        if ranking_requested:
            selected_level = (
                args.sort_level
                if args.sort_level is not None
                else batch_ranking.DEFAULT_SORT_LEVEL
            )

            full_batch_view = batch_ranking.apply_batch_ordering(
                base_batch,
                level=selected_level,
                metric=args.sort_by,
                order=args.sort_order,
                display_limit=None,
            )

            full_batch_view["software_ordering"]["display_limit"] = (
                args.display_limit
            )

        # STEP 20 persistence always records the FULL eligible batch.
        if args.save:
            full_batch_view = batch_history.persist_batch_with_runs(
                database_path,
                full_batch_view,
            )

        selected_batch_view = full_batch_view

        if step22_requested:
            selected_batch_view = batch_selection.apply_batch_selection(
                full_batch_view,
                level=(
                    args.filter_level
                    if args.filter_level is not None
                    else batch_selection.DEFAULT_SELECTION_LEVEL
                ),
                exclude_candidate_ids=args.exclude_candidate,
                max_donor_only=args.max_donor_only,
                min_shared=args.min_shared,
                max_recipient_only=args.max_recipient_only,
            )

            output_func("")
            output_func(
                batch_selection.render_selection_summary(
                    selected_batch_view["step22_selection"]
                )
            )
            output_func(
                "STEP 22 is a NON-CLINICAL selected view. "
                "--save still persists all eligible computed pairs."
            )

        display_batch_view = selected_batch_view

        # STEP 18 limit remains display-only.
        if ranking_requested and args.display_limit is not None:
            if step22_requested:
                display_batch_view = copy.deepcopy(selected_batch_view)
                display_batch_view["rows"] = (
                    selected_batch_view["rows"][:args.display_limit]
                )
                display_batch_view["displayed_pair_count"] = len(
                    display_batch_view["rows"]
                )

                if "software_ordering" in display_batch_view:
                    display_batch_view["software_ordering"][
                        "display_limit"
                    ] = args.display_limit
                    display_batch_view["software_ordering"][
                        "displayed_pair_count"
                    ] = len(display_batch_view["rows"])
            else:
                display_batch_view = batch_ranking.apply_batch_ordering(
                    full_batch_view,
                    level=selected_level,
                    metric=args.sort_by,
                    order=args.sort_order,
                    display_limit=args.display_limit,
                )

        cli.print_batch_analysis_summary(
            display_batch_view,
            output_func=output_func,
        )

        if args.export:
            export_source = (
                selected_batch_view
                if args.export_selection
                else full_batch_view
            )

            export_info = batch_exporters.export_batch(
                batch=export_source,
                output_dir=args.export_dir,
                export_format=args.export_format,
                export_name=args.export_name,
                overwrite=args.overwrite,
            )

            cli.print_batch_export_summary(
                export_info,
                output_func=output_func,
            )

            if step22_requested:
                if args.export_selection:
                    output_func(
                        "STEP 22 export scope: SELECTED pairs only."
                    )
                else:
                    output_func(
                        "STEP 22 export scope: FULL computed batch; "
                        "use --export-selection to export only the "
                        "selected view."
                    )

        return 0

    # ------------------------------------------------------------
    # STEP 20 Persistent batch history
    # ------------------------------------------------------------
    if args.group == "batches":
        if args.command == "list":
            rows = step21_batch_history.load_and_manage_history(
                database_path=database_path,
                batch_history_module=batch_history,
                query=args.query,
                direction=args.direction,
                anchor=args.anchor,
                imgthla_version=args.imgthla_version,
                sort_level=args.sort_level,
                limit=args.limit,
                offset=args.offset,
            )
            output_func(
                step21_batch_history.render_batch_history(
                    rows,
                    title="STEP 21 — PERSISTENT BATCH HISTORY",
                )
            )
            return 0

        if args.command == "search":
            rows = step21_batch_history.load_and_manage_history(
                database_path=database_path,
                batch_history_module=batch_history,
                query=args.query,
                direction=args.direction,
                anchor=args.anchor,
                imgthla_version=args.imgthla_version,
                sort_level=args.sort_level,
                limit=args.limit,
                offset=args.offset,
            )
            output_func(
                step21_batch_history.render_batch_history(
                    rows,
                    title="STEP 21 — BATCH HISTORY SEARCH",
                )
            )
            return 0

        if args.command == "latest":
            rows = batch_history.list_batch_runs(database_path)
            latest = step21_batch_history.latest_batch(rows)

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

        if args.command == "summary":
            rows = batch_history.list_batch_runs(database_path)
            summary = step21_batch_history.summarize_batch_history(rows)

            output_func("")
            output_func("=" * 78)
            output_func("STEP 21 — BATCH HISTORY SUMMARY")
            output_func("=" * 78)
            output_func(f"Persistent batches: {summary['batch_count']}")
            output_func(f"Total pairs: {summary['total_pairs']}")
            output_func(
                f"Total analysis_results: "
                f"{summary['total_analysis_results']}"
            )
            output_func(
                f"Newest batch_id: {summary['newest_batch_id']}"
            )
            output_func(
                f"Oldest batch_id: {summary['oldest_batch_id']}"
            )
            output_func(
                f"Directions: {summary['directions']}"
            )
            output_func(
                f"IPD-IMGT/HLA versions: "
                f"{summary['imgthla_versions']}"
            )
            output_func(
                "Administrative statistics only; no HLA recalculation "
                "and no clinical ranking."
            )
            output_func("=" * 78)
            return 0

        if args.command == "show":
            saved = database.load_batch_run(
                database_path,
                args.batch_id,
            )
            cli.print_persistent_batch_detail(
                saved,
                output_func=output_func,
            )
            return 0

        if args.command == "results":
            batch = database.load_batch_results(
                database_path,
                args.batch_id,
            )
            cli.print_persistent_batch_results(
                batch,
                output_func=output_func,
            )
            return 0

        if args.command == "export":
            batch = database.load_batch_results(
                database_path,
                args.batch_id,
            )
            export_name = (
                args.name
                if args.name is not None
                else f"batch_run_{args.batch_id}"
            )
            info = batch_exporters.export_batch(
                batch=batch,
                output_dir=args.output_dir,
                export_format=args.format,
                export_name=export_name,
                overwrite=args.overwrite,
            )
            cli.print_persistent_batch_export_summary(
                args.batch_id,
                info,
                output_func=output_func,
            )
            return 0

    # ------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------
    if args.group == "workflow":
        legacy_args = ["--db", str(database_path)]

        if args.command == "demo":
            legacy_args.append("--demo")

        if args.no_save:
            legacy_args.append("--no-save")

        return cli.legacy_main(
            argv=legacy_args,
            input_func=input_func,
            output_func=output_func,
        )

    raise CommandCLIError(
        f"Неподдържана команда: {args.group} {args.command}"
    )


def run_command_cli(
    argv=None,
    input_func=input,
    output_func=print,
):
    if argv is None:
        argv = []

    parser = build_parser()

    try:
        args = parser.parse_args(list(argv))
        return _dispatch(
            args,
            input_func=input_func,
            output_func=output_func,
        )
    except CommandCLIError as exc:
        output_func(f"ERROR: {exc}")
        output_func("")
        output_func(command_help_text().rstrip())
        return 2
    except database.MigrationError as exc:
        output_func("")
        output_func("DATABASE MIGRATION ERROR")
        output_func(str(exc))
        return 6
    except database.DatabaseSchemaError as exc:
        output_func("")
        output_func("DATABASE SCHEMA ERROR")
        output_func(str(exc))
        return 6
    except UnicodeError as exc:
        output_func("")
        output_func("OUTPUT ENCODING ERROR")
        output_func(
            "The generated text could not be encoded for the current "
            "console or output stream."
        )
        output_func(str(exc))
        return 7
    except OSError as exc:
        output_func("")
        output_func("INPUT / OUTPUT ERROR")
        output_func(str(exc))
        return 7
    except (
        database.SubjectNotFoundError,
        database.TypingNotFoundError,
        database.IncompleteTypingError,
        database.AnalysisRunNotFoundError,
        database.AnalysisTypingRoleError,
        database.AnalysisVersionMismatchError,
        database.AnalysisResultsError,
        database.AnalysisResultsNotFoundError,
        exporters.ExportError,
        importers.HLAImportError,
        batch_analysis.BatchAnalysisError,
        batch_ranking.BatchRankingError,
        batch_selection.BatchSelectionError,
        pair_profiles.PairProfileError,
        pair_profiles.PairProfileExportError,
        hla_matrix.MatrixError,
        hla_matrix.MatrixExportError,
        mismatch_summary.MismatchSummaryError,
        mismatch_summary.MismatchSummaryExportError,
        comparison_statistics.ComparisonStatisticsError,
        comparison_statistics.ComparisonStatisticsExportError,
        step27_reporting.ReportingError,
        step27_reporting.ReportingExportError,
        step28_report_comparison.ReportComparisonError,
        step28_report_comparison.ReportComparisonExportError,
        batch_exporters.BatchExportError,
        batch_history.BatchRunNotFoundError,
        batch_history.BatchHistoryError,
        batch_history.BatchHistoryIntegrityError,
        step21_batch_history.BatchHistoryManagementError,
        ValueError,
    ) as exc:
        output_func("")
        output_func("DATABASE / ANALYSIS ERROR")
        output_func(str(exc))
        return 5

