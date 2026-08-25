import sys
from pathlib import Path

import database as database
import exporters as exporters

from config import HLA_LOCI
from hla_validation import (
    get_ard,
    validate_allele,
    canonicalize_person,
)
from hla_reduction import (
    reduce_person,
    show_person_reductions,
)
from hla_comparison import (
    compare_locus,
    build_comparison_results_from_bundles,
)

# ============================================================
# STEP 11: RAW INPUT и CANONICAL INPUT са отделни структури
# ============================================================
#
# RAW INPUT:
#   Пази точно подадените стойности за проследимост.
#
# CANONICAL INPUT:
#   Създава се след валидация и почистване.
#   Използва се за всички сравнения и py-ard редукции.
#
# Пример:
#   RAW:       "  HLA-A*02:01  "
#   CANONICAL: "A*02:01"
#
# RAW структурата никога не се презаписва от canonicalization.


donor_raw = {
    "A": ["A*02:01:01:01", "A*24:02"],
    "B": ["B*07:02", "B*44:02"],
    "C": ["C*07:02", "C*05:01"],
    "DRB1": ["DRB1*15:01", "DRB1*04:01"],
    "DQB1": ["DQB1*06:02", "DQB1*03:02"],
    "DPB1": ["DPB1*04:01", "DPB1*02:01"],
}

recipient_raw = {
    "A": ["A*02:02", "A*24:03"],
    "B": ["B*07:03", "B*44:03"],
    "C": ["C*07:05", "C*05:03"],
    "DRB1": ["DRB1*15:02", "DRB1*03:03"],
    "DQB1": ["DQB1*06:01", "DQB1*03:03"],
    "DPB1": ["DPB1*08:01", "DPB1*03:01"],
}


# Съвместимост с тестовете от Step 10.
# Старите имена остават достъпни и сочат към RAW входа.
donor = donor_raw
recipient = recipient_raw






















def print_comparison_result(label, result):
    """Отпечатва Shared / Donor-only / Recipient-only за едно ниво."""
    if result["shared"]:
        print(f"  Shared {label}:       ", ", ".join(result["shared"]))
    else:
        print(f"  Shared {label}:        none")

    if result["donor_only"]:
        print(f"  Donor-only {label}:   ", ", ".join(result["donor_only"]))
    else:
        print(f"  Donor-only {label}:    none")

    if result["recipient_only"]:
        print(
            f"  Recipient-only {label}:",
            ", ".join(result["recipient_only"]),
        )
    else:
        print(f"  Recipient-only {label}: none")

    print(
        f"  Shared {label} copy count:",
        result["shared_count"],
    )
    print(
        f"  Donor-only {label} copy count:",
        result["mismatch_count"],
    )
    print(
        f"  Recipient-only {label} copy count:",
        result["recipient_only_count"],
    )



# ============================================================
# STEP 12: ИНТЕРАКТИВНО ВЪВЕЖДАНЕ ОТ КОНЗОЛАТА
# ============================================================

class InputCancelled(Exception):
    """Сигнализира, че потребителят е прекратил интерактивното въвеждане."""


def prompt_allele(label, locus, copy_number, input_func=input, output_func=print):
    """
    Чете един HLA алел от конзолата.

    - Валидира го веднага чрез py-ard.
    - При грешка иска повторно въвеждане.
    - Връща RAW стойността точно както е въведена.
    - q / quit / exit прекратява въвеждането.
    """
    while True:
        raw_value = input_func(
            f"{label} HLA-{locus} allele {copy_number}: "
        )

        if not isinstance(raw_value, str):
            output_func("  ERROR: въведената стойност трябва да бъде текст.")
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

        # Връщаме RAW текста, а не canonical стойността.
        # Canonical профилът ще бъде създаден отделно.
        return raw_value


def input_person(label, input_func=input, output_func=print):
    """
    Интерактивно събира пълен HLA профил за един човек.

    Резултатът е RAW профил:
        {
            "A": [raw1, raw2],
            ...
        }
    """
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


def clone_profile(profile):
    """Прави независимо копие на HLA профила."""
    return {
        locus: list(profile[locus])
        for locus in HLA_LOCI
    }



# ============================================================
# STEP 13B: SUBJECT ID + SQLITE PERSISTENCE
# ============================================================

def prompt_external_id(label, input_func=input, output_func=print):
    """
    Чете pseudonymous external_id за DONOR/RECIPIENT.

    Примери:
        DONOR-001
        RECIP-001

    q / quit / exit прекратява въвеждането.
    """
    while True:
        value = input_func(f"{label} ID: ")

        if not isinstance(value, str):
            output_func("  ERROR: ID трябва да бъде текст.")
            continue

        stripped = value.strip()

        if stripped.lower() in {"q", "quit", "exit"}:
            raise InputCancelled()

        if not stripped:
            output_func("  ERROR: ID не може да бъде празно.")
            continue

        return stripped


def prepare_profile_representations(raw_profile, label):
    """
    Създава всички представяния, които STEP 13B записва в SQLite.
    """
    canonical = canonicalize_person(raw_profile, label)

    return {
        "raw": clone_profile(raw_profile),
        "canonical": canonical,
        "lgx": reduce_person(canonical, "lgx"),
        "G": reduce_person(canonical, "G"),
        "P": reduce_person(canonical, "P"),
    }


def print_database_save_summary(
    database_path,
    donor_external_id,
    recipient_external_id,
    save_result,
    imgthla_version,
):
    print()
    print("=" * 78)
    print("HLA TYPINGS SAVED TO SQLITE")
    print("=" * 78)
    print("Database:", Path(database_path).resolve())
    print("IPD-IMGT/HLA version:", imgthla_version)
    print()
    print(
        f"DONOR {donor_external_id}: "
        f"subject_id={save_result['donor']['subject_id']}, "
        f"typing_id={save_result['donor']['typing_id']}"
    )
    print(
        f"RECIPIENT {recipient_external_id}: "
        f"subject_id={save_result['recipient']['subject_id']}, "
        f"typing_id={save_result['recipient']['typing_id']}"
    )
    print()
    print("Saved allele rows: 12 DONOR + 12 RECIPIENT = 24")
    print(
        "Stored representations per allele: "
        "RAW / CANONICAL / LGX / G / P"
    )
    print(
        "Analysis comparison rows are NOT saved yet; "
        "that belongs to later STEP 13D/13E."
    )
    print("=" * 78)

