"""
Compatibility facade for the Step 14 modular implementation.

Existing commands and imports can keep using:
    import hla_match as hla
    python hla_match.py ...
"""

import cli as _cli

from config import HLA_LOCI
from hla_validation import (
    pyard,
    get_ard,
    clean_allele,
    validate_allele,
    validate_person,
    canonicalize_person,
)
from hla_reduction import (
    normalize_allele,
    normalize_person,
    reduce_person,
    show_allele_reductions,
    show_person_reductions,
)
from hla_comparison import (
    compare_locus,
    build_comparison_results_from_bundles,
)
from batch_ranking import (
    BatchRankingError,
    normalize_sort_level,
    normalize_sort_metric,
    normalize_sort_order,
    resolve_sort_order,
    order_batch_rows,
    apply_batch_ordering,
)

donor_raw = _cli.donor_raw
recipient_raw = _cli.recipient_raw
donor = donor_raw
recipient = recipient_raw

InputCancelled = _cli.InputCancelled


def prompt_allele(
    label,
    locus,
    copy_number,
    input_func=input,
    output_func=print,
):
    """
    Compatibility wrapper.

    Uses this module's validate_allele reference so legacy unit tests that
    patch hla_match.validate_allele continue to work after the refactor.
    """
    while True:
        raw_value = input_func(
            f"{label} HLA-{locus} allele {copy_number}: "
        )

        if not isinstance(raw_value, str):
            output_func(
                "  ERROR: въведената стойност трябва да бъде текст."
            )
            continue

        command = raw_value.strip().lower()

        if command in {"q", "quit", "exit"}:
            raise InputCancelled()

        if command == "":
            output_func("  ERROR: HLA алелът не може да бъде празен.")
            output_func("  Въведете алела отново.")
            continue

        try:
            canonical = validate_allele(locus, raw_value)
        except ValueError as exc:
            output_func(f"  ERROR: {exc}")
            output_func("  Въведете алела отново.")
            continue

        output_func(f"  OK -> canonical: {canonical}")
        return raw_value


def input_person(label, input_func=input, output_func=print):
    """Compatibility wrapper for interactive RAW profile collection."""
    profile = {}

    output_func("")
    output_func("=" * 70)
    output_func(f"{label} HLA TYPING")
    output_func("=" * 70)
    output_func("Въведете два алела за всеки локус.")
    output_func("За прекратяване въведете q, quit или exit.")
    output_func("")

    for locus in HLA_LOCI:
        output_func(f"HLA-{locus}")

        first = prompt_allele(
            label,
            locus,
            1,
            input_func=input_func,
            output_func=output_func,
        )
        second = prompt_allele(
            label,
            locus,
            2,
            input_func=input_func,
            output_func=output_func,
        )

        profile[locus] = [first, second]
        output_func("")

    return profile


# Re-export CLI/workflow helpers used by existing callers/tests.
clone_profile = _cli.clone_profile
prompt_external_id = _cli.prompt_external_id
prepare_profile_representations = _cli.prepare_profile_representations
print_database_save_summary = _cli.print_database_save_summary
run_workflow = _cli.run_workflow
print_comparison_result = _cli.print_comparison_result

print_subject_list = _cli.print_subject_list
print_saved_typing = _cli.print_saved_typing
print_subject_typing_history = _cli.print_subject_typing_history

print_database_schema_status = _cli.print_database_schema_status
print_migration_summary = _cli.print_migration_summary
print_export_summary = _cli.print_export_summary
print_import_summary = _cli.print_import_summary
print_batch_analysis_summary = _cli.print_batch_analysis_summary
print_batch_export_summary = _cli.print_batch_export_summary
print_persistent_batch_list = _cli.print_persistent_batch_list
print_persistent_batch_detail = _cli.print_persistent_batch_detail
print_persistent_batch_results = _cli.print_persistent_batch_results
print_persistent_batch_export_summary = _cli.print_persistent_batch_export_summary

analyze_and_save_existing_run = _cli.analyze_and_save_existing_run
print_analysis_results_save_summary = (
    _cli.print_analysis_results_save_summary
)
print_loaded_analysis_results = _cli.print_loaded_analysis_results

print_analysis_run_summary = _cli.print_analysis_run_summary
print_analysis_run_list = _cli.print_analysis_run_list
print_loaded_analysis_run = _cli.print_loaded_analysis_run

_extract_optional_value = _cli._extract_optional_value
_extract_pair_values = _cli._extract_pair_values
_extract_database_path = _cli._extract_database_path

uses_command_style = _cli.uses_command_style
legacy_main = _cli.legacy_main
main = _cli.main


if __name__ == "__main__":
    raise SystemExit(main())
