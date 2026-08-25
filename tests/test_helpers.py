import copy
import hla_match as hla


def make_test_bundle(prefix=""):
    """Precomputed database-layer bundle; does not require py-ard."""
    raw = {
        "A": [f"{prefix}A*02:01", "A*24:02"],
        "B": ["B*07:02", "B*44:02"],
        "C": ["C*07:02", "C*05:01"],
        "DRB1": ["DRB1*15:01", "DRB1*04:01"],
        "DQB1": ["DQB1*06:02", "DQB1*03:02"],
        "DPB1": ["DPB1*04:01", "DPB1*02:01"],
    }

    canonical = {
        locus: [value.strip() for value in values]
        for locus, values in raw.items()
    }

    return {
        "raw": raw,
        "canonical": canonical,
        "lgx": copy.deepcopy(canonical),
        "G": copy.deepcopy(canonical),
        "P": copy.deepcopy(canonical),
    }


def make_comparison_results(
    donor_bundle,
    recipient_bundle,
):
    return hla.build_comparison_results_from_bundles(
        donor_bundle,
        recipient_bundle,
    )