def run_workflow(
    donor_raw_profile,
    recipient_raw_profile,
    donor_external_id=None,
    recipient_external_id=None,
    database_path=database.DEFAULT_DATABASE_PATH,
    save_to_database=True,
):
    ard = get_ard()
    print("IPD-IMGT/HLA version:", ard.get_db_version())

    print()
    print("STEP 13G — MIGRATION-AWARE HLA ANALYSIS")
    print()

    print("VALIDATING, CANONICALIZING AND PREPARING HLA DATA...")

    donor_bundle = prepare_profile_representations(
        donor_raw_profile,
        "DONOR",
    )
    recipient_bundle = prepare_profile_representations(
        recipient_raw_profile,
        "RECIPIENT",
    )

    donor_canonical = donor_bundle["canonical"]
    recipient_canonical = recipient_bundle["canonical"]

    print("HLA input validation: OK")
    print("Canonical HLA profiles created: OK")
    print("lgx / G / P representations created: OK")

    show_person_reductions(
        "DONOR HLA — RAW / CANONICAL / REDUCTIONS",
        donor_raw_profile,
        donor_canonical,
    )

    show_person_reductions(
        "RECIPIENT HLA — RAW / CANONICAL / REDUCTIONS",
        recipient_raw_profile,
        recipient_canonical,
    )

    # Всички изчисления оттук нататък използват подготвените
    # CANONICAL / lgx / G / P представяния.
    donor_lgx = donor_bundle["lgx"]
    recipient_lgx = recipient_bundle["lgx"]

    donor_g = donor_bundle["G"]
    recipient_g = recipient_bundle["G"]

    donor_p = donor_bundle["P"]
    recipient_p = recipient_bundle["P"]

    if save_to_database:
        if donor_external_id is None or recipient_external_id is None:
            raise ValueError(
                "За запис в SQLite са нужни DONOR ID и RECIPIENT ID."
            )

        database.initialize_database(database_path)
        database.verify_schema_compatibility(database_path)

        save_result = database.save_donor_recipient_typings(
            database_path=database_path,
            donor_external_id=donor_external_id,
            recipient_external_id=recipient_external_id,
            imgthla_version=str(ard.get_db_version()),
            donor_bundle=donor_bundle,
            recipient_bundle=recipient_bundle,
        )

        print_database_save_summary(
            database_path,
            donor_external_id,
            recipient_external_id,
            save_result,
            str(ard.get_db_version()),
        )

        analysis_run = database.create_analysis_run(
            database_path=database_path,
            donor_typing_id=save_result["donor"]["typing_id"],
            recipient_typing_id=save_result["recipient"]["typing_id"],
            imgthla_version=str(ard.get_db_version()),
        )

        print_analysis_run_summary(
            analysis_run,
            output_func=print,
        )

    results = {
        "canonical": {},
        "lgx": {},
        "G": {},
        "P": {},
    }

    for locus in HLA_LOCI:
        # Exact-name comparison се прави върху CANONICAL, не върху RAW.
        results["canonical"][locus] = compare_locus(
            donor_canonical[locus],
            recipient_canonical[locus],
        )

        results["lgx"][locus] = compare_locus(
            donor_lgx[locus],
            recipient_lgx[locus],
        )

        results["G"][locus] = compare_locus(
            donor_g[locus],
            recipient_g[locus],
        )

        results["P"][locus] = compare_locus(
            donor_p[locus],
            recipient_p[locus],
        )

    if save_to_database:
        linked = database.load_analysis_run_typings(
            database_path,
            analysis_run["run_id"],
        )

        save_info = database.save_analysis_results(
            database_path,
            analysis_run["run_id"],
            results,
        )

        print_analysis_results_save_summary(
            {
                "linked": linked,
                "results": results,
                "save_info": save_info,
            },
            output_func=print,
        )

    print()
    print("=" * 92)
    print(
        "HLA DONOR / RECIPIENT COMPARISON — "
        "RAW / CANONICAL / LGX / G / P"
    )
    print("=" * 92)

    total_mismatches = {
        "canonical": 0,
        "lgx": 0,
        "G": 0,
        "P": 0,
    }

    for locus in HLA_LOCI:
        result_canonical = results["canonical"][locus]
        result_lgx = results["lgx"][locus]
        result_g = results["G"][locus]
        result_p = results["P"][locus]

        print()
        print(f"HLA-{locus}")
        print("-" * 92)

        print("RAW INPUT — preserved exactly as entered")
        print("  Donor:    ", ", ".join(donor_raw_profile[locus]))
        print("  Recipient:", ", ".join(recipient_raw_profile[locus]))

        print()
        print("CANONICAL EXACT-NAME — used for exact-name comparison")
        print("  Donor:    ", ", ".join(donor_canonical[locus]))
        print("  Recipient:", ", ".join(recipient_canonical[locus]))
        print_comparison_result("canonical", result_canonical)

        print()
        print("LGX / ARD")
        print("  Donor:    ", ", ".join(donor_lgx[locus]))
        print("  Recipient:", ", ".join(recipient_lgx[locus]))
        print_comparison_result("lgx", result_lgx)

        print()
        print("G GROUP")
        print("  Donor:    ", ", ".join(donor_g[locus]))
        print("  Recipient:", ", ".join(recipient_g[locus]))
        print_comparison_result("G", result_g)

        print()
        print("P GROUP")
        print("  Donor:    ", ", ".join(donor_p[locus]))
        print("  Recipient:", ", ".join(recipient_p[locus]))
        print_comparison_result("P", result_p)

        total_mismatches["canonical"] += result_canonical["mismatch_count"]
        total_mismatches["lgx"] += result_lgx["mismatch_count"]
        total_mismatches["G"] += result_g["mismatch_count"]
        total_mismatches["P"] += result_p["mismatch_count"]

    print()
    print("=" * 92)
    print("TOTAL COPY-SENSITIVE DONOR→RECIPIENT COUNTS")
    print("=" * 92)
    print(
        "Canonical exact-name level:",
        total_mismatches["canonical"],
    )
    print(
        "lgx / ARD level:          ",
        total_mismatches["lgx"],
    )
    print(
        "G-group level:            ",
        total_mismatches["G"],
    )
    print(
        "P-group level:            ",
        total_mismatches["P"],
    )
    print("=" * 92)

    print()
    print(
        "NOTE: RAW values are preserved for traceability. "
        "All calculations use canonical HLA values. "
        "Counts are copy-sensitive donor-only software-comparison counts, "
        "not a clinical organ-allocation HLA mismatch score."
    )

    return 0




