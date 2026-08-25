from collections import Counter

from config import HLA_LOCI


def compare_locus(donor_alleles, recipient_alleles):
    """
    Copy-sensitive multiset сравнение.
    Запазва повторенията при хомозиготност.
    """
    donor_counter = Counter(donor_alleles)
    recipient_counter = Counter(recipient_alleles)

    shared_counter = donor_counter & recipient_counter
    donor_only_counter = donor_counter - recipient_counter
    recipient_only_counter = recipient_counter - donor_counter

    shared = sorted(shared_counter.elements())
    donor_only = sorted(donor_only_counter.elements())
    recipient_only = sorted(recipient_only_counter.elements())

    return {
        "shared": shared,
        "donor_only": donor_only,
        "recipient_only": recipient_only,
        "shared_count": sum(shared_counter.values()),
        "mismatch_count": sum(donor_only_counter.values()),
        "recipient_only_count": sum(recipient_only_counter.values()),
    }


def build_comparison_results_from_bundles(
    donor_bundle,
    recipient_bundle,
):
    """
    Изчислява 4 × 6 comparison results от вече записаните
    CANONICAL/LGX/G/P представяния.
    """
    results = {
        "canonical": {},
        "lgx": {},
        "G": {},
        "P": {},
    }

    bundle_keys = {
        "canonical": "canonical",
        "lgx": "lgx",
        "G": "G",
        "P": "P",
    }

    for result_key, bundle_key in bundle_keys.items():
        for locus in HLA_LOCI:
            results[result_key][locus] = compare_locus(
                donor_bundle[bundle_key][locus],
                recipient_bundle[bundle_key][locus],
            )

    return results
