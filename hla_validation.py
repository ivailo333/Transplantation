from config import HLA_LOCI, IMGTHLA_VERSION, PYARD_DATA_DIR

try:
    import pyard
except ModuleNotFoundError:
    pyard = None

_ard = None


def get_ard():
    """Инициализира py-ard еднократно и връща ARD обекта."""
    global _ard

    if _ard is None:
        if pyard is None:
            raise RuntimeError(
                "Пакетът pyard не е инсталиран. "
                "Инсталирайте го с: pip install py-ard"
            )

        _ard = pyard.init(
            IMGTHLA_VERSION,
            data_dir=PYARD_DATA_DIR,
            load_mac=False,
        )

    return _ard


def clean_allele(allele):
    """Премахва интервали и незадължителния HLA- префикс."""
    if not isinstance(allele, str):
        raise ValueError(
            f"HLA алелът трябва да бъде текст, а е {type(allele).__name__}."
        )

    allele = allele.strip()

    if allele.startswith("HLA-"):
        allele = allele[4:]

    return allele


def validate_allele(expected_locus, allele):
    """Валидира един HLA алел и връща canonical текстовото му означение."""
    allele = clean_allele(allele)

    if "*" not in allele:
        raise ValueError(f"Невалиден HLA формат: {allele}")

    locus = allele.split("*", 1)[0]

    if locus != expected_locus:
        raise ValueError(
            f"Очакван локус {expected_locus}, но е въведен {allele}"
        )

    if not get_ard().is_valid_allele(allele):
        raise ValueError(f"HLA алелът не е валиден: {allele}")

    return allele


def validate_person(person, label):
    """Валидира структурата и всички HLA алели на донор/реципиент."""
    if not isinstance(person, dict):
        raise ValueError(f"{label}: HLA профилът трябва да бъде dict.")

    missing_loci = [locus for locus in HLA_LOCI if locus not in person]
    extra_loci = [locus for locus in person if locus not in HLA_LOCI]

    if missing_loci:
        raise ValueError(
            f"{label}: липсват HLA локуси: {', '.join(missing_loci)}"
        )

    if extra_loci:
        raise ValueError(
            f"{label}: непознати HLA локуси: {', '.join(extra_loci)}"
        )

    for locus in HLA_LOCI:
        alleles = person[locus]

        if not isinstance(alleles, (list, tuple)):
            raise ValueError(
                f"{label} HLA-{locus}: очаква се списък/кортеж с 2 алела."
            )

        if len(alleles) != 2:
            raise ValueError(
                f"{label} HLA-{locus}: трябва да съдържа точно 2 алела."
            )

        for allele in alleles:
            validate_allele(locus, allele)

    return True


def canonicalize_person(person, label="PERSON"):
    """
    Валидира RAW HLA профила и връща НОВ canonical профил.

    RAW профилът не се модифицира.
    """
    validate_person(person, label)

    canonical = {}

    for locus in HLA_LOCI:
        canonical[locus] = [
            validate_allele(locus, allele)
            for allele in person[locus]
        ]

    return canonical