# ============================================================
# STEP 13C: LOAD SAVED HLA TYPINGS
# ============================================================

def print_subject_list(subjects, output_func=print):
    output_func("")
    output_func("=" * 84)
    output_func("SAVED HLA SUBJECTS")
    output_func("=" * 84)

    if not subjects:
        output_func("No saved subjects.")
        output_func("=" * 84)
        return

    for subject in subjects:
        output_func(
            f"{subject['external_id']} | "
            f"{subject['subject_type']} | "
            f"subject_id={subject['subject_id']} | "
            f"typings={subject['typing_count']} | "
            f"latest_typing_id={subject['latest_typing_id']} | "
            f"IPD-IMGT/HLA={subject['latest_imgthla_version']}"
        )

    output_func("=" * 84)


def print_saved_typing(loaded, output_func=print):
    subject = loaded["subject"]
    typing = loaded["typing"]
    bundle = loaded["bundle"]

    output_func("")
    output_func("=" * 92)
    output_func("STEP 13C — HLA TYPING LOADED FROM SQLITE")
    output_func("=" * 92)
    output_func(
        f"Subject: {subject['external_id']} "
        f"({subject['subject_type']})"
    )
    output_func(f"subject_id: {subject['subject_id']}")
    output_func(f"typing_id: {typing['typing_id']}")
    output_func(f"IPD-IMGT/HLA version: {typing['imgthla_version']}")
    output_func(f"Typing created_at: {typing['created_at']}")

    for locus in HLA_LOCI:
        output_func("")
        output_func(f"HLA-{locus}")
        output_func("-" * 92)

        for index in range(2):
            output_func(f"Allele {index + 1}")
            output_func(f"  RAW:       {bundle['raw'][locus][index]}")
            output_func(
                f"  CANONICAL: {bundle['canonical'][locus][index]}"
            )
            output_func(f"  LGX:       {bundle['lgx'][locus][index]}")
            output_func(f"  G:         {bundle['G'][locus][index]}")
            output_func(f"  P:         {bundle['P'][locus][index]}")

    output_func("")
    output_func(
        "Loaded from SQLite without changing the stored RAW/CANONICAL/"
        "LGX/G/P values."
    )
    output_func("=" * 92)


def print_subject_typing_history(typings, output_func=print):
    output_func("")
    output_func("=" * 84)
    output_func("HLA TYPING HISTORY")
    output_func("=" * 84)

    if not typings:
        output_func("No typings.")
    else:
        for item in typings:
            output_func(
                f"typing_id={item['typing_id']} | "
                f"IPD-IMGT/HLA={item['imgthla_version']} | "
                f"allele_rows={item['allele_row_count']} | "
                f"created_at={item['created_at']}"
            )

    output_func("=" * 84)


def _extract_optional_value(argv, option, cast=None):
    remaining = list(argv)

    if option not in remaining:
        return None, remaining

    index = remaining.index(option)

    if index + 1 >= len(remaining):
        raise ValueError(f"{option} изисква стойност.")

    value = remaining[index + 1]

    if cast is not None:
        try:
            value = cast(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Невалидна стойност за {option}: {value!r}"
            ) from exc

    del remaining[index:index + 2]
    return value, remaining


# ============================================================
# STEP 13G: DATABASE SCHEMA VERSIONING / MIGRATIONS
# ============================================================

def print_database_schema_status(status, output_func=print):
    output_func("")
    output_func("=" * 100)
    output_func("STEP 13G — DATABASE SCHEMA STATUS")
    output_func("=" * 100)
    output_func(f"Database: {status['database_path']}")
    output_func(f"Exists: {status['exists']}")
    output_func(
        f"Schema version: "
        f"{status['current_version']} / "
        f"{status['required_version']}"
    )
    output_func(f"Current: {status['is_current']}")
    output_func(
        "analysis_results UNIQUE(run_id, level, locus): "
        f"{status['analysis_results_unique_key']}"
    )
    output_func(
        "STEP 20 batch history schema: "
        f"{status.get('batch_history_schema', False)}"
    )

    if status["pending"]:
        output_func("Pending migrations:")

        for item in status["pending"]:
            output_func(
                f"  - {item['version']}: {item['name']}"
            )
    else:
        output_func("Pending migrations: none")

    if status["history"]:
        output_func("Applied migrations:")

        for item in status["history"]:
            output_func(
                f"  - {item['version']}: {item['name']} "
                f"| applied_at={item['applied_at']}"
            )

    output_func("=" * 100)


def print_migration_summary(info, output_func=print):
    output_func("")
    output_func("=" * 100)
    output_func("STEP 13G — DATABASE MIGRATION COMPLETE")
    output_func("=" * 100)
    output_func(f"Database: {info['database_path']}")
    output_func(
        f"Schema version: "
        f"{info['current_version']} / "
        f"{info['required_version']}"
    )
    output_func(
        "analysis_results UNIQUE(run_id, level, locus): "
        f"{info['analysis_results_unique_key']}"
    )
    output_func(
        "STEP 20 batch history schema: "
        f"{info.get('batch_history_schema', False)}"
    )

    if info["applied"]:
        output_func("Applied now:")

        for item in info["applied"]:
            output_func(
                f"  - {item['version']}: {item['name']}"
            )
    else:
        output_func("Applied now: none (database already current)")

    output_func("=" * 100)


# ============================================================
# STEP 13F: EXPORT ANALYSIS RUN TO JSON / CSV
# ============================================================

