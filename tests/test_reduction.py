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


@unittest.skipUnless(hla.pyard is not None, "py-ard не е инсталиран в тази среда")
class TestPyardIntegration(unittest.TestCase):
    """Интеграционни тестове срещу IPD-IMGT/HLA 3.65.0 чрез py-ard."""

    def test_current_donor_profile_is_valid(self):
        self.assertTrue(
            hla.validate_person(hla.donor_raw, "DONOR")
        )

    def test_current_recipient_profile_is_valid(self):
        self.assertTrue(
            hla.validate_person(hla.recipient_raw, "RECIPIENT")
        )

    def test_hla_prefix_is_accepted(self):
        self.assertEqual(
            hla.validate_allele("A", "HLA-A*02:01"),
            "A*02:01",
        )

    def test_invalid_allele_is_rejected(self):
        with self.assertRaises(ValueError):
            hla.validate_allele("A", "A*99:99")

    def test_high_resolution_a_reduces_to_lgx(self):
        self.assertEqual(
            hla.normalize_allele("A", "A*02:01:01:01"),
            "A*02:01",
        )

    def test_c_05_03_reduces_to_c_05_01_lgx(self):
        self.assertEqual(
            hla.normalize_allele("C", "C*05:03"),
            "C*05:01",
        )

    def test_c_05_01_and_c_05_03_have_same_g_group(self):
        ard = hla.get_ard()

        self.assertEqual(
            ard.redux("C*05:01", "G"),
            ard.redux("C*05:03", "G"),
        )

    def test_c_05_01_and_c_05_03_have_same_p_group(self):
        ard = hla.get_ard()

        self.assertEqual(
            ard.redux("C*05:01", "P"),
            ard.redux("C*05:03", "P"),
        )

    def test_original_and_lgx_comparison_can_differ(self):
        donor_c = ["C*07:02", "C*05:01"]
        recipient_c = ["C*07:05", "C*05:03"]

        original = hla.compare_locus(
            donor_c,
            recipient_c,
        )

        donor_lgx = [
            hla.normalize_allele("C", allele)
            for allele in donor_c
        ]
        recipient_lgx = [
            hla.normalize_allele("C", allele)
            for allele in recipient_c
        ]

        lgx = hla.compare_locus(
            donor_lgx,
            recipient_lgx,
        )

        self.assertEqual(original["shared_count"], 0)
        self.assertEqual(original["mismatch_count"], 2)
        self.assertEqual(lgx["shared_count"], 1)
        self.assertEqual(lgx["mismatch_count"], 1)
