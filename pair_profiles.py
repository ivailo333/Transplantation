from __future__ import annotations

import csv
import json
from pathlib import Path

import analyses
import hla_comparison
import typings
from config import HLA_LOCI

PROFILE_SCHEMA = "hla-pair-profile-v1"
PROFILE_LEVELS = ("canonical", "lgx", "G", "P")
LEVEL_LABELS = {"canonical": "CANONICAL", "lgx": "LGX", "G": "G", "P": "P"}
DEFAULT_EXPORT_DIR = Path(__file__).with_name("exports") / "pairs"
VALID_EXPORT_FORMATS = ("json", "csv", "both")
CSV_COLUMNS = (
    "source","run_id","donor_external_id","donor_typing_id",
    "recipient_external_id","recipient_typing_id","imgthla_version",
    "level","locus","shared_count","donor_only_count","recipient_only_count",
    "shared_values_json","donor_only_values_json","recipient_only_values_json",
)

class PairProfileError(ValueError):
    pass

class PairProfileExportError(RuntimeError):
    pass

class PairProfileExportExistsError(PairProfileExportError):
    pass

def normalize_level(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise PairProfileError("level трябва да бъде текст.")
    mapping = {"canonical":"canonical","lgx":"lgx","g":"G","p":"P"}
    key = value.strip().lower()
    if key not in mapping:
        raise PairProfileError("Невалидно level. Допустими: canonical, lgx, G, P.")
    return mapping[key]

def normalize_locus(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise PairProfileError("locus трябва да бъде текст.")
    locus = value.strip().upper()
    if locus not in HLA_LOCI:
        raise PairProfileError("Невалиден HLA locus. Допустими: " + ", ".join(HLA_LOCI) + ".")
    return locus

def normalize_export_format(value):
    if value is None:
        return "both"
    if not isinstance(value, str):
        raise PairProfileError("export format трябва да бъде текст.")
    value = value.strip().lower()
    if value not in VALID_EXPORT_FORMATS:
        raise PairProfileError("Невалиден export format. Допустими: json, csv, both.")
    return value

def _copy_result(result):
    return {
        "shared": list(result["shared"]),
        "donor_only": list(result["donor_only"]),
        "recipient_only": list(result["recipient_only"]),
        "shared_count": int(result["shared_count"]),
        "donor_only_count": int(result["mismatch_count"]),
        "recipient_only_count": int(result["recipient_only_count"]),
    }

def _profile_results(results, level=None, locus=None):
    level = normalize_level(level)
    locus = normalize_locus(locus)
    levels = [level] if level else list(PROFILE_LEVELS)
    loci = [locus] if locus else list(HLA_LOCI)
    out = {}
    for lv in levels:
        out[lv] = {}
        for lc in loci:
            try:
                out[lv][lc] = _copy_result(results[lv][lc])
            except KeyError as exc:
                raise PairProfileError(f"Липсва comparison result за {LEVEL_LABELS[lv]}/{lc}.") from exc
    return out

def _totals(results):
    return {
        level: {
            "shared_count": sum(v["shared_count"] for v in loci.values()),
            "donor_only_count": sum(v["donor_only_count"] for v in loci.values()),
            "recipient_only_count": sum(v["recipient_only_count"] for v in loci.values()),
            "loci_count": len(loci),
        }
        for level, loci in results.items()
    }

def build_live_pair_profile(database_path, donor_external_id, recipient_external_id,
                            *, donor_typing_id=None, recipient_typing_id=None,
                            level=None, locus=None):
    donor = typings.load_subject_typing(
        database_path=database_path, external_id=donor_external_id,
        subject_type="DONOR", typing_id=donor_typing_id,
    )
    recipient = typings.load_subject_typing(
        database_path=database_path, external_id=recipient_external_id,
        subject_type="RECIPIENT", typing_id=recipient_typing_id,
    )
    dv = donor["typing"]["imgthla_version"]
    rv = recipient["typing"]["imgthla_version"]
    if dv != rv:
        raise PairProfileError("DONOR и RECIPIENT typing използват различни IPD-IMGT/HLA версии.")
    comparison = hla_comparison.build_comparison_results_from_bundles(
        donor["bundle"], recipient["bundle"]
    )
    filtered = _profile_results(comparison, level=level, locus=locus)
    return {
        "schema": PROFILE_SCHEMA,
        "source": "LIVE-STORED-TYPINGS",
        "run_id": None,
        "donor": {"external_id": donor["subject"]["external_id"], "typing_id": donor["typing"]["typing_id"]},
        "recipient": {"external_id": recipient["subject"]["external_id"], "typing_id": recipient["typing"]["typing_id"]},
        "imgthla_version": dv,
        "analysis_created_at": None,
        "filter": {"level": normalize_level(level), "locus": normalize_locus(locus)},
        "results": filtered,
        "totals": _totals(filtered),
        "recalculated_py_ard": False,
        "clinical_score": False,
    }

def build_stored_run_profile(database_path, run_id, *, level=None, locus=None):
    loaded = analyses.load_analysis_results(database_path=database_path, run_id=run_id, require_complete=True)
    run = loaded["run"]
    filtered = _profile_results(loaded["results"], level=level, locus=locus)
    return {
        "schema": PROFILE_SCHEMA,
        "source": "STORED-ANALYSIS-RUN",
        "run_id": run["run_id"],
        "donor": {"external_id": run["donor"]["external_id"], "typing_id": run["donor_typing_id"]},
        "recipient": {"external_id": run["recipient"]["external_id"], "typing_id": run["recipient_typing_id"]},
        "imgthla_version": run["imgthla_version"],
        "analysis_created_at": run["created_at"],
        "filter": {"level": normalize_level(level), "locus": normalize_locus(locus)},
        "results": filtered,
        "totals": _totals(filtered),
        "recalculated_py_ard": False,
        "clinical_score": False,
    }

def render_pair_profile(profile):
    lines = [
        "="*112, "STEP 23 — PAIR COMPARISON PROFILE", "="*112,
        f"Source: {profile['source']}",
        f"DONOR: {profile['donor']['external_id']} | typing_id={profile['donor']['typing_id']}",
        f"RECIPIENT: {profile['recipient']['external_id']} | typing_id={profile['recipient']['typing_id']}",
        f"IPD-IMGT/HLA version: {profile['imgthla_version']}",
    ]
    if profile.get("run_id") is not None:
        lines.append(f"run_id: {profile['run_id']} | created_at={profile['analysis_created_at']}")
    lf = profile["filter"]["level"]
    loc = profile["filter"]["locus"]
    lines.append(f"Filter: level={LEVEL_LABELS[lf] if lf else 'ALL'} | locus={loc or 'ALL'}")
    lines.append("-"*112)
    for level in PROFILE_LEVELS:
        if level not in profile["results"]:
            continue
        lines += [LEVEL_LABELS[level], "-"*112]
        for locus in HLA_LOCI:
            if locus not in profile["results"][level]:
                continue
            r = profile["results"][level][locus]
            lines.append(
                f"HLA-{locus} | shared={r['shared']} | donor_only={r['donor_only']} | "
                f"recipient_only={r['recipient_only']} | counts="
                f"{r['shared_count']}/{r['donor_only_count']}/{r['recipient_only_count']}"
            )
        t = profile["totals"][level]
        lines.append(
            f"{LEVEL_LABELS[level]} TOTAL | shared={t['shared_count']} | "
            f"donor_only={t['donor_only_count']} | recipient_only={t['recipient_only_count']} | loci={t['loci_count']}"
        )
        lines.append("-"*112)
    lines += [
        "Loaded/compared from stored SQLite representations; py-ard reductions were NOT recalculated.",
        "STEP 23 output is NON-CLINICAL software-comparison data.",
        "It is NOT an organ-allocation score, virtual crossmatch, DSA, eplet, cPRA, or transplant-compatibility decision.",
        "="*112,
    ]
    return "\n".join(lines)

def iter_csv_rows(profile):
    for level in PROFILE_LEVELS:
        if level not in profile["results"]:
            continue
        for locus in HLA_LOCI:
            if locus not in profile["results"][level]:
                continue
            r = profile["results"][level][locus]
            yield {
                "source": profile["source"], "run_id": profile["run_id"],
                "donor_external_id": profile["donor"]["external_id"], "donor_typing_id": profile["donor"]["typing_id"],
                "recipient_external_id": profile["recipient"]["external_id"], "recipient_typing_id": profile["recipient"]["typing_id"],
                "imgthla_version": profile["imgthla_version"], "level": LEVEL_LABELS[level], "locus": locus,
                "shared_count": r["shared_count"], "donor_only_count": r["donor_only_count"],
                "recipient_only_count": r["recipient_only_count"],
                "shared_values_json": json.dumps(r["shared"], ensure_ascii=False),
                "donor_only_values_json": json.dumps(r["donor_only"], ensure_ascii=False),
                "recipient_only_values_json": json.dumps(r["recipient_only"], ensure_ascii=False),
            }

def default_export_name(profile):
    if profile.get("run_id") is not None:
        return f"pair_run_{profile['run_id']}"
    return f"pair_{profile['donor']['external_id']}_to_{profile['recipient']['external_id']}"

def export_pair_profile(profile, *, output_dir=DEFAULT_EXPORT_DIR, export_format="both",
                        export_name=None, overwrite=False):
    export_format = normalize_export_format(export_format)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    name = (export_name or default_export_name(profile)).strip()
    if not name:
        raise PairProfileError("export_name не може да бъде празно.")
    targets = {}
    if export_format in ("json","both"):
        targets["json"] = output_dir / f"{name}.json"
    if export_format in ("csv","both"):
        targets["csv"] = output_dir / f"{name}.csv"
    if not overwrite:
        existing = [p for p in targets.values() if p.exists()]
        if existing:
            raise PairProfileExportExistsError(
                "STEP 23 export файл вече съществува. Използвайте --overwrite: "
                + ", ".join(str(p) for p in existing)
            )
    if "json" in targets:
        tmp = targets["json"].with_name(targets["json"].name + ".tmp")
        try:
            tmp.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            tmp.replace(targets["json"])
        finally:
            if tmp.exists(): tmp.unlink()
    if "csv" in targets:
        tmp = targets["csv"].with_name(targets["csv"].name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                w.writeheader()
                w.writerows(iter_csv_rows(profile))
            tmp.replace(targets["csv"])
        finally:
            if tmp.exists(): tmp.unlink()
    return {
        "format": export_format.upper(), "output_dir": output_dir,
        "json_path": targets.get("json"), "csv_path": targets.get("csv"),
        "row_count": sum(len(x) for x in profile["results"].values()),
        "export_name": name, "source": profile["source"], "run_id": profile.get("run_id"),
    }

def render_export_summary(info):
    lines = [
        "="*90, "STEP 23 — PAIR PROFILE EXPORT COMPLETE", "="*90,
        f"Export name: {info['export_name']}", f"Format: {info['format']}",
        f"Profile rows represented: {info['row_count']}", f"Source: {info['source']}",
        f"Output directory: {info['output_dir']}",
    ]
    if info.get("json_path") is not None: lines.append(f"JSON: {info['json_path']}")
    if info.get("csv_path") is not None: lines.append(f"CSV: {info['csv_path']}")
    lines += [
        "Export preserves the STEP 23 profile view and does not recalculate py-ard reductions.",
        "="*90,
    ]
    return "\n".join(lines)