def print_export_summary(export_info, output_func=print):
    output_func("")
    output_func("=" * 100)
    output_func("STEP 13F — ANALYSIS EXPORT COMPLETE")
    output_func("=" * 100)
    output_func(f"run_id: {export_info['run_id']}")
    output_func(
        f"Saved analysis_result rows represented: "
        f"{export_info['row_count']}"
    )
    output_func(f"Output directory: {export_info['output_dir']}")

    for file_type in ("json", "csv"):
        path = export_info["files"].get(file_type)

        if path is not None:
            output_func(f"{file_type.upper()}: {path}")

    output_func(
        "Export reads the already stored analysis_results; "
        "it does not recalculate HLA reductions."
    )
    output_func("=" * 100)


# ============================================================
# STEP 13E: COMPUTE + SAVE 24 ANALYSIS RESULT ROWS
# ============================================================



def analyze_and_save_existing_run(
    database_path,
    run_id,
):
    """
    Зарежда точно типовете, свързани с run_id,
    изчислява 24 резултата и ги записва в analysis_results.
    """
    linked = database.load_analysis_run_typings(
        database_path,
        run_id,
    )

    results = build_comparison_results_from_bundles(
        linked["donor"]["bundle"],
        linked["recipient"]["bundle"],
    )

    save_info = database.save_analysis_results(
        database_path,
        run_id,
        results,
    )

    return {
        "linked": linked,
        "results": results,
        "save_info": save_info,
    }


def print_analysis_results_save_summary(
    analyzed,
    output_func=print,
):
    linked = analyzed["linked"]
    save_info = analyzed["save_info"]

    output_func("")
    output_func("=" * 100)
    output_func("STEP 13E — ANALYSIS RESULTS SAVED")
    output_func("=" * 100)
    output_func(f"run_id: {save_info['run_id']}")
    output_func(
        f"DONOR: {linked['run']['donor']['external_id']} | "
        f"typing_id={save_info['donor_typing_id']}"
    )
    output_func(
        f"RECIPIENT: {linked['run']['recipient']['external_id']} | "
        f"typing_id={save_info['recipient_typing_id']}"
    )
    output_func(
        f"IPD-IMGT/HLA version: {save_info['imgthla_version']}"
    )
    output_func("Saved analysis_result rows: 24")
    output_func(
        "Levels: CANONICAL / LGX / G / P × "
        "A / B / C / DRB1 / DQB1 / DPB1"
    )
    output_func(
        "The analysis uses the representations already stored in SQLite; "
        "it does not re-reduce the alleles with the current py-ard database."
    )
    output_func("=" * 100)


def print_loaded_analysis_results(
    loaded,
    output_func=print,
):
    run = loaded["run"]
    results = loaded["results"]

    output_func("")
    output_func("=" * 110)
    output_func("SAVED ANALYSIS RESULTS")
    output_func("=" * 110)
    output_func(
        f"run_id={run['run_id']} | "
        f"{run['donor']['external_id']} "
        f"(typing {run['donor_typing_id']}) -> "
        f"{run['recipient']['external_id']} "
        f"(typing {run['recipient_typing_id']})"
    )
    output_func(
        f"IPD-IMGT/HLA={run['imgthla_version']} | "
        f"rows={loaded['row_count']}"
    )

    labels = {
        "canonical": "CANONICAL",
        "lgx": "LGX",
        "G": "G",
        "P": "P",
    }

    for locus in HLA_LOCI:
        output_func("")
        output_func(f"HLA-{locus}")
        output_func("-" * 110)

        for result_key in ("canonical", "lgx", "G", "P"):
            result = results[result_key][locus]

            output_func(
                f"{labels[result_key]} | "
                f"shared={result['shared']} | "
                f"donor_only={result['donor_only']} | "
                f"recipient_only={result['recipient_only']} | "
                f"counts="
                f"{result['shared_count']}/"
                f"{result['mismatch_count']}/"
                f"{result['recipient_only_count']}"
            )

    output_func("")
    output_func(
        "Counts are copy-sensitive software-comparison counts, "
        "not a clinical organ-allocation score."
    )
    output_func("=" * 110)


# ============================================================
# STEP 13D: ANALYSIS RUN CLI / DISPLAY
# ============================================================

def print_analysis_run_summary(run, output_func=print):
    output_func("")
    output_func("=" * 92)
    output_func("STEP 13D — ANALYSIS RUN SAVED")
    output_func("=" * 92)
    output_func(f"run_id: {run['run_id']}")
    output_func(f"IPD-IMGT/HLA version: {run['imgthla_version']}")
    output_func(
        f"DONOR: {run['donor']['external_id']} | "
        f"typing_id={run['donor']['typing_id']}"
    )
    output_func(
        f"RECIPIENT: {run['recipient']['external_id']} | "
        f"typing_id={run['recipient']['typing_id']}"
    )
    output_func(
        "STEP 13D stores only the DONOR↔RECIPIENT typing link. "
        "analysis_results are not saved yet."
    )
    output_func("=" * 92)


def print_analysis_run_list(runs, output_func=print):
    output_func("")
    output_func("=" * 100)
    output_func("SAVED ANALYSIS RUNS")
    output_func("=" * 100)

    if not runs:
        output_func("No saved analysis runs.")
        output_func("=" * 100)
        return

    for run in runs:
        output_func(
            f"run_id={run['run_id']} | "
            f"{run['donor_external_id']} "
            f"(typing {run['donor_typing_id']}) -> "
            f"{run['recipient_external_id']} "
            f"(typing {run['recipient_typing_id']}) | "
            f"IPD-IMGT/HLA={run['imgthla_version']} | "
            f"results={run['analysis_result_count']} | "
            f"created_at={run['created_at']}"
        )

    output_func("=" * 100)


def print_loaded_analysis_run(run, output_func=print):
    output_func("")
    output_func("=" * 92)
    output_func("ANALYSIS RUN")
    output_func("=" * 92)
    output_func(f"run_id: {run['run_id']}")
    output_func(f"created_at: {run['created_at']}")
    output_func(f"IPD-IMGT/HLA version: {run['imgthla_version']}")
    output_func(
        f"DONOR: {run['donor']['external_id']} | "
        f"typing_id={run['donor_typing_id']}"
    )
    output_func(
        f"RECIPIENT: {run['recipient']['external_id']} | "
        f"typing_id={run['recipient_typing_id']}"
    )
    output_func(
        f"Saved analysis_result rows: "
        f"{run['analysis_result_count']}"
    )
    output_func("=" * 92)


