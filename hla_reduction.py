from config import HLA_LOCI
from hla_validation import (
    get_ard,
    validate_allele,
    canonicalize_person,
)


def normalize_allele(expected_locus, allele):
    """Валидира и редуцира един алел до lgx / 2-field ARD ниво."""
    allele = validate_allele(expected_locus, allele)
    return get_ard().redux(allele, "lgx")


def normalize_person(person):
    """
    Съвместима функция от предишните стъпки.
    Първо canonicalize-ва профила, после го редуцира до lgx.
    """
    canonical = canonicalize_person(person)
    return reduce_person(canonical, "lgx")


def reduce_person(canonical_person, mode):
    """
    Редуцира canonical HLA профил до избрано py-ard ниво.

    В Step 11 тази функция трябва да получава canonical, а не RAW профил.
    """
    reduced = {}

    for locus in HLA_LOCI:
        reduced[locus] = [
            get_ard().redux(allele, mode)
            for allele in canonical_person[locus]
        ]

    return reduced


def show_allele_reductions(raw_allele, canonical_allele):
    """Показва RAW -> CANONICAL -> lgx / G / P за един алел."""
    print(f"Raw:       {raw_allele}")
    print(f"Canonical: {canonical_allele}")

    lgx = get_ard().redux(canonical_allele, "lgx")
    print(f"lgx:       {lgx}")

    g_group = get_ard().redux(canonical_allele, "G")
    print(f"G group:   {g_group}")

    p_group = get_ard().redux(canonical_allele, "P")
    print(f"P group:   {p_group}")

    print()


def show_person_reductions(title, raw_person, canonical_person):
    """Показва RAW/CANONICAL и редукциите за целия профил."""
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    for locus in HLA_LOCI:
        print()
        print(f"HLA-{locus}")
        print("-" * 78)

        for raw_allele, canonical_allele in zip(
            raw_person[locus],
            canonical_person[locus],
        ):
            show_allele_reductions(raw_allele, canonical_allele)
