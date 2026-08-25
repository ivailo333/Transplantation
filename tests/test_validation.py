import copy
import csv
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
import unittest
from unittest.mock import patch

import hla_match as hla
import database as database
import exporters as exporters
import migrations as migrations

from test_helpers import make_test_bundle, make_comparison_results


class TestInputStructure(unittest.TestCase):
    """Структурни тестове, които не изискват реална HLA база."""

    def test_clean_allele_removes_spaces_and_hla_prefix(self):
        self.assertEqual(
            hla.clean_allele("  HLA-A*02:01  "),
            "A*02:01",
        )

    def test_raw_aliases_point_to_raw_profiles(self):
        self.assertIs(hla.donor, hla.donor_raw)
        self.assertIs(hla.recipient, hla.recipient_raw)

    def test_wrong_locus_raises_value_error(self):
        with self.assertRaises(ValueError):
            hla.validate_allele("A", "B*07:02")

    def test_missing_locus_raises_value_error(self):
        person = dict(hla.donor_raw)
        del person["DPB1"]

        with self.assertRaises(ValueError):
            hla.validate_person(person, "TEST")

    def test_extra_locus_raises_value_error(self):
        person = dict(hla.donor_raw)
        person["XYZ"] = ["XYZ*01:01", "XYZ*01:02"]

        with self.assertRaises(ValueError):
            hla.validate_person(person, "TEST")

    def test_wrong_container_type_raises_value_error(self):
        person = dict(hla.donor_raw)
        person["A"] = "A*02:01"

        with self.assertRaises(ValueError):
            hla.validate_person(person, "TEST")

    def test_wrong_allele_count_raises_value_error(self):
        person = dict(hla.donor_raw)
        person["A"] = ["A*02:01"]

        with self.assertRaises(ValueError):
            hla.validate_person(person, "TEST")

    def test_non_string_allele_is_rejected(self):
        with self.assertRaises(ValueError):
            hla.clean_allele(12345)


class TestStep11RawCanonical(unittest.TestCase):
    """Нови тестове специално за STEP 11 RAW -> CANONICAL."""

    @unittest.skipUnless(
        hla.pyard is not None,
        "py-ard не е инсталиран в тази среда",
    )
    def test_canonicalize_removes_prefix_and_spaces(self):
        raw = copy.deepcopy(hla.donor_raw)
        raw["A"][0] = "  HLA-A*02:01:01:01  "
        raw["A"][1] = " HLA-A*24:02 "

        canonical = hla.canonicalize_person(
            raw,
            "TEST",
        )

        self.assertEqual(
            canonical["A"],
            ["A*02:01:01:01", "A*24:02"],
        )

    @unittest.skipUnless(
        hla.pyard is not None,
        "py-ard не е инсталиран в тази среда",
    )
    def test_canonicalization_does_not_mutate_raw_input(self):
        raw = copy.deepcopy(hla.donor_raw)
        raw["A"][0] = "  HLA-A*02:01:01:01  "
        original_raw = copy.deepcopy(raw)

        hla.canonicalize_person(
            raw,
            "TEST",
        )

        self.assertEqual(
            raw,
            original_raw,
        )

    @unittest.skipUnless(
        hla.pyard is not None,
        "py-ard не е инсталиран в тази среда",
    )
    def test_canonical_profile_is_a_separate_structure(self):
        canonical = hla.canonicalize_person(
            hla.donor_raw,
            "DONOR",
        )

        self.assertIsNot(
            canonical,
            hla.donor_raw,
        )

        for locus in hla.HLA_LOCI:
            self.assertIsNot(
                canonical[locus],
                hla.donor_raw[locus],
            )

    @unittest.skipUnless(
        hla.pyard is not None,
        "py-ard не е инсталиран в тази среда",
    )
    def test_canonicalization_does_not_perform_lgx_reduction(self):
        canonical = hla.canonicalize_person(
            hla.donor_raw,
            "DONOR",
        )

        # Canonical пази пълното валидно име.
        self.assertEqual(
            canonical["A"][0],
            "A*02:01:01:01",
        )

        # lgx е отделна следваща операция.
        lgx = hla.reduce_person(
            canonical,
            "lgx",
        )

        self.assertEqual(
            lgx["A"][0],
            "A*02:01",
        )

    @unittest.skipUnless(
        hla.pyard is not None,
        "py-ard не е инсталиран в тази среда",
    )
    def test_formatting_only_differences_disappear_at_canonical_level(self):
        donor_raw = copy.deepcopy(hla.donor_raw)
        recipient_raw = copy.deepcopy(hla.donor_raw)

        donor_raw["A"] = [
            " HLA-A*02:01:01:01 ",
            "A*24:02",
        ]

        recipient_raw["A"] = [
            "A*02:01:01:01",
            " HLA-A*24:02 ",
        ]

        donor_canonical = hla.canonicalize_person(
            donor_raw,
            "DONOR_TEST",
        )
        recipient_canonical = hla.canonicalize_person(
            recipient_raw,
            "RECIPIENT_TEST",
        )

        raw_result = hla.compare_locus(
            donor_raw["A"],
            recipient_raw["A"],
        )
        canonical_result = hla.compare_locus(
            donor_canonical["A"],
            recipient_canonical["A"],
        )

        # RAW текстовете се различават по форматиране.
        self.assertEqual(
            raw_result["shared_count"],
            0,
        )

        # След canonicalization те са точно същите два алела.
        self.assertEqual(
            canonical_result["shared_count"],
            2,
        )
        self.assertEqual(
            canonical_result["mismatch_count"],
            0,
        )
        self.assertEqual(
            canonical_result["recipient_only_count"],
            0,
        )

    @unittest.skipUnless(
        hla.pyard is not None,
        "py-ard не е инсталиран в тази среда",
    )
    def test_reductions_use_canonical_values(self):
        raw = copy.deepcopy(hla.recipient_raw)
        raw["C"][1] = "  HLA-C*05:03  "

        canonical = hla.canonicalize_person(
            raw,
            "TEST",
        )

        self.assertEqual(
            canonical["C"][1],
            "C*05:03",
        )

        lgx = hla.reduce_person(
            canonical,
            "lgx",
        )

        self.assertEqual(
            lgx["C"][1],
            "C*05:01",
        )