def _extract_pair_values(argv, option):
    remaining = list(argv)

    if option not in remaining:
        return None, remaining

    index = remaining.index(option)

    if index + 2 >= len(remaining):
        raise ValueError(
            f"{option} изисква две стойности: DONOR_ID RECIPIENT_ID."
        )

    first = remaining[index + 1]
    second = remaining[index + 2]

    del remaining[index:index + 3]

    return (first, second), remaining

def _extract_database_path(argv):
    """
    Чете --db PATH от argv без външни зависимости.
    Връща (database_path, remaining_args).
    """
    remaining = list(argv)
    database_path = database.DEFAULT_DATABASE_PATH

    if "--db" in remaining:
        index = remaining.index("--db")

        if index + 1 >= len(remaining):
            raise ValueError("--db изисква път до SQLite файл.")

        database_path = Path(remaining[index + 1])
        del remaining[index:index + 2]

    return database_path, remaining




def legacy_main(argv=None, input_func=input, output_func=print):
    """
    STEP 13G entry point.

    New analysis-run operations:
        --create-analysis DONOR_ID RECIPIENT_ID
        --donor-typing-id N
        --recipient-typing-id N
        --list-analyses
        --show-analysis RUN_ID

    STEP 13C read operations remain available:
        --list-subjects
        --history EXTERNAL_ID
        --load EXTERNAL_ID
        --typing-id N

    STEP 13B interactive save remains available.
    """
    if argv is None:
        argv = sys.argv[1:]

    try:
        database_path, argv = _extract_database_path(argv)

        typing_id, argv = _extract_optional_value(
            argv,
            "--typing-id",
            cast=int,
        )
        load_external_id, argv = _extract_optional_value(
            argv,
            "--load",
        )
        history_external_id, argv = _extract_optional_value(
            argv,
            "--history",
        )

        donor_typing_id, argv = _extract_optional_value(
            argv,
            "--donor-typing-id",
            cast=int,
        )
        recipient_typing_id, argv = _extract_optional_value(
            argv,
            "--recipient-typing-id",
            cast=int,
        )
        show_analysis_id, argv = _extract_optional_value(
            argv,
            "--show-analysis",
            cast=int,
        )
        analyze_run_id, argv = _extract_optional_value(
            argv,
            "--analyze-run",
            cast=int,
        )
        show_results_id, argv = _extract_optional_value(
            argv,
            "--show-results",
            cast=int,
        )
        export_analysis_id, argv = _extract_optional_value(
            argv,
            "--export-analysis",
            cast=int,
        )
        export_format, argv = _extract_optional_value(
            argv,
            "--format",
        )
        export_output_dir, argv = _extract_optional_value(
            argv,
            "--output-dir",
        )
        analysis_pair, argv = _extract_pair_values(
            argv,
            "--create-analysis",
        )

    except ValueError as exc:
        output_func(f"ERROR: {exc}")
        return 2

    if "--help" in argv or "-h" in argv:
        output_func("Usage:")
        output_func(
            "  python hla_match_step13g_fixed.py --db-status"
        )
        output_func(
            "      Shows current and pending schema migrations."
        )
        output_func("")
        output_func(
            "  python hla_match_step13g_fixed.py --migrate-db"
        )
        output_func(
            "      Applies pending migrations."
        )
        output_func("")
        output_func(
            "  python hla_match_step13d_fixed.py "
            "--create-analysis DONOR-001 RECIP-001"
        )
        output_func(
            "      Creates an analysis_run using the latest typings."
        )
        output_func("")
        output_func(
            "  python hla_match_step13d_fixed.py "
            "--create-analysis DONOR-001 RECIP-001 "
            "--donor-typing-id 1 --recipient-typing-id 2"
        )
        output_func(
            "      Creates an analysis_run using specific typings."
        )
        output_func("")
        output_func(
            "  python hla_match_step13d_fixed.py --list-analyses"
        )
        output_func("      Lists saved analysis runs.")
        output_func("")
        output_func(
            "  python hla_match_step13d_fixed.py --show-analysis 1"
        )
        output_func("      Shows one saved analysis run.")
        output_func("")
        output_func(
            "  python hla_match_step13e_fixed.py --analyze-run 1"
        )
        output_func(
            "      Computes and saves exactly 24 analysis_result rows."
        )
        output_func("")
        output_func(
            "  python hla_match_step13e_fixed.py --show-results 1"
        )
        output_func(
            "      Loads and displays the 24 saved result rows."
        )
        output_func("")
        output_func(
            "  python hla_match_step13g_fixed.py --export-analysis 1"
        )
        output_func(
            "      Exports analysis_run 1 to JSON + CSV."
        )
        output_func("")
        output_func(
            "  python hla_match_step13g_fixed.py "
            "--export-analysis 1 --format json"
        )
        output_func(
            "      Exports only JSON. Formats: json, csv, both."
        )
        output_func("")
        output_func(
            "  Optional: --output-dir exports --overwrite"
        )
        output_func("")
        output_func(
            "  STEP 13C options remain available: "
            "--list-subjects, --history, --load."
        )
        output_func(
            "  Add --db PATH to select another SQLite database."
        )
        return 0

    # --------------------------------------------------------
    # STEP 13G schema status / migration commands
    # --------------------------------------------------------
    if "--db-status" in argv:
        status = database.get_database_schema_status(
            database_path
        )
        print_database_schema_status(
            status,
            output_func=output_func,
        )
        return 0

    if "--migrate-db" in argv:
        try:
            info = database.migrate_database(database_path)
        except database.MigrationError as exc:
            output_func("")
            output_func("DATABASE MIGRATION ERROR")
            output_func(str(exc))
            return 6

        print_migration_summary(
            info,
            output_func=output_func,
        )
        return 0

    # Normal commands auto-migrate before accessing the DB.
    try:
        database.migrate_database(database_path)
        database.verify_database_is_current(database_path)
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

    try:
        # ----------------------------------------------------
        # STEP 13D operations
        # ----------------------------------------------------
        if export_analysis_id is not None:
            export_info = exporters.export_analysis(
                database_path=database_path,
                run_id=export_analysis_id,
                output_dir=(
                    export_output_dir
                    if export_output_dir is not None
                    else exporters.DEFAULT_EXPORT_DIR
                ),
                export_format=(
                    export_format
                    if export_format is not None
                    else "both"
                ),
                overwrite=("--overwrite" in argv),
            )

            print_export_summary(
                export_info,
                output_func=output_func,
            )
            return 0

        if export_format is not None or export_output_dir is not None:
            output_func(
                "ERROR: --format и --output-dir се използват "
                "с --export-analysis."
            )
            return 2

        if "--overwrite" in argv:
            output_func(
                "ERROR: --overwrite се използва с --export-analysis."
            )
            return 2

        if analyze_run_id is not None:
            analyzed = analyze_and_save_existing_run(
                database_path,
                analyze_run_id,
            )
            print_analysis_results_save_summary(
                analyzed,
                output_func=output_func,
            )
            return 0

        if show_results_id is not None:
            loaded_results = database.load_analysis_results(
                database_path,
                show_results_id,
            )
            print_loaded_analysis_results(
                loaded_results,
                output_func=output_func,
            )
            return 0

        if "--list-analyses" in argv:
            runs = database.list_analysis_runs(database_path)
            print_analysis_run_list(
                runs,
                output_func=output_func,
            )
            return 0

        if show_analysis_id is not None:
            run = database.load_analysis_run(
                database_path,
                show_analysis_id,
            )
            print_loaded_analysis_run(
                run,
                output_func=output_func,
            )
            return 0

        if analysis_pair is not None:
            donor_external_id, recipient_external_id = analysis_pair

            run = database.create_analysis_run_for_subjects(
                database_path=database_path,
                donor_external_id=donor_external_id,
                recipient_external_id=recipient_external_id,
                donor_typing_id=donor_typing_id,
                recipient_typing_id=recipient_typing_id,
            )

            print_analysis_run_summary(
                run,
                output_func=output_func,
            )
            return 0

        if donor_typing_id is not None or recipient_typing_id is not None:
            output_func(
                "ERROR: --donor-typing-id и --recipient-typing-id "
                "се използват с --create-analysis."
            )
            return 2

        # ----------------------------------------------------
        # STEP 13C operations
        # ----------------------------------------------------
        if "--list-subjects" in argv:
            subjects = database.list_subjects(database_path)
            print_subject_list(
                subjects,
                output_func=output_func,
            )
            return 0

        if history_external_id is not None:
            typings = database.list_subject_typings(
                database_path,
                history_external_id,
            )
            print_subject_typing_history(
                typings,
                output_func=output_func,
            )
            return 0

        if load_external_id is not None:
            loaded = database.load_subject_typing(
                database_path=database_path,
                external_id=load_external_id,
                typing_id=typing_id,
            )
            print_saved_typing(
                loaded,
                output_func=output_func,
            )
            return 0

        if typing_id is not None:
            output_func(
                "ERROR: --typing-id може да се използва само с --load."
            )
            return 2

    except (
        database.DatabaseSchemaError,
        database.SubjectNotFoundError,
        database.TypingNotFoundError,
        database.IncompleteTypingError,
        database.AnalysisRunNotFoundError,
        database.AnalysisTypingRoleError,
        database.AnalysisVersionMismatchError,
        database.AnalysisResultsError,
        database.AnalysisResultsNotFoundError,
        exporters.ExportError,
        ValueError,
    ) as exc:
        output_func("")
        output_func("DATABASE / ANALYSIS ERROR")
        output_func(str(exc))
        return 5

    # --------------------------------------------------------
    # Existing interactive/save workflow.
    # It now also creates an analysis_run automatically.
    # --------------------------------------------------------
    save_to_database = "--no-save" not in argv
    demo_mode = "--demo" in argv

    if demo_mode:
        output_func("STEP 13G: DEMO / SAVE MODE")
        donor_external_id = "DONOR-DEMO-001"
        recipient_external_id = "RECIP-DEMO-001"
        donor_input = clone_profile(donor_raw)
        recipient_input = clone_profile(recipient_raw)
    else:
        output_func("STEP 13G: INTERACTIVE HLA INPUT / SAVE MODE")
        output_func(
            "Използвайте pseudonymous IDs, например "
            "DONOR-001 и RECIP-001."
        )
        output_func(
            "Всеки HLA алел се валидира чрез "
            "py-ard / IPD-IMGT/HLA 3.65.0."
        )

        try:
            if save_to_database:
                donor_external_id = prompt_external_id(
                    "DONOR",
                    input_func=input_func,
                    output_func=output_func,
                )
            else:
                donor_external_id = None

            donor_input = input_person(
                "DONOR",
                input_func=input_func,
                output_func=output_func,
            )

            if save_to_database:
                recipient_external_id = prompt_external_id(
                    "RECIPIENT",
                    input_func=input_func,
                    output_func=output_func,
                )
            else:
                recipient_external_id = None

            recipient_input = input_person(
                "RECIPIENT",
                input_func=input_func,
                output_func=output_func,
            )

        except InputCancelled:
            output_func("")
            output_func("Въвеждането е прекратено от потребителя.")
            return 1

    try:
        return run_workflow(
            donor_input,
            recipient_input,
            donor_external_id=donor_external_id,
            recipient_external_id=recipient_external_id,
            database_path=database_path,
            save_to_database=save_to_database,
        )
    except (
        database.DatabaseSchemaError,
        database.SubjectTypeConflictError,
        database.TypingNotFoundError,
        database.IncompleteTypingError,
        database.AnalysisTypingRoleError,
        database.AnalysisVersionMismatchError,
        database.AnalysisResultsError,
        database.AnalysisResultsNotFoundError,
        exporters.ExportError,
        ValueError,
    ) as exc:
        output_func("")
        output_func("SAVE / ANALYSIS ERROR")
        output_func(str(exc))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())

# ============================================================
# STEP 20: PERSISTENT BATCH HISTORY DISPLAY
# ============================================================

def print_persistent_batch_list(rows, output_func=print):
    output_func("")
    output_func("=" * 118)
    output_func("STEP 20 — PERSISTENT BATCH HISTORY")
    output_func("=" * 118)

    if not rows:
        output_func("No persistent batch runs saved.")
        output_func("=" * 118)
        return

    for row in rows:
        sort_text = "none"

        if row["sort_level"] is not None:
            sort_text = (
                f"{row['sort_level']}/"
                f"{row['sort_metric']}/"
                f"{row['sort_order']}"
            )

        output_func(
            f"batch_id={row['batch_id']} | "
            f"{row['direction']} anchor={row['anchor_external_id']} "
            f"(typing {row['anchor_typing_id']}) | "
            f"pairs={row['pair_count']} | items={row['item_count']} | "
            f"results={row['analysis_result_count']} | sort={sort_text} | "
            f"IPD-IMGT/HLA={row['imgthla_version']} | "
            f"created_at={row['created_at']}"
        )

    output_func("=" * 118)


def print_persistent_batch_detail(saved, output_func=print):
    output_func("")
    output_func("=" * 118)
    output_func("STEP 20 — PERSISTENT BATCH")
    output_func("=" * 118)
    output_func(f"batch_id: {saved['batch_id']}")
    output_func(
        f"Direction: {saved['direction']} | "
        f"anchor={saved['anchor_external_id']} "
        f"(typing {saved['anchor_typing_id']})"
    )
    output_func(
        f"IPD-IMGT/HLA={saved['imgthla_version']} | "
        f"pairs={saved['pair_count']} | "
        f"skipped={saved['skipped_count']} | "
        f"created_at={saved['created_at']}"
    )

    if saved["sort_level"] is None:
        output_func("Software ordering: none")
    else:
        output_func(
            "Software ordering: "
            f"level={saved['sort_level']} | "
            f"metric={saved['sort_metric']} | "
            f"order={saved['sort_order']} | "
            f"requested={saved['requested_sort_order']} | "
            f"original_display_limit={saved['display_limit']}"
        )

    output_func("-" * 118)

    for item in saved["items"]:
        rank_text = ""
        if item["software_rank"] is not None:
            rank_text = (
                f" | software_position={item['software_position']}"
                f" | software_rank={item['software_rank']}"
                f" | criterion={item['criterion_value']}"
            )

        output_func(
            f"item={item['item_position']} | run_id={item['analysis_run_id']} | "
            f"{item['donor_external_id']} (typing {item['donor_typing_id']}) -> "
            f"{item['recipient_external_id']} (typing {item['recipient_typing_id']})"
            f"{rank_text} | results={item['analysis_result_count']}"
        )

    output_func("=" * 118)


def print_persistent_batch_results(batch, output_func=print):
    output_func("")
    output_func("=" * 118)
    output_func("STEP 20 — RELOADED PERSISTENT BATCH RESULTS")
    output_func("=" * 118)
    output_func(
        f"batch_id={batch['batch_id']} | loaded entirely from SQLite; "
        "py-ard reductions were not recalculated."
    )
    print_batch_analysis_summary(
        batch,
        output_func=output_func,
    )


def print_persistent_batch_export_summary(
    batch_id,
    export_info,
    output_func=print,
):
    output_func("")
    output_func("=" * 118)
    output_func("STEP 20 — PERSISTENT BATCH RE-EXPORT")
    output_func("=" * 118)
    output_func(f"batch_id: {batch_id}")
    output_func(
        "Source: stored batch metadata + stored analysis_results in SQLite."
    )
    print_batch_export_summary(
        export_info,
        output_func=output_func,
    )


# ============================================================
# STEP 19: BATCH JSON / CSV EXPORT DISPLAY
# ============================================================

def print_batch_export_summary(
    export_info,
    output_func=print,
):
    output_func("")
    output_func("=" * 118)
    output_func(
        "STEP 19 — BATCH EXPORT COMPLETE"
    )
    output_func("=" * 118)
    output_func(
        f"Export name: {export_info['export_name']}"
    )
    output_func(
        f"Format: {export_info['format'].upper()}"
    )
    output_func(
        f"Exported pairs: {export_info['pair_count']}"
    )
    output_func(
        "CSV data rows represented: "
        f"{export_info['csv_data_row_count']} "
        "(24 rows per pair)"
    )
    output_func(
        f"Source batch save mode: "
        f"{'SAVE' if export_info['source_save_mode'] else 'NO SAVE'}"
    )
    output_func(
        f"Output directory: "
        f"{Path(export_info['output_dir']).resolve()}"
    )

    for kind, path in export_info["files"].items():
        output_func(
            f"{kind.upper()}: {Path(path).resolve()}"
        )

    ordering = export_info.get(
        "software_ordering"
    )

    if ordering:
        output_func(
            "Export ordering: "
            f"level={ordering['level_label']} | "
            f"metric={ordering['metric_key']} | "
            f"order={ordering['order'].upper()}"
        )
        output_func(
            "Export scope: ALL software-ordered pairs. "
            "CLI --limit/--display-limit does not truncate export."
        )
    else:
        output_func(
            "Export scope: ALL computed batch pairs "
            "in the ordinary STEP 17 order."
        )

    output_func(
        "Exporting does not recalculate py-ard reductions and "
        "does not create analysis_runs by itself."
    )
    output_func(
        "The exported counts remain NON-CLINICAL "
        "copy-sensitive software-comparison data."
    )
    output_func("=" * 118)


# ============================================================
# STEP 17: BATCH DONOR↔RECIPIENT ANALYSIS DISPLAY
# ============================================================

def print_batch_analysis_summary(
    batch,
    output_func=print,
):
    ordering = batch.get("software_ordering")

    output_func("")
    output_func("=" * 118)

    if ordering:
        output_func(
            "STEP 18 — BATCH SOFTWARE ORDERING "
            "(NON-CLINICAL)"
        )
    else:
        output_func(
            "STEP 17 — BATCH DONOR↔RECIPIENT ANALYSIS"
        )

    output_func("=" * 118)
    output_func(
        f"Direction: one {batch['anchor_role']} vs many "
        f"{batch['candidate_role']} subjects"
    )
    output_func(
        f"Anchor: {batch['anchor_external_id']} | "
        f"typing_id={batch['anchor_typing_id']} | "
        f"IPD-IMGT/HLA={batch['imgthla_version']}"
    )
    output_func(
        f"Mode: {'SAVE' if batch['save'] else 'NO SAVE'} | "
        f"pairs={batch['pair_count']} | "
        f"skipped={batch['skipped_count']}"
    )

    if batch.get("batch_id") is not None:
        output_func(
            f"Persistent batch_id: {batch['batch_id']} | "
            f"created_at={batch.get('batch_created_at')}"
        )

    if ordering:
        limit_text = (
            str(ordering["display_limit"])
            if ordering["display_limit"] is not None
            else "none"
        )

        output_func(
            "Software ordering: "
            f"level={ordering['level_label']} | "
            f"metric={ordering['metric_key']} | "
            f"order={ordering['order'].upper()} | "
            f"displayed={ordering['displayed_pair_count']}/"
            f"{ordering['total_pair_count']} | "
            f"display_limit={limit_text}"
        )

        if batch["save"]:
            output_func(
                "Persistence scope: ALL eligible pairs were saved "
                "before display ordering/limiting."
            )

    output_func("-" * 118)

    for row in batch["rows"]:
        run_part = (
            f"run_id={row['run_id']}"
            if row["run_id"] is not None
            else "run_id=not-saved"
        )

        if ordering:
            order_info = row["software_order"]
            prefix = (
                f"[position={order_info['position']} | "
                f"software_rank={order_info['rank']} | "
                f"{order_info['metric_key']}="
                f"{order_info['criterion_value']}] "
            )
        else:
            prefix = ""

        output_func(
            prefix
            + f"{row['donor_external_id']} "
            f"(typing {row['donor_typing_id']}) -> "
            f"{row['recipient_external_id']} "
            f"(typing {row['recipient_typing_id']}) | "
            f"{run_part}"
        )

        pieces = []

        for level in ("canonical", "lgx", "G", "P"):
            totals = row["summary"][level]
            label = {
                "canonical": "CANONICAL",
                "lgx": "LGX",
                "G": "G",
                "P": "P",
            }[level]

            pieces.append(
                f"{label}: shared={totals['shared_count']}, "
                f"donor_only={totals['donor_only_count']}, "
                f"recipient_only={totals['recipient_only_count']}"
            )

        output_func("  " + " | ".join(pieces))

    if batch["skipped"]:
        output_func("-" * 118)
        output_func("Skipped candidates:")

        for item in batch["skipped"]:
            output_func(
                f"  - {item['external_id']}: {item['reason']}"
            )

    output_func("-" * 118)

    if ordering:
        output_func(
            "STEP 18 ordering is ONLY a deterministic sort of one "
            "selected software count. Equal values are ties; external_id "
            "is used only for stable display order."
        )

    output_func(
        "Totals are copy-sensitive software-comparison counts across "
        "A/B/C/DRB1/DQB1/DPB1. They are NOT a clinical organ-allocation, "
        "crossmatch, DSA, eplet, cPRA, or transplant-compatibility score."
    )

    if batch["save"]:
        output_func(
            "The persisted batch is atomic: if one pair fails during "
            "database save, all analysis_runs/results from that batch "
            "are rolled back."
        )
    else:
        output_func(
            "NO SAVE mode did not create analysis_runs or "
            "analysis_results."
        )

    output_func("=" * 118)


# ============================================================
# STEP 16: HLA TYPING FILE IMPORT DISPLAY
# ============================================================

def print_import_summary(
    import_info,
    output_func=print,
):
    output_func("")
    output_func("=" * 100)
    output_func("STEP 16 — HLA TYPING FILE IMPORT")
    output_func("=" * 100)
    output_func(
        f"Source: {Path(import_info['source_path']).resolve()}"
    )
    output_func(
        f"Format: {import_info['format'].upper()}"
    )
    output_func(
        f"Records found: {import_info['record_count']}"
    )
    output_func(
        f"Validated with py-ard: {import_info['validated_count']}"
    )

    if import_info["dry_run"]:
        output_func("Mode: DRY RUN — database was not changed")
        output_func("Saved typings: 0")
    else:
        output_func("Mode: IMPORT")
        output_func(
            f"Saved typings: {import_info['saved_count']}"
        )

        for item in import_info["saved"]:
            output_func(
                f"  - {item['external_id']} | "
                f"{item['subject_type']} | "
                f"subject_id={item['subject_id']} | "
                f"typing_id={item['typing_id']} | "
                f"IPD-IMGT/HLA={item['imgthla_version']}"
            )

    output_func(
        "RAW values are preserved; CANONICAL/LGX/G/P are "
        "computed with the active py-ard database before save."
    )
    output_func(
        "Batch SQL save is atomic: one failing record rolls "
        "back the whole file."
    )
    output_func("=" * 100)


# ============================================================
# STEP 15: COMMAND-BASED CLI DISPATCH
# ============================================================

STEP15_COMMAND_GROUPS = frozenset({
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
    "doctor",
    "audit",
})


def uses_command_style(argv):
    """
    Detects the new STEP 15 command syntax.

    Supports:
        python main.py db status
        python main.py --db other.db db status
        python main.py --help

    Legacy flags such as --db-status remain routed to legacy_main().
    """
    args = list(argv)
    index = 0

    while index < len(args):
        token = args[index]

        if token == "--db":
            index += 2
            continue

        if token in {"--help", "-h"}:
            return True

        if token.startswith("-"):
            return False

        return token in STEP15_COMMAND_GROUPS

    return False


def main(argv=None, input_func=input, output_func=print):
    """
    Public CLI entry point.

    STEP 15 command syntax is preferred.
    STEP 13/14 flag syntax remains fully backward compatible.
    """
    if argv is None:
        argv = sys.argv[1:]

    if uses_command_style(argv):
        from command_cli import run_command_cli

        return run_command_cli(
            argv=argv,
            input_func=input_func,
            output_func=output_func,
        )

    return legacy_main(
        argv=argv,
        input_func=input_func,
        output_func=output_func,
    )


if __name__ == "__main__":
    raise SystemExit(main())
